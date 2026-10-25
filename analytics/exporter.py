from __future__ import annotations

import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .schema import BatchManifest, ExportResult, NEWS_COLUMNS

def write_ndjson(rows: list[dict], path: Path) -> str:
    content = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n" for row in rows)
    raw = content.encode("utf-8")
    if len(raw) > 64 * 1024 * 1024: raise ValueError("batch_too_large")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw: raise ValueError("immutable_batch_collision")
    else: path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def _row(event, batch_id: str) -> dict:
    p = dict(event.payload_json or {}); event_at = event.event_at.isoformat()
    row = {"event_id": event.event_id, "batch_id": batch_id, "news_id": event.news_id, "record_version": event.record_version, "event_at": event_at, "operation": event.operation, "publication_status": p.get("publication_status", "archived" if event.operation in ("delete", "archive") else "published"), "is_deleted": bool(p.get("is_deleted", event.operation in ("delete", "archive"))), "university_id": p.get("university_id"), "university": p.get("university"), "title": p.get("title"), "body": p.get("body", p.get("content")), "category": p.get("category"), "published_on": p.get("published_on"), "source_url": p.get("source_url", p.get("canonical_url")), "content_hash": p.get("content_hash"), "image_status": p.get("image_status"), "image_original_url": p.get("image_original_url"), "image_gcs_uri": p.get("image_gcs_uri"), "image_sha256": p.get("image_sha256"), "image_width": p.get("image_width"), "image_height": p.get("image_height")}
    return row

def _events(db, limit):
    from models import AnalyticsOutbox
    q = db.query(AnalyticsOutbox).filter(AnalyticsOutbox.acknowledged_at.is_(None)).order_by(AnalyticsOutbox.event_at, AnalyticsOutbox.event_id).limit(limit)
    return list(q)

def prepare_batch(db, output_dir: Path, limit: int = 1000) -> BatchManifest | None:
    events = _events(db, limit)
    if not events: return None
    # A process restart before ACK must reopen the same claimed batch.  The
    # manifest is the durable claim when running against the legacy backend
    # schema (newer schemas additionally persist batch_id on the outbox row).
    wanted = {e.event_id for e in events}
    for candidate in sorted(Path(output_dir).glob("*/manifest.json")):
        try:
            old = BatchManifest.from_dict(json.loads(candidate.read_text(encoding="utf-8")))
            if set(old.event_ids) == wanted and Path(old.ndjson_path).exists(): return old
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    batch_id = str(uuid4()); rows = [_row(e, batch_id) for e in events]
    folder = Path(output_dir) / batch_id; ndjson = folder / "events.ndjson"; digest = write_ndjson(rows, ndjson)
    dates = [r["event_at"][:10] for r in rows]
    manifest = BatchManifest(batch_id, [e.event_id for e in events], len(rows), str(ndjson), digest, min(dates), max(dates))
    (folder / "manifest.json").write_text(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    # Newer backend schema can claim events; old schema remains replayable via ACK.
    from models import AnalyticsOutbox
    if hasattr(AnalyticsOutbox, "batch_id"):
        for e in events: e.batch_id = batch_id
        db.commit()
    return manifest

def upload_batch(manifest: BatchManifest, sink, storage) -> ExportResult:
    uri = storage.put_file(Path(manifest.ndjson_path), f"batches/{manifest.batch_id}/events.ndjson", manifest.sha256)
    load_id = sink.load(uri, manifest); merge_id = sink.merge(manifest)
    return ExportResult(manifest.batch_id, manifest.record_count, load_id, merge_id, datetime.now(timezone.utc).isoformat())

def ack_batch(db, batch_id: str, result: ExportResult) -> None:
    from models import AnalyticsOutbox
    if hasattr(AnalyticsOutbox, "batch_id"):
        now = datetime.now(timezone.utc)
        values = {"acknowledged_at": now}
        if hasattr(AnalyticsOutbox, "exported_at"): values["exported_at"] = now
        db.query(AnalyticsOutbox).filter(AnalyticsOutbox.batch_id == batch_id).update(values, synchronize_session=False)
    db.commit()
