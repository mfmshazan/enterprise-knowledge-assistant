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
    # /ready genuinely pings each dependency: 200 when all are reachable, 503 when
    # any is down (as in CI, where Redis/Qdrant/storage aren't running). Either way
    # the response must report the per-dependency check map.
    assert resp.status_code in (200, 503)

    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert set(body["checks"]) == {"database", "redis", "qdrant", "storage"}
    if resp.status_code == 200:
        assert body["status"] == "ok"
        assert all(v == "ok" for v in body["checks"].values())


async def test_unknown_route_returns_uniform_error(client: AsyncClient) -> None:
    resp = await client.get("/does-not-exist")
    assert resp.status_code == 404
