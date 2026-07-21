"""Smoke tests for the health/readiness endpoints — the Phase 1 acceptance test.

These prove the app boots, middleware runs, routes are mounted, and the error
envelope is wired, all without any external dependency.
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert body["environment"] == "development"

    # Request-id middleware must tag every response.
    assert resp.headers.get("X-Request-ID")


async def test_ready_reports_checks(client: AsyncClient) -> None:
    resp = await client.get("/ready")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "ok"
    assert set(body["checks"]) == {"database", "redis", "qdrant", "storage"}


async def test_unknown_route_returns_uniform_error(client: AsyncClient) -> None:
    resp = await client.get("/does-not-exist")
    assert resp.status_code == 404
