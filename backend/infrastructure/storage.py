import asyncio
from datetime import timedelta
from io import BytesIO
import logging
from typing import BinaryIO, Any

from minio import Minio


logger = logging.getLogger(__name__)


class StorageClient:
    _ensured_buckets: set[tuple[str, str]] = set()

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        self.endpoint = endpoint
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket
        self.ensure_bucket(self.bucket)

    def ensure_bucket(self, bucket_name: str) -> None:
        cache_key = (self.endpoint, bucket_name)
        if cache_key in self._ensured_buckets:
            return
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            logger.info("MinIO bucket created endpoint=%s bucket=%s", self.endpoint, bucket_name)
        else:
            logger.debug("MinIO bucket exists endpoint=%s bucket=%s", self.endpoint, bucket_name)
        self._ensured_buckets.add(cache_key)

    def ensure_buckets(self, bucket_names: list[str]) -> None:
        for bucket_name in bucket_names:
            self.ensure_bucket(bucket_name)

    async def upload_file(self, file_name: str, data: bytes, content_type: str, bucket: str | None = None) -> str:
        target_bucket = bucket or self.bucket
        self.ensure_bucket(target_bucket)
        loop = asyncio.get_running_loop()
        logger.debug(
            "MinIO upload start bucket=%s object_key=%s bytes=%s content_type=%s",
            target_bucket,
            file_name,
            len(data),
            content_type,
        )
        await loop.run_in_executor(
            None,
            lambda: self.client.put_object(
                target_bucket,
                file_name,
                BytesIO(data),
                len(data),
                content_type=content_type,
            ),
        )
        logger.info(
            "MinIO upload complete bucket=%s object_key=%s bytes=%s",
            target_bucket,
            file_name,
            len(data),
        )
        return f"{target_bucket}/{file_name}"

    async def upload_file_stream(
        self,
        file_name: str,
        data_stream: BinaryIO,
        length: int,
        content_type: str,
        bucket: str | None = None,
        part_size: int = 10 * 1024 * 1024,
    ) -> str:
        target_bucket = bucket or self.bucket
        self.ensure_bucket(target_bucket)
        loop = asyncio.get_running_loop()

        if hasattr(data_stream, "seek"):
            data_stream.seek(0)

        logger.debug(
            "MinIO stream upload start bucket=%s object_key=%s length=%s content_type=%s part_size=%s",
            target_bucket,
            file_name,
            length,
            content_type,
            part_size,
        )

        await loop.run_in_executor(
            None,
            lambda: self.client.put_object(
                target_bucket,
                file_name,
                data_stream,
                length=length,
                part_size=part_size,
                content_type=content_type,
            ),
        )
        logger.info(
            "MinIO stream upload complete bucket=%s object_key=%s length=%s",
            target_bucket,
            file_name,
            length,
        )
        return f"{target_bucket}/{file_name}"

    async def download_file(self, file_name: str, bucket: str | None = None) -> bytes:
        target_bucket = bucket or self.bucket
        self.ensure_bucket(target_bucket)
        loop = asyncio.get_running_loop()

        def _download() -> bytes:
            response = self.client.get_object(target_bucket, file_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        data = await loop.run_in_executor(None, _download)
        logger.debug(
            "MinIO download complete bucket=%s object_key=%s bytes=%s",
            target_bucket,
            file_name,
            len(data),
        )
        return data

    async def remove_object(self, file_name: str, bucket: str | None = None) -> None:
        target_bucket = bucket or self.bucket
        self.ensure_bucket(target_bucket)
        loop = asyncio.get_running_loop()

        logger.debug("MinIO object delete start bucket=%s object_key=%s", target_bucket, file_name)
        await loop.run_in_executor(
            None,
            lambda: self.client.remove_object(target_bucket, file_name),
        )
        logger.info("MinIO object deleted bucket=%s object_key=%s", target_bucket, file_name)

    def presigned_put_url(
        self,
        file_name: str,
        bucket: str | None = None,
        expires: timedelta = timedelta(minutes=20),
    ) -> str:
        target_bucket = bucket or self.bucket
        self.ensure_bucket(target_bucket)
        return self.client.presigned_put_object(target_bucket, file_name, expires=expires)

    def stat_object(self, file_name: str, bucket: str | None = None) -> dict[str, Any]:
        target_bucket = bucket or self.bucket
        self.ensure_bucket(target_bucket)
        stat = self.client.stat_object(target_bucket, file_name)
        return {
            "size": stat.size,
            "etag": stat.etag,
            "last_modified": stat.last_modified,
            "content_type": getattr(stat, "content_type", None),
        }

    def get_url(
        self,
        file_name: str,
        bucket: str | None = None,
        expires: timedelta = timedelta(hours=12),
    ) -> str:
        target_bucket = bucket or self.bucket
        self.ensure_bucket(target_bucket)
        return self.client.presigned_get_object(target_bucket, file_name, expires=expires)
