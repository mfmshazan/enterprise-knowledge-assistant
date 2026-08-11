"""Document data access — org-scoped.

Every query is automatically constrained to `self.org_id`, so listing or
fetching a document can never cross tenant boundaries.
"""

from __future__ import annotations

from sqlalchemy import desc

from app.models.document import Document
from app.repositories.base import OrgScopedRepository


class DocumentRepository(OrgScopedRepository[Document]):
    model = Document

    async def list_recent(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        result = await self.session.scalars(
            self._scoped().order_by(desc(Document.created_at)).limit(limit).offset(offset)
        )
        return list(result.all())
