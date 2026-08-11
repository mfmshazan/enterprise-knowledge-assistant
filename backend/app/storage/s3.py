"""S3-compatible object storage via boto3 (works with MinIO and AWS S3).

boto3 is synchronous, so each call is offloaded to a worker thread with
`anyio.to_thread.run_sync` to avoid blocking the event loop. The boto3 client is
thread-safe and created once per instance.

MinIO note: MinIO requires **path-style** addressing (`host/bucket/key`) rather
than virtual-host style (`bucket.host/key`), and signature v4 — both configured
below so the same class works against MinIO and real S3.
"""

from __future__ import annotations

from typing import Any

import boto3
from anyio import to_thread
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.logging import get_logger
from app.storage.base import ObjectStorage

logger = get_logger(__name__)


class S3ObjectStorage(ObjectStorage):
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str,
        bucket: str,
        use_ssl: bool = False,
    ) -> None:
        self._bucket = bucket
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            use_ssl=use_ssl,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    async def ensure_bucket(self) -> None:
        def _ensure() -> None:
            try:
                self._client.head_bucket(Bucket=self._bucket)
            except ClientError:
                self._client.create_bucket(Bucket=self._bucket)
                logger.info("bucket_created", bucket=self._bucket)

        await to_thread.run_sync(_ensure)

    async def put_object(self, key: str, data: bytes, content_type: str | None = None) -> None:
        def _put() -> None:
            extra = {"ContentType": content_type} if content_type else {}
            self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **extra)

        await to_thread.run_sync(_put)

    async def get_object(self, key: str) -> bytes:
        def _get() -> bytes:
            resp = self._client.get_object(Bucket=self._bucket, Key=key)
            body: bytes = resp["Body"].read()
            return body

        return await to_thread.run_sync(_get)

    async def delete_object(self, key: str) -> None:
        def _delete() -> None:
            self._client.delete_object(Bucket=self._bucket, Key=key)

        await to_thread.run_sync(_delete)

    async def generate_presigned_url(self, key: str, *, expires_in: int = 3600) -> str:
        def _sign() -> str:
            url: str = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url

        return await to_thread.run_sync(_sign)
