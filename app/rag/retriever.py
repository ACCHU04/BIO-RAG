"""
RAG Pipeline — document ingestion, chunking, embedding, and retrieval.
Uses ChromaDB with biomedical-specific sentence embeddings.
"""

import os
from functools import cache
from pathlib import Path
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from loguru import logger

from app.config import get_settings

settings = get_settings()


@cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """Load biomedical-specific embedding model (cached after first load)."""
    logger.info(f"Loading embedding model: {settings.embedding_model}")
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vectorstore() -> Chroma:
    """Get or create ChromaDB vector store."""
    embeddings = get_embeddings()
    vectorstore = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_db_path,
    )
    logger.info(f"ChromaDB loaded from: {settings.chroma_db_path}")
    return vectorstore


def ingest_documents(source_dir: str = "./data/documents") -> int:
    """
    Ingest PDF and text documents from source_dir into ChromaDB.
    Returns number of chunks stored.
    """
    source_path = Path(source_dir)
    if not source_path.exists():
        logger.warning(f"Source directory not found: {source_dir}")
        return 0

    docs: List[Document] = []

    for file_path in source_path.rglob("*"):
        if file_path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(file_path))
            docs.extend(loader.load())
            logger.info(f"Loaded PDF: {file_path.name}")
        elif file_path.suffix.lower() in [".txt", ".md"]:
            loader = TextLoader(str(file_path), encoding="utf-8")
            docs.extend(loader.load())
            logger.info(f"Loaded text: {file_path.name}")

    if not docs:
        logger.warning("No documents found to ingest.")
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    logger.info(f"Split into {len(chunks)} chunks")

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    vectorstore.persist()
    logger.success(f"Ingested {len(chunks)} chunks into ChromaDB")
    return len(chunks)


def retrieve(query: str, k: int = None) -> List[Dict[str, Any]]:
    """
    Retrieve top-k relevant document chunks for a query.
    Returns list of dicts with content, source, and relevance score.
    """
    k = k or settings.max_documents_per_query
    vectorstore = get_vectorstore()

    results = vectorstore.similarity_search_with_relevance_scores(query, k=k)

    filtered = []
    for doc, score in results:
        if score >= settings.relevance_threshold:
            filtered.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", 0),
                "score": round(score, 4),
            })

    logger.info(f"Retrieved {len(filtered)}/{k} chunks above threshold for query: '{query[:60]}...'")
    return filtered
