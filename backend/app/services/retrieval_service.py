"""Retrieval: find the chunks most relevant to a query, within one organization.

The read-path counterpart to ingestion. It embeds the query with the *same*
provider used at index time, runs an org-filtered vector search, then hydrates
the hits from Postgres so the returned text and source title are authoritative
(not whatever lived in the vector payload).

Tenant safety is doubled: the vector store filters by `org_id`, and chunk rows
are loaded through the org-scoped repository — so results can never cross tenants.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.embeddings.base import EmbeddingProvider
from app.repositories.document_chunk import DocumentChunkRepository
from app.vectorstore.base import VectorStore

# Guardrails on how many chunks a single query may pull back.
DEFAULT_TOP_K = 5
MAX_TOP_K = 20


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    content: str
    score: float


class RetrievalService:
    def __init__(
        self,
        chunks: DocumentChunkRepository,
        embedder: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.chunks = chunks
        self.embedder = embedder
        self.vector_store = vector_store

    async def search(self, query: str, *, top_k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
        query = query.strip()
        if not query:
            return []
        top_k = max(1, min(top_k, MAX_TOP_K))

        query_vector = await self.embedder.embed_query(query)
        hits = await self.vector_store.search(self.chunks.org_id, query_vector, limit=top_k)
        if not hits:
            return []

        scores = {hit.id: hit.score for hit in hits}
        rows = await self.chunks.get_by_ids(list(scores))

        results = [
            RetrievedChunk(
                chunk_id=str(row.id),
                document_id=str(row.document_id),
                document_title=row.document.title,
                chunk_index=row.chunk_index,
                content=row.content,
                score=scores[row.id],
            )
            for row in rows
        ]
        # Preserve vector-store ranking (DB load order is arbitrary).
        results.sort(key=lambda c: c.score, reverse=True)
        return results
