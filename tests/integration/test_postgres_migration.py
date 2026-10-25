import sqlite3
from backend.scripts.migrate_to_postgres import migrate_to_postgres
import pytest


def test_migration_aborts_if_source_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        migrate_to_postgres(tmp_path / "nonexistent.db", "sqlite:///:memory:")
