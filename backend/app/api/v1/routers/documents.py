"""Document endpoints, mounted under /orgs/{org_id}/documents.

Access is gated by `DocumentServiceDep` (which requires org membership) for
reads/uploads; deletion additionally requires admin+. Uploads return a `pending`
document immediately — the worker processes it asynchronously (Phase 3d+), and
clients poll GET to watch `status` progress to `indexed`.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import CurrentUser, DocumentServiceDep, require_role
from app.core.exceptions import ValidationError
from app.models.enums import Role
from app.schemas.document import DocumentRead, UrlIngestRequest

router = APIRouter()


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document (PDF/DOCX/Markdown/txt)",
)
async def upload_document(
    service: DocumentServiceDep,
    user: CurrentUser,
    file: Annotated[UploadFile, File(description="The document file to ingest")],
) -> DocumentRead:
    if not file.filename:
        raise ValidationError("A filename is required.")
    content = await file.read()
    document = await service.create_from_upload(
        filename=file.filename,
        content=content,
        content_type=file.content_type,
        uploaded_by=user.id,
    )
    return DocumentRead.model_validate(document)


@router.post(
    "/url",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a web page for ingestion",
)
async def ingest_url(
    payload: UrlIngestRequest,
    service: DocumentServiceDep,
    user: CurrentUser,
) -> DocumentRead:
    document = await service.create_from_url(
        url=payload.url, title=payload.title, uploaded_by=user.id
    )
    return DocumentRead.model_validate(document)


@router.get("", response_model=list[DocumentRead], summary="List documents in the org")
async def list_documents(service: DocumentServiceDep) -> list[DocumentRead]:
    documents = await service.list()
    return [DocumentRead.model_validate(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentRead, summary="Get a document")
async def get_document(document_id: uuid.UUID, service: DocumentServiceDep) -> DocumentRead:
    document = await service.get(document_id)
    return DocumentRead.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(Role.ADMIN))],
    summary="Delete a document (admin+)",
)
async def delete_document(document_id: uuid.UUID, service: DocumentServiceDep) -> None:
    await service.delete(document_id)
