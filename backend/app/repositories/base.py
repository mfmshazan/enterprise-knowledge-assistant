"""Generic base repository.

Provides the handful of operations common to every entity (get by id, add,
delete, list) so concrete repositories only add entity-specific queries. It is
intentionally thin: repositories orchestrate queries; they do not commit. The
request-scoped transaction (see `get_db`) owns commit/rollback, so a repository
never partially persists state on its own.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
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
