"""Sliding-window rate limiter (Redis / InMemory)."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from fastapi import Request, Response

from app.core.exceptions import RateLimitExceededError

if TYPE_CHECKING:
    from redis.asyncio import Redis


class InMemoryRateLimiter:
    """In-memory fallback sliding window limiter for local dev and unit testing."""

    def __init__(self) -> None:
        self._store: dict[str, list[float]] = defaultdict(list)

    async def is_allowed(
        self, key: str, limit: int, window_seconds: int
    ) -> tuple[bool, int, int]:
        now = time.time()
        window_start = now - window_seconds
        timestamps = [t for t in self._store[key] if t > window_start]
        self._store[key] = timestamps

        if len(timestamps) >= limit:
            oldest = timestamps[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            remaining = 0
            return False, remaining, retry_after

        self._store[key].append(now)
        remaining = limit - len(self._store[key])
        reset = window_seconds
        return True, remaining, reset


class RedisRateLimiter:
    """Redis sliding-window rate limiter using sorted sets."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def is_allowed(
        self, key: str, limit: int, window_seconds: int
    ) -> tuple[bool, int, int]:
        now = time.time()
        window_start = now - window_seconds
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zrange(key, 0, 0, withscores=True)
        results = await pipe.execute()
        current_count = results[1]
        oldest_records = results[2]

        if current_count >= limit:
            oldest_ts = oldest_records[0][1] if oldest_records else window_start
            retry_after = max(1, int(oldest_ts + window_seconds - now))
            return False, 0, retry_after

        pipe = self._redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        await pipe.execute()

        remaining = max(0, limit - (current_count + 1))
        return True, remaining, window_seconds


_in_memory_limiter = InMemoryRateLimiter()


def rate_limiter(
    limit: int = 60,
    window_seconds: int = 60,
    key_prefix: str = "rl",
) -> Callable[[Request, Response], Awaitable[None]]:
    """FastAPI dependency for rate limiting by caller IP or org path."""

    async def _guard(request: Request, response: Response) -> None:
        org_id = request.path_params.get("org_id")
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"{key_prefix}:{org_id or client_ip}"

        allowed, remaining, reset = await _in_memory_limiter.is_allowed(
            identifier, limit=limit, window_seconds=window_seconds
        )

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

        if not allowed:
            raise RateLimitExceededError(
                f"Rate limit exceeded. Try again in {reset} seconds."
            )

    return _guard
