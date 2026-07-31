"""Organization & membership management endpoints.

Access control is expressed declaratively through dependencies:
* `CurrentUser`        — must be authenticated.
* `CurrentMembership`  — must be a member of the org in the path (else 404).
* `require_role(...)`   — must hold at least the given role in that org.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentMembership, CurrentUser, DbSession, require_role
from app.models.enums import Role
from app.models.membership import Membership
from app.repositories.membership import MembershipRepository
from app.repositories.organization import OrganizationRepository
from app.schemas.membership import MemberRoleUpdate, MembershipRead, OrgMemberRead
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.services.organization_service import OrganizationService

router = APIRouter()


def _org_service(db: DbSession) -> OrganizationService:
    return OrganizationService(OrganizationRepository(db), MembershipRepository(db))


@router.post(
    "",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization (caller becomes owner)",
)
async def create_organization(
    payload: OrganizationCreate,
    user: CurrentUser,
    db: DbSession,
) -> OrganizationRead:
    service = _org_service(db)
    org = await service.create(owner=user, name=payload.name, slug=payload.slug)
    return OrganizationRead.model_validate(org)


@router.get(
    "",
    response_model=list[MembershipRead],
    summary="List the organizations the current user belongs to",
)
async def list_my_organizations(user: CurrentUser, db: DbSession) -> list[MembershipRead]:
    memberships = await MembershipRepository(db).list_for_user(user.id)
    return [MembershipRead.model_validate(m) for m in memberships]


@router.get(
    "/{org_id}",
    response_model=OrganizationRead,
    summary="Get an organization (members only)",
)
async def get_organization(
    org_id: uuid.UUID,
    membership: CurrentMembership,
    db: DbSession,
) -> OrganizationRead:
    org = await OrganizationRepository(db).get(org_id)
    # membership dependency already guaranteed access; org must exist.
    assert org is not None  # noqa: S101
    return OrganizationRead.model_validate(org)


@router.get(
    "/{org_id}/members",
    response_model=list[OrgMemberRead],
    summary="List organization members (members only)",
)
async def list_members(
    org_id: uuid.UUID,
    membership: CurrentMembership,
    db: DbSession,
) -> list[OrgMemberRead]:
    members = await _org_service(db).list_members(org_id=org_id)
    return [OrgMemberRead.model_validate(m) for m in members]


@router.patch(
    "/{org_id}/members/{user_id}",
    response_model=OrgMemberRead,
    summary="Change a member's role (admin+, with owner protection)",
)
async def update_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: MemberRoleUpdate,
    db: DbSession,
    actor: Annotated[Membership, Depends(require_role(Role.ADMIN))],
) -> OrgMemberRead:
    updated = await _org_service(db).update_member_role(
        org_id=org_id,
        target_user_id=user_id,
        new_role=payload.role,
        actor=actor,
    )
    return OrgMemberRead.model_validate(updated)
