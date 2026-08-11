"""In-memory vector store — a dependency-free fake for tests.

Implements cosine-similarity search over a dict of points, with the same
org-scoped filtering as the real store. Lets the ingestion and (later) retrieval
paths be tested without a running Qdrant.
"""

from __future__ import annotations

import math
import uuid

from app.vectorstore.base import SearchHit, VectorPoint, VectorStore


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._points: dict[uuid.UUID, VectorPoint] = {}
        self.dimension: int | None = None

    async def ensure_collection(self, dimension: int) -> None:
        self.dimension = dimension

    async def upsert(self, points: list[VectorPoint]) -> None:
        for point in points:
            self._points[point.id] = point

    async def delete_by_document(self, org_id: uuid.UUID, document_id: uuid.UUID) -> None:
        to_remove = [
            pid
            for pid, p in self._points.items()
            if p.payload.get("org_id") == str(org_id)
            and p.payload.get("document_id") == str(document_id)
        ]
        for pid in to_remove:
            del self._points[pid]

    async def search(
        self, org_id: uuid.UUID, query_vector: list[float], *, limit: int = 5
    ) -> list[SearchHit]:
        hits = [
            SearchHit(id=p.id, score=_cosine(query_vector, p.vector), payload=p.payload)
            for p in self._points.values()
            if p.payload.get("org_id") == str(org_id)
        ]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]
