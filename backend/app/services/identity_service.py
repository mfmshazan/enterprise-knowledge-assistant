"""Just-in-time (JIT) identity provisioning.

When an authenticated request arrives, the auth provider tells us *who* the user
is (an `AuthIdentity`) but the user may not yet exist in our database. This
service maps that external identity onto local rows, creating them on first sight
and keeping mutable fields (email, name) in sync on subsequent requests.

If the token carries organization context (Clerk org-scoped session, or a dev
token like `dev:a@b.com:acme:owner`), we also mirror that org locally and ensure
a membership exists — so a fresh Clerk org "just works" the first time a member
of it calls the API.

Idempotent by construction: every step is get-or-create keyed on a unique column,
so repeated calls converge on the same rows.
"""

from __future__ import annotations

from app.auth.base import AuthIdentity
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.core.slug import slugify
from app.models.enums import Role
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.membership import MembershipRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class IdentityService:
    def __init__(
        self,
        users: UserRepository,
        orgs: OrganizationRepository,
        memberships: MembershipRepository,
    ) -> None:
        self.users = users
        self.orgs = orgs
        self.memberships = memberships

    async def provision(self, identity: AuthIdentity) -> User:
        user = await self._get_or_create_user(identity)
        if identity.org_external_id or identity.org_slug:
            await self._ensure_org_membership(user, identity)
        return user

    async def _get_or_create_user(self, identity: AuthIdentity) -> User:
        user = await self.users.get_by_external_id(identity.subject)

        if user is None:
            email = identity.email or f"{identity.subject}@clerk.user"
            user = User(
                external_id=identity.subject,
                email=email,
                full_name=identity.full_name or "User",
            )
            self.users.add(user)
            await self.users.session.flush()
            logger.info("user_provisioned", user_id=str(user.id), email=user.email)
            return user

        # Keep profile fields fresh if the provider's copy changed.
        if identity.email and user.email != identity.email:
            user.email = identity.email
        if identity.full_name and user.full_name != identity.full_name:
            user.full_name = identity.full_name
        return user

    async def _ensure_org_membership(self, user: User, identity: AuthIdentity) -> None:
        org = await self._get_or_create_org(identity)

        membership = await self.memberships.get_by_user_and_org(user.id, org.id)
        if membership is None:
            role = self._resolve_role(identity.org_role)
            membership = Membership(user_id=user.id, org_id=org.id, role=role)
            self.memberships.add(membership)
            await self.memberships.session.flush()
            logger.info(
                "membership_provisioned",
                user_id=str(user.id),
                org_id=str(org.id),
                role=role.value,
            )

    async def _get_or_create_org(self, identity: AuthIdentity) -> Organization:
        org: Organization | None = None
        if identity.org_external_id:
            org = await self.orgs.get_by_external_id(identity.org_external_id)
        if org is None and identity.org_slug:
            org = await self.orgs.get_by_slug(identity.org_slug)

        if org is None:
            slug = slugify(identity.org_slug or identity.org_external_id or "workspace")
            org = Organization(
                external_id=identity.org_external_id,
                name=identity.org_slug or slug,
                slug=slug,
            )
            self.orgs.add(org)
            await self.orgs.session.flush()
            logger.info("org_provisioned", org_id=str(org.id), slug=org.slug)
        return org

    @staticmethod
    def _resolve_role(raw: str | None) -> Role:
        if not raw:
            return Role.MEMBER
        try:
            return Role(raw)
        except ValueError:
            return Role.MEMBER
