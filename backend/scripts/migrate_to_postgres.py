"""Migrate a local SQLite database to PostgreSQL without losing legacy data."""
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, inspect, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import normalize_database_url  # noqa: E402
from scripts.backfill_media_bytes import _verified_file  # noqa: E402

ORDERED_TABLES: tuple[str, ...] = (
    "universities", "sources", "source_versions", "news", "news_revisions",
    "media_assets", "news_media_history", "scrape_runs", "ingest_receipts",
    "collector_status", "analytics_outbox",
)
SEQUENCE_TABLES: tuple[str, ...] = (
    "universities", "sources", "news", "news_revisions", "news_media_history",
)


@dataclass
class MigrationReport:
    table_counts: dict[str, int]
    verified_hashes: dict[str, str]
    source_backup_sha256: str
    completed_at: datetime


def sync_postgres_sequences(conn) -> None:
    for table_name in SEQUENCE_TABLES:
        conn.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), "
            f"(SELECT MAX(id) IS NOT NULL FROM {table_name}))"
        ))


def migrate_to_postgres(source_sqlite: Path, destination_url: str, media_roots: list[Path] | None = None) -> MigrationReport:
    source_sqlite = Path(source_sqlite)
    if not source_sqlite.is_file():
        raise FileNotFoundError(f"Source database not found: {source_sqlite}")
    destination_url = normalize_database_url(destination_url)
    backup_sha = hashlib.sha256(source_sqlite.read_bytes()).hexdigest()
    sqlite_engine = create_engine(f"sqlite:///{source_sqlite.resolve().as_posix()}")
    pg_engine = create_engine(destination_url)
    try:
        existing_tables = set(inspect(pg_engine).get_table_names())
        if not existing_tables:
            from scripts.bootstrap_db import bootstrap_database
            bootstrap_database(destination_url)
            existing_tables = set(inspect(pg_engine).get_table_names())
        sqlite_meta = MetaData()
        sqlite_meta.reflect(bind=sqlite_engine)
        names = [name for name in ORDERED_TABLES if name in sqlite_meta.tables]
        names.extend(name for name in sqlite_meta.tables if name not in names and not name.startswith("sqlite_") and name != "alembic_version")
        counts: dict[str, int] = {}
        hashes: dict[str, str] = {}
        roots = [Path(root) for root in (media_roots or [])]
        with sqlite_engine.connect() as s_conn, pg_engine.begin() as p_conn:
            for table_name in names:
                if table_name not in existing_tables:
                    raise RuntimeError(f"destination_schema_missing:{table_name}")
                s_table = sqlite_meta.tables[table_name]
                rows = [dict(row) for row in s_conn.execute(s_table.select()).mappings().all()]
                counts[table_name] = len(rows)
                if table_name == "media_assets":
                    for row in rows:
                        if row.get("content_bytes") is None:
                            class Asset:
                                pass
                            asset = Asset()
                            for key, value in row.items():
                                setattr(asset, key, value)
                            data = _verified_file(asset, roots)
                            if data is None:
                                raise RuntimeError(f"media_bytes_unavailable:{row['sha256']}")
                            row["content_bytes"] = data
                            row["storage_backend"] = "database"
                            row["storage_key"] = f"db://{row['sha256']}"
                if rows:
                    target_table = Table(table_name, MetaData(), autoload_with=pg_engine)
                    p_conn.execute(target_table.insert(), rows)
                target_table = Table(table_name, MetaData(), autoload_with=pg_engine)
                target_count = p_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
                if target_count != counts[table_name]:
                    raise RuntimeError(f"row_count_mismatch:{table_name}")
                hashes[table_name] = hashlib.sha256(str(counts[table_name]).encode()).hexdigest()
            if pg_engine.dialect.name == "postgresql":
                sync_postgres_sequences(p_conn)
        return MigrationReport(counts, hashes, backup_sha, datetime.now(UTC))
    finally:
        sqlite_engine.dispose()
        pg_engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--media-root", action="append", type=Path, default=[])
    args = parser.parse_args()
    report = migrate_to_postgres(args.source, args.destination, args.media_root)
    print("Migration completed successfully:")
    for table, count in report.table_counts.items():
        print(f"  {table}: {count} rows")


if __name__ == "__main__":
    main()
