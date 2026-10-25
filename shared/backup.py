"""Copias consistentes de SQLite sin copiar WAL a mano."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def backup_sqlite(source: Path, destination: Path) -> None:
    """Create a verified SQLite online backup without overwriting data."""
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("backup_target_equals_source")
    if not source.is_file() or destination.exists():
        raise ValueError("source_missing_or_target_exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_uri = source.as_uri() + "?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as source_db, sqlite3.connect(destination) as destination_db:
        source_db.backup(destination_db)
        if destination_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("invalid_backup")
