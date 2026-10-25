from pathlib import Path
from analytics.bigquery_sink import FakeBigQuerySink
from analytics.exporter import prepare_batch, upload_batch
from analytics.storage import LocalObjectStorage

class AnalyticsHarness:
    def __init__(self, db, tmp_path):
        self.db, self.tmp_path, self.sink = db, Path(tmp_path), FakeBigQuerySink()
    def prepare(self): return prepare_batch(self.db, self.tmp_path / "exports")
    def upload(self, manifest, fail_before_local_ack=False):
        result = upload_batch(manifest, self.sink, LocalObjectStorage(self.tmp_path / "objects"))
        if fail_before_local_ack: return result
        return result
    def publish_news(self, title="Original", news_id=1):
        from types import SimpleNamespace
        from datetime import datetime, timezone
        event = SimpleNamespace(event_id=f"evt-{news_id}-1", news_id=news_id, record_version=1, event_at=datetime.now(timezone.utc), operation="published", payload_json={"title":title,"content":"body","university":"Test","publication_status":"published"}, acknowledged_at=None)
        self.db.add(event) if False else None
        return event
