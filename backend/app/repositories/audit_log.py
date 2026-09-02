"""AuditLog repository — org-scoped."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, func, select

from app.models.audit_log import AuditLog
from app.repositories.base import OrgScopedRepository


class AuditLogRepository(OrgScopedRepository[AuditLog]):
    model = AuditLog

    async def log(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        actor_user_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            org_id=self.org_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata or {},
            ip_address=ip_address,
        )
        self.add(entry)
        await self.session.flush()
        return entry

    async def list_paginated(
        self,
        *,
        action: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        stmt = self._scoped()
        count_stmt = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.org_id == self.org_id)
        )

        if action:
            stmt = stmt.where(AuditLog.action == action)
            count_stmt = count_stmt.where(AuditLog.action == action)

        total = await self.session.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size)

        result = await self.session.scalars(stmt)
        return list(result.all()), total
