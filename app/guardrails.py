"""
Security guardrails — input validation and output hallucination checking.
Assignment Requirement: Section E — Security & Guardrails.

Input guardrails:  block prompt injection, jailbreaks, out-of-scope queries.
Output guardrails: verify LLM answer is grounded in retrieved context.
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from app.config import get_settings

settings = get_settings()


@dataclass
class GuardrailResult:
    passed: bool
    reason: str
    severity: str  # "block" | "warn" | "ok"


# ── Input Guardrails ──────────────────────────────────────────────────────────

# Patterns that indicate prompt injection or jailbreak attempts
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now\s+(a\s+)?(\w+\s+)?ai",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if\s+you\s+are|a)",
    r"forget\s+(your|all)\s+(instructions|rules|constraints)",
    r"system\s*prompt\s*:",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"bypass\s+(safety|filter|guardrail)",
    r"</?(system|user|assistant)>",
    r"\[INST\]|\[\/INST\]",
    r"###\s*(instruction|system|human)",
]

# Patterns indicating clearly out-of-scope queries for a biomedical system
OUT_OF_SCOPE_PATTERNS = [
    r"\b(write\s+(code|script|program)|debug|programming)\b",
    r"\b(recipe|cook(ing)?|food)\b",
    r"\b(stock\s+price|cryptocurrency|bitcoin|invest(ment)?)\b",
    r"\b(weather|forecast|temperature)\b",
    r"\b(sports|football|basketball|cricket)\b",
]

MIN_QUERY_LENGTH = 5
MAX_QUERY_LENGTH = 2000


def check_input(query: str) -> GuardrailResult:
    """
    Validate a user query before it reaches the agent.
    Checks for: injection attempts, out-of-scope, length, empty input.
    """
    # Empty / too short
    if not query or len(query.strip()) < MIN_QUERY_LENGTH:
        return GuardrailResult(
            passed=False,
            reason="Query is too short or empty. Please provide a meaningful biomedical research question.",
            severity="block",
        )

    # Too long (potential token flooding attack)
    if len(query) > MAX_QUERY_LENGTH:
        return GuardrailResult(
            passed=False,
            reason=f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters.",
            severity="block",
        )

    query_lower = query.lower()

    # Prompt injection / jailbreak detection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            logger.warning(f"[GUARDRAIL INPUT] Injection pattern matched: '{pattern}' in query: '{query[:80]}'")
            return GuardrailResult(
                passed=False,
                reason="Your query contains instructions that attempt to manipulate the AI system. This has been blocked.",
                severity="block",
            )

    # Out-of-scope detection
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, query_lower):
            logger.info(f"[GUARDRAIL INPUT] Out-of-scope pattern matched: '{pattern}'")
            return GuardrailResult(
                passed=False,
                reason="This system is specialized for biomedical and life sciences research queries. Your question appears to be outside this domain.",
                severity="block",
            )

    logger.debug(f"[GUARDRAIL INPUT] Passed: '{query[:80]}'")
    return GuardrailResult(passed=True, reason="ok", severity="ok")


# ── Output Guardrails ─────────────────────────────────────────────────────────

def check_output(
    answer: str,
    retrieved_chunks: List[Dict[str, Any]],
    query: str,
) -> GuardrailResult:
    """
    Verify that the LLM's answer is grounded in the retrieved context.
    Uses a lightweight LLM call to check for hallucinated claims.

    Strategy:
    1. Extract specific factual claims from the answer.
    2. Check each claim against the retrieved chunks.
    3. Block or warn if unverified claims are detected.
    """
    if not answer or not answer.strip():
        return GuardrailResult(
            passed=False,
            reason="Empty answer received from LLM.",
            severity="block",
        )

    # If no context was retrieved, we can't verify — warn but don't block
    if not retrieved_chunks:
        return GuardrailResult(
            passed=True,
            reason="No retrieved context available for verification. Answer may be based on model knowledge only.",
            severity="warn",
        )

    context_text = "\n".join([c.get("content", "") for c in retrieved_chunks[:5]])

    # Skip LLM-based verification if answer is empty or is a fallback evidence dump
    if len(answer) < 50 or answer.startswith("### Evidence Retrieved"):
        return GuardrailResult(
            passed=True,
            reason="Answer is evidence-only display (fallback or offline). Skipping LLM verification.",
            severity="ok",
        )

    llm = ChatGoogleGenerativeAI(
        model=settings.google_model,
        google_api_key=settings.google_api_key,
        temperature=0,
        max_tokens=300,
        transport="rest",
    )

    system_prompt = """You are a strict hallucination detector for a biomedical RAG system.
Your job: determine if the given answer is grounded in the provided context.
Respond ONLY with JSON: {"grounded": true/false, "unverified_claims": ["claim1", "claim2"], "confidence": 0.0-1.0}
- grounded: true if all major factual claims in the answer can be traced to the context
- unverified_claims: list any specific claims NOT supported by context (empty list if grounded)
- confidence: your confidence in this assessment"""

    user_prompt = f"""Query: {query}

Retrieved context:
{context_text[:1500]}

Answer to verify:
{answer[:1000]}

Is this answer grounded in the context?"""

    try:
        import json
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        raw = response.content.strip().strip("```json").strip("```")
        result = json.loads(raw)

        is_grounded = result.get("grounded", True)
        unverified = result.get("unverified_claims", [])
        confidence = result.get("confidence", 1.0)

        if not is_grounded and unverified:
            claims_str = "; ".join(unverified[:3])
            logger.warning(f"[GUARDRAIL OUTPUT] Unverified claims detected: {claims_str}")
            return GuardrailResult(
                passed=False,
                reason=f"The answer contains claims not supported by retrieved evidence: {claims_str}. Please verify these independently.",
                severity="warn",  # warn rather than block — partial answers are still useful
            )

        if confidence < 0.6:
            return GuardrailResult(
                passed=True,
                reason=f"Answer appears grounded but verification confidence is low ({confidence:.0%}).",
                severity="warn",
            )

        logger.debug(f"[GUARDRAIL OUTPUT] Answer verified as grounded (confidence: {confidence:.0%})")
        return GuardrailResult(passed=True, reason="Answer is grounded in retrieved context.", severity="ok")

    except Exception as e:
        logger.error(f"[GUARDRAIL OUTPUT] Verification failed: {e}")
        # If verification itself fails, pass with a warning rather than block
        return GuardrailResult(
            passed=True,
            reason="Output verification could not be completed. Treat answer with caution.",
            severity="warn",
        )


def format_guardrail_response(result: GuardrailResult, query: str = "") -> Dict[str, Any]:
    """Format a blocked guardrail as a safe API response."""
    return {
        "query": query,
        "answer": result.reason,
        "blocked": True,
        "severity": result.severity,
        "sources": [],
        "reasoning_steps": [f"Guardrail triggered: {result.reason}"],
        "self_corrections": 0,
        "pubmed_articles_used": 0,
        "local_docs_used": 0,
        "latency_seconds": 0.0,
    }
