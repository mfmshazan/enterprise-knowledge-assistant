"""DocumentChunk data access — org-scoped.

Used by retrieval to hydrate vector-search hits: given the chunk ids returned by
the vector store, load the authoritative text (and parent document, for
citations) from Postgres — filtered to the caller's organization.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import selectinload

from app.models.document_chunk import DocumentChunk
from app.repositories.base import OrgScopedRepository


class DocumentChunkRepository(OrgScopedRepository[DocumentChunk]):
    model = DocumentChunk

    async def get_by_ids(self, ids: Sequence[uuid.UUID]) -> list[DocumentChunk]:
        """Load chunks by id (org-scoped), with the parent document eager-loaded
        so the caller can cite the document title without an extra query."""
        if not ids:
            return []
        result = await self.session.scalars(
            self._scoped()
            .where(DocumentChunk.id.in_(ids))
            .options(selectinload(DocumentChunk.document))
        )
        return list(result.all())
