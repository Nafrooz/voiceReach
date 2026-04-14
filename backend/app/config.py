from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    QDRANT_URL: str
    QDRANT_API_KEY: str

    GROQ_API_KEY: str  # FREE at console.groq.com — no card

    VAPI_SECRET: str

    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # best free Groq model
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"  # for fast classification

    COLLECTION_KNOWLEDGE: str = "voicereach_knowledge"
    COLLECTION_SESSIONS: str = "voicereach_sessions"

    VECTOR_SIZE: int = 768
    MAX_RESPONSE_TOKENS: int = 150  # keep voice responses short

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
