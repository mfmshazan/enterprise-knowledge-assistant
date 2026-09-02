"""ApiKeyService — generation, verification, and lifecycle management."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from app.core.exceptions import NotFoundError
from app.models.api_key import ApiKey
from app.models.user import User
from app.repositories.api_key import ApiKeyRepository

_KEY_PREFIX = "eka_live_"


def _hash_key(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class ApiKeyService:
    def __init__(self, api_key_repo: ApiKeyRepository) -> None:
        self.api_key_repo = api_key_repo

    async def create_key(
        self,
        *,
        name: str,
        user: User | None = None,
        expires_in_days: int | None = None,
    ) -> tuple[ApiKey, str]:
        random_part = secrets.token_urlsafe(32)
        secret_key = f"{_KEY_PREFIX}{random_part}"
        key_prefix = secret_key[:16] + "..."
        key_hash = _hash_key(secret_key)

        now = datetime.now(UTC).replace(tzinfo=None)
        expires_at = now + timedelta(days=expires_in_days) if expires_in_days is not None else None

        api_key = ApiKey(
            org_id=self.api_key_repo.org_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            created_by_user_id=user.id if user else None,
            expires_at=expires_at,
        )
        self.api_key_repo.add(api_key)
        await self.api_key_repo.session.commit()
        return api_key, secret_key

    async def list_keys(self) -> list[ApiKey]:
        return await self.api_key_repo.list_all()

    async def revoke_key(self, key_id: uuid.UUID) -> ApiKey:
        key = await self.api_key_repo.revoke(key_id)
        if key is None:
            raise NotFoundError("API Key not found.")
        await self.api_key_repo.session.commit()
        return key

    async def verify_secret(self, secret: str) -> ApiKey | None:
        key_hash = _hash_key(secret)
        key = await self.api_key_repo.get_by_hash(key_hash)
        if key is None or not key.is_active:
            return None
        return key
