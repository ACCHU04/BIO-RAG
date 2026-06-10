from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # LLM (Gemini — used by Query page)
    google_api_key: str
    google_model: str = "gemini-2.0-flash-lite"

    # LLM (OpenRouter — used by Incognito mode)
    openrouter_api_key: str = ""

    # Search
    tavily_api_key: str = ""

    # Biomedical APIs
    entrez_email: str = "researcher@university.edu"
    entrez_api_key: str = ""

    # Vector Store
    chroma_db_path: str = "./data/chroma_db"
    chroma_collection_name: str = "biomedical_docs"

    # Embeddings
    embedding_model: str = "pritamdeka/S-PubMedBert-MS-MARCO"

    # Agent
    max_iterations: int = 10
    max_documents_per_query: int = 5
    relevance_threshold: float = 0.75
    self_correction_attempts: int = 3

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8742
    debug: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
