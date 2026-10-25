"""Read-only live sample of each configured DatosLab university source."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from collector.discovery import discover
from collector.documents import build_document
from collector.http import FetchError, HttpFetcher
from config import BackendSettings
from database import make_engine, make_session_factory
from models import Source
from scripts.datoslab_catalog import DATOSLAB_PROFILES
from services.sources import source_config
from shared.contracts import Selection
from shared.validation import materialize


def audit_source(config, fetcher: HttpFetcher) -> dict:
    result = {
        "slug": config.start_url.rsplit("/", 1)[-1], "university": config.university_name,
        "source_id": config.id, "source_revision": config.revision,
    }
    try:
        batch = discover(config, fetcher, None, set())
        if not batch.urls:
            return {**result, "status": "no_links"}
        rejected = []
        for url in batch.urls[:config.max_articles]:
            try:
                article = fetcher.fetch(url, config)
                if article.status >= 400:
                    rejected.append({"url": str(article.url), "status": f"http_{article.status}"})
                    continue
                document = build_document(article, config)
                title = next((block for block in document.blocks if block.kind == "title"), None)
                date = next((block for block in document.blocks if block.kind == "date"), None)
                body_chars = sum(len(block.text) for block in document.blocks if block.kind == "body")
                output = {
                    **result, "url": document.canonical_url, "title_chars": len(title.text) if title else 0,
                    "body_chars": body_chars, "date_text": date.text if date else None,
                    "trusted_container": document.trusted_container,
                }
                if not title or len(title.text) < 15 or not date or body_chars < config.min_body_chars or not document.trusted_container:
                    rejected.append({**output, "status": "incomplete_evidence"})
                    continue
                fields = materialize(
                    document,
                    Selection(
                        title_id=title.id, date_id=date.id, body_ids=document.expected_body_ids,
                        category="General",
                    ),
                    config.timezone,
                )
                today = datetime.now(UTC).date()
                if fields.published_on is None or fields.published_on > today or fields.published_on.year < 1900:
                    rejected.append({**output, "status": "invalid_date"})
                    continue
                return {**output, "status": "sample_ok", "published_on": fields.published_on.isoformat(), "rejected_candidates": rejected}
            except FetchError as exc:
                rejected.append({"url": url, "status": "fetch_error", "error_code": exc.code})
            except (ValueError, httpx.HTTPError) as exc:
                rejected.append({"url": url, "status": "parse_error", "error_code": type(exc).__name__})
        return {**result, "status": "no_valid_sample", "rejected_candidates": rejected}
    except FetchError as exc:
        return {**result, "status": "fetch_error", "error_code": exc.code}
    except (ValueError, httpx.HTTPError) as exc:
        return {**result, "status": "parse_error", "error_code": type(exc).__name__}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, default=Path(__file__).resolve().parents[1] / ".env")
    parser.add_argument("--slug", action="append", help="limit the audit to one slug; repeat as needed")
    parser.add_argument("--output", type=Path, help="optional new JSONL report file")
    args = parser.parse_args()
    allowed_slugs = {profile.slug for profile in DATOSLAB_PROFILES}
    requested = set(args.slug or allowed_slugs)
    if requested - allowed_slugs:
        parser.error(f"unknown slugs: {sorted(requested - allowed_slugs)}")
    if args.output and args.output.exists():
        parser.error("output already exists")
    settings = BackendSettings(_env_file=str(args.env.resolve()))
    engine = make_engine(settings.database_url)
    with make_session_factory(engine)() as db, httpx.Client(
        trust_env=False, timeout=httpx.Timeout(30, connect=10)
    ) as client:
        fetcher = HttpFetcher(client)
        sources = [source_config(db, source) for source in db.query(Source).all()]
        by_slug = {source.start_url.rsplit("/", 1)[-1]: source for source in sources
                   if source.start_url.startswith("https://uninews.datoslab.cl/universidad/")}
        records = [audit_source(by_slug[slug], fetcher) for slug in sorted(requested) if slug in by_slug]
    lines = "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(lines, encoding="utf-8")
    print(lines, end="")


if __name__ == "__main__":
    main()
