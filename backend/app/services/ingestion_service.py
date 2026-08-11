"""The ingestion pipeline: pending Document -> searchable chunks.

Runs the write path end to end for a single document:

    load source text  ->  chunk  ->  embed  ->  upsert vectors + persist chunks
                                                     -> status = indexed

It owns its database transaction (it runs in a worker/background context, not a
request), and it is defensive: any failure flips the document to `failed` with
the error recorded, so the UI can show it and the job can be retried. Re-running
on a document first clears its previous chunks/vectors, so ingestion is
idempotent (safe to retry) and supports re-indexing.

All external dependencies (storage, embedder, vector store) are injected, so the
whole pipeline is tested with fakes — no OpenAI, Qdrant, or MinIO required.
"""

from __future__ import annotations

import uuid

from anyio import to_thread
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.embeddings.base import EmbeddingProvider
from app.ingestion.chunker import TextChunker, estimate_tokens
from app.ingestion.extractors import extract_text
from app.ingestion.filetypes import detect_format
from app.ingestion.web import fetch_url_text
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, SourceType
from app.storage.base import ObjectStorage
from app.vectorstore.base import VectorPoint, VectorStore

logger = get_logger(__name__)


class IngestionService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        storage: ObjectStorage,
        embedder: EmbeddingProvider,
        vector_store: VectorStore,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self.session = session
        self.storage = storage
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunker = TextChunker(chunk_size, chunk_overlap)

    async def ingest(self, document_id: uuid.UUID) -> None:
        document = await self.session.get(Document, document_id)
        if document is None:
            logger.warning("ingest_document_missing", document_id=str(document_id))
            return
        # Only process fresh or previously-failed documents.
        if document.status not in (DocumentStatus.PENDING, DocumentStatus.FAILED):
            return

        try:
            document.status = DocumentStatus.PROCESSING
            document.error = None
            await self.session.commit()

            text, discovered_title = await self._load_text(document)
            chunks = self.chunker.split_text(text)
            if not chunks:
                raise ValueError("No extractable text found in document.")

            await self._clear_previous(document)

            await self.vector_store.ensure_collection(self.embedder.dimension)
            vectors = await self.embedder.embed_documents(chunks)

            points, rows = self._build_records(document, chunks, vectors)
            self.session.add_all(rows)
            await self.vector_store.upsert(points)

            document.chunk_count = len(rows)
            title_is_placeholder = not document.title or document.title == document.source_url
            if discovered_title and document.source_type is SourceType.URL and title_is_placeholder:
                document.title = discovered_title[:512]
            document.status = DocumentStatus.INDEXED
            await self.session.commit()
            logger.info("ingested", document_id=str(document.id), chunks=len(rows))

        except Exception as exc:  # noqa: BLE001 - we record any failure and continue
            await self._mark_failed(document_id, exc)

    async def _load_text(self, document: Document) -> tuple[str, str | None]:
        if document.source_type is SourceType.FILE:
            if not document.storage_key:
                raise ValueError("File document has no storage key.")
            data = await self.storage.get_object(document.storage_key)
            fmt = detect_format(document.filename or "")
            if fmt is None:
                raise ValueError("Unsupported file type.")
            # Extraction is sync/CPU-bound -> offload from the event loop.
            text = await to_thread.run_sync(extract_text, fmt, data)
            return text, None

        if not document.source_url:
            raise ValueError("URL document has no source URL.")
        return await fetch_url_text(document.source_url)

    async def _clear_previous(self, document: Document) -> None:
        """Idempotency/re-index safety: drop any existing chunks + vectors first."""
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        await self.vector_store.delete_by_document(document.org_id, document.id)

    def _build_records(
        self, document: Document, chunks: list[str], vectors: list[list[float]]
    ) -> tuple[list[VectorPoint], list[DocumentChunk]]:
        points: list[VectorPoint] = []
        rows: list[DocumentChunk] = []
        for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True)):
            chunk_id = uuid.uuid4()
            rows.append(
                DocumentChunk(
                    id=chunk_id,
                    org_id=document.org_id,
                    document_id=document.id,
                    chunk_index=index,
                    content=content,
                    token_count=estimate_tokens(content),
                    embedding_model=self.embedder.model,
                )
            )
            points.append(
                VectorPoint(
                    id=chunk_id,
                    vector=vector,
                    payload={
                        "org_id": str(document.org_id),
                        "document_id": str(document.id),
                        "chunk_index": index,
                    },
                )
            )
        return points, rows

    async def _mark_failed(self, document_id: uuid.UUID, exc: Exception) -> None:
        await self.session.rollback()
        document = await self.session.get(Document, document_id)
        if document is not None:
            document.status = DocumentStatus.FAILED
            document.error = str(exc)[:2000]
            await self.session.commit()
        logger.exception("ingestion_failed", document_id=str(document_id))
