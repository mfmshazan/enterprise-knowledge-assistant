"""Document upload/list/get/delete API, including tenant isolation and RBAC."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.exceptions import NotFoundError
from app.storage.memory import InMemoryObjectStorage
from tests.conftest import RecordingDispatcher, auth

ORGS = "/api/v1/orgs"
OWNER = "dev:alice@acme.com:acme:owner"
MEMBER = "dev:bob@acme.com:acme"
OTHER = "dev:carol@globex.com:globex:owner"


async def _org_id(client: AsyncClient, token: str) -> str:
    rows = (await client.get(ORGS, headers=auth(token))).json()
    return str(rows[0]["organization"]["id"])


def _docs_url(org_id: str) -> str:
    return f"{ORGS}/{org_id}/documents"


async def test_upload_requires_auth(client: AsyncClient) -> None:
    # No token, and a made-up org id -> unauthenticated.
    resp = await client.post(
        _docs_url(str(uuid.uuid4())),
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 401


async def test_upload_stores_file_and_creates_pending_document(
    client: AsyncClient, storage: InMemoryObjectStorage
) -> None:
    org_id = await _org_id(client, OWNER)
    resp = await client.post(
        _docs_url(org_id),
        files={"file": ("report.txt", b"hello world", "text/plain")},
        headers=auth(OWNER),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["source_type"] == "file"
    assert body["filename"] == "report.txt"
    assert body["size_bytes"] == len(b"hello world")

    # The bytes really landed in object storage under the org-scoped key.
    key = f"documents/{org_id}/{body['id']}/report.txt"
    assert await storage.get_object(key) == b"hello world"


async def test_upload_enqueues_ingestion(
    client: AsyncClient, dispatcher: RecordingDispatcher
) -> None:
    org_id = await _org_id(client, OWNER)
    resp = await client.post(
        _docs_url(org_id),
        files={"file": ("a.md", b"# hello", "text/markdown")},
        headers=auth(OWNER),
    )
    doc_id = uuid.UUID(resp.json()["id"])
    assert doc_id in dispatcher.enqueued


async def test_upload_rejects_unsupported_type(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    resp = await client.post(
        _docs_url(org_id),
        files={"file": ("evil.exe", b"MZ", "application/octet-stream")},
        headers=auth(OWNER),
    )
    assert resp.status_code == 422


async def test_upload_rejects_empty_file(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    resp = await client.post(
        _docs_url(org_id),
        files={"file": ("empty.md", b"", "text/markdown")},
        headers=auth(OWNER),
    )
    assert resp.status_code == 422


async def test_url_ingest_creates_pending_url_document(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    resp = await client.post(
        f"{_docs_url(org_id)}/url",
        json={"url": "https://example.com/docs", "title": "Example"},
        headers=auth(OWNER),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["source_type"] == "url"
    assert body["source_url"] == "https://example.com/docs"
    assert body["status"] == "pending"


async def test_list_and_get_document(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    created = await client.post(
        _docs_url(org_id),
        files={"file": ("a.md", b"# hi", "text/markdown")},
        headers=auth(OWNER),
    )
    doc_id = created.json()["id"]

    listing = await client.get(_docs_url(org_id), headers=auth(OWNER))
    assert listing.status_code == 200
    assert any(d["id"] == doc_id for d in listing.json())

    got = await client.get(f"{_docs_url(org_id)}/{doc_id}", headers=auth(OWNER))
    assert got.status_code == 200
    assert got.json()["id"] == doc_id


async def test_get_unknown_document_404(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    resp = await client.get(f"{_docs_url(org_id)}/{uuid.uuid4()}", headers=auth(OWNER))
    assert resp.status_code == 404


async def test_tenant_isolation(client: AsyncClient) -> None:
    acme_id = await _org_id(client, OWNER)
    created = await client.post(
        _docs_url(acme_id),
        files={"file": ("secret.txt", b"acme only", "text/plain")},
        headers=auth(OWNER),
    )
    doc_id = created.json()["id"]

    # Carol belongs to a different org; she must not be a member of acme.
    await client.get(ORGS, headers=auth(OTHER))  # provision Carol + globex
    cross = await client.get(f"{_docs_url(acme_id)}/{doc_id}", headers=auth(OTHER))
    assert cross.status_code == 404  # not a member -> org "not found"


async def test_delete_requires_admin(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    await client.get(ORGS, headers=auth(MEMBER))  # provision Bob as member
    created = await client.post(
        _docs_url(org_id),
        files={"file": ("a.txt", b"x", "text/plain")},
        headers=auth(OWNER),
    )
    doc_id = created.json()["id"]

    denied = await client.delete(f"{_docs_url(org_id)}/{doc_id}", headers=auth(MEMBER))
    assert denied.status_code == 403


async def test_admin_can_delete_and_file_removed(
    client: AsyncClient, storage: InMemoryObjectStorage
) -> None:
    org_id = await _org_id(client, OWNER)
    created = await client.post(
        _docs_url(org_id),
        files={"file": ("a.txt", b"bytes", "text/plain")},
        headers=auth(OWNER),
    )
    doc_id = created.json()["id"]
    key = f"documents/{org_id}/{doc_id}/a.txt"
    assert await storage.get_object(key) == b"bytes"

    deleted = await client.delete(f"{_docs_url(org_id)}/{doc_id}", headers=auth(OWNER))
    assert deleted.status_code == 204

    gone = await client.get(f"{_docs_url(org_id)}/{doc_id}", headers=auth(OWNER))
    assert gone.status_code == 404
    # storage object removed too
    with pytest.raises(NotFoundError):
        await storage.get_object(key)
