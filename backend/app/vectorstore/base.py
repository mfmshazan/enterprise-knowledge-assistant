"""Vector store contract and value types.

Tenant isolation is a first-class parameter here: `search` *requires* an
`org_id` and filters to it, so a similarity query can never surface another
organization's chunks. `delete_by_document` supports document deletion and
re-indexing (remove old vectors before writing new ones).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VectorPoint:
    """A vector to store: its id (== the DocumentChunk id) plus filter payload."""

    id: uuid.UUID
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    id: uuid.UUID
    score: float
    payload: dict[str, Any]


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, dimension: int) -> None:
        """Create the collection (sized to `dimension`) if it doesn't exist."""

    @abstractmethod
    async def upsert(self, points: list[VectorPoint]) -> None:
        """Insert or replace vectors by id."""

    @abstractmethod
    async def delete_by_document(self, org_id: uuid.UUID, document_id: uuid.UUID) -> None:
        """Remove all vectors belonging to a document (for delete / re-index)."""

    @abstractmethod
    async def search(
        self, org_id: uuid.UUID, query_vector: list[float], *, limit: int = 5
    ) -> list[SearchHit]:
        """Return the `limit` nearest vectors within the given organization."""
