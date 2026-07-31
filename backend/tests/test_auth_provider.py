"""Unit tests for the auth provider layer (no database, no network)."""

from __future__ import annotations

import pytest

from app.auth.base import AuthProvider
from app.auth.dev import DevAuthProvider
from app.auth.factory import _build_provider
from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.models.enums import Role


class TestRoleHierarchy:
    def test_owner_outranks_admin_and_member(self) -> None:
        assert Role.OWNER.satisfies(Role.ADMIN)
        assert Role.OWNER.satisfies(Role.MEMBER)

    def test_member_does_not_satisfy_admin(self) -> None:
        assert not Role.MEMBER.satisfies(Role.ADMIN)

    def test_role_satisfies_itself(self) -> None:
        assert Role.ADMIN.satisfies(Role.ADMIN)


class TestDevAuthProvider:
    async def test_email_only(self) -> None:
        identity = await DevAuthProvider().authenticate("dev:Alice@Acme.com")
        assert identity.subject == "dev:alice@acme.com"
        assert identity.email == "alice@acme.com"
        assert identity.full_name == "Alice"
        assert identity.org_slug is None
        assert identity.org_role is None

    async def test_email_org_role(self) -> None:
        identity = await DevAuthProvider().authenticate("dev:bob@acme.com:acme:owner")
        assert identity.email == "bob@acme.com"
        assert identity.org_slug == "acme"
        assert identity.org_role == Role.OWNER.value

    async def test_same_email_is_stable_subject(self) -> None:
        a = await DevAuthProvider().authenticate("dev:x@y.com")
        b = await DevAuthProvider().authenticate("dev:x@y.com:acme:admin")
        assert a.subject == b.subject

    @pytest.mark.parametrize(
        "token",
        [
            "no-prefix@acme.com",
            "dev:not-an-email",
            "dev:",
            "dev:carol@acme.com:acme:superadmin",  # invalid role
        ],
    )
    async def test_invalid_tokens_rejected(self, token: str) -> None:
        with pytest.raises(AuthenticationError):
            await DevAuthProvider().authenticate(token)


class TestProviderFactory:
    def test_dev_provider_selected(self) -> None:
        settings = Settings(ENVIRONMENT="development", AUTH_PROVIDER="dev")
        provider = _build_provider(settings)
        assert isinstance(provider, DevAuthProvider)
        assert isinstance(provider, AuthProvider)

    def test_dev_provider_refused_in_production(self) -> None:
        settings = Settings(ENVIRONMENT="production", AUTH_PROVIDER="dev")
        with pytest.raises(RuntimeError, match="not allowed in production"):
            _build_provider(settings)

    def test_clerk_requires_jwks_url(self) -> None:
        settings = Settings(AUTH_PROVIDER="clerk", CLERK_JWKS_URL=None)
        with pytest.raises(RuntimeError, match="CLERK_JWKS_URL"):
            _build_provider(settings)
