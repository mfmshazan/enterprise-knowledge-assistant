"""The object-storage contract.

Deliberately tiny: put/get/delete bytes by key, ensure the bucket exists, and
mint a presigned download URL. Keys are opaque strings; callers decide the
layout (we use `documents/{org_id}/{document_id}/{filename}`). All methods are
async so implementations that do blocking I/O (boto3) can offload to a thread
without changing call sites.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    @abstractmethod
    async def ensure_bucket(self) -> None:
        """Create the configured bucket if it does not already exist."""

    @abstractmethod
    async def put_object(self, key: str, data: bytes, content_type: str | None = None) -> None:
        """Store `data` at `key`, overwriting any existing object."""

    @abstractmethod
    async def get_object(self, key: str) -> bytes:
        """Return the bytes stored at `key`. Raises if the key is missing."""

    @abstractmethod
    async def delete_object(self, key: str) -> None:
        """Delete `key`. Idempotent — deleting a missing key is not an error."""

    @abstractmethod
    async def generate_presigned_url(self, key: str, *, expires_in: int = 3600) -> str:
        """Return a time-limited URL a browser can use to download `key`."""
