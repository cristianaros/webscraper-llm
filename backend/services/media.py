"""Safe local persistence and association of original collector images."""
from __future__ import annotations
import hashlib
import os
import re
import struct
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from models import IngestReceipt, MediaAsset, News, NewsMediaHistory, NewsRevision
from services.analytics_events import emit_event
from shared.contracts import ImageAsset, ImageDelivery, MediaReceipt, StoredImage, payload_digest

_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

def _jpeg_size(data: bytes) -> tuple[int, int]:
    if not data.startswith(b"\xff\xd8"): raise ValueError("invalid_image_format")
    offset = 2
    while offset + 9 <= len(data):
        if data[offset] != 0xFF:
            offset += 1; continue
        while offset < len(data) and data[offset] == 0xFF: offset += 1
        marker = data[offset]; offset += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7: continue
        if offset + 2 > len(data): break
        size = struct.unpack(">H", data[offset:offset + 2])[0]
        if size < 2 or offset + size > len(data): break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            return struct.unpack(">HH", data[offset + 3:offset + 7])
        offset += size
    raise ValueError("invalid_image_format")

def _image_details(data: bytes) -> tuple[str, int, int]:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24 and data[12:16] == b"IHDR":
        width, height = struct.unpack(">II", data[16:24]); return "image/png", width, height
    if data.startswith(b"\xff\xd8"):
        width, height = _jpeg_size(data); return "image/jpeg", width, height
    if data.startswith(b"RIFF") and len(data) >= 30 and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X" and len(data) >= 30:
            width = int.from_bytes(data[24:27], "little") + 1; height = int.from_bytes(data[27:30], "little") + 1
        elif chunk == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
            width, height = struct.unpack("<HH", data[26:30]); width &= 0x3FFF; height &= 0x3FFF
        elif chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little"); width = (bits & 0x3FFF) + 1; height = ((bits >> 14) & 0x3FFF) + 1
        else: raise ValueError("invalid_image_format")
        return "image/webp", width, height
    raise ValueError("invalid_image_format")

def validate_upload(asset: ImageAsset, content: bytes, uploaded_content_type: str | None) -> None:
    if asset.status != "ready": raise HTTPException(422, "image_not_ready")
    if not content or len(content) > _MAX_IMAGE_BYTES: raise HTTPException(413, "invalid_image_size")
    try: content_type, width, height = _image_details(content)
    except ValueError as exc: raise HTTPException(422, "invalid_image_format") from exc
    if (hashlib.sha256(content).hexdigest() != asset.sha256 or len(content) != asset.byte_size or content_type != asset.content_type or width != asset.width or height != asset.height or (uploaded_content_type and uploaded_content_type.split(";", 1)[0].lower() != content_type)):
        raise HTTPException(422, "image_evidence_mismatch")

class LocalMediaStore:
    def __init__(self, root: Path): self.root = Path(root)
    def put(self, sha256: str, content: bytes, content_type: str) -> StoredImage:
        extension = _EXTENSIONS.get(content_type)
        if extension is None or not re.fullmatch(r"[0-9a-f]{64}", sha256): raise ValueError("invalid_media_key")
        path = self.root / sha256[:2] / f"{sha256}{extension}"; path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=".upload-", suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as temporary:
                    temporary.write(content); temporary.flush(); os.fsync(temporary.fileno())
                os.replace(temporary_name, path)
            finally:
                if os.path.exists(temporary_name): os.unlink(temporary_name)
        return StoredImage(sha256=sha256, url=f"/api/media/{sha256}", storage_uri=str(path))
    def open(self, sha256: str):
        path = next((item for item in self.root.glob(f"{sha256[:2]}/{sha256}.*") if item.is_file()), None)
        if path is None: raise FileNotFoundError(sha256)
        return path.open("rb")

def receive_media(db, settings, delivery: ImageDelivery, content: bytes, uploaded_content_type: str | None, now: datetime) -> MediaReceipt:
    validate_upload(delivery.image, content, uploaded_content_type)
    receipt_key = f"{delivery.delivery_id}:image"; digest = payload_digest(delivery.model_dump(mode="json")); prior = db.get(IngestReceipt, receipt_key)
    if prior:
        if prior.payload_hash != digest or prior.kind != "image": raise HTTPException(409, "delivery_id_content_collision")
        return MediaReceipt.model_validate(prior.receipt_json)
    revision = db.get(NewsRevision, delivery.revision_id)
    if revision is None: raise HTTPException(404, "revision_not_found")
    if revision.document_hash != delivery.expected_document_hash: raise HTTPException(409, "revision_document_mismatch")
    try:
        stored = LocalMediaStore(settings.media_root).put(delivery.image.sha256, content, delivery.image.content_type)
        asset = db.get(MediaAsset, delivery.image.sha256)
        if asset is None:
            db.add(MediaAsset(sha256=delivery.image.sha256, storage_key=stored.storage_uri, storage_backend="local", content_type=delivery.image.content_type, width=delivery.image.width, height=delivery.image.height, byte_size=delivery.image.byte_size))
        news = db.get(News, revision.news_id) if revision.news_id else None; applied = bool(news and news.content_hash == delivery.expected_document_hash)
        if applied:
            changed = news.image_status != "ready" or news.image_sha256 != delivery.image.sha256
            news.image_status = "ready"; news.image_sha256 = delivery.image.sha256; news.image_original_url = delivery.image.original_url; news.image_alt = delivery.image.alt; news.image_credit = delivery.image.credit; news.image_url = stored.url
            if changed:
                emit_event(db, news, "image_updated", now)
        db.add(NewsMediaHistory(revision_id=revision.id, news_id=news.id if news else None, image_json=delivery.image.model_dump(mode="json")))
        receipt = MediaReceipt(delivery_id=delivery.delivery_id, revision_id=revision.id, news_id=news.id if news else None, applied_to_current=applied)
        db.add(IngestReceipt(delivery_id=receipt_key, payload_hash=digest, receipt_json=receipt.model_dump(mode="json"), kind="image", created_at=now)); db.commit(); return receipt
    except Exception:
        db.rollback(); raise
