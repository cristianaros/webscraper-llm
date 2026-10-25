"""Materialización fiel y validación compartida de artículos."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, time
from zoneinfo import ZoneInfo

import dateparser

from shared.contracts import ArticleFields, Document, Selection, SourceConfig, TextBlock
from shared.urls import normalize_url


def document_digest(blocks: list[TextBlock], expected_body_ids: list[int]) -> str:
    value = {"blocks": [block.model_dump() for block in blocks], "body_ids": expected_body_ids}
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def select_body(doc: Document, selection: Selection) -> str:
    blocks = {block.id: block for block in doc.blocks}
    ids = selection.body_ids
    if ids != sorted(set(ids)):
        raise ValueError("unordered_or_repeated_body_ids")
    if any(block_id not in blocks or blocks[block_id].kind != "body" for block_id in ids):
        raise ValueError("invalid_body_reference")
    return "\n\n".join(blocks[block_id].text for block_id in ids)


def materialize(doc: Document, selection: Selection, timezone_name: str) -> ArticleFields:
    blocks = {block.id: block for block in doc.blocks}
    title = blocks.get(selection.title_id)
    if title is None or title.kind != "title":
        raise ValueError("invalid_title_reference")
    content = select_body(doc, selection)
    values: dict[str, object] = {"title": title.text, "content": content, "category": selection.category, "summary": selection.summary}
    if selection.date_id is None:
        return ArticleFields(**values)
    date_block = blocks.get(selection.date_id)
    if date_block is None or date_block.kind != "date":
        raise ValueError("invalid_date_reference")
    # Estas expresiones dependen del momento de extracción y no son evidencia editorial.
    if re.search(r"\b(hoy|ayer|mañana|hace\s+\d+)\b", date_block.text, flags=re.IGNORECASE):
        return ArticleFields(**values, original_date_text=date_block.text)
    date_text = date_block.text.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[Tt ].+)?", date_text):
        try:
            parsed = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
    else:
        parsed = dateparser.parse(
            date_text,
            languages=["es"],
            settings={"DATE_ORDER": "DMY", "STRICT_PARSING": True, "RETURN_AS_TIMEZONE_AWARE": False},
        )
    if parsed is None:
        return ArticleFields(**values, original_date_text=date_block.text)
    zone = ZoneInfo(timezone_name)
    if parsed.tzinfo is None:
        local = parsed.replace(tzinfo=zone)
        precision = "day" if parsed.time() == time.min else "instant"
    else:
        local = parsed.astimezone(zone)
        precision = "instant"
    return ArticleFields(
        **values,
        published_at=local.astimezone(ZoneInfo("UTC")),
        published_on=local.date(),
        date_precision=precision,
        original_date_text=date_block.text,
    )


def body_issues(doc: Document, selection: Selection | None) -> list[str]:
    if selection is None:
        return ["llm_selection_missing"]
    if not doc.trusted_container:
        return ["unvalidated_container"]
    if selection.body_ids != doc.expected_body_ids:
        return ["body_coverage_mismatch"]
    return []


def validate_article(fields: ArticleFields, doc: Document, selection: Selection | None, source: SourceConfig, now: datetime) -> list[str]:
    issues = body_issues(doc, selection)
    if fields.title is None or not 5 <= len(fields.title.strip()) <= 255:
        issues.append("title_missing_or_length")
    if fields.content is None or len(fields.content.strip()) < source.min_body_chars:
        issues.append("body_too_short")
    if fields.category is None:
        issues.append("missing_category")
    if fields.published_at is None or fields.published_on is None or fields.date_precision is None:
        issues.append("missing_publication_date")
        if selection is not None and selection.date_id is not None:
            issues.append("invalid_publication_date")
    else:
        local_now = now.astimezone(ZoneInfo(source.timezone)).date()
        if fields.published_on.year < 1900 or fields.published_on > local_now.fromordinal(local_now.toordinal() + 1):
            issues.append("invalid_publication_date")
    if selection is not None:
        try:
            materialized = materialize(doc, selection, source.timezone)
        except ValueError:
            issues.append("selection_reference_invalid")
        else:
            if fields.title != materialized.title or fields.content != materialized.content:
                issues.append("selection_text_mismatch")
            if fields.category != materialized.category:
                issues.append("selection_category_mismatch")
            if (fields.published_at, fields.published_on, fields.date_precision, fields.original_date_text) != (
                materialized.published_at, materialized.published_on, materialized.date_precision, materialized.original_date_text,
            ):
                issues.append("selection_date_mismatch")
    if source.validated_revision != source.revision:
        issues.append("source_revision_unvalidated")
    if not source.enabled:
        issues.append("source_disabled")
    try:
        from urllib.parse import urlsplit

        hostname = urlsplit(normalize_url(doc.canonical_url)).hostname
        assert hostname is not None
        hostname = hostname.lower()
        if hostname not in {host.lower().rstrip(".") for host in source.allowed_hosts}:
            issues.append("invalid_origin")
    except ValueError:
        issues.append("invalid_origin")
    if document_digest(doc.blocks, doc.expected_body_ids) != doc.document_hash:
        issues.append("invalid_document_hash")
    if sum(len(block.text) for block in doc.blocks if block.kind == "body") > 40_000:
        issues.append("input_too_large")
    return list(dict.fromkeys(issues))
