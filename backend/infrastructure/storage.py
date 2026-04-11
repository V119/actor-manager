from minio import Minio
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

class StorageClient:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def upload_file(self, file_name: str, data: bytes, content_type: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.client.put_object,
            self.bucket,
            file_name,
            BytesIO(data),
            len(data),
            content_type
        )
        return f"{self.bucket}/{file_name}"

    def get_url(self, file_name: str):
        return self.client.presigned_get_object(self.bucket, file_name)
