import sqlite3
from shared.backup import backup_sqlite


def test_backup_contains_committed_wal_data(tmp_path):
    source = tmp_path / "news.db"
    target = tmp_path / "backup.db"
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE evidence(id INTEGER PRIMARY KEY, text TEXT)")
        db.execute("INSERT INTO evidence VALUES(1,'Texto original')")
        db.commit()
    backup_sqlite(source, target)
    with sqlite3.connect(target) as copy:
        assert copy.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert copy.execute("SELECT text FROM evidence").fetchone()[0] == "Texto original"
