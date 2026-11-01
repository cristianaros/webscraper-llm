"""Idempotently preload the production DatosLab university source catalog."""
from __future__ import annotations

import json
import os
from pathlib import Path

from config import BackendSettings
from database import make_engine, make_session_factory
from models import Source, SourceVersion, University
from scripts.datoslab_catalog import DATOSLAB_PROFILES, VERIFIED_SLUGS, build_source_input
from services.sources import normalize_name, source_config


def seed_production_sources(db) -> dict[str, int]:
    """Create catalog universities/sources, enabling only untouched verified profiles."""
    summary = {"universities_total": 0, "sources_created": 0, "sources_enabled": 0}
    try:
        for profile in DATOSLAB_PROFILES:
            university = db.query(University).filter(
                University.normalized_name == normalize_name(profile.name)
            ).one_or_none()
            if university is None:
                university = University(name=profile.name, normalized_name=normalize_name(profile.name))
                db.add(university)
                db.flush()

            desired = build_source_input(profile, university.id)
            source = db.query(Source).filter(
                Source.university_id == university.id,
                Source.start_url == desired.start_url,
            ).one_or_none()
            created = source is None
            if created:
                raw = desired.model_dump()
                raw.pop("university_id")
                raw.pop("start_url")
                source = Source(
                    university_id=university.id,
                    start_url=desired.start_url,
                    config_json=raw,
                    revision=1,
                    enabled=False,
                    auto_publish=False,
                )
                db.add(source)
                db.flush()
                summary["sources_created"] += 1

            should_enable = profile.slug in VERIFIED_SLUGS and (
                created or (source.revision == 1 and source.validated_revision is None)
            )
            if should_enable:
                source.enabled = True
                source.auto_publish = True
                source.validated_revision = source.revision

            if created or should_enable:
                # Every new source needs a revision snapshot for ingestion. Verified
                # sources snapshot their enabled state; unverified ones stay inactive.
                existing_version = db.get(SourceVersion, (source.id, source.revision))
                if existing_version is None:
                    db.add(SourceVersion(
                        source_id=source.id,
                        revision=source.revision,
                        snapshot_json=source_config(db, source).model_dump(mode="json"),
                    ))
                else:
                    existing_version.snapshot_json = source_config(db, source).model_dump(mode="json")
            if source.enabled:
                summary["sources_enabled"] += 1

        summary["universities_total"] = db.query(University).count()
        db.commit()
    except Exception:
        db.rollback()
        raise
    return summary


def main() -> None:
    env_file = Path(__file__).resolve().parents[1] / ".env"
    # Environment values take precedence; use backend/.env only when it exists.
    settings = BackendSettings(_env_file=str(env_file) if env_file.is_file() else None)
    engine = make_engine(os.environ.get("DATABASE_URL", settings.database_url))
    try:
        with make_session_factory(engine)() as db:
            print(json.dumps(seed_production_sources(db), ensure_ascii=False))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
