"""Declarative base and shared model mixins.

Two things here that matter for long-term maintainability:

1. **A constraint naming convention.** Without it, databases auto-generate names
   for indexes/constraints, and Alembic autogenerate produces noisy, unstable
   migrations (and you can't reliably `DROP CONSTRAINT` by name). Pinning a
   convention makes migrations deterministic across Postgres and SQLite.

2. **Reusable mixins** for the two columns almost every table needs: a UUID
   primary key and created/updated timestamps. `sqlalchemy.Uuid` is portable —
   it maps to native `UUID` on PostgreSQL and to `CHAR(32)` on SQLite (tests),
   so the same models run in both without change.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Deterministic names for constraints/indexes -> stable Alembic migrations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key generated application-side (portable, non-guessable)."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds server-managed created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
