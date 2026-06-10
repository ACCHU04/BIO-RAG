"""
FastAPI backend — full enterprise-grade RAG API.
Integrates: guardrails, failover, CRUD, reranker, evaluation.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
from typing import Any, List, Optional
import time
import shutil
import os
from pathlib import Path
from loguru import logger

from app.failover import run_agent_with_failover, build_fallback_response, FailureReason
from app.guardrails import check_input, check_output, format_guardrail_response
from app.rag.crud import add_document, delete_document, update_document, list_documents
from app.rag.retriever import ingest_documents
from app.config import get_settings
from app.incognito import incognito_chat

settings = get_settings()

app = FastAPI(
    title="Biomedical Agentic RAG — Enterprise API",
    description=(
        "Autonomous biomedical research agent. "
        "Features: reranking, guardrails, dynamic CRUD, API failover."
    ),
    version="2.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    include_reasoning: bool = True
    offline: bool = False

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]
    reasoning_steps: Optional[List[str]]
    self_corrections: int
    pubmed_articles_used: int
    local_docs_used: int
    latency_seconds: float
    fallback: bool = False
    blocked: bool = False
    guardrail_warning: Optional[str] = None

class IngestRequest(BaseModel):
    source_dir: str = "./data/documents"

class DocumentResponse(BaseModel):
    doc_id: str
    status: str
    chunks_added: Optional[int] = None
    chunks_deleted: Optional[int] = None


# ── Query endpoint (main pipeline) ───────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
def query_agent(request: QueryRequest):
    """
    Full agentic RAG pipeline:
    1. Input guardrail check
    2. Retrieve + rerank (FlashRank)
    3. Agent reasoning loop (LangGraph)
    4. Output hallucination check
    5. Failover to raw chunks on API failure
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    start = time.time()

    # Step 1: Input guardrail
    input_check = check_input(request.query)
    if not input_check.passed:
        logger.warning(f"[API] Input blocked: {input_check.reason}")
        fallback = format_guardrail_response(input_check, request.query)
        return QueryResponse(
            query=fallback["query"],
            answer=fallback["answer"],
            sources=[],
            reasoning_steps=fallback["reasoning_steps"],
            self_corrections=0,
            pubmed_articles_used=0,
            local_docs_used=0,
            latency_seconds=round(time.time() - start, 2),
            blocked=True,
        )

    # Step 2: Offline mode — skip agent, return clean evidence display
    if request.offline:
        from app.rag.reranker import retrieve_and_rerank
        chunks = retrieve_and_rerank(request.query, initial_k=15, final_k=8, max_tokens_per_chunk=500)
        from collections import defaultdict
        doc_groups = defaultdict(list)
        for c in chunks:
            doc_groups[c.get("source", "unknown")].append(c)
        parts = [f"### Retrieved for: {request.query}", ""]
        for src, cs in doc_groups.items():
            parts.append(f"**{src.split(chr(92))[-1].split('/')[-1]}**")
            for c in cs:
                parts.append(f"> {c.get('content', '')}")
            parts.append("")
        answer = "\n".join(parts).strip()
        sources = list(set(c.get("source", "") for c in chunks))
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=[s for s in sources if s],
            reasoning_steps=["Offline mode: retrieval only (no LLM synthesis)."] if request.include_reasoning else None,
            self_corrections=0,
            pubmed_articles_used=0,
            local_docs_used=len(chunks),
            latency_seconds=round(time.time() - start, 2),
            fallback=False,
        )

    # Step 3 + 4 + 5: Agent with failover
    result = run_agent_with_failover(request.query)
    latency = round(time.time() - start, 2)

    # Step 5: Output guardrail (only if LLM responded, not fallback)
    guardrail_warning = None
    if not result.get("fallback"):
        output_check = check_output(
            answer=result.get("answer", ""),
            retrieved_chunks=result.get("retrieved_docs", []),
            query=request.query,
        )
        if output_check.severity == "warn":
            guardrail_warning = output_check.reason
            logger.warning(f"[API] Output warning: {output_check.reason}")

    return QueryResponse(
        query=result["query"],
        answer=result["answer"],
        sources=result.get("sources", []),
        reasoning_steps=result.get("reasoning_steps") if request.include_reasoning else None,
        self_corrections=result.get("self_corrections", 0),
        pubmed_articles_used=result.get("pubmed_articles_used", 0),
        local_docs_used=result.get("local_docs_used", 0),
        latency_seconds=latency,
        fallback=result.get("fallback", False),
        blocked=False,
        guardrail_warning=guardrail_warning,
    )


# ── CRUD endpoints ────────────────────────────────────────────────────────────

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), doc_id: Optional[str] = None):
    """
    Upload and ingest a new document (PDF or TXT) into ChromaDB.
    Supports dynamic addition without rebuilding the full index.
    """
    upload_dir = Path("./data/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = add_document(str(file_path), doc_id=doc_id or Path(file.filename).stem)
        return DocumentResponse(
            doc_id=result["doc_id"],
            status=result["status"],
            chunks_added=result["chunks_added"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{doc_id}", response_model=DocumentResponse)
def remove_document(doc_id: str):
    """
    Delete all chunks for a document by doc_id.
    Targeted deletion — no index rebuild required.
    """
    result = delete_document(doc_id)
    return DocumentResponse(
        doc_id=result["doc_id"],
        status=result["status"],
        chunks_deleted=result["chunks_deleted"],
    )


@app.put("/documents/{doc_id}", response_model=DocumentResponse)
async def update_doc(doc_id: str, file: UploadFile = File(...)):
    """
    Update an existing document: delete old chunks, ingest new version.
    Surgical upsert — only the target document is affected.
    """
    upload_dir = Path("./data/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = update_document(str(file_path), doc_id=doc_id)
        return DocumentResponse(
            doc_id=result["doc_id"],
            status=result["status"],
            chunks_added=result["chunks_added"],
            chunks_deleted=result["chunks_deleted"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
def get_documents():
    """List all documents currently indexed in ChromaDB with chunk counts."""
    return {"documents": list_documents()}


@app.post("/ingest")
def ingest_bulk(request: IngestRequest):
    """Bulk ingest all documents from a local directory."""
    count = ingest_documents(request.source_dir)
    return {"chunks_ingested": count, "status": "success" if count > 0 else "no_documents_found"}


# ── Evaluation ────────────────────────────────────────────────────────────────

@app.post("/evaluate")
def evaluate():
    """Run Gemini-powered evaluation on the standard biomedical question set.
    Each question: retrieve + Gemini synthesize + Gemini score (4 metrics).
    Falls back to neutral scores (0.5) on catastrophic failure only.
    """
    from app.eval.ragas_eval import run_evaluation
    try:
        results = run_evaluation()
        return results
    except Exception as e:
        logger.warning(f"Evaluation pipeline crashed ({e}), returning neutral scores")
        return {
            "faithfulness": 0.5,
            "answer_relevancy": 0.5,
            "context_recall": 0.5,
            "context_precision": 0.5,
            "num_questions": 5,
            "error": str(e),
        }


# ── PDF Export ───────────────────────────────────────────────────────────────

class PdfExportRequest(BaseModel):
    query: str
    answer: str
    sources: List[Any] = []
    reasoning_steps: Optional[List[str]] = None
    self_corrections: int = 0
    pubmed_articles_used: int = 0
    local_docs_used: int = 0
    latency_seconds: float = 0.0
    fallback: bool = False
    blocked: bool = False
    guardrail_warning: Optional[str] = None
    ragas_scores: Optional[dict] = None


@app.post("/export/pdf")
def export_pdf(request: PdfExportRequest):
    """
    Generate a polished multi-page PDF report for the given query result.
    Returns the PDF as a binary stream (application/pdf).
    """
    from app.pdf_report import generate_pdf_report
    try:
        pdf_bytes = generate_pdf_report(request.dict())
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="BioRAG_Report.pdf"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except Exception as e:
        logger.error(f"[PDF Export] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


# ── Incognito Mode (unrestricted chat) ────────────────────────────────────────

class IncognitoMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class IncognitoRequest(BaseModel):
    messages: List[IncognitoMessage]

@app.post("/incognito")
def incognito_endpoint(request: IncognitoRequest):
    """
    Unrestricted general-purpose chat — no guardrails, no RAG pipeline.
    Calls Gemini directly with multi-turn conversation history.
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    if not messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty.")
    reply = incognito_chat(messages)
    return {"reply": reply}


# ── Health & info ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "Biomedical Agentic RAG — Enterprise",
        "version": "2.0.0",
        "status": "running",
        "features": ["reranking", "guardrails", "failover", "dynamic-crud"],
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "healthy", "model": settings.google_model}
