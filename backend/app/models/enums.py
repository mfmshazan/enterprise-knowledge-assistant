"""Domain enums shared by models, schemas, and RBAC dependencies."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """A member's role *within a single organization*.

    `StrEnum` makes the value JSON-serializable and stored as plain text. Roles
    are hierarchical: OWNER outranks ADMIN outranks MEMBER. `rank` powers the
    `require_role` RBAC check (a higher rank satisfies a lower requirement).
    """

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

    @property
    def rank(self) -> int:
        return _ROLE_RANK[self]

    def satisfies(self, required: Role) -> bool:
        """True if this role meets or exceeds the required role."""
        return self.rank >= required.rank


_ROLE_RANK: dict[Role, int] = {
    Role.MEMBER: 1,
    Role.ADMIN: 2,
    Role.OWNER: 3,
}


class SourceType(StrEnum):
    """Where a document came from."""

    FILE = "file"  # an uploaded PDF/DOCX/Markdown, stored in object storage
    URL = "url"  # a fetched web page


class DocumentStatus(StrEnum):
    """Lifecycle of a document through the ingestion pipeline.

    pending    -> just uploaded, job enqueued, nothing processed yet
    processing -> a worker is extracting/chunking/embedding it
    indexed    -> chunks embedded and searchable in the vector store
    failed     -> processing errored (see Document.error); safe to retry
    """

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class MessageRole(StrEnum):
    """Author of a chat message."""

    USER = "user"
    ASSISTANT = "assistant"
