"""Tests for rate limiting logic and HTTP 429 response handling."""

import pytest

from app.core.rate_limit import InMemoryRateLimiter


@pytest.mark.asyncio
async def test_in_memory_rate_limiter_allows_under_limit() -> None:
    limiter = InMemoryRateLimiter()
    key = "test:org_1"
    allowed, remaining, reset = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is True
    assert remaining == 2

    allowed, remaining, reset = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is True
    assert remaining == 1

    allowed, remaining, reset = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is True
    assert remaining == 0

    # 4th request exceeds limit
    allowed, remaining, reset = await limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is False
    assert remaining == 0
    assert reset > 0
