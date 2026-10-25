from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .schema import BatchManifest, NEWS_COLUMNS

def _identifier(value: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value): raise ValueError(f"invalid_{label}")
    return value

def render_merge_sql(project_id: str, dataset: str) -> str:
    project_id, dataset = _identifier(project_id, "project"), _identifier(dataset, "dataset")
    columns = list(NEWS_COLUMNS)
    assignments = ", ".join(f"{x}=S.{x}" for x in columns if x != "news_id")
    names = ", ".join(columns); values = ", ".join(f"S.{x}" for x in columns)
    return f"""MERGE `{project_id}.{dataset}.news_current` T USING (SELECT * FROM `{project_id}.{dataset}.news_events` WHERE DATE(event_at) BETWEEN @min_date AND @max_date AND batch_id=@batch_id QUALIFY ROW_NUMBER() OVER (PARTITION BY news_id ORDER BY record_version DESC,event_at DESC,event_id DESC)=1) S ON T.news_id=S.news_id WHEN MATCHED AND S.record_version>T.record_version THEN UPDATE SET {assignments} WHEN NOT MATCHED THEN INSERT ({names}) VALUES ({values})"""

class FakeBigQuerySink:
    def __init__(self):
        self.events: dict[str, dict[str, Any]] = {}; self.current_news: dict[int, dict[str, Any]] = {}; self.jobs: dict[str, str] = {}
    def load(self, uri: str, manifest: BatchManifest) -> str:
        job = f"uninews_load_{manifest.batch_id}"; self.jobs.setdefault(job, "done")
        import json
        with open(uri.removeprefix("file://"), encoding="utf-8") as h:
            for line in h:
                if line.strip():
                    row = json.loads(line); self.events[row["event_id"]] = row
        return job
    def merge(self, manifest: BatchManifest) -> str:
        job = f"uninews_merge_{manifest.batch_id}"; self.jobs.setdefault(job, "done")
        for row in self.events.values():
            old = self.current_news.get(row["news_id"])
            if old is None or (row["record_version"], row["event_at"], row["event_id"]) > (old["record_version"], old["event_at"], old["event_id"]): self.current_news[row["news_id"]] = row
        return job
    @property
    def published_news(self): return [r for r in self.current_news.values() if r["publication_status"] == "published" and not r["is_deleted"]]

class BigQuerySink:
    def __init__(self, project: str, dataset: str, location: str = "us-central1"):
        self.project, self.dataset, self.location = project, dataset, location
        try:
            from google.cloud import bigquery  # lazy import by design
        except ImportError as exc: raise RuntimeError("install analytics cloud extras for upload") from exc
        self.client = bigquery.Client(project=project)
    def load(self, uri: str, manifest: BatchManifest) -> str:
        from google.cloud import bigquery
        config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, write_disposition="WRITE_APPEND", schema=[bigquery.SchemaField(k, v) for k,v in NEWS_COLUMNS.items()], ignore_unknown_values=False)
        job = self.client.load_table_from_uri(uri, f"{self.project}.{self.dataset}.news_events", job_id=f"uninews_load_{manifest.batch_id}", job_config=config, location=self.location); job.result(); return job.job_id
    def merge(self, manifest: BatchManifest) -> str:
        query = render_merge_sql(self.project, self.dataset)
        job = self.client.query(query, job_id=f"uninews_merge_{manifest.batch_id}", location=self.location); job.result(); return job.job_id
