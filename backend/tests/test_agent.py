"""Tests for the LangGraph agentic answer engine (fakes, no real model)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.engine import AgenticAnswerEngine
from app.embeddings.fake import FakeEmbeddingProvider
from app.llm.fake import FakeLLMProvider
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, SourceType
from app.repositories.document_chunk import DocumentChunkRepository
from app.services.retrieval_service import RetrievalService
from app.vectorstore.base import VectorPoint
from app.vectorstore.memory import InMemoryVectorStore

CONTENT = "The security policy requires two-factor authentication for all admins."


async def _retrieval_with_doc(
    session: AsyncSession,
    vector_store: InMemoryVectorStore,
    org_id: uuid.UUID,
) -> RetrievalService:
    embedder = FakeEmbeddingProvider(dimension=16)
    doc_id, chunk_id = uuid.uuid4(), uuid.uuid4()
    session.add(
        Document(
            id=doc_id,
            org_id=org_id,
            source_type=SourceType.FILE,
            title="Security",
            status=DocumentStatus.INDEXED,
        )
    )
    session.add(
        DocumentChunk(
            id=chunk_id, org_id=org_id, document_id=doc_id, chunk_index=0, content=CONTENT
        )
    )
    await session.commit()
    (vector,) = await embedder.embed_documents([CONTENT])
    await vector_store.upsert(
        [
            VectorPoint(
                id=chunk_id,
                vector=vector,
                payload={"org_id": str(org_id), "document_id": str(doc_id), "chunk_index": 0},
            )
        ]
    )
    return RetrievalService(DocumentChunkRepository(session, org_id), embedder, vector_store)


async def test_agent_answers_with_grounded_sources(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = uuid.uuid4()
    async with db_sessionmaker() as session:
        retrieval = await _retrieval_with_doc(session, vector_store, org_id)
        engine = AgenticAnswerEngine(retrieval, FakeLLMProvider(), max_attempts=2)
        result = await engine.answer(CONTENT, top_k=3)

    assert result.answer
    assert result.chunks
    assert result.chunks[0].document_title == "Security"


async def test_agent_terminates_when_never_grounded(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    # Verifier always rejects -> the self-correction loop must still terminate at
    # max_attempts and return the best draft (never loops forever).
    org_id = uuid.uuid4()
    async with db_sessionmaker() as session:
        retrieval = await _retrieval_with_doc(session, vector_store, org_id)
        engine = AgenticAnswerEngine(
            retrieval, FakeLLMProvider(always_grounded=False), max_attempts=2
        )
        result = await engine.answer(CONTENT, top_k=2)

    assert result.answer  # returns the best-effort draft rather than hanging


async def test_agent_handles_no_context(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = uuid.uuid4()
    async with db_sessionmaker() as session:
        # No documents seeded for this org.
        embedder = FakeEmbeddingProvider(dimension=16)
        retrieval = RetrievalService(
            DocumentChunkRepository(session, org_id), embedder, vector_store
        )
        engine = AgenticAnswerEngine(retrieval, FakeLLMProvider(), max_attempts=2)
        result = await engine.answer("anything?", top_k=3)

    assert result.answer
    assert result.chunks == []
