from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from shared.contracts import (
    ArticleFields, Delivery, Document, ImageAsset, RunReport, Selection, SourceConfig, TextBlock,
    payload_digest, stable_json,
)
from shared.validation import document_digest


def _source() -> SourceConfig:
    return SourceConfig(id=1, university_id=1, university_name="Universidad de Prueba", start_url="https://uni.example/noticias/", allowed_hosts=["uni.example"], revision=1, validated_revision=1)


def _document() -> Document:
    blocks = [TextBlock(id=0, kind="title", text="Investigación sobre el agua"), TextBlock(id=1, kind="date", text="2026-09-05"), TextBlock(id=2, kind="body", text="La universidad presentó una investigación sobre conservación del agua. " * 4)]
    return Document(source_id=1, source_revision=1, canonical_url="https://uni.example/noticias/agua", fetched_at=datetime(2026, 9, 6, tzinfo=timezone.utc), document_hash=document_digest(blocks, [2]), html_sha256="a" * 64, blocks=blocks, expected_body_ids=[2], trusted_container=True)


def test_llm_cannot_supply_university_or_rewrite_body():
    with pytest.raises(ValidationError):
        Selection.model_validate({"title_id": 0, "body_ids": [2], "date_id": 1, "category": "Investigación", "summary": None, "university": "Otra universidad", "body": "Contenido inventado"})


def test_operational_datetime_requires_timezone():
    with pytest.raises(ValidationError):
        Document.model_validate({**_document().model_dump(mode="json"), "fetched_at": "2026-09-06T00:00:00"})


def test_paid_model_and_extra_delivery_field_are_rejected():
    with pytest.raises(ValidationError):
        Delivery.model_validate({"delivery_id": str(UUID(int=1)), "run_id": str(UUID(int=2)), "document": _document().model_dump(mode="json"), "selection": None, "fields": {}, "issues": [], "model": "paid/model"})


def test_report_counts_are_limited_and_non_negative():
    report = {"run_id": str(UUID(int=1)), "source_id": 1, "trigger": "scheduled", "status": "success", "started_at": "2026-09-06T00:00:00Z", "finished_at": None, "counts": {"downloaded": 1}}
    assert RunReport.model_validate(report).counts == {"downloaded": 1}
    with pytest.raises(ValidationError):
        RunReport.model_validate({**report, "counts": {"invented": 1}})


def test_ready_image_requires_complete_original_evidence():
    with pytest.raises(ValidationError):
        ImageAsset(status="ready", sha256="a" * 64, content_type="image/png", width=1, height=1, byte_size=1)


def test_canonical_payload_hash_is_key_order_independent():
    assert stable_json({"b": 1, "a": "á"}) == '{"a":"á","b":1}'
    assert payload_digest({"b": 1, "a": "á"}) == payload_digest({"a": "á", "b": 1})
