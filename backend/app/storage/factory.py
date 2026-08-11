"""Builds and caches the configured `ObjectStorage`."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.storage.base import ObjectStorage
from app.storage.s3 import S3ObjectStorage


@lru_cache
def get_object_storage() -> ObjectStorage:
    return S3ObjectStorage(
        endpoint_url=settings.S3_ENDPOINT_URL,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        region=settings.S3_REGION,
        bucket=settings.S3_BUCKET,
        use_ssl=settings.S3_USE_SSL,
    )
