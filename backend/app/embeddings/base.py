"""The embedding provider contract.

`embed_documents` and `embed_query` are separated deliberately: some providers
use different prompts/instructions for indexing vs. querying. Both return plain
lists of floats so nothing downstream is coupled to a vendor SDK type. All
vectors from one provider share `dimension`, which must match the vector store's
collection size.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def model(self) -> str:
        """Identifier of the underlying model (stored on each chunk for rebuilds)."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector length produced by this provider."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of passages for indexing."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string for search."""
