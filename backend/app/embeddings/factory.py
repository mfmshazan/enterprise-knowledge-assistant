"""Builds and caches the configured embedding provider."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.openai import OpenAIEmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    if settings.EMBEDDING_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI embedding provider.")
        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIM,
        )
    raise RuntimeError(f"Unsupported EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER!r}.")
