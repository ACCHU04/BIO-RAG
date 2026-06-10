"""
Dynamic CRUD operations for ChromaDB vector store.
Supports add, update, delete at document and page level using metadata.
Assignment Requirement: Section A — Dynamic Indexing.
"""

import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document
from loguru import logger

from app.rag.retriever import get_vectorstore


def _make_doc_id(source: str, page: int) -> str:
    """Generate a stable chunk ID from source path + page number."""
    return f"{Path(source).stem}__page{page}__{uuid.uuid4().hex[:8]}"


def add_document(file_path: str, doc_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Ingest a single document (PDF or TXT) into ChromaDB.
    Each chunk is tagged with doc_id, source, and page_number metadata
    so it can be individually updated or deleted later.

    Returns: summary dict with doc_id and chunks added.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    doc_id = doc_id or path.stem

    # Load document
    if path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(str(path))
    elif path.suffix.lower() in [".txt", ".md"]:
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    raw_docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(raw_docs)

    # Tag every chunk with rich metadata for targeted CRUD
    tagged_chunks = []
    chunk_ids = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}__chunk{i}"
        chunk.metadata.update({
            "doc_id": doc_id,
            "source": str(path),
            "page_number": chunk.metadata.get("page", i),
            "chunk_index": i,
            "chunk_id": chunk_id,
        })
        tagged_chunks.append(chunk)
        chunk_ids.append(chunk_id)

    vectorstore = get_vectorstore()
    vectorstore.add_documents(tagged_chunks, ids=chunk_ids)
    vectorstore.persist()

    logger.success(f"[ADD] doc_id='{doc_id}' — {len(tagged_chunks)} chunks added")
    return {
        "doc_id": doc_id,
        "source": str(path),
        "chunks_added": len(tagged_chunks),
        "status": "added",
    }


def delete_document(doc_id: str) -> Dict[str, Any]:
    """
    Delete all chunks associated with a doc_id from ChromaDB.
    Uses metadata filtering — no full index rebuild needed.
    """
    vectorstore = get_vectorstore()
    collection = vectorstore._collection

    # Find all chunk IDs with this doc_id
    results = collection.get(where={"doc_id": doc_id})
    ids_to_delete = results.get("ids", [])

    if not ids_to_delete:
        logger.warning(f"[DELETE] No chunks found for doc_id='{doc_id}'")
        return {"doc_id": doc_id, "chunks_deleted": 0, "status": "not_found"}

    collection.delete(ids=ids_to_delete)
    vectorstore.persist()

    logger.success(f"[DELETE] doc_id='{doc_id}' — {len(ids_to_delete)} chunks deleted")
    return {
        "doc_id": doc_id,
        "chunks_deleted": len(ids_to_delete),
        "status": "deleted",
    }


def update_document(file_path: str, doc_id: str) -> Dict[str, Any]:
    """
    Update a document: delete all existing chunks for doc_id, then re-ingest.
    This is a targeted upsert — no full index rebuild.
    """
    logger.info(f"[UPDATE] Starting update for doc_id='{doc_id}'")

    delete_result = delete_document(doc_id)
    add_result = add_document(file_path, doc_id=doc_id)

    logger.success(f"[UPDATE] doc_id='{doc_id}' — deleted {delete_result['chunks_deleted']}, added {add_result['chunks_added']}")
    return {
        "doc_id": doc_id,
        "chunks_deleted": delete_result["chunks_deleted"],
        "chunks_added": add_result["chunks_added"],
        "status": "updated",
    }


def delete_page(doc_id: str, page_number: int) -> Dict[str, Any]:
    """
    Delete a specific page's chunks from a document.
    Allows surgical page-level updates without touching the rest of the doc.
    """
    vectorstore = get_vectorstore()
    collection = vectorstore._collection

    results = collection.get(where={
        "$and": [
            {"doc_id": {"$eq": doc_id}},
            {"page_number": {"$eq": page_number}},
        ]
    })
    ids_to_delete = results.get("ids", [])

    if not ids_to_delete:
        return {"doc_id": doc_id, "page_number": page_number, "chunks_deleted": 0, "status": "not_found"}

    collection.delete(ids=ids_to_delete)
    vectorstore.persist()

    logger.success(f"[DELETE PAGE] doc_id='{doc_id}' page={page_number} — {len(ids_to_delete)} chunks deleted")
    return {
        "doc_id": doc_id,
        "page_number": page_number,
        "chunks_deleted": len(ids_to_delete),
        "status": "deleted",
    }


def list_documents() -> List[Dict[str, Any]]:
    """
    List all unique documents currently indexed in ChromaDB.
    Returns doc_id, source, and chunk count for each.
    """
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    results = collection.get(include=["metadatas"])

    doc_map: Dict[str, Dict] = {}
    for meta in results.get("metadatas", []):
        if not meta:
            continue
        doc_id = meta.get("doc_id", "unknown")
        if doc_id not in doc_map:
            doc_map[doc_id] = {
                "doc_id": doc_id,
                "source": meta.get("source", ""),
                "chunk_count": 0,
            }
        doc_map[doc_id]["chunk_count"] += 1

    return list(doc_map.values())
