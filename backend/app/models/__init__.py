"""SQLAlchemy ORM models.

Importing the models here ensures they are registered on `Base.metadata` before
Alembic autogenerate or `create_all` runs. Anything that needs "all tables"
(migrations env, test fixtures) imports from this package.
"""

from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog
from app.models.citation import Citation
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, MessageRole, Role, SourceType
from app.models.membership import Membership
from app.models.message import Message
from app.models.organization import Organization
from app.models.user import User

__all__ = [
    "ApiKey",
    "AuditLog",
    "Citation",
    "Conversation",
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "Membership",
    "Message",
    "MessageRole",
    "Organization",
    "Role",
    "SourceType",
    "User",
]
