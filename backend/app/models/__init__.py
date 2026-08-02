"""SQLAlchemy ORM models.

Importing the models here ensures they are registered on `Base.metadata` before
Alembic autogenerate or `create_all` runs. Anything that needs "all tables"
(migrations env, test fixtures) imports from this package.
"""

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.enums import DocumentStatus, Role, SourceType
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User

__all__ = [
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "Membership",
    "Organization",
    "Role",
    "SourceType",
    "User",
]
