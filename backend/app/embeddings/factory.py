"""Builds and caches the configured embedding provider.

Both "openai" and "gemini" are served by the OpenAI-compatible client — Gemini
just points at Google's OpenAI-compatible base URL and uses the Google API key.
This keeps a single, well-tested code path while letting you choose the vendor
via configuration.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.openai import OpenAIEmbeddingProvider

# Google's OpenAI-compatible endpoint for Gemini models.
_GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.EMBEDDING_PROVIDER

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI embedding provider.")
        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIM,
            base_url=settings.OPENAI_BASE_URL,
        )

    if provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is required for the Gemini embedding provider.")
        return OpenAIEmbeddingProvider(
            api_key=settings.GOOGLE_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIM,
            base_url=settings.OPENAI_BASE_URL or _GEMINI_OPENAI_BASE_URL,
        )

    raise RuntimeError(f"Unsupported EMBEDDING_PROVIDER: {provider!r}.")
