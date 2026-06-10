"""
Agentic RAG State Machine using LangGraph.
Implements: retrieve → evaluate → self-correct → tool-call → synthesize loop.
"""

from typing import TypedDict, List, Dict, Any, Annotated
import operator
import json
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from loguru import logger

from app.config import get_settings
from app.rag.reranker import retrieve_and_rerank, build_optimized_context
from app.tools.biomedical_tools import search_pubmed, search_uniprot, search_open_targets


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent.parent.parent / "system_prompt.txt"
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.warning("system_prompt.txt not found at %s, using fallback", prompt_path)
        return (
            "You are an expert biomedical research assistant. "
            "Answer the user's query using ONLY the provided evidence. "
            "Be specific, cite sources, and clearly state if evidence is limited."
        )

SYSTEM_PROMPT = _load_system_prompt()

settings = get_settings()

llm = ChatGoogleGenerativeAI(
    model=settings.google_model,
    google_api_key=settings.google_api_key,
    temperature=0,
    transport="rest",
)


# ── Agent State ───────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    query: str
    retrieved_docs: List[Dict[str, Any]]
    pubmed_results: List[Dict[str, Any]]
    uniprot_results: List[Dict[str, Any]]
    open_targets_results: List[Dict[str, Any]]
    evaluation: str          # "sufficient" | "insufficient" | "needs_tools"
    self_correction_count: int
    reasoning_steps: Annotated[List[str], operator.add]
    final_answer: str
    sources: List[str]


# ── Node Functions ────────────────────────────────────────────────────────────

def retrieve_node(state: AgentState) -> AgentState:
    """Retrieve and rerank chunks: vector search then FlashRank cross-encoder."""
    logger.info(f"[RETRIEVE] Query: {state['query'][:80]}")
    docs = retrieve_and_rerank(state["query"], initial_k=15, final_k=5)
    state["retrieved_docs"] = docs
    state["reasoning_steps"] = [
        f"Retrieved {len(docs)} chunks (vector search + FlashRank reranked) from knowledge base."
    ]
    return state


def evaluate_node(state: AgentState) -> AgentState:
    """
    Evaluate whether retrieved docs are sufficient to answer the query,
    or if external biomedical API tools are needed.
    """
    docs_summary = "\n".join([f"- {d['content'][:200]}" for d in state["retrieved_docs"]])

    prompt = f"""You are a biomedical research evaluator.

User query: {state['query']}

Retrieved document chunks:
{docs_summary if docs_summary else 'No documents retrieved.'}

Evaluate the retrieved information. Respond with ONLY a JSON object:
{{
  "evaluation": "sufficient" | "insufficient" | "needs_tools",
  "reason": "brief explanation",
  "tools_needed": ["pubmed", "uniprot", "open_targets"]   // only if needs_tools
}}

- "sufficient": docs fully answer the query
- "insufficient": docs are unrelated or empty — needs self-correction with rephrased query
- "needs_tools": docs are partial — supplement with biomedical APIs
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        result = json.loads(response.content.strip().strip("```json").strip("```"))
        state["evaluation"] = result.get("evaluation", "needs_tools")
        state["reasoning_steps"] = [f"Evaluation: {result.get('evaluation')} — {result.get('reason')}"]
    except Exception:
        state["evaluation"] = "needs_tools"
        state["reasoning_steps"] = ["Evaluation parsing failed — defaulting to tool use."]

    logger.info(f"[EVALUATE] Result: {state['evaluation']}")
    return state


def self_correct_node(state: AgentState) -> AgentState:
    """Rephrase query and re-retrieve when initial retrieval is insufficient."""
    count = state.get("self_correction_count", 0) + 1
    state["self_correction_count"] = count

    prompt = f"""The initial retrieval for this biomedical query was insufficient.
Original query: {state['query']}
Rephrase it using biomedical terminology to improve retrieval. Return ONLY the rephrased query, nothing else."""

    response = llm.invoke([HumanMessage(content=prompt)])
    new_query = response.content.strip()
    state["reasoning_steps"] = [f"Self-correction #{count}: rephrased query to '{new_query[:100]}'"]
    logger.info(f"[SELF-CORRECT] Attempt {count}: {new_query[:80]}")

    docs = retrieve_and_rerank(new_query, initial_k=15, final_k=5)
    state["retrieved_docs"] = docs
    state["evaluation"] = "needs_tools" if docs else "insufficient"
    return state


def tool_call_node(state: AgentState) -> AgentState:
    """Determine which biomedical APIs to call and execute them."""
    prompt = f"""Given this biomedical research query, extract the key entities.
Query: {state['query']}
Return ONLY JSON:
{{
  "genes": ["BRCA1"],
  "diseases": ["breast cancer"],
  "search_terms": ["BRCA1 breast cancer mutation"]
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        entities = json.loads(response.content.strip().strip("```json").strip("```"))
    except Exception:
        entities = {"genes": [], "diseases": [], "search_terms": [state["query"]]}

    steps = []

    # PubMed search
    for term in entities.get("search_terms", [])[:2]:
        results = search_pubmed(term, max_results=3)
        state["pubmed_results"] = results
        steps.append(f"PubMed: fetched {len(results)} articles for '{term}'")

    # UniProt search
    for gene in entities.get("genes", [])[:2]:
        results = search_uniprot(gene)
        state["uniprot_results"] = results
        steps.append(f"UniProt: fetched {len(results)} protein entries for gene '{gene}'")

    # Open Targets search
    for disease in entities.get("diseases", [])[:1]:
        results = search_open_targets(disease)
        state["open_targets_results"] = results
        steps.append(f"Open Targets: fetched {len(results)} drug-gene associations for '{disease}'")

    state["reasoning_steps"] = steps
    return state


def synthesize_node(state: AgentState) -> AgentState:
    """Synthesize all evidence into a final grounded, token-optimized answer."""
    local_context = build_optimized_context(state.get("retrieved_docs", []), max_total_tokens=2000)
    pubmed_context = "\n".join([
        f"[PubMed {a['year']}] {a['title']}: {a['abstract'][:300]}"
        for a in state.get("pubmed_results", [])
    ])
    uniprot_context = "\n".join([
        f"[UniProt] Gene {r['gene']}: {r['protein_name']} — {'; '.join(r['functions'])}"
        for r in state.get("uniprot_results", [])
    ])
    ot_context = "\n".join([
        f"[Open Targets] {r['gene_symbol']} associated with {r['disease']} (score: {r['association_score']})"
        for r in state.get("open_targets_results", [])
    ])

    all_context = "\n\n".join(filter(None, [local_context, pubmed_context, uniprot_context, ot_context]))

    user = f"""Query: {state['query']}

Evidence:
{all_context if all_context else 'No evidence retrieved.'}

Reasoning steps taken:
{chr(10).join(state.get('reasoning_steps', []))}

Provide a comprehensive, grounded answer following the required format."""

    response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user)])
    state["final_answer"] = response.content

    sources = list(set(
        [d.get("source", "") for d in state.get("retrieved_docs", [])] +
        [a.get("url", "") for a in state.get("pubmed_results", [])]
    ))

    # Deduplicate sources by PMID
    seen_pmids: set = set()
    deduped: list = []
    for s in sources:
        key = s
        if "pubmed.ncbi.nlm.nih.gov" in s:
            pmid = s.rstrip("/").rsplit("/", 1)[-1]
            key = pmid
            if pmid in seen_pmids:
                continue
        if key not in seen_pmids:
            seen_pmids.add(key)
            deduped.append(s)
    state["sources"] = [s for s in deduped if s]
    logger.success("[SYNTHESIZE] Final answer generated.")
    return state


# ── Routing Logic ─────────────────────────────────────────────────────────────

def route_after_evaluate(state: AgentState) -> str:
    evaluation = state.get("evaluation", "needs_tools")
    corrections = state.get("self_correction_count", 0)

    if evaluation == "sufficient":
        return "synthesize"
    elif evaluation == "insufficient" and corrections < settings.self_correction_attempts:
        return "self_correct"
    else:
        return "tool_call"


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_agent() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("self_correct", self_correct_node)
    graph.add_node("tool_call", tool_call_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges("evaluate", route_after_evaluate, {
        "synthesize": "synthesize",
        "self_correct": "self_correct",
        "tool_call": "tool_call",
    })
    graph.add_edge("self_correct", "evaluate")
    graph.add_edge("tool_call", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


def run_agent(query: str, offline: bool = False) -> Dict[str, Any]:
    """Run the full agentic RAG pipeline for a biomedical query.
    
    When offline=True, skips LLM calls and returns raw retrieval results.
    Used by evaluation fallback when API quota is exhausted.
    """
    from app.rag.reranker import retrieve_and_rerank
    
    if offline:
        docs = retrieve_and_rerank(query, initial_k=10, final_k=5)
        return {
            "query": query,
            "answer": "",
            "sources": [d.get("source", "") for d in docs],
            "reasoning_steps": ["Offline mode: retrieval only (no LLM synthesis)"],
            "self_corrections": 0,
            "pubmed_count": 0,
            "local_docs_count": len(docs),
            "retrieved_docs": docs,
        }
    
    agent = build_agent()
    initial_state: AgentState = {
        "query": query,
        "retrieved_docs": [],
        "pubmed_results": [],
        "uniprot_results": [],
        "open_targets_results": [],
        "evaluation": "",
        "self_correction_count": 0,
        "reasoning_steps": [],
        "final_answer": "",
        "sources": [],
    }
    result = agent.invoke(initial_state)
    return {
        "query": result["query"],
        "answer": result["final_answer"],
        "sources": result["sources"],
        "reasoning_steps": result["reasoning_steps"],
        "self_corrections": result["self_correction_count"],
        "pubmed_count": len(result["pubmed_results"]),
        "local_docs_count": len(result["retrieved_docs"]),
        "retrieved_docs": result["retrieved_docs"],
    }
