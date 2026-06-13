from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project (4 levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # Vector store
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    collection_name: str = "medibot"

    # Embedding models
    dense_model: str = "BAAI/bge-large-en-v1.5"
    sparse_model: str = "Qdrant/bm25"

    # Reranker
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    retrieval_top_k: int = 10
    rerank_top_n: int = 3

    # Database
    database_path: str = "database/mediassist.db"

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours


settings = Settings()
