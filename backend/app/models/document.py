"""Document model — a single ingested source (uploaded file or fetched URL).

This is the first *tenant-owned* entity: every row carries `org_id`, and all
access goes through an org-scoped repository so one organization can never see
another's documents.

The row is the source of truth for ingestion state. `status` moves
pending -> processing -> indexed | failed, and `error` records why a failure
happened so it can be surfaced in the UI and retried. `storage_key` points at
the raw bytes in object storage (files); `source_url` holds the origin (URLs).
Keeping the raw file + this row means the vector index is always rebuildable.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DocumentStatus, SourceType

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Keep the document if the uploader is later removed -> SET NULL, nullable.
    uploaded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type", native_enum=False, length=16),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Exactly one of these is set depending on source_type.
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status", native_enum=False, length=16),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(default=0, nullable=False)

    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Document id={self.id} title={self.title!r} status={self.status}>"
