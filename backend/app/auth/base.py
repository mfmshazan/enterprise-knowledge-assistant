"""The auth provider contract.

`AuthIdentity` is the **normalized** result of verifying a credential: whatever
provider we use, the rest of the app sees the same small, stable shape. The
`subject` is the external, provider-issued user id — we store it as
`User.external_id` and look users up by it on every request.

`AuthProvider.authenticate` takes a raw bearer token and returns an
`AuthIdentity`, or raises `AuthenticationError` if the token is missing/invalid/
expired. It performs *authentication only* (who are you) — never authorization
(what may you do); that is the job of the RBAC dependencies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AuthIdentity:
    """Provider-agnostic identity extracted from a verified token."""

    subject: str
    """Stable external user id (Clerk `sub`, or a dev-provider synthetic id)."""

    email: str | None = None
    full_name: str | None = None

    # Present only when the token is scoped to an organization (Clerk orgs, or a
    # dev token that encodes one). We map these to our own Organization rows.
    org_external_id: str | None = None
    org_slug: str | None = None
    org_role: str | None = None

    raw_claims: dict[str, Any] = field(default_factory=dict)
    """Original token claims, kept for debugging and future extension."""


class AuthProvider(ABC):
    """Interface every authentication backend implements."""

    @abstractmethod
    async def authenticate(self, token: str) -> AuthIdentity:
        """Verify `token` and return the identity, or raise AuthenticationError."""
        raise NotImplementedError
