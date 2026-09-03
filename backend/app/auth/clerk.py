"""Clerk authentication provider.

Verifies a Clerk-issued session JWT. Clerk signs tokens with RS256 (asymmetric):
Clerk holds the private key; we verify with the matching **public** key published
at Clerk's JWKS endpoint. We never see or store a shared secret for this — that
is the whole security advantage of asymmetric verification.

Flow:
1. Read the token header's `kid` (key id).
2. Fetch the matching public key from JWKS (PyJWKClient caches keys in memory, so
   this is a network call only on the first use / key rotation).
3. Verify the signature and standard claims (exp/nbf/iat, and `iss` if configured).
4. Map the verified claims into our provider-agnostic `AuthIdentity`.

Note on email: Clerk's default session token does *not* include the email. Add a
custom claim in the Clerk dashboard (Session token):
    { "email": "{{user.primary_email_address}}", "name": "{{user.full_name}}" }
so JIT provisioning can create the local user. If it's absent we surface a clear
error rather than guessing.

JWT verification (PyJWKClient + jwt.decode) is synchronous/blocking, so we run it
in a worker thread to avoid stalling the event loop.
"""

from __future__ import annotations

from typing import Any

import jwt
from anyio import to_thread
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError

from app.auth.base import AuthIdentity, AuthProvider
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClerkAuthProvider(AuthProvider):
    def __init__(self, jwks_url: str, issuer: str | None = None) -> None:
        if not jwks_url:
            raise ValueError("CLERK_JWKS_URL is required when AUTH_PROVIDER=clerk.")
        # PyJWKClient maintains an in-memory, TTL'd cache of signing keys.
        self._jwk_client = PyJWKClient(jwks_url, cache_keys=True)
        self._issuer = issuer

    async def authenticate(self, token: str) -> AuthIdentity:
        try:
            claims = await to_thread.run_sync(self._verify, token)
        except PyJWKClientError as exc:
            logger.warning("clerk_jwks_error", error=str(exc))
            raise AuthenticationError("Unable to verify token signing key.") from exc
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("Token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            logger.warning("clerk_invalid_token", error=str(exc))
            raise AuthenticationError("Invalid authentication token.") from exc

        return self._to_identity(claims)

    def _verify(self, token: str) -> dict[str, Any]:
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {}
        if self._issuer:
            decode_kwargs["issuer"] = self._issuer
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"require": ["exp", "sub"], "verify_aud": False},
            **decode_kwargs,
        )
        return claims

    @staticmethod
    def _to_identity(claims: dict[str, Any]) -> AuthIdentity:
        # Clerk includes org context claims only when the session is org-scoped.
        org_role = claims.get("org_role")
        if isinstance(org_role, str):
            org_role = org_role.removeprefix("org:")  # "org:admin" -> "admin"

        email = (
            claims.get("email")
            or claims.get("email_address")
            or claims.get("primary_email_address")
            or claims.get("preferred_username")
        )

        return AuthIdentity(
            subject=str(claims["sub"]),
            email=email,
            full_name=claims.get("name") or claims.get("full_name") or claims.get("first_name"),
            org_external_id=claims.get("org_id"),
            org_slug=claims.get("org_slug"),
            org_role=org_role,
            raw_claims=claims,
        )
