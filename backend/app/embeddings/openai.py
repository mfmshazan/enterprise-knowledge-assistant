"""OpenAI embedding provider.

Sends batches to the OpenAI embeddings API. We cap batch size defensively so a
document with thousands of chunks is split across requests rather than sent as
one oversized payload. The async client keeps the event loop free during the
network round-trips.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.embeddings.base import EmbeddingProvider

_MAX_BATCH = 128


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, api_key: str, model: str, dimension: int) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimension = dimension

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _MAX_BATCH):
            batch = texts[start : start + _MAX_BATCH]
            response = await self._client.embeddings.create(model=self._model, input=batch)
            vectors.extend(item.embedding for item in response.data)
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(model=self._model, input=[text])
        return response.data[0].embedding
