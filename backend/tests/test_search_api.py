"""End-to-end test of the /search endpoint (auth + retrieval wired together)."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.embeddings.fake import FakeEmbeddingProvider
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, SourceType
from app.vectorstore.base import VectorPoint
from app.vectorstore.memory import InMemoryVectorStore
from tests.conftest import TEST_EMBED_DIM, auth

ORGS = "/api/v1/orgs"
OWNER = "dev:alice@acme.com:acme:owner"
OUTSIDER = "dev:bob@globex.com:globex:owner"

CONTENT = "The annual leave allowance is 25 days per year."


async def _org_id(client: AsyncClient, token: str) -> str:
    rows = (await client.get(ORGS, headers=auth(token))).json()
    return str(rows[0]["organization"]["id"])


async def _seed_indexed_doc(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
    org_id: uuid.UUID,
) -> None:
    embedder = FakeEmbeddingProvider(dimension=TEST_EMBED_DIM)
    doc_id, chunk_id = uuid.uuid4(), uuid.uuid4()
    async with db_sessionmaker() as session:
        session.add(
            Document(
                id=doc_id,
                org_id=org_id,
                source_type=SourceType.FILE,
                title="HR Handbook",
                status=DocumentStatus.INDEXED,
            )
        )
        session.add(
            DocumentChunk(
                id=chunk_id, org_id=org_id, document_id=doc_id, chunk_index=0, content=CONTENT
            )
        )
        await session.commit()

    (vector,) = await embedder.embed_documents([CONTENT])
    await vector_store.upsert(
        [
            VectorPoint(
                id=chunk_id,
                vector=vector,
                payload={"org_id": str(org_id), "document_id": str(doc_id), "chunk_index": 0},
            )
        ]
    )


async def test_search_returns_relevant_chunk(
    client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = await _org_id(client, OWNER)
    await _seed_indexed_doc(db_sessionmaker, vector_store, uuid.UUID(org_id))

    resp = await client.post(
        f"{ORGS}/{org_id}/search",
        json={"query": CONTENT, "top_k": 3},
        headers=auth(OWNER),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == CONTENT
    assert len(body["results"]) >= 1
    top = body["results"][0]
    assert top["content"] == CONTENT
    assert top["document_title"] == "HR Handbook"
    assert top["score"] > 0.99


async def test_search_requires_membership(
    client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = await _org_id(client, OWNER)
    await _seed_indexed_doc(db_sessionmaker, vector_store, uuid.UUID(org_id))
    await client.get(ORGS, headers=auth(OUTSIDER))  # provision the outsider + their own org

    resp = await client.post(
        f"{ORGS}/{org_id}/search",
        json={"query": CONTENT},
        headers=auth(OUTSIDER),
    )
    assert resp.status_code == 404  # not a member of acme


async def test_search_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(f"{ORGS}/{uuid.uuid4()}/search", json={"query": "hi"})
    assert resp.status_code == 401
