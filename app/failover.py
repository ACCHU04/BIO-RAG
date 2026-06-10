"""
Graceful degradation — API failover handler.
Assignment Requirement: Section F — Resiliency & API Failover.

If the primary LLM API (OpenAI) fails for any reason (timeout, rate limit,
authentication error, service outage), the system must NOT crash.
Instead it falls back to returning the raw retrieved chunks directly to the
user with a clear warning message.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import time

from loguru import logger
import google.api_core.exceptions


class FailureReason(str, Enum):
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    TIMEOUT = "timeout"
    SERVICE_ERROR = "service_error"
    UNKNOWN = "unknown"


def classify_google_error(error: Exception) -> FailureReason:
    """Classify the type of Google API failure for logging and response."""
    error_msg = str(error).lower()

    if isinstance(error, google.api_core.exceptions.ResourceExhausted):
        return FailureReason.RATE_LIMIT
    elif isinstance(error, google.api_core.exceptions.PermissionDenied):
        return FailureReason.AUTH_ERROR
    elif isinstance(error, google.api_core.exceptions.DeadlineExceeded):
        return FailureReason.TIMEOUT
    elif isinstance(error, google.api_core.exceptions.ServiceUnavailable):
        return FailureReason.SERVICE_ERROR
    elif isinstance(error, google.api_core.exceptions.GoogleAPIError):
        return FailureReason.SERVICE_ERROR
    elif "timeout" in error_msg or "timed out" in error_msg:
        return FailureReason.TIMEOUT
    elif "rate" in error_msg and "limit" in error_msg:
        return FailureReason.RATE_LIMIT
    return FailureReason.UNKNOWN


def build_fallback_response(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    pubmed_results: List[Dict[str, Any]],
    failure_reason: FailureReason,
    latency: float,
) -> Dict[str, Any]:
    """
    Build a partial RAG response from raw retrieved chunks.
    This is the fallback when LLM synthesis is unavailable.
    The user still gets the evidence — just not the AI synthesis.
    """
    # Format raw chunks as readable fallback answer
    from collections import defaultdict
    doc_groups = defaultdict(list)
    for chunk in retrieved_chunks:
        source = chunk.get("source", "unknown")
        doc_groups[source].append(chunk)

    fallback_parts = []

    if doc_groups:
        fallback_parts.append(f"### Evidence Retrieved for: {query}")
        fallback_parts.append("")
        for source, chunks in doc_groups.items():
            doc_name = source.split("\\")[-1].split("/")[-1]
            fallback_parts.append(f"**Source:** {doc_name}")
            for chunk in chunks:
                fallback_parts.append(f"> {chunk.get('content', '')}")
            fallback_parts.append("")
    else:
        fallback_parts.append("No local document chunks were retrieved for this query.")
        fallback_parts.append("")

    if pubmed_results:
        fallback_parts.append("## PubMed References")
        for i, art in enumerate(pubmed_results, 1):
            title = art.get("title", "No title")
            year = art.get("year", "")
            abstract = art.get("abstract", "")[:400]
            url = art.get("url", "")
            fallback_parts.append(
                f"{i}. **{title}** ({year})\n"
                f"   *{abstract}*\n"
                f"   --- {url}"
            )
        fallback_parts.append("")

    fallback_answer = "\n".join(fallback_parts)

    sources = list(set(
        [c.get("source", "") for c in retrieved_chunks] +
        [a.get("url", "") for a in pubmed_results]
    ))

    logger.warning(f"[FAILOVER] Serving partial RAG response. Reason: {failure_reason.value}")

    return {
        "query": query,
        "answer": fallback_answer,
        "sources": [s for s in sources if s],
        "reasoning_steps": [
            f"AI synthesis unavailable ({failure_reason.value}). Showing curated evidence.",
        ],
        "self_corrections": 0,
        "pubmed_articles_used": len(pubmed_results),
        "local_docs_used": len(retrieved_chunks),
        "latency_seconds": round(latency, 2),
        "fallback": True,
        "failure_reason": failure_reason.value,
    }


def run_agent_with_failover(query: str) -> Dict[str, Any]:
    """
    Run the full agentic pipeline with automatic failover.
    On any LLM API failure, gracefully degrade to raw chunk response.
    """
    from app.agent.graph import run_agent
    from app.rag.reranker import retrieve_and_rerank
    from app.tools.biomedical_tools import search_pubmed

    start = time.time()

    try:
        # Primary path — full agentic RAG
        result = run_agent(query)
        result["fallback"] = False
        return result

    except google.api_core.exceptions.GoogleAPIError as e:
        failure_reason = classify_google_error(e)
        logger.error(f"[FAILOVER] Google API error ({failure_reason.value}): {e}")

    except Exception as e:
        failure_reason = FailureReason.UNKNOWN
        error_msg = str(e).lower()
        if "api" in error_msg or "gemini" in error_msg:
            failure_reason = classify_google_error(e)
        logger.error(f"[FAILOVER] Unexpected error: {e}")

    # Fallback path — retrieve without LLM synthesis
    logger.info("[FAILOVER] Attempting direct retrieval for partial response...")
    try:
        chunks = retrieve_and_rerank(query, initial_k=10, final_k=5)
    except Exception as retrieval_error:
        logger.error(f"[FAILOVER] Retrieval also failed: {retrieval_error}")
        chunks = []

    try:
        pubmed = search_pubmed(query, max_results=3)
    except Exception:
        pubmed = []

    latency = time.time() - start
    return build_fallback_response(query, chunks, pubmed, failure_reason, latency)
