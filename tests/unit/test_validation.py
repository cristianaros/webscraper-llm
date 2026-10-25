from datetime import datetime, timezone

from shared.contracts import Document, Selection, SourceConfig, TextBlock
from shared.validation import document_digest, materialize, validate_article


def _source() -> SourceConfig:
    return SourceConfig(id=1, university_id=1, university_name="Universidad de Prueba", start_url="https://uni.example/noticias/", allowed_hosts=["uni.example"], revision=1, validated_revision=1, enabled=True, auto_publish=True, min_body_chars=50)


def _document() -> Document:
    body = "La universidad presentó una investigación sobre conservación del agua. " * 4
    blocks = [TextBlock(id=0, kind="title", text="Investigación sobre el agua"), TextBlock(id=1, kind="date", text="05/09/2026"), TextBlock(id=2, kind="body", text=body.strip())]
    return Document(source_id=1, source_revision=1, canonical_url="https://uni.example/noticias/agua", fetched_at=datetime(2026, 9, 6, 16, tzinfo=timezone.utc), document_hash=document_digest(blocks, [2]), html_sha256="a" * 64, trusted_container=True, expected_body_ids=[2], blocks=blocks)


def test_keeps_original_body_and_day():
    document, source = _document(), _source()
    selection = Selection(title_id=0, body_ids=[2], date_id=1, category="Investigación")
    fields = materialize(document, selection, source.timezone)
    assert fields.content == document.blocks[2].text
    assert fields.published_on.isoformat() == "2026-09-05"
    assert fields.date_precision == "day"


def test_iso_publication_date_keeps_year_month_day_order():
    document, source = _document(), _source()
    document.blocks[1] = TextBlock(id=1, kind="date", text="2026-10-09")
    selection = Selection(title_id=0, body_ids=[2], date_id=1, category="Investigación")
    fields = materialize(document, selection, source.timezone)
    assert fields.published_on.isoformat() == "2026-10-09"
    assert fields.original_date_text == "2026-10-09"
    assert fields.date_precision == "day"


def test_missing_date_requires_review():
    document, source = _document(), _source()
    selection = Selection(title_id=0, body_ids=[2], date_id=None, category="Investigación")
    fields = materialize(document, selection, source.timezone)
    issues = validate_article(fields, document, selection, source, document.fetched_at)
    assert fields.published_at is None
    assert "missing_publication_date" in issues


def test_omitted_trusted_body_and_hash_mismatch_require_review():
    document, source = _document(), _source()
    selection = Selection(title_id=0, body_ids=[2], date_id=1, category="Investigación")
    fields = materialize(document, selection, source.timezone)
    assert "invalid_document_hash" not in validate_article(fields, document, selection, source, document.fetched_at)
    altered = document.model_copy(update={"document_hash": "b" * 64})
    assert "invalid_document_hash" in validate_article(fields, altered, selection, source, document.fetched_at)
