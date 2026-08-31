"""Builds and caches the configured LLM provider (OpenAI or Gemini)."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.openai import OpenAICompatibleLLMProvider

# Google's OpenAI-compatible endpoint for Gemini models.
_GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


@lru_cache
def get_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI LLM provider.")
        return OpenAICompatibleLLMProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL,
            base_url=settings.OPENAI_BASE_URL,
        )

    if provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is required for the Gemini LLM provider.")
        return OpenAICompatibleLLMProvider(
            api_key=settings.GOOGLE_API_KEY,
            model=settings.LLM_MODEL,
            base_url=settings.OPENAI_BASE_URL or _GEMINI_OPENAI_BASE_URL,
        )

    raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider!r}.")
