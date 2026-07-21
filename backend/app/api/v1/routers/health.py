"""Health & readiness endpoints.

Two distinct checks, following the Kubernetes liveness/readiness convention:

* **/health (liveness)** — "is the process up?" Cheap, no dependencies. Used by
  orchestrators to decide whether to restart the container. Must never fail just
  because a downstream (DB) is down, or you get restart storms.
* **/ready (readiness)** — "can it serve traffic?" Checks critical dependencies.
  Used to decide whether to route requests here. In Phase 1 the dependency
  checks are stubs; we'll fill them in as Postgres/Redis/Qdrant come online.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=settings.ENVIRONMENT,
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def ready() -> ReadinessResponse:
    # Phase 1: dependency checks are placeholders. Each will become a real
    # ping (SELECT 1, Redis PING, Qdrant collection info) in later phases.
    checks = {
        "database": "skipped",
        "redis": "skipped",
        "qdrant": "skipped",
        "storage": "skipped",
    }
    return ReadinessResponse(status="ok", checks=checks)
