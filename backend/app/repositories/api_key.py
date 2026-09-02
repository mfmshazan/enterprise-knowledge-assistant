"""ApiKey repository — org-scoped."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc

from app.models.api_key import ApiKey
from app.repositories.base import OrgScopedRepository


class ApiKeyRepository(OrgScopedRepository[ApiKey]):
    model = ApiKey

    async def list_active(self) -> list[ApiKey]:
        now = datetime.now(UTC).replace(tzinfo=None)
        stmt = (
            self._scoped()
            .where(ApiKey.revoked_at.is_(None))
            .where((ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > now))
            .order_by(desc(ApiKey.created_at))
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def list_all(self) -> list[ApiKey]:
        stmt = self._scoped().order_by(desc(ApiKey.created_at))
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        stmt = self._scoped().where(ApiKey.key_hash == key_hash)
        return await self.session.scalar(stmt)

    async def revoke(self, key_id: uuid.UUID) -> ApiKey | None:
        key = await self.get(key_id)
        if key is None or key.revoked_at is not None:
            return key
        key.revoked_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.flush()
        return key
