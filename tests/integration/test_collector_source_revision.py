from datetime import UTC, datetime

from collector.store import CollectorStore


def test_changed_source_revision_is_due_immediately(tmp_path, source):
    now = datetime(2026, 10, 25, tzinfo=UTC)
    with CollectorStore(tmp_path / "queue.db") as store:
        store.cache_sources([source], now)
        store.save_discovery(source, cursor="https://uni.example/noticias?page=2", now=now)
        assert store.source_due(source, now) is False

        updated = source.model_copy(update={"revision": 2, "validated_revision": 2})
        store.cache_sources([updated], now)

        assert store.source_due(updated, now) is True
        assert store.source_cursor(updated.id) is None
