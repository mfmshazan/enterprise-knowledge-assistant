"""Citation — a source that grounded an assistant message.

A citation is a real foreign-key link from a message to the `DocumentChunk` that
supported it (not free text), which is what makes an answer *verifiable* — you
can click through to the exact passage.

We also snapshot `document_title` and `snippet` at answer time so the citation
remains meaningful even if the underlying document or chunk is later deleted
(the FKs then null out, but the displayed source survives).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.message import Message


class Citation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "citations"

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Soft links: keep the citation even if the source is removed.
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # the [n] marker, 1-based
    document_title: Mapped[str] = mapped_column(String(512), nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)

    message: Mapped[Message] = relationship(back_populates="citations")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Citation msg={self.message_id} rank={self.rank}>"
