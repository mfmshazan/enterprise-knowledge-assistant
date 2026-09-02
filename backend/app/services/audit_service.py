"""Audit service — tenant-bound audit logging and retrieval."""

from __future__ import annotations

from typing import Any

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository


class AuditService:
    def __init__(self, audit_repo: AuditLogRepository) -> None:
        self.audit_repo = audit_repo

    async def log_event(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        actor: User | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        return await self.audit_repo.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_user_id=actor.id if actor else None,
            metadata=metadata,
            ip_address=ip_address,
        )

    async def list_logs(
        self,
        *,
        action: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        return await self.audit_repo.list_paginated(
            action=action,
            page=page,
            page_size=page_size,
        )
