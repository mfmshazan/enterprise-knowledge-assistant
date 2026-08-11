"""Vector store abstraction.

Holds chunk embeddings for similarity search. Qdrant is the default backend; an
in-memory implementation backs tests. Per ADR-0002 the vector store is a
*derived index* — its payload carries only `org_id`/`document_id`/`chunk_index`
(for tenant-filtered search and cleanup), while chunk text lives in Postgres, so
the index can be rebuilt at any time.
"""

from app.vectorstore.base import SearchHit, VectorPoint, VectorStore
from app.vectorstore.factory import get_vector_store

__all__ = ["SearchHit", "VectorPoint", "VectorStore", "get_vector_store"]
