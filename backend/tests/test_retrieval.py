"""Unit tests for RetrievalService (fake embedder + in-memory vector store)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.embeddings.fake import FakeEmbeddingProvider
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, SourceType
from app.repositories.document_chunk import DocumentChunkRepository
from app.services.retrieval_service import RetrievalService
from app.vectorstore.base import VectorPoint
from app.vectorstore.memory import InMemoryVectorStore

CHUNKS = [
    "The refund policy allows returns within 30 days.",
    "Our headquarters are located in Berlin.",
    "Cats are small domesticated mammals.",
]


async def _seed(
    session: AsyncSession,
    vector_store: InMemoryVectorStore,
    embedder: FakeEmbeddingProvider,
    org_id: uuid.UUID,
    *,
    title: str = "Handbook",
) -> uuid.UUID:
    doc_id = uuid.uuid4()
    session.add(
        Document(
            id=doc_id,
            org_id=org_id,
            source_type=SourceType.FILE,
            title=title,
            status=DocumentStatus.INDEXED,
        )
    )
    chunk_ids = [uuid.uuid4() for _ in CHUNKS]
    for cid, index, text in zip(chunk_ids, range(len(CHUNKS)), CHUNKS, strict=True):
        session.add(
            DocumentChunk(
                id=cid, org_id=org_id, document_id=doc_id, chunk_index=index, content=text
            )
        )
    await session.commit()

    vectors = await embedder.embed_documents(CHUNKS)
    await vector_store.upsert(
        [
            VectorPoint(
                id=cid,
                vector=vec,
                payload={
                    "org_id": str(org_id),
                    "document_id": str(doc_id),
                    "chunk_index": index,
                },
            )
            for cid, index, vec in zip(chunk_ids, range(len(CHUNKS)), vectors, strict=True)
        ]
    )
    return doc_id


async def test_ranks_matching_chunk_first(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    embedder = FakeEmbeddingProvider(dimension=16)
    org_id = uuid.uuid4()

    async with db_sessionmaker() as session:
        await _seed(session, vector_store, embedder, org_id, title="Policy")
        service = RetrievalService(DocumentChunkRepository(session, org_id), embedder, vector_store)

        # Exact match -> identical fake vector -> cosine 1.0 -> ranked first.
        results = await service.search(CHUNKS[0], top_k=3)

    assert results
    assert results[0].content == CHUNKS[0]
    assert results[0].document_title == "Policy"
    assert results[0].score == pytest.approx(1.0, abs=1e-6)


async def test_empty_query_returns_no_results(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    embedder = FakeEmbeddingProvider(dimension=16)
    org_id = uuid.uuid4()
    async with db_sessionmaker() as session:
        service = RetrievalService(DocumentChunkRepository(session, org_id), embedder, vector_store)
        assert await service.search("   ") == []


async def test_search_is_tenant_isolated(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    embedder = FakeEmbeddingProvider(dimension=16)
    org_a, org_b = uuid.uuid4(), uuid.uuid4()

    async with db_sessionmaker() as session:
        await _seed(session, vector_store, embedder, org_a)
        # Searching as org B (which has no chunks) must return nothing.
        service_b = RetrievalService(
            DocumentChunkRepository(session, org_b), embedder, vector_store
        )
        assert await service_b.search(CHUNKS[0]) == []
