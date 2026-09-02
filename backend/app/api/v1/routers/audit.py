"""Audit log endpoints, mounted under /orgs/{org_id}/audit-logs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentMembership, DbSession, require_role
from app.models.enums import Role
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_log import AuditLogListResponse, AuditLogRead

router = APIRouter()


@router.get(
    "",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_role(Role.ADMIN))],
    summary="List organization audit events (Admin+)",
)
async def list_audit_logs(
    db: DbSession,
    membership: CurrentMembership,
    action: Annotated[str | None, Query(description="Filter by action name")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
) -> AuditLogListResponse:
    repo = AuditLogRepository(db, membership.org_id)
    items, total = await repo.list_paginated(action=action, page=page, page_size=page_size)
    return AuditLogListResponse(
        items=[AuditLogRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
