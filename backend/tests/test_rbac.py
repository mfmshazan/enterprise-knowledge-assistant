"""Role-based access control on member management.

Scenario: a shared org "acme" is provisioned from dev tokens carrying org context
(`dev:<email>:acme:<role>`), then role-change requests are attempted by actors of
differing privilege to prove the guards hold.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.conftest import auth

ME = "/api/v1/users/me"
ORGS = "/api/v1/orgs"

OWNER = "dev:alice@acme.com:acme:owner"
ADMIN = "dev:carol@acme.com:acme:admin"
MEMBER = "dev:bob@acme.com:acme"
OUTSIDER = "dev:dave@globex.com"


async def _provision(client: AsyncClient, token: str) -> None:
    resp = await client.get(ME, headers=auth(token))
    assert resp.status_code == 200


async def _org_id(client: AsyncClient, token: str) -> str:
    rows = (await client.get(ORGS, headers=auth(token))).json()
    return str(rows[0]["organization"]["id"])


async def _member_id(client: AsyncClient, token: str, org_id: str, email: str) -> str:
    members = (await client.get(f"{ORGS}/{org_id}/members", headers=auth(token))).json()
    return next(m["user"]["id"] for m in members if m["user"]["email"] == email)


async def test_member_cannot_change_roles(client: AsyncClient) -> None:
    await _provision(client, OWNER)
    await _provision(client, MEMBER)
    org_id = await _org_id(client, OWNER)
    bob_id = await _member_id(client, OWNER, org_id, "bob@acme.com")

    resp = await client.patch(
        f"{ORGS}/{org_id}/members/{bob_id}", json={"role": "admin"}, headers=auth(MEMBER)
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "permission_denied"


async def test_admin_can_promote_member_to_admin(client: AsyncClient) -> None:
    await _provision(client, OWNER)
    await _provision(client, ADMIN)
    await _provision(client, MEMBER)
    org_id = await _org_id(client, OWNER)
    bob_id = await _member_id(client, OWNER, org_id, "bob@acme.com")

    resp = await client.patch(
        f"{ORGS}/{org_id}/members/{bob_id}", json={"role": "admin"}, headers=auth(ADMIN)
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


async def test_admin_cannot_grant_owner(client: AsyncClient) -> None:
    await _provision(client, OWNER)
    await _provision(client, ADMIN)
    await _provision(client, MEMBER)
    org_id = await _org_id(client, OWNER)
    bob_id = await _member_id(client, OWNER, org_id, "bob@acme.com")

    resp = await client.patch(
        f"{ORGS}/{org_id}/members/{bob_id}", json={"role": "owner"}, headers=auth(ADMIN)
    )
    assert resp.status_code == 403


async def test_owner_can_grant_owner(client: AsyncClient) -> None:
    await _provision(client, OWNER)
    await _provision(client, MEMBER)
    org_id = await _org_id(client, OWNER)
    bob_id = await _member_id(client, OWNER, org_id, "bob@acme.com")

    resp = await client.patch(
        f"{ORGS}/{org_id}/members/{bob_id}", json={"role": "owner"}, headers=auth(OWNER)
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "owner"


async def test_cannot_demote_last_owner(client: AsyncClient) -> None:
    await _provision(client, OWNER)
    org_id = await _org_id(client, OWNER)
    alice_id = await _member_id(client, OWNER, org_id, "alice@acme.com")

    resp = await client.patch(
        f"{ORGS}/{org_id}/members/{alice_id}", json={"role": "admin"}, headers=auth(OWNER)
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


async def test_outsider_gets_404_not_403(client: AsyncClient) -> None:
    await _provision(client, OWNER)
    await _provision(client, OUTSIDER)
    org_id = await _org_id(client, OWNER)
    alice_id = await _member_id(client, OWNER, org_id, "alice@acme.com")

    # Dave is not a member of acme -> membership resolves to 404 before RBAC.
    resp = await client.patch(
        f"{ORGS}/{org_id}/members/{alice_id}", json={"role": "member"}, headers=auth(OUTSIDER)
    )
    assert resp.status_code == 404


async def test_patch_unknown_member_returns_404(client: AsyncClient) -> None:
    await _provision(client, OWNER)
    org_id = await _org_id(client, OWNER)
    ghost = uuid.uuid4()

    resp = await client.patch(
        f"{ORGS}/{org_id}/members/{ghost}", json={"role": "admin"}, headers=auth(OWNER)
    )
    assert resp.status_code == 404
