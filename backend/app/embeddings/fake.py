"""Deterministic fake embedding provider for tests.

Produces a stable vector from a hash of the input text, so:
* the same text always embeds to the same vector (a query matches its own chunk
  exactly — useful for retrieval tests in Phase 4), and
* no network calls or API keys are needed in CI.

The numbers are meaningless as semantics; they only need to be deterministic.
"""

from __future__ import annotations

import hashlib
import struct

from app.embeddings.base import EmbeddingProvider


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, dimension: int = 16, model: str = "fake-embedding") -> None:
        self._dimension = dimension
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def _vector(self, text: str) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < self._dimension:
            digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
            for offset in range(0, len(digest), 4):
                if len(values) >= self._dimension:
                    break
                (raw,) = struct.unpack(">I", digest[offset : offset + 4])
                values.append(raw / 2**32)
            counter += 1
        return values

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector(text)
