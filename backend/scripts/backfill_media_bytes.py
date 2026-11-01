"""Recover verified local image files into the operational database."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import make_engine, make_session_factory  # noqa: E402
from models import MediaAsset  # noqa: E402


def _verified_file(asset: MediaAsset, roots: list[Path]) -> bytes | None:
    candidates = [Path(asset.storage_key)]
    candidates.extend(root / asset.sha256[:2] / f"{asset.sha256}.*" for root in roots)
    for candidate in candidates:
        paths = list(candidate.parent.glob(candidate.name)) if "*" in candidate.name else [candidate]
        for path in paths:
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if len(data) == asset.byte_size and hashlib.sha256(data).hexdigest() == asset.sha256:
                return data
    return None


def backfill_media_bytes(db, search_roots: list[Path] | None = None) -> dict[str, int]:
    stats = {"already_in_db": 0, "backfilled": 0, "missing_or_corrupt": 0}
    roots = [Path(root) for root in (search_roots or [])]
    try:
        for asset in db.query(MediaAsset).all():
            if asset.content_bytes is not None:
                stats["already_in_db"] += 1
                continue
            data = _verified_file(asset, roots)
            if data is None:
                stats["missing_or_corrupt"] += 1
                continue
            asset.content_bytes = data
            asset.storage_backend = "database"
            asset.storage_key = f"db://{asset.sha256}"
            stats["backfilled"] += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--media-root", action="append", type=Path, default=[])
    args = parser.parse_args()
    engine = make_engine(args.database_url)
    try:
        with make_session_factory(engine)() as db:
            print(backfill_media_bytes(db, args.media_root))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
