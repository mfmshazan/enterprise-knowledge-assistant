"""Shared pytest fixtures.

`client` yields an httpx AsyncClient wired to the ASGI app *in-process* (no
network, no running server). `LifespanManager` ensures startup/shutdown hooks
run so the app is exercised exactly as in production.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
