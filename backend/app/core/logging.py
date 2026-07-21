"""Structured logging setup with `structlog`.

Why structured logging (not bare `print` / stdlib `logging` strings)?

* In production, logs are consumed by machines (Loki, CloudWatch, Datadog).
  JSON logs are queryable by field — `event=document_indexed org_id=... ms=...` —
  instead of being regex-scraped.
* We bind **context** (request_id, org_id, user_id) once and it flows through
  every log line in that request, which is essential for tracing an issue
  across the async ingestion/query paths.
* In development we render pretty, colored console logs for readability; in
  production we emit JSON. Same call sites, different renderer.

Call `configure_logging()` exactly once at startup (from the app factory).
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure stdlib logging + structlog processors for the whole process."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # pull in request-bound context
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_JSON:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound logger. Pass `__name__` at each call site."""
    return structlog.get_logger(name)
