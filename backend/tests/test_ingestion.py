"""End-to-end ingestion pipeline tests using fakes (no OpenAI/Qdrant/MinIO)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.embeddings.fake import FakeEmbeddingProvider
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, SourceType
from app.services.ingestion_service import IngestionService
from app.storage.memory import InMemoryObjectStorage
from app.vectorstore.memory import InMemoryVectorStore


def _service(
    session: AsyncSession,
    storage: InMemoryObjectStorage,
    vector_store: InMemoryVectorStore,
) -> IngestionService:
    return IngestionService(
        session=session,
        storage=storage,
        embedder=FakeEmbeddingProvider(dimension=16),
        vector_store=vector_store,
        chunk_size=200,
        chunk_overlap=40,
    )


async def test_pipeline_indexes_a_file(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    storage: InMemoryObjectStorage,
    vector_store: InMemoryVectorStore,
) -> None:
    org_id, doc_id = uuid.uuid4(), uuid.uuid4()
    key = f"documents/{org_id}/{doc_id}/a.txt"
    body = "Alpha beta gamma.\n\n" + " ".join(f"word{i}" for i in range(400))
    await storage.put_object(key, body.encode(), "text/plain")

    async with db_sessionmaker() as session:
        session.add(
            Document(
                id=doc_id,
                org_id=org_id,
                source_type=SourceType.FILE,
                title="a",
                filename="a.txt",
                storage_key=key,
                status=DocumentStatus.PENDING,
            )
        )
        await session.commit()

        await _service(session, storage, vector_store).ingest(doc_id)

        document = await session.get(Document, doc_id)
        assert document is not None
        assert document.status is DocumentStatus.INDEXED
        assert document.chunk_count > 1

        rows = (
            await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
        ).all()
        assert len(rows) == document.chunk_count
        assert all(r.embedding_model == "fake-embedding" for r in rows)

    # Vectors were upserted and are searchable within the org.
    query = await FakeEmbeddingProvider(dimension=16).embed_query("Alpha beta gamma.")
    hits = await vector_store.search(org_id, query, limit=3)
    assert hits
    assert hits[0].payload["document_id"] == str(doc_id)


async def test_pipeline_marks_failed_on_missing_file(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    storage: InMemoryObjectStorage,
    vector_store: InMemoryVectorStore,
) -> None:
    org_id, doc_id = uuid.uuid4(), uuid.uuid4()
    async with db_sessionmaker() as session:
        session.add(
            Document(
                id=doc_id,
                org_id=org_id,
                source_type=SourceType.FILE,
                title="x",
                filename="x.txt",
                storage_key="documents/missing/x.txt",  # not in storage
                status=DocumentStatus.PENDING,
            )
        )
        await session.commit()

        await _service(session, storage, vector_store).ingest(doc_id)

        document = await session.get(Document, doc_id)
        assert document is not None
        assert document.status is DocumentStatus.FAILED
        assert document.error


async def test_pipeline_fails_when_no_text(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    storage: InMemoryObjectStorage,
    vector_store: InMemoryVectorStore,
) -> None:
    org_id, doc_id = uuid.uuid4(), uuid.uuid4()
    key = f"documents/{org_id}/{doc_id}/blank.txt"
    await storage.put_object(key, b"   \n  \n", "text/plain")

    async with db_sessionmaker() as session:
        session.add(
            Document(
                id=doc_id,
                org_id=org_id,
                source_type=SourceType.FILE,
                title="blank",
                filename="blank.txt",
                storage_key=key,
                status=DocumentStatus.PENDING,
            )
        )
        await session.commit()

        await _service(session, storage, vector_store).ingest(doc_id)

        document = await session.get(Document, doc_id)
        assert document is not None
        assert document.status is DocumentStatus.FAILED


async def test_reingest_is_idempotent(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    storage: InMemoryObjectStorage,
    vector_store: InMemoryVectorStore,
) -> None:
    org_id, doc_id = uuid.uuid4(), uuid.uuid4()
    key = f"documents/{org_id}/{doc_id}/a.txt"
    await storage.put_object(key, ("para. " * 300).encode(), "text/plain")

    async with db_sessionmaker() as session:
        session.add(
            Document(
                id=doc_id,
                org_id=org_id,
                source_type=SourceType.FILE,
                title="a",
                filename="a.txt",
                storage_key=key,
                status=DocumentStatus.PENDING,
            )
        )
        await session.commit()
        service = _service(session, storage, vector_store)

        await service.ingest(doc_id)
        first_count = (await session.get(Document, doc_id)).chunk_count  # type: ignore[union-attr]

        # Re-ingest (simulate retry): must not duplicate chunks.
        document = await session.get(Document, doc_id)
        assert document is not None
        document.status = DocumentStatus.PENDING
        await session.commit()
        await service.ingest(doc_id)

        rows = (
            await session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
        ).all()
        assert len(rows) == first_count
