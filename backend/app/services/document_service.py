"""Document use-cases: upload, register-from-URL, list, get, delete.

This is the front half of the ingestion write path. It stores the raw bytes in
object storage, creates a `pending` Document row, and returns immediately — the
heavy extraction/embedding work is done later by the worker (Phase 3d+). Storing
the file *before* creating the row means a failed DB write leaves at most an
orphaned object (cheaply garbage-collected), never a row pointing at missing
bytes.

All DB access goes through the org-scoped `DocumentRepository`, so a service
instance is bound to a single tenant and cannot touch another's documents.
"""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from app.core.config import settings
from app.core.exceptions import NotFoundError, PayloadTooLargeError, ValidationError
from app.ingestion.filetypes import SUPPORTED_EXTENSIONS, detect_format
from app.models.document import Document
from app.models.enums import DocumentStatus, SourceType
from app.repositories.document import DocumentRepository
from app.storage.base import ObjectStorage


class DocumentService:
    def __init__(self, documents: DocumentRepository, storage: ObjectStorage) -> None:
        self.documents = documents
        self.storage = storage

    async def create_from_upload(
        self,
        *,
        filename: str,
        content: bytes,
        content_type: str | None,
        uploaded_by: uuid.UUID | None,
    ) -> Document:
        if detect_format(filename) is None:
            raise ValidationError(
                f"Unsupported file type. Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}."
            )

        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise PayloadTooLargeError(f"File exceeds the {settings.MAX_UPLOAD_MB} MB limit.")
        if len(content) == 0:
            raise ValidationError("Uploaded file is empty.")

        safe_name = PurePosixPath(filename).name
        doc_id = uuid.uuid4()
        storage_key = f"documents/{self.documents.org_id}/{doc_id}/{safe_name}"

        # Store bytes first; only then record the row that references them.
        await self.storage.put_object(storage_key, content, content_type)

        document = Document(
            id=doc_id,
            source_type=SourceType.FILE,
            title=PurePosixPath(safe_name).stem or safe_name,
            filename=safe_name,
            content_type=content_type,
            storage_key=storage_key,
            size_bytes=len(content),
            status=DocumentStatus.PENDING,
            uploaded_by_user_id=uploaded_by,
        )
        self.documents.add(document)  # stamps org_id
        await self.documents.session.flush()
        return document

    async def create_from_url(
        self,
        *,
        url: str,
        title: str | None,
        uploaded_by: uuid.UUID | None,
    ) -> Document:
        document = Document(
            source_type=SourceType.URL,
            title=title or url,
            source_url=url,
            status=DocumentStatus.PENDING,
            uploaded_by_user_id=uploaded_by,
        )
        self.documents.add(document)
        await self.documents.session.flush()
        return document

    async def list(self) -> list[Document]:
        return await self.documents.list_recent()

    async def get(self, document_id: uuid.UUID) -> Document:
        document = await self.documents.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.")
        return document

    async def delete(self, document_id: uuid.UUID) -> None:
        document = await self.get(document_id)
        if document.storage_key:
            await self.storage.delete_object(document.storage_key)
        # Vector cleanup is wired when the vector store lands (Phase 3f).
        await self.documents.delete(document)
