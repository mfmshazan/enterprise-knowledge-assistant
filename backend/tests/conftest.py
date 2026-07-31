"""Shared pytest fixtures.

Test strategy for Phase 2:
* **Database** — a fresh in-memory SQLite per test, created directly from the ORM
  metadata (fast, isolated, no Postgres service needed). `StaticPool` keeps a
  single underlying connection so the in-memory DB persists across sessions
  within one test.
* **Auth** — the app's `get_auth_provider` is overridden with `DevAuthProvider`,
  so tests authenticate with simple `dev:<email>[:<org>[:<role>]]` bearer tokens
  and never touch Clerk or JWKS.
* **Wiring** — `get_db` is overridden to use the test session factory. Because
  handlers/deps depend on the exact `get_db`/`get_auth_provider` objects, these
  overrides fully redirect the app to the test doubles.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  # register models on Base.metadata
from app.auth.dev import DevAuthProvider
from app.auth.factory import get_auth_provider
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture
async def db_sessionmaker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    await engine.dispose()


@pytest.fixture
async def db_session(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with db_sessionmaker() as session:
        yield session


@pytest.fixture
def app(db_sessionmaker: async_sessionmaker[AsyncSession]) -> FastAPI:
    application = create_app()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        async with db_sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_auth_provider] = lambda: DevAuthProvider()
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


def auth(token: str) -> dict[str, str]:
    """Build an Authorization header for a dev token.

    Example: auth("dev:alice@acme.com:acme:owner")
    """
    return {"Authorization": f"Bearer {token}"}
