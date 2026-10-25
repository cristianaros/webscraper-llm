from datetime import UTC, datetime, timedelta
from uuid import uuid4

from collector.store import CollectorStore
from shared.contracts import RunReport


def test_unsent_run_report_survives_reopen(tmp_path):
    run_id = uuid4(); now = datetime.now(UTC)
    report = RunReport(run_id=run_id, source_id=1, trigger='scheduled', status='partial', started_at=now, finished_at=now,
        counts={'discovered': 1}, error_code='deadline_reached')
    path = tmp_path / 'collector.db'
    with CollectorStore(path) as store:
        store.save_run(report)
    with CollectorStore(path) as store:
        assert store.pending_reports()[0] == report
        store.acknowledge_report(run_id)
        assert store.pending_reports() == []
