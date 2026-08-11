"""Document request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus, SourceType


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: SourceType
    title: str
    filename: str | None
    content_type: str | None
    source_url: str | None
    size_bytes: int | None
    status: DocumentStatus
    error: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class UrlIngestRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048, examples=["https://example.com/docs"])
    title: str | None = Field(default=None, max_length=512)
