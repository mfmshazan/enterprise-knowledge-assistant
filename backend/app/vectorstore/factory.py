"""Builds and caches the configured vector store."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.vectorstore.base import VectorStore
from app.vectorstore.qdrant import QdrantVectorStore


@lru_cache
def get_vector_store() -> VectorStore:
    return QdrantVectorStore(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection=settings.QDRANT_COLLECTION,
    )
