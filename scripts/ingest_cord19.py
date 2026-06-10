"""
CORD-19 Dataset Ingestion Script.
Downloads CORD-19 metadata from Kaggle, extracts a subset of research papers,
and ingests them into the ChromaDB vector store.
"""

import os
import sys
import argparse
import zipfile
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from loguru import logger
from dotenv import load_dotenv

# Load environment variables before initializing Kaggle API
load_dotenv()

def check_credentials():
    """Ensure Kaggle credentials are configured."""
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    
    # If credentials are in env/dotenv, set them for the kaggle client
    if username and key:
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = key
        logger.info("Using Kaggle credentials from environment variables.")
        return True
        
    # Otherwise, check default kaggle.json location
    home_dir = Path.home()
    kaggle_json = home_dir / ".kaggle" / "kaggle.json"
    if kaggle_json.exists():
        logger.info(f"Using Kaggle credentials from {kaggle_json}")
        return True
        
    return False

def download_from_s3_fallback(target_path: Path, max_bytes: int = 15 * 1024 * 1024):
    """
    Downloads a sample of metadata.csv directly from the public CORD-19 S3 bucket.
    This doesn't require any API token or AWS credentials.
    """
    import requests
    from tqdm import tqdm
    
    url = "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2022-06-02/metadata.csv"
    logger.info(f"Streaming public CORD-19 metadata from {url}...")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Read up to max_bytes to get a high-quality sample of papers
        downloaded = 0
        chunk_size = 1024 * 1024 # 1 MB chunks
        
        with open(target_path, "wb") as f, tqdm(
            desc="Downloading CORD-19 Metadata Sample",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            total=max_bytes
        ) as bar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                bar.update(len(chunk))
                if downloaded >= max_bytes:
                    logger.info(f"Reached sample limit of {max_bytes / (1024*1024):.1f} MB. Stopping download.")
                    break
        logger.info(f"Successfully saved metadata sample to {target_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download from public S3: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download and ingest CORD-19 dataset subset.")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=100, 
        help="Number of documents to extract and ingest (default: 100)"
    )
    parser.add_argument(
        "--force-download", 
        action="store_true", 
        help="Force download metadata.csv even if it already exists locally"
    )
    args = parser.parse_args()

    has_credentials = check_credentials()

    dataset = "allen-institute-for-ai/CORD-19-research-challenge"
    file_name = "metadata.csv"
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = data_dir / file_name
    zip_path = data_dir / "metadata.csv.zip"

    # Download metadata.csv if it doesn't exist
    if not csv_path.exists() or args.force_download:
        if has_credentials:
            logger.info(f"Downloading {file_name} from Kaggle dataset '{dataset}'...")
            try:
                # Delayed import of kaggle so environment variables can be set first
                from kaggle.api.kaggle_api_extended import KaggleApi
                api = KaggleApi()
                api.authenticate()
                api.dataset_download_file(
                    dataset, 
                    file_name, 
                    path=str(data_dir), 
                    force=args.force_download, 
                    quiet=False
                )
                
                # Kaggle API downloads files as zip if they are large
                if zip_path.exists():
                    logger.info(f"Extracting {zip_path}...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(data_dir)
                    zip_path.unlink() # Clean up zip file
                    logger.info(f"Extracted to {csv_path}")
                else:
                    logger.info(f"Downloaded {csv_path} directly.")
            except Exception as e:
                logger.warning(f"Failed to download from Kaggle: {e}. Falling back to public S3...")
                if not download_from_s3_fallback(csv_path):
                    raise RuntimeError("Failed to download metadata from both Kaggle and S3 fallback.")
        else:
            logger.warning("Kaggle credentials not configured. Falling back to public S3...")
            if not download_from_s3_fallback(csv_path):
                raise RuntimeError("Failed to download metadata from S3 fallback.")
    else:
        logger.info(f"Found existing CORD-19 metadata file at {csv_path}. Skipping download.")

    # Parse and extract subset of documents from metadata.csv
    logger.info(f"Parsing CORD-19 metadata.csv and extracting {args.limit} papers...")
    
    output_dir = data_dir / "documents" / "cord19"
    # Clean up previous extractions in this folder to avoid duplicating/mixing
    if output_dir.exists():
        for f in output_dir.glob("*.md"):
            f.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_count = 0
    # Read in chunks to optimize memory usage
    chunksize = 10000
    try:
        for chunk in pd.read_csv(
            csv_path, 
            chunksize=chunksize, 
            usecols=['cord_uid', 'title', 'abstract', 'publish_time', 'authors', 'journal', 'url'],
            on_bad_lines='skip',
            low_memory=False
        ):
            # Drop rows missing title or abstract
            valid_rows = chunk.dropna(subset=['title', 'abstract'])
            
            for _, row in valid_rows.iterrows():
                cord_uid = str(row['cord_uid'])
                # If uid is nan or empty, fallback to a safe name
                if not cord_uid or cord_uid == 'nan':
                    continue
                    
                title = str(row['title']).strip()
                abstract = str(row['abstract']).strip()
                authors = str(row['authors']).strip() if pd.notna(row['authors']) else "Unknown"
                journal = str(row['journal']).strip() if pd.notna(row['journal']) else "Unknown"
                publish_time = str(row['publish_time']).strip() if pd.notna(row['publish_time']) else "Unknown"
                url = str(row['url']).strip() if pd.notna(row['url']) else "Unknown"
                
                # Write to Markdown file
                doc_file = output_dir / f"{cord_uid}.md"
                with open(doc_file, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"**Authors:** {authors}  \n")
                    f.write(f"**Journal:** {journal}  \n")
                    f.write(f"**Publish Time:** {publish_time}  \n")
                    f.write(f"**Source URL:** {url}  \n")
                    f.write(f"**CORD UID:** {cord_uid}  \n\n")
                    f.write(f"## Abstract\n{abstract}\n")
                
                extracted_count += 1
                if extracted_count >= args.limit:
                    break
                    
            if extracted_count >= args.limit:
                break
    except Exception as e:
        logger.error(f"Error parsing metadata.csv: {e}")
        raise

    logger.info(f"Successfully generated {extracted_count} Markdown articles in {output_dir}")

    # Import and run retriever ingestion
    logger.info("Ingesting documents into ChromaDB...")
    try:
        from app.rag.retriever import ingest_documents
        ingested_chunks = ingest_documents(source_dir=str(output_dir))
        logger.success(f"Ingestion complete! Ingested {ingested_chunks} chunks into ChromaDB.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()
