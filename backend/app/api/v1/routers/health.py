"""Health & readiness endpoints.

Two distinct checks, following the Kubernetes liveness/readiness convention:

* **/health (liveness)** — "is the process up?" Cheap, no dependencies. Used by
  orchestrators to decide whether to restart the container. Must never fail just
  because a downstream (DB) is down, or you get restart storms.
* **/ready (readiness)** — "can it serve traffic?" Checks critical dependencies.
  Used by Render/Vercel/Kubernetes to decide whether to route requests here.
  Returns 503 if any critical dependency is unhealthy.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    responses={503: {"description": "One or more dependencies are unhealthy"}},
)
async def ready() -> ReadinessResponse:
    from fastapi.responses import JSONResponse

    checks: dict[str, str] = {}

    # --- Postgres ---
    try:
        from sqlalchemy import text

        from app.db.session import get_engine
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.warning("readiness_db_fail", error=str(exc))
        checks["database"] = "error"

    # --- Redis ---
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        logger.warning("readiness_redis_fail", error=str(exc))
        checks["redis"] = "error"

    # --- Qdrant ---
    try:
        from app.vectorstore.factory import get_vector_store
        from app.vectorstore.qdrant import QdrantVectorStore
        store = get_vector_store()
        if isinstance(store, QdrantVectorStore):
            await store._client.collection_exists(settings.QDRANT_COLLECTION)
        checks["qdrant"] = "ok"
    except Exception as exc:
        logger.warning("readiness_qdrant_fail", error=str(exc))
        checks["qdrant"] = "error"

    # --- Object storage (S3 / MinIO) ---
    try:
        from anyio import to_thread

        from app.storage.factory import get_object_storage
        from app.storage.s3 import S3ObjectStorage
        storage = get_object_storage()
        if isinstance(storage, S3ObjectStorage):
            def _head() -> None:
                storage._client.head_bucket(Bucket=storage._bucket)
            await to_thread.run_sync(_head)
        checks["storage"] = "ok"
    except Exception as exc:
        logger.warning("readiness_storage_fail", error=str(exc))
        checks["storage"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    overall = "ok" if all_ok else "degraded"

    if not all_ok:
        return JSONResponse(
            status_code=503,
            content=ReadinessResponse(status=overall, checks=checks).model_dump(),
        )

    return ReadinessResponse(status=overall, checks=checks)
