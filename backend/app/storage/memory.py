"""In-memory object storage — a dependency-free fake for tests.

Backs the same `ObjectStorage` interface with a dict, so the ingestion pipeline
and upload endpoints can be tested without MinIO/S3 (or moto). Never used in
production; wired only via test overrides.
"""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.storage.base import ObjectStorage


class InMemoryObjectStorage(ObjectStorage):
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def ensure_bucket(self) -> None:
        return None

    async def put_object(self, key: str, data: bytes, content_type: str | None = None) -> None:
        self._store[key] = data

    async def get_object(self, key: str) -> bytes:
        try:
            return self._store[key]
        except KeyError as exc:
            raise NotFoundError(f"Object not found: {key}") from exc

    async def delete_object(self, key: str) -> None:
        self._store.pop(key, None)

    async def generate_presigned_url(self, key: str, *, expires_in: int = 3600) -> str:
        return f"memory://{key}"
