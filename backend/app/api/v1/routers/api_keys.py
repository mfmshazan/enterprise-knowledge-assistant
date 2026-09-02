"""API Key management endpoints, mounted under /orgs/{org_id}/api-keys."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentMembership, CurrentUser, DbSession, require_role
from app.models.enums import Role
from app.repositories.api_key import ApiKeyRepository
from app.repositories.audit_log import AuditLogRepository
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyRead
from app.services.api_key_service import ApiKeyService

router = APIRouter()


@router.get(
    "",
    response_model=list[ApiKeyRead],
    dependencies=[Depends(require_role(Role.ADMIN))],
    summary="List organization API keys (Admin+)",
)
async def list_api_keys(
    db: DbSession,
    membership: CurrentMembership,
) -> list[ApiKeyRead]:
    service = ApiKeyService(ApiKeyRepository(db, membership.org_id))
    keys = await service.list_keys()
    return [ApiKeyRead.model_validate(k) for k in keys]


@router.post(
    "",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.ADMIN))],
    summary="Generate a new API key (Admin+)",
)
async def create_api_key(
    payload: ApiKeyCreate,
    db: DbSession,
    membership: CurrentMembership,
    user: CurrentUser,
) -> ApiKeyCreatedResponse:
    service = ApiKeyService(ApiKeyRepository(db, membership.org_id))
    key, secret = await service.create_key(
        name=payload.name,
        user=user,
        expires_in_days=payload.expires_in_days,
    )

    audit = AuditLogRepository(db, membership.org_id)
    await audit.log(
        action="api_key.create",
        resource_type="api_key",
        resource_id=str(key.id),
        actor_user_id=user.id,
        metadata={"name": key.name, "prefix": key.key_prefix},
    )
    await db.commit()

    return ApiKeyCreatedResponse(
        id=key.id,
        org_id=key.org_id,
        name=key.name,
        key_prefix=key.key_prefix,
        created_by_user_id=key.created_by_user_id,
        expires_at=key.expires_at,
        revoked_at=key.revoked_at,
        created_at=key.created_at,
        is_active=key.is_active,
        secret_key=secret,
    )


@router.delete(
    "/{key_id}",
    response_model=ApiKeyRead,
    dependencies=[Depends(require_role(Role.ADMIN))],
    summary="Revoke an API key (Admin+)",
)
async def revoke_api_key(
    key_id: uuid.UUID,
    db: DbSession,
    membership: CurrentMembership,
    user: CurrentUser,
) -> ApiKeyRead:
    service = ApiKeyService(ApiKeyRepository(db, membership.org_id))
    key = await service.revoke_key(key_id)

    audit = AuditLogRepository(db, membership.org_id)
    await audit.log(
        action="api_key.revoke",
        resource_type="api_key",
        resource_id=str(key.id),
        actor_user_id=user.id,
        metadata={"name": key.name, "prefix": key.key_prefix},
    )
    await db.commit()

    return ApiKeyRead.model_validate(key)
