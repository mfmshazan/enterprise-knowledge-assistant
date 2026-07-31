"""Authentication + JIT provisioning via GET /users/me."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth

ME = "/api/v1/users/me"


async def test_me_requires_authentication(client: AsyncClient) -> None:
    resp = await client.get(ME)
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


async def test_me_rejects_malformed_dev_token(client: AsyncClient) -> None:
    resp = await client.get(ME, headers=auth("not-a-dev-token"))
    assert resp.status_code == 401


async def test_me_provisions_user_on_first_login(client: AsyncClient) -> None:
    resp = await client.get(ME, headers=auth("dev:alice@acme.com"))
    assert resp.status_code == 200

    body = resp.json()
    assert body["user"]["email"] == "alice@acme.com"
    assert body["user"]["full_name"] == "Alice"
    assert body["memberships"] == []


async def test_me_is_idempotent_same_user(client: AsyncClient) -> None:
    first = await client.get(ME, headers=auth("dev:alice@acme.com"))
    second = await client.get(ME, headers=auth("dev:alice@acme.com"))
    assert first.json()["user"]["id"] == second.json()["user"]["id"]


async def test_me_provisions_org_and_membership_from_token(client: AsyncClient) -> None:
    resp = await client.get(ME, headers=auth("dev:alice@acme.com:acme:owner"))
    assert resp.status_code == 200

    memberships = resp.json()["memberships"]
    assert len(memberships) == 1
    assert memberships[0]["role"] == "owner"
    assert memberships[0]["organization"]["slug"] == "acme"
