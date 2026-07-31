"""Shared FastAPI dependencies (dependency injection).

This module is the seam where HTTP meets the domain. It turns a raw request into
the typed things handlers actually want: a DB session, the current `User`, the
current `Membership` (role in a specific org), and RBAC guards.

Reusable `Annotated` aliases (`DbSession`, `CurrentUser`, ...) keep handler
signatures short and make the dependency graph explicit and testable — tests
override `get_db`/`get_auth_provider` to run without Postgres or Clerk.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.base import AuthProvider
from app.auth.factory import get_auth_provider
from app.core.exceptions import AuthenticationError, NotFoundError, PermissionDeniedError
from app.db.session import get_db
from app.models.enums import Role
from app.models.membership import Membership
from app.models.user import User
from app.repositories.membership import MembershipRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.services.identity_service import IdentityService

DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthProviderDep = Annotated[AuthProvider, Depends(get_auth_provider)]

# auto_error=False: we raise our own AuthenticationError (uniform 401 envelope)
# instead of FastAPI's default, so error responses stay consistent.
_bearer = HTTPBearer(auto_error=False, description="Bearer token from the auth provider")


async def get_current_user(
    db: DbSession,
    provider: AuthProviderDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Authenticate the bearer token and return the (JIT-provisioned) local user."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Missing or malformed Authorization header.")

    identity = await provider.authenticate(credentials.credentials)
    service = IdentityService(
        UserRepository(db),
        OrganizationRepository(db),
        MembershipRepository(db),
    )
    return await service.provision(identity)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_membership(
    db: DbSession,
    user: CurrentUser,
    org_id: Annotated[uuid.UUID, Path(description="Organization id")],
) -> Membership:
    """Resolve the caller's membership in the org named in the path.

    Returns 404 (not 403) when the user isn't a member: we don't disclose the
    existence of organizations the caller has no access to.
    """
    membership = await MembershipRepository(db).get_by_user_and_org(user.id, org_id)
    if membership is None:
        raise NotFoundError("Organization not found.")
    return membership


CurrentMembership = Annotated[Membership, Depends(get_current_membership)]


def require_role(minimum: Role) -> Callable[[Membership], Awaitable[Membership]]:
    """Dependency factory enforcing a minimum role in the path's organization.

    Usage:
        @router.post("/{org_id}/members",
                     dependencies=[Depends(require_role(Role.ADMIN))])
    """

    async def _guard(membership: CurrentMembership) -> Membership:
        if not membership.role.satisfies(minimum):
            raise PermissionDeniedError(
                f"This action requires the '{minimum.value}' role or higher."
            )
        return membership

    return _guard
