"""Tests for API Key generation, listing, and revocation."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth

ORGS = "/api/v1/orgs"
OWNER = "dev:alice@acme.com:acme:owner"
MEMBER = "dev:bob@acme.com:acme:member"


async def _org_id(client: AsyncClient, token: str) -> str:
    rows = (await client.get(ORGS, headers=auth(token))).json()
    return str(rows[0]["organization"]["id"])


async def test_api_key_lifecycle(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)

    # 1. Create an API key
    create_resp = await client.post(
        f"{ORGS}/{org_id}/api-keys",
        json={"name": "Production Service Key", "expires_in_days": 30},
        headers=auth(OWNER),
    )
    assert create_resp.status_code == 201
    created_body = create_resp.json()
    key_id = created_body["id"]
    secret_key = created_body["secret_key"]
    assert secret_key.startswith("eka_live_")
    assert created_body["name"] == "Production Service Key"
    assert created_body["is_active"] is True

    # 2. List API keys
    list_resp = await client.get(f"{ORGS}/{org_id}/api-keys", headers=auth(OWNER))
    assert list_resp.status_code == 200
    keys = list_resp.json()
    assert any(k["id"] == key_id for k in keys)

    # 3. Revoke API key
    revoke_resp = await client.delete(f"{ORGS}/{org_id}/api-keys/{key_id}", headers=auth(OWNER))
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["is_active"] is False


async def test_member_cannot_manage_api_keys(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    await client.get(ORGS, headers=auth(MEMBER))  # provision member

    resp = await client.post(
        f"{ORGS}/{org_id}/api-keys",
        json={"name": "Hack Key"},
        headers=auth(MEMBER),
    )
    assert resp.status_code == 403
