"""
config/settings.py
──────────────────
Central configuration loaded from environment variables.
Uses pydantic BaseSettings so every value is type-validated at startup.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── PostgreSQL ───────────────────────────────────────────
    postgres_host: str = "dea.cgyi97rb4alr.us-east-1.rds.amazonaws.com"
    postgres_port: int = 5432
    postgres_db: str = "dea_analytics_dev"
    postgres_user: str = "student_user"
    postgres_password: str = "DataEngineer12345"
    postgres_schema: str = "sales_raw"

    # ── OpenAI ───────────────────────────────────────────────
    openai_api_key: str = ""
    openai_embed_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # ── Pinecone ─────────────────────────────────────────────
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_nurture: str = "crm-nurture-content"
    pinecone_index_testimonials: str = "crm-testimonials"
    pinecone_embed_dimension: int = 1536

    # ── LangSmith ────────────────────────────────────────────
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "crm-ai-followup"

    # ── App Settings ─────────────────────────────────────────
    log_level: str = "INFO"
    max_activities_per_lead: int = 50
    email_cooldown_hours: int = 48
    top_k_retrieval: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton Settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
