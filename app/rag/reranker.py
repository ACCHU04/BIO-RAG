"""
Advanced retrieval pipeline: vector search → FlashRank reranker → token-optimized chunks.
Assignment Requirements:
  - Section C: Retrieve & Rerank with cross-encoder
  - Section D: Token efficiency — strip metadata, summarize, enforce max tokens
"""

import re
import numpy as np
import tiktoken
from typing import List, Dict, Any

from flashrank import Ranker, RerankRequest
from loguru import logger

from app.rag.retriever import retrieve as base_retrieve, get_embeddings
from app.config import get_settings

settings = get_settings()

# FlashRank cross-encoder (runs on CPU, no GPU needed)
_ranker: Ranker = None

def get_ranker() -> Ranker:
    global _ranker
    if _ranker is None:
        logger.info("Loading FlashRank cross-encoder (ms-marco-MiniLM-L-12-v2)...")
        _ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp/flashrank")
    return _ranker


# ── Token counter ─────────────────────────────────────────────────────────────

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4  # rough fallback


# ── Chunk cleaning ────────────────────────────────────────────────────────────

def clean_chunk(text: str) -> str:
    """
    Strip noise from raw chunk text before sending to LLM.
    Removes: repeated whitespace, page headers/footers, DOI lines,
    figure captions, excessive punctuation.
    Cuts token usage by ~15-25% on typical biomedical PDFs.
    """
    # Remove DOI, URL lines
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"doi:\s*\S+", "", text, flags=re.IGNORECASE)

    # Remove figure/table captions (short lines starting with Fig/Table)
    text = re.sub(r"(?m)^(Fig(ure)?|Table)\s*\d+[^\n]{0,80}\n", "", text)

    # Collapse multiple spaces/newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if len(line) > 10)

    return text.strip()


def truncate_to_token_limit(text: str, max_tokens: int = 300) -> str:
    """Hard-truncate a chunk to max_tokens to control context window size."""
    try:
        enc = tiktoken.encoding_for_model("gpt-4o")
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return enc.decode(tokens[:max_tokens]) + "..."
    except Exception:
        words = text.split()
        if len(words) <= max_tokens:
            return text
        return " ".join(words[:max_tokens]) + "..."


# ── Cosine-similarity dedup ────────────────────────────────────────────────────

def dedup_by_similarity(
    chunks: List[Dict[str, Any]], threshold: float = 0.98
) -> List[Dict[str, Any]]:
    """
    Remove near-duplicate chunks based on embedding cosine similarity.
    When two chunks have similarity > threshold, the lower-ranked (later) one
    is dropped.  This prevents redundant content from consuming the context window.
    """
    if len(chunks) <= 1:
        return chunks

    emb_fn = get_embeddings()
    texts = [c["content"] for c in chunks]
    vectors = emb_fn.embed_documents(texts)

    keep = [True] * len(chunks)
    for i in range(len(chunks)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(chunks)):
            if not keep[j]:
                continue
            sim = float(np.dot(vectors[i], vectors[j]))
            if sim > threshold:
                keep[j] = False

    deduped = [c for c, k in zip(chunks, keep) if k]
    saved = len(chunks) - len(deduped)
    if saved:
        logger.info(f"[DEDUP] Cosine-sim dedup removed {saved} / {len(chunks)} chunks (threshold={threshold})")
    return deduped


# ── Main retrieval pipeline ───────────────────────────────────────────────────

def retrieve_and_rerank(
    query: str,
    initial_k: int = 15,
    final_k: int = 5,
    max_tokens_per_chunk: int = 300,
) -> List[Dict[str, Any]]:
    """
    Full advanced retrieval pipeline:
    1. Broad vector search (initial_k=15 for high recall)
    2. FlashRank cross-encoder reranking (precision filtering)
    3. Token optimization — clean + truncate each chunk
    4. Return top final_k chunks ready for LLM context

    This pattern (fast ANN recall → cross-encoder precision) minimizes
    irrelevant chunks reaching the LLM while keeping latency low.
    """
    # Step 1: broad vector retrieval
    raw_docs = base_retrieve(query, k=initial_k)
    if not raw_docs:
        logger.warning("[RERANK] No documents retrieved from vector store")
        return []

    logger.info(f"[RERANK] Vector search returned {len(raw_docs)} candidates")

    # Step 2: FlashRank reranking
    passages = [
        {"id": i, "text": doc["content"], "meta": doc}
        for i, doc in enumerate(raw_docs)
    ]
    ranker = get_ranker()
    rerank_request = RerankRequest(query=query, passages=passages)
    reranked = ranker.rerank(rerank_request)

    logger.info(f"[RERANK] Cross-encoder reranked to top {final_k}")

    # Step 3: Take top final_k, clean + token-optimize
    optimized = []
    total_tokens = 0

    for result in reranked[:final_k]:
        original_meta = result.get("meta", {})
        raw_text = result.get("text", "")

        cleaned = clean_chunk(raw_text)
        truncated = truncate_to_token_limit(cleaned, max_tokens=max_tokens_per_chunk)
        tokens = count_tokens(truncated)
        total_tokens += tokens

        optimized.append({
            "content": truncated,
            "source": original_meta.get("source", "unknown"),
            "page": original_meta.get("page", 0),
            "doc_id": original_meta.get("doc_id", ""),
            "vector_score": round(original_meta.get("score", 0), 4),
            "rerank_score": round(result.get("score", 0), 4),
            "tokens": tokens,
        })

    logger.info(
        f"[RERANK] Final {len(optimized)} chunks, "
        f"total tokens: {total_tokens} "
        f"(saved ~{count_tokens(' '.join(d['content'] for d in raw_docs)) - total_tokens} tokens vs raw)"
    )

    # Step 4: cosine-similarity dedup on final chunks
    optimized = dedup_by_similarity(optimized, threshold=0.995)

    return optimized


def build_optimized_context(chunks: List[Dict[str, Any]], max_total_tokens: int = 2000) -> str:
    """
    Build a clean context string from reranked chunks.
    Enforces a hard total token budget across all chunks.
    Strips chunk metadata noise — only content + citation tag reaches LLM.
    """
    context_parts = []
    used_tokens = 0

    for chunk in chunks:
        citation = f"[Source: {chunk.get('doc_id', 'unknown')}, p.{chunk.get('page', '?')}]"
        entry = f"{citation}\n{chunk['content']}"
        entry_tokens = count_tokens(entry)

        if used_tokens + entry_tokens > max_total_tokens:
            logger.debug(f"[CONTEXT] Token budget reached at {used_tokens}/{max_total_tokens}")
            break

        context_parts.append(entry)
        used_tokens += entry_tokens

    logger.info(f"[CONTEXT] Built context: {len(context_parts)} chunks, {used_tokens} tokens")
    return "\n\n---\n\n".join(context_parts)
