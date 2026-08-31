"""LLM provider abstraction.

The chat pipeline depends on the `LLMProvider` interface, not a vendor SDK. The
default implementation speaks the OpenAI Chat Completions API, which also serves
Gemini via Google's OpenAI-compatible endpoint (same class, different base URL) —
the same swap-a-vendor discipline used for auth and embeddings. A deterministic
fake backs the tests.
"""

from app.llm.base import ChatMessage, LLMProvider
from app.llm.factory import get_llm_provider

__all__ = ["ChatMessage", "LLMProvider", "get_llm_provider"]
