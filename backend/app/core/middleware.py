"""HTTP middleware for request-scoped observability.

`RequestContextMiddleware` assigns each request a unique `request_id`, binds it
(plus timing) into the structlog contextvars so *every* log line emitted during
that request is automatically tagged, and echoes the id back in the
`X-Request-ID` response header for client-side correlation.

This is the backbone of debuggability in an async system where many requests
interleave: without a request id, logs from concurrent requests are impossible
to untangle.
"""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info("request_completed", duration_ms=elapsed_ms)
            structlog.contextvars.clear_contextvars()

        response.headers["X-Request-ID"] = request_id
        return response
