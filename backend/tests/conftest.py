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

import uuid
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
from app.embeddings.factory import get_embedding_provider
from app.embeddings.fake import FakeEmbeddingProvider
from app.ingestion.dispatcher import IngestionDispatcher, get_ingestion_dispatcher
from app.llm.factory import get_llm_provider
from app.llm.fake import FakeLLMProvider
from app.main import create_app
from app.storage.factory import get_object_storage
from app.storage.memory import InMemoryObjectStorage
from app.vectorstore.factory import get_vector_store
from app.vectorstore.memory import InMemoryVectorStore

# Shared fake embedder dimension for tests (query + stored vectors must match).
TEST_EMBED_DIM = 16


class RecordingDispatcher(IngestionDispatcher):
    """Test dispatcher that records enqueued document ids instead of running the
    real pipeline — keeps API tests isolated from ingestion/OpenAI/Qdrant."""

    def __init__(self) -> None:
        self.enqueued: list[uuid.UUID] = []

    async def enqueue(self, document_id: uuid.UUID) -> None:
        self.enqueued.append(document_id)


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
def storage() -> InMemoryObjectStorage:
    """A per-test in-memory object store, shared between the app override and
    the test so assertions can inspect stored bytes."""
    return InMemoryObjectStorage()


@pytest.fixture
def vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def dispatcher() -> RecordingDispatcher:
    return RecordingDispatcher()


@pytest.fixture
def app(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    storage: InMemoryObjectStorage,
    vector_store: InMemoryVectorStore,
    dispatcher: RecordingDispatcher,
) -> FastAPI:
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
    application.dependency_overrides[get_object_storage] = lambda: storage
    application.dependency_overrides[get_vector_store] = lambda: vector_store
    application.dependency_overrides[get_ingestion_dispatcher] = lambda: dispatcher
    application.dependency_overrides[get_embedding_provider] = lambda: FakeEmbeddingProvider(
        dimension=TEST_EMBED_DIM
    )
    application.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider()
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
