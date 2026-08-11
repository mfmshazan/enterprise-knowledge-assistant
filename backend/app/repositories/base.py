"""Generic base repository.

Provides the handful of operations common to every entity (get by id, add,
delete, list) so concrete repositories only add entity-specific queries. It is
intentionally thin: repositories orchestrate queries; they do not commit. The
request-scoped transaction (see `get_db`) owns commit/rollback, so a repository
never partially persists state on its own.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[ModelT: Base]:
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self.session.scalars(select(self.model).limit(limit).offset(offset))
        return list(result.all())

    def add(self, obj: ModelT) -> ModelT:
        """Stage a new object. `flush` (not commit) makes DB-generated values
        (ids, defaults) available immediately without ending the transaction."""
        self.session.add(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)


class OrgScopedRepository[ModelT: Base]:
    """Base repository for **tenant-owned** entities (those with an `org_id`).

    This is the multi-tenancy guardrail made concrete: the repository cannot be
    constructed without an `org_id`, and every read is filtered by it. There is
    no method to fetch across organizations, so a developer physically cannot
    forget to scope a query — the unscoped path does not exist. `add` also
    stamps `org_id` onto new rows so writes stay inside the tenant boundary.

    (Column access uses `getattr` because the generic `ModelT` is only known to
    be a `Base`; concrete subclasses are the ones guaranteed to have `org_id`.)
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession, org_id: uuid.UUID) -> None:
        self.session = session
        self.org_id = org_id

    def _scoped(self) -> Select[tuple[ModelT]]:
        org_col: Any = getattr(self.model, "org_id")  # noqa: B009
        return select(self.model).where(org_col == self.org_id)

    async def get(self, id_: uuid.UUID) -> ModelT | None:
        id_col: Any = getattr(self.model, "id")  # noqa: B009
        return await self.session.scalar(self._scoped().where(id_col == id_))

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self.session.scalars(self._scoped().limit(limit).offset(offset))
        return list(result.all())

    def add(self, obj: ModelT) -> ModelT:
        setattr(obj, "org_id", self.org_id)  # noqa: B010
        self.session.add(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
