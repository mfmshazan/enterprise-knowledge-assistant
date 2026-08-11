"""Object storage abstraction.

Raw uploaded files live in S3-compatible object storage (MinIO locally, AWS S3
in production), never in Postgres. The rest of the app depends on the
`ObjectStorage` interface; `get_object_storage()` returns the configured
concrete implementation. Same provider-swap discipline as auth and (soon) the
embedding layer.
"""

from app.storage.base import ObjectStorage
from app.storage.factory import get_object_storage

__all__ = ["ObjectStorage", "get_object_storage"]
