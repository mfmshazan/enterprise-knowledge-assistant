"""Behavioral tests for the in-memory object storage fake."""

from __future__ import annotations

import pytest

from app.core.exceptions import NotFoundError
from app.storage.memory import InMemoryObjectStorage


async def test_put_then_get_roundtrip() -> None:
    storage = InMemoryObjectStorage()
    await storage.put_object("docs/a.txt", b"hello", content_type="text/plain")
    assert await storage.get_object("docs/a.txt") == b"hello"


async def test_get_missing_raises_not_found() -> None:
    storage = InMemoryObjectStorage()
    with pytest.raises(NotFoundError):
        await storage.get_object("nope")


async def test_delete_is_idempotent() -> None:
    storage = InMemoryObjectStorage()
    await storage.put_object("k", b"x")
    await storage.delete_object("k")
    await storage.delete_object("k")  # deleting again must not raise
    with pytest.raises(NotFoundError):
        await storage.get_object("k")


async def test_presigned_url_shape() -> None:
    storage = InMemoryObjectStorage()
    assert await storage.generate_presigned_url("k") == "memory://k"
