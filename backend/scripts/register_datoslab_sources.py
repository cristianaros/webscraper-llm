"""Idempotently register the user-selected DatosLab universities as inactive sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import BackendSettings
from database import make_engine, make_session_factory
from models import Source, University
from scripts.datoslab_catalog import DATOSLAB_PROFILES, build_source_input
from services.sources import create_source, create_university, normalize_name, patch_source, source_config
from shared.contracts import SourceInput


def register_catalog(db, *, update_inactive: bool = False) -> dict[str, int]:
    summary = {"created": 0, "existing": 0, "updated": 0}
    for profile in DATOSLAB_PROFILES:
        university = next(
            (
                row for row in db.query(University).all()
                if row.normalized_name == normalize_name(profile.name)
                or row.name.casefold().endswith(f"({profile.slug.casefold()})")
            ),
            None,
        )
        if university is None:
            university = create_university(db, profile.name)
        desired = build_source_input(profile, university.id)
        start_url = desired.start_url
        existing = db.query(Source).filter(
            Source.university_id == university.id,
            Source.start_url == start_url,
        ).first()
        if existing is not None:
            current = source_config(db, existing)
            current_input = SourceInput.model_validate(current.model_dump(
                exclude={"id", "university_name", "revision", "validated_revision"}
            ))
            extraction_input = current_input.model_copy(update={"enabled": False, "auto_publish": False})
            if extraction_input != desired:
                if not update_inactive or existing.enabled or existing.auto_publish or existing.validated_revision is not None:
                    raise ValueError(f"source_was_edited:{profile.slug}")
                patch_source(db, existing.id, desired.model_dump(), expected_revision=existing.revision)
                summary["updated"] += 1
                continue
            summary["existing"] += 1
            continue
        create_source(db, desired)
        summary["created"] += 1
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, default=Path(__file__).resolve().parents[1] / ".env")
    parser.add_argument("--update-inactive", action="store_true", help="update previously registered inactive profiles")
    args = parser.parse_args()
    settings = BackendSettings(_env_file=str(args.env.resolve()))
    engine = make_engine(settings.database_url)
    with make_session_factory(engine)() as db:
        print(json.dumps(register_catalog(db, update_inactive=args.update_inactive), ensure_ascii=False))


if __name__ == "__main__":
    main()
