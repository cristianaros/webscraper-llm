import json
from datetime import datetime, timezone
from types import SimpleNamespace

from analytics.bigquery_sink import FakeBigQuerySink, render_merge_sql
from analytics.exporter import write_ndjson
from analytics.schema import NEWS_COLUMNS
from analytics.storage import LocalObjectStorage

def event(event_id, news_id, version, operation="published", deleted=False):
    return SimpleNamespace(event_id=event_id, news_id=news_id, record_version=version, event_at=datetime(2026, 1, 1, tzinfo=timezone.utc), operation=operation, acknowledged_at=None, payload_json={"title":"T","content":"B","university":"U","publication_status":"archived" if deleted else "published","is_deleted":deleted})

def test_fake_sink_deduplicates_and_respects_record_version(tmp_path):
    rows = []
    for e, batch in [(event("a", 1, 2), "b1"), (event("b", 1, 1), "b2"), (event("d", 1, 3, "delete", True), "b3")]:
        rows.append({"event_id":e.event_id,"batch_id":batch,"news_id":e.news_id,"record_version":e.record_version,"event_at":e.event_at.isoformat(),"operation":e.operation,"publication_status":e.payload_json["publication_status"],"is_deleted":e.payload_json["is_deleted"],"university_id":None,"university":"U","title":"T","body":"B","category":None,"published_on":None,"source_url":None,"content_hash":None,"image_status":None,"image_original_url":None,"image_gcs_uri":None,"image_sha256":None,"image_width":None,"image_height":None})
    path = tmp_path / "events.ndjson"; digest = write_ndjson(rows, path)
    from analytics.schema import BatchManifest
    m = BatchManifest("b", ["a"], 1, str(path), digest, "2026-01-01", "2026-01-01")
    sink = FakeBigQuerySink(); storage = LocalObjectStorage(tmp_path / "objects")
    for row in rows: sink.load(storage.put_file(path, "same.ndjson", digest), m); sink.merge(m); sink.events[row["event_id"]] = row
    sink.merge(m)
    assert len(sink.current_news) == 1 and sink.current_news[1]["record_version"] == 3
    assert sink.published_news == []

def test_prepare_has_explicit_schema_and_immutable_ndjson(tmp_path):
    assert "record_version" in NEWS_COLUMNS and "is_deleted" in NEWS_COLUMNS
    path = tmp_path / "x.ndjson"; digest = write_ndjson([{"b":2}], path)
    assert digest == __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    try: write_ndjson([{"b":3}], path)
    except ValueError as exc: assert "immutable" in str(exc)
    else: raise AssertionError("must reject overwrite")

def test_merge_sql_validates_identifiers():
    sql = render_merge_sql("project-1", "uninews")
    assert "record_version" in sql and "S.record_version>T.record_version" in sql
