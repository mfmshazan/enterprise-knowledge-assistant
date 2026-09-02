"""Application configuration.

We use `pydantic-settings` so that:

* Every setting is **typed and validated at startup** — a missing or malformed
  env var fails fast with a clear error instead of surfacing as a mysterious
  runtime bug deep in the request path.
* Configuration has a single source of truth (this class), not `os.getenv`
  calls scattered across the codebase.
* The settings object is created once and cached, so it behaves like a
  read-only singleton that can be injected as a FastAPI dependency.

Grouping note: as the app grows you can split this into nested settings models
(DatabaseSettings, AuthSettings, ...). For Phase 1 a single flat class keeps the
surface small and readable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings, loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # tolerate unrelated env vars (e.g. frontend NEXT_PUBLIC_*)
    )

    # ---------- General ----------
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    PROJECT_NAME: str = "Enterprise Knowledge Assistant"
    API_V1_PREFIX: str = "/api/v1"

    # ---------- Backend / API ----------
    SECRET_KEY: str = Field(default="change-me", min_length=8)
    BACKEND_CORS_ORIGINS: list[str] | str = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # ---------- Datastores ----------
    DATABASE_URL: str = "postgresql+asyncpg://eka:eka_password@localhost:5432/eka"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "eka_chunks"

    # ---------- Object storage ----------
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "eka-documents"
    S3_USE_SSL: bool = False

    # ---------- Uploads ----------
    MAX_UPLOAD_MB: int = 25  # reject files larger than this at the API boundary

    # ---------- Ingestion ----------
    # How a pending document is processed: "inline" runs the pipeline in a
    # background task inside the API process (zero extra services, great for dev);
    # "arq" enqueues a job for a separate worker (production scale).
    INGEST_MODE: Literal["inline", "arq"] = "inline"
    CHUNK_SIZE: int = 1000  # target characters per chunk
    CHUNK_OVERLAP: int = 150  # characters shared between adjacent chunks
    URL_FETCH_TIMEOUT: int = 20  # seconds, for URL ingestion

    # ---------- Chat / agents ----------
    # "linear" = single RAG pass (retrieve -> generate). "agentic" = LangGraph
    # multi-agent graph (plan -> retrieve -> generate -> verify, with self-correction).
    CHAT_MODE: Literal["linear", "agentic"] = "linear"
    AGENT_MAX_ATTEMPTS: int = 2  # retrieval/generation retries before finalizing

    # ---------- Auth ----------
    AUTH_PROVIDER: Literal["clerk", "authjs", "dev"] = "clerk"
    CLERK_SECRET_KEY: str | None = None
    CLERK_JWKS_URL: str | None = None
    CLERK_ISSUER: str | None = None  # optional: verify the JWT `iss` claim if set
    CLERK_WEBHOOK_SECRET: str | None = None

    # ---------- AI providers ----------
    # Providers speak the OpenAI API. "gemini" uses Google's OpenAI-compatible
    # endpoint, so the same client works with a different base URL + key.
    LLM_PROVIDER: Literal["openai", "gemini"] = "openai"
    EMBEDDING_PROVIDER: Literal["openai", "gemini"] = "openai"
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None  # Gemini API key
    # Optional override of the OpenAI-compatible base URL (advanced / local models).
    OPENAI_BASE_URL: str | None = None
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def _normalize_cors(cls, value: object) -> list[str]:
        """Allow CORS origins as a list, JSON string, or comma-separated string."""
        if isinstance(value, str):
            if value.startswith("[") and value.endswith("]"):
                import json

                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return ["http://localhost:3000"]

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Automatically normalize Neon/Supabase/Render Postgres URLs for asyncpg."""
        url = value.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        url = url.replace("sslmode=require", "ssl=require")
        url = url.replace("&channel_binding=require", "")
        url = url.replace("?channel_binding=require&", "?")
        url = url.replace("?channel_binding=require", "")
        return url

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton.

    `lru_cache` guarantees the environment is parsed exactly once per process.
    Import this everywhere instead of instantiating `Settings()` directly so the
    cache is shared and tests can override it via dependency injection.
    """
    return Settings()


settings = get_settings()
