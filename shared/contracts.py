"""DTOs estrictos e inmutables en significado para UniNews."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

FREE_MODEL = "nvidia/nemotron-3.5-super-vl:free"
LEGACY_FREE_MODEL = "minimax/minimax-m3:free"

Category = Literal[
    "Academia", "Admisión", "Becas", "Cultura", "Deportes", "Empleo", "Género",
    "Infraestructura", "Investigación", "Tecnología", "Vinculación", "Institucional",
    "Opinión", "General",
]

Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class StrictModel(BaseModel):
    """Base deliberadamente cerrada para payloads entre procesos."""

    model_config = ConfigDict(extra="forbid")


class SourceInput(StrictModel):
    university_id: int = Field(gt=0)
    start_url: str
    allowed_hosts: list[str] = Field(min_length=1, max_length=20)
    allowed_image_hosts: list[str] = Field(default_factory=list, max_length=20)
    feed_url: str | None = None
    article_url_pattern: str | None = None
    link_selector: str = "article a[href]"
    next_selector: str = "a[rel=next]"
    content_selector: str | None = None
    title_selector: str = "h1"
    date_selector: str = "time"
    render_mode: Literal["http", "browser"] = "http"
    wait_selector: str | None = None
    interval_minutes: int = Field(default=360, ge=15, le=10080)
    timezone: str = "America/Santiago"
    max_pages: int = Field(default=10, ge=1, le=50)
    max_articles: int = Field(default=100, ge=1, le=500)
    min_body_chars: int = Field(default=200, ge=50, le=2000)
    image_min_width: int = Field(default=300, ge=50, le=4000)
    image_min_height: int = Field(default=160, ge=50, le=4000)
    enabled: bool = False
    auto_publish: bool = False

    @model_validator(mode="after")
    def _valid_source_shape(self) -> "SourceInput":
        from urllib.parse import urlsplit
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        for value, label in ((self.start_url, "start_url"), (self.feed_url, "feed_url")):
            if value is None:
                continue
            parsed = urlsplit(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError(f"invalid_{label}")
            if parsed.username or parsed.password:
                raise ValueError(f"credentials_in_{label}")
        if any(not host or "://" in host or "/" in host for host in self.allowed_hosts):
            raise ValueError("invalid_allowed_host")
        if any(not host or "://" in host or "/" in host for host in self.allowed_image_hosts):
            raise ValueError("invalid_allowed_image_host")
        if self.render_mode == "browser" and not self.wait_selector:
            raise ValueError("browser_requires_wait_selector")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("invalid_timezone") from exc
        return self


class SourceConfig(SourceInput):
    id: int = Field(gt=0)
    university_name: str = Field(min_length=1, max_length=200)
    revision: int = Field(ge=1)
    validated_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _valid_revision(self) -> "SourceConfig":
        if self.validated_revision is not None and self.validated_revision > self.revision:
            raise ValueError("validated_revision_ahead_of_revision")
        return self


class TextBlock(StrictModel):
    id: int = Field(ge=0)
    kind: Literal["title", "date", "body", "metadata"]
    text: str = Field(min_length=1)


class Document(StrictModel):
    source_id: int = Field(gt=0)
    source_revision: int = Field(ge=1)
    canonical_url: str
    fetched_at: AwareDatetime
    document_hash: Hash
    html_sha256: Hash
    parser_version: str = "blocks-v1"
    blocks: list[TextBlock]
    expected_body_ids: list[int]
    trusted_container: bool = False

    @model_validator(mode="after")
    def _unique_block_ids(self) -> "Document":
        from shared.urls import normalize_url

        normalize_url(self.canonical_url)
        ids = [block.id for block in self.blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate_block_id")
        if any(block_id not in set(ids) for block_id in self.expected_body_ids):
            raise ValueError("expected_body_id_not_found")
        return self


class Selection(StrictModel):
    title_id: int = Field(ge=0)
    body_ids: list[int] = Field(min_length=1)
    date_id: int | None = Field(default=None, ge=0)
    category: Category
    summary: str | None = Field(default=None, max_length=500)


class ArticleFields(StrictModel):
    title: str | None = None
    content: str | None = None
    category: Category | None = None
    summary: str | None = Field(default=None, max_length=500)
    published_at: AwareDatetime | None = None
    published_on: date | None = None
    date_precision: Literal["day", "instant"] | None = None
    original_date_text: str | None = None

    @model_validator(mode="after")
    def _date_fields_cohere(self) -> "ArticleFields":
        provided = (self.published_at, self.published_on, self.date_precision)
        if any(value is not None for value in provided) and any(value is None for value in provided):
            raise ValueError("incomplete_publication_date")
        return self


class ImageAsset(StrictModel):
    status: Literal["not_found", "pending", "ready", "failed"]
    original_url: str | None = None
    sha256: Hash | None = None
    content_type: Literal["image/jpeg", "image/png", "image/webp"] | None = None
    width: int | None = None
    height: int | None = None
    byte_size: int | None = None
    alt: str | None = None
    credit: str | None = None
    error_code: str | None = None

    @model_validator(mode="after")
    def _ready_requires_evidence(self) -> "ImageAsset":
        file_fields = (self.sha256, self.content_type, self.width, self.height, self.byte_size)
        if self.status == "ready":
            if any(value is None for value in file_fields) or not self.original_url:
                raise ValueError("ready_image_requires_file_evidence")
            if any(value <= 0 for value in (self.width, self.height, self.byte_size)):
                raise ValueError("invalid_image_dimensions")
        elif any(value is not None for value in file_fields):
            raise ValueError("non_ready_image_has_file_evidence")
        return self


class StoredImage(StrictModel):
    sha256: Hash
    url: str
    storage_uri: str | None = None


class Delivery(StrictModel):
    delivery_id: UUID
    run_id: UUID
    document: Document
    selection: Selection | None
    fields: ArticleFields
    issues: list[str]
    model: Literal[FREE_MODEL, LEGACY_FREE_MODEL] | None
    prompt_version: str = "extract-v1"
    image: ImageAsset = Field(default_factory=lambda: ImageAsset(status="not_found"))


class Receipt(StrictModel):
    delivery_id: UUID
    revision_id: int
    news_id: int | None
    outcome: Literal["published", "pending", "unchanged", "stale"]


class ImageDelivery(StrictModel):
    delivery_id: UUID
    revision_id: int
    expected_document_hash: Hash
    image: ImageAsset


class MediaReceipt(StrictModel):
    delivery_id: UUID
    revision_id: int
    news_id: int | None
    applied_to_current: bool


_COUNT_KEYS = frozenset({"discovered", "downloaded", "llm_processed", "delivered", "published", "unchanged", "pending", "failed"})


class RunReport(StrictModel):
    run_id: UUID
    source_id: int = Field(gt=0)
    trigger: Literal["scheduled", "manual", "preview"]
    status: Literal["requested", "running", "success", "partial", "failed", "blocked"]
    started_at: AwareDatetime
    finished_at: AwareDatetime | None
    counts: dict[str, int]
    error_code: str | None = None

    @model_validator(mode="after")
    def _valid_counts(self) -> "RunReport":
        if set(self.counts) - _COUNT_KEYS or any(value < 0 for value in self.counts.values()):
            raise ValueError("invalid_run_counts")
        return self


class RunRequest(StrictModel):
    run_id: UUID
    source: SourceConfig
    trigger: Literal["manual", "preview"]
    lease_token: UUID
    lease_until: AwareDatetime


class RunSummary(StrictModel):
    started_at: AwareDatetime
    finished_at: AwareDatetime
    counts: dict[str, int]
    pending_count: int = Field(ge=0)
    exit_code: int = Field(ge=0)


class PreviewResult(StrictModel):
    source_revision: int = Field(ge=1)
    documents: list[Document] = Field(max_length=3)
    selections: list[Selection | None] = Field(max_length=3)
    issues: list[list[str]] = Field(max_length=3)

    @model_validator(mode="after")
    def _parallel_preview_lists(self) -> "PreviewResult":
        if len(self.documents) != len(self.selections) or len(self.documents) != len(self.issues):
            raise ValueError("preview_lengths_mismatch")
        return self


class CollectorHeartbeat(StrictModel):
    collector_id: str = Field(min_length=1, max_length=80)
    queue_size: int = Field(ge=0)
    oldest_pending_at: AwareDatetime | None = None
    last_sources_sync_at: AwareDatetime | None = None
    llm_status: str
    disk_free_bytes: int = Field(ge=0)
    version: str = Field(min_length=1, max_length=80)


# Nombre breve útil para clientes HTTP; se conserva el nombre descriptivo anterior.
Heartbeat = CollectorHeartbeat


def stable_json(value: object) -> str:
    """Serialización canónica para identidad y recibos entre procesos."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_digest(value: object) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()
