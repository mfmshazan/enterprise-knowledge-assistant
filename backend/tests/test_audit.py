"""Tests for audit logging and retrieval."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth

ORGS = "/api/v1/orgs"
OWNER = "dev:alice@acme.com:acme:owner"
ADMIN = "dev:carol@acme.com:acme:admin"
MEMBER = "dev:bob@acme.com:acme:member"


async def _org_id(client: AsyncClient, token: str) -> str:
    rows = (await client.get(ORGS, headers=auth(token))).json()
    return str(rows[0]["organization"]["id"])


async def test_audit_logs_recorded_on_org_and_member_actions(
    client: AsyncClient,
) -> None:
    org_id = await _org_id(client, OWNER)
    await client.get(ORGS, headers=auth(ADMIN))  # provision admin

    # Invite a new member
    invite_resp = await client.post(
        f"{ORGS}/{org_id}/members",
        json={"email": "newuser@acme.com", "role": "member"},
        headers=auth(OWNER),
    )
    assert invite_resp.status_code == 201

    # Fetch audit logs as owner
    resp = await client.get(f"{ORGS}/{org_id}/audit-logs", headers=auth(OWNER))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    actions = [item["action"] for item in body["items"]]
    assert "member.invite" in actions


async def test_audit_logs_restricted_to_admins(client: AsyncClient) -> None:
    org_id = await _org_id(client, OWNER)
    await client.get(ORGS, headers=auth(MEMBER))  # provision member

    resp = await client.get(f"{ORGS}/{org_id}/audit-logs", headers=auth(MEMBER))
    assert resp.status_code == 403
