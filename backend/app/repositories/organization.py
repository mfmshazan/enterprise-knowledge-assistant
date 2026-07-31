"""Organization data access."""

from __future__ import annotations

from sqlalchemy import select

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    async def get_by_slug(self, slug: str) -> Organization | None:
        return await self.session.scalar(select(Organization).where(Organization.slug == slug))

    async def get_by_external_id(self, external_id: str) -> Organization | None:
        return await self.session.scalar(
            select(Organization).where(Organization.external_id == external_id)
        )
