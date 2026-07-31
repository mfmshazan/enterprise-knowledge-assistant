"""Selects and caches the configured `AuthProvider`.

`get_auth_provider()` is the single place that knows about concrete providers.
Everything else depends on the abstract `AuthProvider`. The result is cached
(one instance per process) so, e.g., Clerk's JWKS key cache is shared across
requests instead of being rebuilt each time.

Safety rail: the `dev` provider bypasses real credential checks, so it is
**refused in production** — a misconfiguration there fails loudly at startup
rather than silently accepting fake tokens.
"""

from __future__ import annotations

from functools import lru_cache

from app.auth.base import AuthProvider
from app.auth.clerk import ClerkAuthProvider
from app.auth.dev import DevAuthProvider
from app.core.config import Settings, get_settings


def _build_provider(settings: Settings) -> AuthProvider:
    provider = settings.AUTH_PROVIDER

    if provider == "dev":
        if settings.is_production:
            raise RuntimeError(
                "AUTH_PROVIDER=dev is not allowed in production. "
                "Set AUTH_PROVIDER=clerk and configure Clerk credentials."
            )
        return DevAuthProvider()

    if provider == "clerk":
        if not settings.CLERK_JWKS_URL:
            raise RuntimeError("AUTH_PROVIDER=clerk requires CLERK_JWKS_URL to be set.")
        return ClerkAuthProvider(
            jwks_url=settings.CLERK_JWKS_URL,
            issuer=settings.CLERK_ISSUER,
        )

    # "authjs" and any future providers land here until implemented.
    raise RuntimeError(f"Unsupported AUTH_PROVIDER: {provider!r}.")


@lru_cache
def get_auth_provider() -> AuthProvider:
    return _build_provider(get_settings())
