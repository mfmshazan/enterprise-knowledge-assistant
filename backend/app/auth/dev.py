"""Development / test authentication provider.

Purpose: let the entire stack run and be tested **without a Clerk account or any
network calls**. Selected with `AUTH_PROVIDER=dev`. It must never be enabled in
production — the factory enforces that.

Token format (sent as `Authorization: Bearer <token>`):

    dev:<email>[:<org_slug>[:<role>]]

Examples:
    dev:alice@acme.com                      -> user only, no org context
    dev:alice@acme.com:acme                 -> user + org "acme", default member
    dev:alice@acme.com:acme:owner           -> user + org "acme" as owner

This makes it trivial to script different users/roles in tests to exercise RBAC.
The `subject` (external id) is derived deterministically from the email so the
same email always resolves to the same user.
"""

from __future__ import annotations

from app.auth.base import AuthIdentity, AuthProvider
from app.core.exceptions import AuthenticationError
from app.models.enums import Role

_PREFIX = "dev:"


class DevAuthProvider(AuthProvider):
    async def authenticate(self, token: str) -> AuthIdentity:
        if not token.startswith(_PREFIX):
            raise AuthenticationError(
                "Dev tokens must look like 'dev:<email>[:<org_slug>[:<role>]]'."
            )

        parts = token.removeprefix(_PREFIX).split(":")
        email = parts[0].strip().lower()
        if not email or "@" not in email:
            raise AuthenticationError("Dev token must include a valid email.")

        org_slug = parts[1].strip().lower() if len(parts) > 1 and parts[1].strip() else None

        org_role: str | None = None
        if len(parts) > 2 and parts[2].strip():
            raw_role = parts[2].strip().lower()
            try:
                org_role = Role(raw_role).value
            except ValueError as exc:
                valid = ", ".join(r.value for r in Role)
                raise AuthenticationError(f"Unknown role '{raw_role}'. Valid: {valid}.") from exc

        full_name = email.split("@", 1)[0].replace(".", " ").title()

        return AuthIdentity(
            subject=f"dev:{email}",
            email=email,
            full_name=full_name,
            org_external_id=f"dev-org:{org_slug}" if org_slug else None,
            org_slug=org_slug,
            org_role=org_role,
            raw_claims={"provider": "dev", "token": token},
        )
