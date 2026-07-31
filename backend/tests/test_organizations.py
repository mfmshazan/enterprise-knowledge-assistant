"""Organization CRUD and membership visibility."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth

ORGS = "/api/v1/orgs"
ALICE = "dev:alice@acme.com"
BOB = "dev:bob@globex.com"


async def test_create_organization_makes_creator_owner(client: AsyncClient) -> None:
    resp = await client.post(ORGS, json={"name": "Acme Inc."}, headers=auth(ALICE))
    assert resp.status_code == 201
    org = resp.json()
    assert org["name"] == "Acme Inc."
    assert org["slug"] == "acme-inc"

    # It now shows up under the creator's memberships as owner.
    mine = await client.get(ORGS, headers=auth(ALICE))
    assert mine.status_code == 200
    rows = mine.json()
    assert len(rows) == 1
    assert rows[0]["role"] == "owner"
    assert rows[0]["organization"]["id"] == org["id"]


async def test_duplicate_slug_conflicts(client: AsyncClient) -> None:
    await client.post(ORGS, json={"name": "Acme", "slug": "acme"}, headers=auth(ALICE))
    dup = await client.post(ORGS, json={"name": "Acme Two", "slug": "acme"}, headers=auth(ALICE))
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "conflict"


async def test_non_member_cannot_read_org(client: AsyncClient) -> None:
    created = await client.post(ORGS, json={"name": "Acme"}, headers=auth(ALICE))
    org_id = created.json()["id"]

    # Bob is a valid user but not a member -> 404 (existence not disclosed).
    resp = await client.get(f"{ORGS}/{org_id}", headers=auth(BOB))
    assert resp.status_code == 404


async def test_member_can_read_org_and_list_members(client: AsyncClient) -> None:
    created = await client.post(ORGS, json={"name": "Acme"}, headers=auth(ALICE))
    org_id = created.json()["id"]

    got = await client.get(f"{ORGS}/{org_id}", headers=auth(ALICE))
    assert got.status_code == 200
    assert got.json()["id"] == org_id

    members = await client.get(f"{ORGS}/{org_id}/members", headers=auth(ALICE))
    assert members.status_code == 200
    emails = {m["user"]["email"] for m in members.json()}
    assert emails == {"alice@acme.com"}
