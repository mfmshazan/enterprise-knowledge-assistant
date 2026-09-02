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
from app.repositories.audit_log import AuditLogRepository
from app.repositories.membership import MembershipRepository
from app.repositories.organization import OrganizationRepository
from app.schemas.membership import MemberInvite, MemberRoleUpdate, MembershipRead, OrgMemberRead
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
    audit = AuditLogRepository(db, org.id)
    await audit.log(
        action="organization.create",
        resource_type="organization",
        resource_id=str(org.id),
        actor_user_id=user.id,
        metadata={"name": org.name, "slug": org.slug},
    )
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


@router.post(
    "/{org_id}/members",
    response_model=OrgMemberRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.ADMIN))],
    summary="Invite or add a member to the organization (admin+)",
)
async def invite_member(
    org_id: uuid.UUID,
    payload: MemberInvite,
    db: DbSession,
    actor: Annotated[Membership, Depends(require_role(Role.ADMIN))],
) -> OrgMemberRead:
    invited = await _org_service(db).add_or_invite_member(
        org_id=org_id,
        email=payload.email,
        role=payload.role,
        actor=actor,
    )
    audit = AuditLogRepository(db, org_id)
    await audit.log(
        action="member.invite",
        resource_type="membership",
        resource_id=str(invited.id),
        actor_user_id=actor.user_id,
        metadata={"email": payload.email, "role": payload.role.value},
    )
    return OrgMemberRead.model_validate(invited)


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
    audit = AuditLogRepository(db, org_id)
    await audit.log(
        action="member.role_update",
        resource_type="membership",
        resource_id=str(updated.id),
        actor_user_id=actor.user_id,
        metadata={"target_user_id": str(user_id), "new_role": payload.role.value},
    )
    return OrgMemberRead.model_validate(updated)


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(Role.ADMIN))],
    summary="Remove a member from the organization (admin+, with owner protection)",
)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DbSession,
    actor: Annotated[Membership, Depends(require_role(Role.ADMIN))],
) -> None:
    await _org_service(db).remove_member(
        org_id=org_id,
        target_user_id=user_id,
        actor=actor,
    )
    audit = AuditLogRepository(db, org_id)
    await audit.log(
        action="member.remove",
        resource_type="membership",
        resource_id=str(user_id),
        actor_user_id=actor.user_id,
        metadata={"removed_user_id": str(user_id)},
    )
