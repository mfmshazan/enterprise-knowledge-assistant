"""End-to-end chat tests (retrieval + grounding + persistence) using fakes."""

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

CONTENT = "The parental leave policy grants 16 weeks of paid leave."


async def _org_id(client: AsyncClient, token: str) -> str:
    rows = (await client.get(ORGS, headers=auth(token))).json()
    return str(rows[0]["organization"]["id"])


async def _seed(
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
                title="Policies",
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


def _chat_url(org_id: str) -> str:
    return f"{ORGS}/{org_id}/chat"


async def test_chat_answers_with_citations(
    client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = await _org_id(client, OWNER)
    await _seed(db_sessionmaker, vector_store, uuid.UUID(org_id))

    resp = await client.post(
        _chat_url(org_id),
        json={"message": "How much parental leave do we get?"},
        headers=auth(OWNER),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation_id"]
    msg = body["message"]
    assert msg["role"] == "assistant"
    assert msg["content"]
    assert len(msg["citations"]) == 1
    assert msg["citations"][0]["document_title"] == "Policies"
    assert msg["citations"][0]["rank"] == 1


async def test_chat_without_context_still_answers_without_citations(
    client: AsyncClient,
) -> None:
    org_id = await _org_id(client, OWNER)  # no documents seeded
    resp = await client.post(
        _chat_url(org_id),
        json={"message": "What is the capital of Mars?"},
        headers=auth(OWNER),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"]["content"]
    assert body["message"]["citations"] == []


async def test_chat_continues_conversation_and_history(
    client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = await _org_id(client, OWNER)
    await _seed(db_sessionmaker, vector_store, uuid.UUID(org_id))

    first = await client.post(
        _chat_url(org_id), json={"message": "First question?"}, headers=auth(OWNER)
    )
    conv_id = first.json()["conversation_id"]

    second = await client.post(
        _chat_url(org_id),
        json={"message": "Follow-up question?", "conversation_id": conv_id},
        headers=auth(OWNER),
    )
    assert second.json()["conversation_id"] == conv_id

    detail = await client.get(f"{_chat_url(org_id)}/conversations/{conv_id}", headers=auth(OWNER))
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    # 2 user + 2 assistant, in order.
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]

    listing = await client.get(f"{_chat_url(org_id)}/conversations", headers=auth(OWNER))
    assert any(c["id"] == conv_id and c["title"] == "First question?" for c in listing.json())


async def test_chat_requires_membership(
    client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = await _org_id(client, OWNER)
    await _seed(db_sessionmaker, vector_store, uuid.UUID(org_id))
    await client.get(ORGS, headers=auth(OUTSIDER))  # provision outsider

    resp = await client.post(_chat_url(org_id), json={"message": "secret?"}, headers=auth(OUTSIDER))
    assert resp.status_code == 404


async def test_chat_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(f"{ORGS}/{uuid.uuid4()}/chat", json={"message": "hi"})
    assert resp.status_code == 401


async def test_unknown_conversation_returns_404(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    resp = await client.get(
        f"{_chat_url(org_id)}/conversations/{uuid.uuid4()}", headers=auth(OWNER)
    )
    assert resp.status_code == 404


async def test_chat_stream_returns_sse_events(
    client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = await _org_id(client, OWNER)
    await _seed(db_sessionmaker, vector_store, uuid.UUID(org_id))

    resp = await client.post(
        f"{_chat_url(org_id)}/stream",
        json={"message": "How much leave?", "mode": "agentic"},
        headers=auth(OWNER),
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    text = resp.text
    assert "data: " in text
    assert '"event": "done"' in text
    assert '"role": "assistant"' in text


async def test_chat_with_explicit_linear_mode(
    client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vector_store: InMemoryVectorStore,
) -> None:
    org_id = await _org_id(client, OWNER)
    await _seed(db_sessionmaker, vector_store, uuid.UUID(org_id))

    resp = await client.post(
        _chat_url(org_id),
        json={"message": "How much leave?", "mode": "linear"},
        headers=auth(OWNER),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"]["content"]
    assert len(body["message"]["citations"]) == 1
