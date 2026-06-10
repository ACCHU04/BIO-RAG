"""
Fetch full-text biomedical PDFs from PubMed Central (PMC) via Biopython Entrez.
Downloads ~500 PDFs across diverse biomedical topics for RAG ingestion.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Set

sys.path.append(str(Path(__file__).resolve().parent.parent))

import requests
from Bio import Entrez
from loguru import logger
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

Entrez.email = os.getenv("ENTREZ_EMAIL", "researcher@university.edu")
Entrez.api_key = os.getenv("ENTREZ_API_KEY", "")

HAS_API_KEY = bool(Entrez.api_key)
REQUEST_DELAY = 0.1 if HAS_API_KEY else 0.34
logger.info(f"Entrez API key {'found' if HAS_API_KEY else 'not found'}, delay={REQUEST_DELAY}s")

PDF_DIR = Path("./data/documents/pmc")
PDF_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_QUERIES = [
    ("cancer[Abstract] AND therapy[Abstract]", 55),
    ("diabetes[Abstract] AND treatment[Abstract]", 55),
    ("cardiovascular[Abstract] AND disease[Abstract]", 55),
    ("immunology[Abstract] AND mechanism[Abstract]", 55),
    ("neurodegenerative[Abstract] AND disease[Abstract]", 55),
    ("gene[Abstract] AND therapy[Abstract] AND clinical[Abstract]", 55),
    ("infectious[Abstract] AND disease[Abstract] AND treatment[Abstract]", 55),
    ("artificial intelligence[Abstract] AND medicine[Abstract]", 55),
    ("drug discovery[Abstract] AND development[Abstract]", 50),
]


def search_pmc(term: str, retmax: int) -> List[str]:
    logger.info(f"Searching PMC for: '{term}' (max={retmax})")
    try:
        handle = Entrez.esearch(db="pmc", term=term, retmax=retmax, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        ids = record.get("IdList", [])
        logger.info(f"  Found {len(ids)} results")
        time.sleep(REQUEST_DELAY)
        return ids
    except Exception as e:
        logger.error(f"  Search failed: {e}")
        return []


def download_pdf(pmc_id: str) -> bool:
    pdf_path = PDF_DIR / f"PMC{pmc_id}.pdf"
    if pdf_path.exists() and pdf_path.stat().st_size > 10000:
        return True

    url = f"https://europepmc.org/articles/PMC{pmc_id}?pdf=render"

    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=30, allow_redirects=True,
                                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            resp.raise_for_status()
            content = resp.content
            if not content.startswith(b'%PDF') or len(content) < 10000:
                logger.warning(f"PMC{pmc_id}: Not a valid PDF (size={len(content)})")
                return False
            with open(pdf_path, "wb") as f:
                f.write(content)
            return True
        except Exception as e:
            if attempt < 2:
                time.sleep(1 * (attempt + 1))
            else:
                logger.warning(f"PMC{pmc_id}: Failed after 3 attempts: {e}")
                return False


def main():
    all_ids: Set[str] = set()
    for term, target in SEARCH_QUERIES:
        ids = search_pmc(term, target)
        all_ids.update(ids)
        time.sleep(REQUEST_DELAY)

    logger.info(f"Total unique PMC IDs collected: {len(all_ids)}")
    if not all_ids:
        logger.error("No PMC IDs found. Aborting.")
        return

    pdf_ids = sorted(all_ids)
    logger.info(f"Downloading PDFs to {PDF_DIR}...")

    success = 0
    skipped = 0
    failed = 0
    for pmc_id in tqdm(pdf_ids, desc="Downloading PDFs"):
        pdf_path = PDF_DIR / f"PMC{pmc_id}.pdf"
        if pdf_path.exists() and pdf_path.stat().st_size > 10000:
            skipped += 1
            continue
        if download_pdf(pmc_id):
            success += 1
        else:
            failed += 1
        time.sleep(1.0)

    logger.info(f"PDF download complete: {success} new, {skipped} existing, {failed} failed")

    total_pdfs = len(list(PDF_DIR.glob("*.pdf")))
    total_mb = sum(f.stat().st_size for f in PDF_DIR.glob("*.pdf")) / (1024*1024)
    logger.info(f"Total PDFs: {total_pdfs} ({total_mb:.1f} MB)")

    logger.info("Ingesting PDFs into ChromaDB...")
    try:
        from app.rag.retriever import ingest_documents
        ingested = ingest_documents(source_dir=str(PDF_DIR))
        logger.success(f"Ingestion complete! {ingested} chunks added to ChromaDB.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise


if __name__ == "__main__":
    main()
