"""Enable only sources with a successful, recorded live sample."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from config import BackendSettings
from database import make_engine, make_session_factory
from models import Source
from scripts.datoslab_catalog import DATOSLAB_PROFILES


def activate_from_audit(db, records: list[dict], slugs: set[str], auto_publish: set[str]) -> dict[str, int]:
    profiles = {profile.slug: profile for profile in DATOSLAB_PROFILES}
    if not slugs <= profiles.keys() or not auto_publish <= slugs:
        raise ValueError("unknown_or_unselected_slug")
    by_slug = {row["slug"]: row for row in records}
    if len(by_slug) != len(records):
        raise ValueError("duplicate_audit_slug")
    targets = []
    for slug in sorted(slugs):
        row = by_slug.get(slug)
        profile = profiles[slug]
        if not row or row.get("status") != "sample_ok":
            raise ValueError(f"sample_not_verified:{slug}")
        if urlsplit(row.get("url", "")).hostname not in profile.official_hosts:
            raise ValueError(f"unexpected_article_host:{slug}")
        if row.get("title_chars", 0) < 15 or row.get("body_chars", 0) < 200:
            raise ValueError(f"incomplete_article:{slug}")
        if date.fromisoformat(row["published_on"]) > date.today():
            raise ValueError(f"future_publication_date:{slug}")
        source = db.query(Source).filter(
            Source.start_url == f"https://uninews.datoslab.cl/universidad/{slug}"
        ).one_or_none()
        if source is None:
            raise ValueError(f"source_not_registered:{slug}")
        if row.get("source_id") != source.id or row.get("source_revision") != source.revision:
            raise ValueError(f"stale_audit:{slug}")
        targets.append((source, slug))
    for source, slug in targets:
        source.validated_revision = source.revision
        source.enabled = True
        source.auto_publish = slug in auto_publish
    db.commit()
    return {"enabled": len(targets), "auto_publish": len(auto_publish)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, default=Path(__file__).resolve().parents[1] / ".env")
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--slug", action="append", required=True)
    parser.add_argument("--auto-publish", action="append", default=[])
    args = parser.parse_args()
    records = [json.loads(line) for line in args.audit.read_text(encoding="utf-8").splitlines() if line.strip()]
    settings = BackendSettings(_env_file=str(args.env.resolve()))
    engine = make_engine(settings.database_url)
    with make_session_factory(engine)() as db:
        print(json.dumps(activate_from_audit(db, records, set(args.slug), set(args.auto_publish))))


if __name__ == "__main__":
    main()
