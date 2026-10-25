"""Google Cloud Storage media backend for persistent image storage."""
from __future__ import annotations

import io
import re
from shared.contracts import StoredImage

_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class GcsMediaStore:
    """Stores images in a private Google Cloud Storage bucket partitioned by SHA-256."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client = None
        self._bucket = None

    def _get_bucket(self):
        if self._bucket is None:
            from google.cloud import storage
            self._client = storage.Client()
            self._bucket = self._client.bucket(self.bucket_name)
        return self._bucket

    def put(self, sha256: str, content: bytes, content_type: str) -> StoredImage:
        extension = _EXTENSIONS.get(content_type)
        if extension is None or not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise ValueError("invalid_media_key")

        blob_path = f"images/{sha256[:2]}/{sha256}{extension}"
        bucket = self._get_bucket()
        blob = bucket.blob(blob_path)

        if not blob.exists():
            blob.upload_from_string(content, content_type=content_type)

        storage_uri = f"gs://{self.bucket_name}/{blob_path}"
        return StoredImage(sha256=sha256, url=f"/api/media/{sha256}", storage_uri=storage_uri)

    def open(self, sha256: str):
        bucket = self._get_bucket()
        for ext in [".jpg", ".png", ".webp"]:
            blob = bucket.blob(f"images/{sha256[:2]}/{sha256}{ext}")
            if blob.exists():
                return io.BytesIO(blob.download_as_bytes())
        raise FileNotFoundError(sha256)
