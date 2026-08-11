"""Embedding provider abstraction.

Embeddings turn text into vectors so semantically similar passages sit close
together in vector space — the basis of retrieval. The app depends on the
`EmbeddingProvider` interface; OpenAI is the default implementation and a
deterministic fake backs the tests (no API calls, no cost).
"""

from app.embeddings.base import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider

__all__ = ["EmbeddingProvider", "get_embedding_provider"]
