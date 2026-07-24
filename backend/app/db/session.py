"""Async engine, session factory, and the request-scoped `get_db` dependency.

Lifecycle: the engine is created once at app startup (`init_engine`, called from
`main.lifespan`) and disposed at shutdown (`dispose_engine`). We keep the engine
and sessionmaker at module scope rather than on `app.state` so that both the
FastAPI dependency and background workers (Phase 3) can reach them uniformly.

Transaction model: **one transaction per request.** `get_db` commits if the
handler returns normally and rolls back on any exception. Handlers and services
therefore never call `commit()` themselves — a request is atomic by default,
which prevents half-written state from leaking out on errors.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str | None = None) -> None:
    """Create the global async engine + session factory. Idempotent-ish: calling
    again replaces the previous engine (used by tests to point at SQLite)."""
    global _engine, _sessionmaker

    url = database_url or settings.DATABASE_URL
    # `pool_pre_ping` transparently recycles connections dropped by the DB/proxy,
    # avoiding "server closed the connection unexpectedly" after idle periods.
    _engine = create_async_engine(url, pool_pre_ping=True, future=True)
    _sessionmaker = async_sessionmaker(
        _engine,
        expire_on_commit=False,  # keep attributes usable after commit (for responses)
        autoflush=False,
    )
    logger.info("db_engine_initialized", dialect=_engine.dialect.name)


async def dispose_engine() -> None:
    """Close all pooled connections on shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        logger.info("db_engine_disposed")
    _engine = None
    _sessionmaker = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Call init_engine() first.")
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("Database engine is not initialized. Call init_engine() first.")
    return _sessionmaker


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped, transactional session."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
