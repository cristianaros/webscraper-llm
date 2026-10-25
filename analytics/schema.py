from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

NEWS_COLUMNS = {
    "event_id": "STRING", "batch_id": "STRING", "news_id": "INTEGER",
    "record_version": "INTEGER", "event_at": "TIMESTAMP", "operation": "STRING",
    "publication_status": "STRING", "is_deleted": "BOOLEAN", "university_id": "INTEGER",
    "university": "STRING", "title": "STRING", "body": "STRING", "category": "STRING",
    "published_on": "DATE", "source_url": "STRING", "content_hash": "STRING",
    "image_status": "STRING", "image_original_url": "STRING", "image_gcs_uri": "STRING",
    "image_sha256": "STRING", "image_width": "INTEGER", "image_height": "INTEGER",
}

@dataclass(frozen=True)
class BatchManifest:
    batch_id: str
    event_ids: list[str]
    record_count: int
    ndjson_path: str
    sha256: str
    min_event_date: str
    max_event_date: str
    schema_version: int = 1
    load_job_id: str = ""
    merge_job_id: str = ""

    def to_dict(self) -> dict[str, Any]: return asdict(self)
    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BatchManifest": return cls(**value)

@dataclass(frozen=True)
class ExportResult:
    batch_id: str
    loaded_rows: int
    load_job_id: str
    merge_job_id: str
    completed_at: str

def manifest_path(path: str | Path) -> Path: return Path(path)
