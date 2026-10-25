"""Periodic SQLite backup runner with retention management."""
from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from shared.backup import backup_sqlite


def run_backup(database: Path, directory: Path, keep: int = 7) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    target = directory / f"backup_{timestamp}.db"
    backup_sqlite(database, target)

    # Retention
    existing = sorted(directory.glob("backup_*.db"), key=lambda p: p.stat().st_mtime)
    while len(existing) > keep:
        oldest = existing.pop(0)
        try:
            oldest.unlink()
        except OSError:
            pass
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup SQLite database")
    parser.add_argument("--database", type=Path, required=True, help="Path to SQLite database")
    parser.add_argument("--directory", type=Path, required=True, help="Destination directory")
    parser.add_argument("--interval-hours", type=int, default=24, help="Backup interval in hours")
    parser.add_argument("--keep", type=int, default=7, help="Number of backups to keep")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        target = run_backup(args.database, args.directory, args.keep)
        print(f"Backup created: {target}")
        return

    while True:
        try:
            target = run_backup(args.database, args.directory, args.keep)
            print(f"[{datetime.now(UTC).isoformat()}] Backup created: {target}")
        except Exception as exc:
            print(f"[{datetime.now(UTC).isoformat()}] Backup failed: {exc}", file=sys.stderr)
        time.sleep(args.interval_hours * 3600)


if __name__ == "__main__":
    main()
