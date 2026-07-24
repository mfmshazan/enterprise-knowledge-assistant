"""FastAPI application factory.

We build the app inside `create_app()` rather than as a module-level global so
that tests can construct a fresh, independently-configured instance. `app` at
the bottom is the ASGI target uvicorn imports (`app.main:app`).

Startup/shutdown logic lives in a `lifespan` context manager (the modern
replacement for `@app.on_event`). In later phases this is where we open the DB
engine, Redis pool, and Qdrant client, and close them cleanly on shutdown.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.routers import health
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.db.session import dispose_engine, init_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info(
        "startup",
        project=settings.PROJECT_NAME,
        version=__version__,
        environment=settings.ENVIRONMENT,
    )
    init_engine()
    # Phase 3+: initialize Redis pool / Qdrant client here.
    yield
    await dispose_engine()
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Order matters: request-context middleware first so its request_id is bound
    # for everything downstream, including CORS-handled requests.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    register_exception_handlers(app)

    # Liveness/readiness live at the root for infra probes.
    app.include_router(health.router)

    # Versioned business API. (Empty for now; populated from Phase 2 onward.)
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
