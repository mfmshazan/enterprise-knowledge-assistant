"""Membership data access — the authorization-critical joins.

`get` answers the core auth question: "is this user a member of this org, and in
what role?" `list_for_user`/`list_for_org` eagerly load the related entity
(`selectinload`) so callers can render "my orgs" or "org members" without N+1
queries.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.membership import Membership
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[Membership]):
    model = Membership

    async def get_by_user_and_org(self, user_id: uuid.UUID, org_id: uuid.UUID) -> Membership | None:
        return await self.session.scalar(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.org_id == org_id,
            )
        )

    async def list_for_user(self, user_id: uuid.UUID) -> list[Membership]:
        result = await self.session.scalars(
            select(Membership)
            .where(Membership.user_id == user_id)
            .options(selectinload(Membership.organization))
            .order_by(Membership.created_at)
        )
        return list(result.all())

    async def get_by_user_and_org_with_user(
        self, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> Membership | None:
        """Like `get_by_user_and_org` but eagerly loads `user`, so the result is
        safe to serialize into an `OrgMemberRead` response."""
        return await self.session.scalar(
            select(Membership)
            .where(Membership.user_id == user_id, Membership.org_id == org_id)
            .options(selectinload(Membership.user))
        )

    async def list_for_org(self, org_id: uuid.UUID) -> list[Membership]:
        result = await self.session.scalars(
            select(Membership)
            .where(Membership.org_id == org_id)
            .options(selectinload(Membership.user))
            .order_by(Membership.created_at)
        )
        return list(result.all())
