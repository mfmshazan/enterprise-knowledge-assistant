"""User model.

`external_id` is the identity from the auth provider (Clerk's `user_...` id, or a
synthesized id from the dev provider). It is unique and indexed because *every*
authenticated request looks a user up by it. The local `id` (UUID) is what the
rest of the schema references via foreign keys — we never FK to the external id,
so we can swap auth providers without rewriting relationships.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.membership import Membership


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<User id={self.id} email={self.email!r}>"
