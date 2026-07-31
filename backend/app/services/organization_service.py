"""Organization use-cases.

Creating an organization is more than an INSERT: the creator must atomically
become its **owner**. Doing both in one service method (within the request's
transaction) guarantees you can never end up with an ownerless org. Slug
uniqueness is enforced here with a friendly 409 rather than leaking a raw DB
integrity error.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.core.slug import slugify
from app.models.enums import Role
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.membership import MembershipRepository
from app.repositories.organization import OrganizationRepository


class OrganizationService:
    def __init__(
        self,
        orgs: OrganizationRepository,
        memberships: MembershipRepository,
    ) -> None:
        self.orgs = orgs
        self.memberships = memberships

    async def create(self, *, owner: User, name: str, slug: str | None = None) -> Organization:
        desired_slug = slugify(slug or name)
        if await self.orgs.get_by_slug(desired_slug):
            raise ConflictError(f"An organization with slug '{desired_slug}' already exists.")

        org = Organization(name=name, slug=desired_slug)
        self.orgs.add(org)
        await self.orgs.session.flush()

        # The creator is the owner.
        self.memberships.add(Membership(user_id=owner.id, org_id=org.id, role=Role.OWNER))
        await self.memberships.session.flush()
        return org

    async def get_for_member(self, *, org_id: uuid.UUID, user: User) -> Organization:
        """Fetch an org only if `user` is a member — otherwise 404 (we do not
        reveal existence of orgs the caller can't see)."""
        membership = await self.memberships.get_by_user_and_org(user.id, org_id)
        if membership is None:
            raise NotFoundError("Organization not found.")
        org = await self.orgs.get(org_id)
        if org is None:  # pragma: no cover - membership implies org exists
            raise NotFoundError("Organization not found.")
        return org

    async def list_members(self, *, org_id: uuid.UUID) -> list[Membership]:
        return await self.memberships.list_for_org(org_id)

    async def update_member_role(
        self,
        *,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: Role,
        actor: Membership,
    ) -> Membership:
        """Change a member's role, enforcing owner-protection invariants.

        Rules:
        * Only an OWNER may grant the owner role or modify an existing owner.
          (An admin cannot promote themselves to owner or demote an owner.)
        * The last remaining owner cannot be demoted — an org always has one.
        """
        target = await self.memberships.get_by_user_and_org_with_user(target_user_id, org_id)
        if target is None:
            raise NotFoundError("Member not found in this organization.")

        touches_ownership = new_role == Role.OWNER or target.role == Role.OWNER
        if touches_ownership and actor.role != Role.OWNER:
            raise PermissionDeniedError("Only an owner can assign or change the owner role.")

        if target.role == Role.OWNER and new_role != Role.OWNER:
            members = await self.memberships.list_for_org(org_id)
            owner_count = sum(1 for m in members if m.role == Role.OWNER)
            if owner_count <= 1:
                raise ConflictError("Cannot demote the last owner of the organization.")

        target.role = new_role
        await self.memberships.session.flush()
        return target
