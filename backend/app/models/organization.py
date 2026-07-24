"""Organization (workspace) model — the tenant boundary.

Every tenant-owned entity in later phases (documents, conversations, chunks)
carries an `org_id` that points here. `external_id` is nullable because an org
may originate locally (created via our API) rather than in Clerk. `slug` is a
stable, URL-friendly handle used in the frontend routing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.membership import Membership


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    external_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Organization id={self.id} slug={self.slug!r}>"
