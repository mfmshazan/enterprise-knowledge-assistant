"""DocumentChunk — a single embeddable slice of a document.

Documents are split into overlapping chunks because embedding models have a
bounded context and retrieval works best on focused passages. Each chunk's
`content` is stored here (source of truth) alongside `embedding_model`, so the
vector index can be regenerated at any time (ADR-0002).

Design note: the chunk's primary key (`id`) doubles as its **vector id** in
Qdrant. That 1:1 mapping means we need no separate join table between rows and
vectors — given a search hit's id, we can load the exact chunk (and its parent
document) for citation.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        # A document's chunk positions are unique -> stable, reproducible ordering.
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_document_index"),
    )

    # Denormalized org_id: lets us tenant-filter chunks directly and mirrors the
    # value we store in the Qdrant payload for isolated vector search.
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)

    document: Mapped[Document] = relationship(back_populates="chunks")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<DocumentChunk doc={self.document_id} idx={self.chunk_index}>"
