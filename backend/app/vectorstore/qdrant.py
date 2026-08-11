"""Qdrant vector store.

Uses the async Qdrant client. On first use we create the collection sized to the
embedding dimension with cosine distance, plus a keyword payload index on
`org_id` so tenant-filtered search is fast. Point ids are the chunk UUIDs, so a
search hit maps straight back to its Postgres row.
"""

from __future__ import annotations

import uuid

from qdrant_client import AsyncQdrantClient, models

from app.core.logging import get_logger
from app.vectorstore.base import SearchHit, VectorPoint, VectorStore

logger = get_logger(__name__)


class QdrantVectorStore(VectorStore):
    def __init__(self, *, url: str, api_key: str | None, collection: str) -> None:
        self._client = AsyncQdrantClient(url=url, api_key=api_key or None)
        self._collection = collection

    async def ensure_collection(self, dimension: int) -> None:
        if await self._client.collection_exists(self._collection):
            return
        await self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
        )
        await self._client.create_payload_index(
            collection_name=self._collection,
            field_name="org_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        logger.info("qdrant_collection_created", collection=self._collection, dim=dimension)

    async def upsert(self, points: list[VectorPoint]) -> None:
        if not points:
            return
        await self._client.upsert(
            collection_name=self._collection,
            points=[
                models.PointStruct(id=str(p.id), vector=p.vector, payload=p.payload) for p in points
            ],
        )

    async def delete_by_document(self, org_id: uuid.UUID, document_id: uuid.UUID) -> None:
        await self._client.delete(
            collection_name=self._collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="org_id", match=models.MatchValue(value=str(org_id))
                        ),
                        models.FieldCondition(
                            key="document_id", match=models.MatchValue(value=str(document_id))
                        ),
                    ]
                )
            ),
        )

    async def search(
        self, org_id: uuid.UUID, query_vector: list[float], *, limit: int = 5
    ) -> list[SearchHit]:
        result = await self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=limit,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(key="org_id", match=models.MatchValue(value=str(org_id)))
                ]
            ),
        )
        return [
            SearchHit(id=uuid.UUID(str(point.id)), score=point.score, payload=point.payload or {})
            for point in result.points
        ]
