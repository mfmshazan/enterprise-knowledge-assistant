"""Membership: the many-to-many join between users and organizations, carrying
the user's role *in that specific org*.

This is what makes the workspace model work: one user can belong to several orgs
with a different role in each. The `UniqueConstraint(user_id, org_id)` enforces
"at most one membership per (user, org)" at the database level — the source of
truth for authorization, not just an application check.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Role

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "org_id", name="uq_membership_user_org"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="role", native_enum=False, length=32),
        default=Role.MEMBER,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="memberships")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Membership user_id={self.user_id} org_id={self.org_id} role={self.role}>"
