"""Offline production acceptance across migrations, collection, media, chat and API."""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import socket
from pathlib import Path
from datetime import date, datetime, timezone
from uuid import uuid4

import httpx
from PIL import Image

from models import CollectorStatus, News, Source, SourceVersion
from scripts.datoslab_catalog import VERIFIED_SLUGS
from scripts.seed_production_sources import seed_production_sources
from shared.contracts import (
    ArticleFields, Delivery, Document, FREE_MODEL, Selection, TextBlock,
)
from shared.validation import document_digest


def _upgrade_empty_database(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "backend" / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")


def _large_test_png() -> bytes:
    image = Image.new("RGB", (320, 180), color=(20, 90, 140))
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def test_seeded_uach_collection_media_and_contextual_chat_are_ready(monkeypatch, tmp_path):
    """Use only MockTransport and a migrated SQLite DB for the full acceptance path."""
    from rag.chat_guard import ChatGuard
    from rag.news_assistant import NewsAssistant
    from rag.openrouter import OpenRouterClient
    from services.sources import source_config
    from tests.integration import pipeline_harness as harness_module
    from tests.integration.pipeline_harness import PipelineHarness

    # The collector validates DNS destinations before sending HTTP. Resolve the
    # fixture hosts to a public test address without consulting system DNS.
    monkeypatch.setattr(
        socket, "getaddrinfo",
        lambda host, *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
    )
    monkeypatch.setattr(harness_module, "bootstrap_database", _upgrade_empty_database)
    harness = PipelineHarness(tmp_path)
    harness.current_time = harness.current_time.replace(month=10, day=30)
    media_root = tmp_path / "media-root"
    media_root.mkdir()
    harness.app.state.settings.media_root = media_root

    with harness.app.state.session_factory() as db:
        seeded = seed_production_sources(db)
        assert seeded["universities_total"] == 22
        assert seeded["sources_enabled"] == len(VERIFIED_SLUGS) == 11

        # Configure the seeded UACH catalog entry for deterministic fixture URLs.
        uach = db.query(Source).filter(Source.start_url.endswith("/UACH")).one()
        config_json = dict(uach.config_json)
        config_json.update(
            allowed_hosts=["uninews.datoslab.cl", "diario.uach.cl"],
            allowed_image_hosts=["uach.cl", "www.uach.cl"],
            link_selector="article a[href]",
            content_selector="article",
            title_selector="h1",
            date_selector="time",
            min_body_chars=50,
            image_min_width=300,
            image_min_height=160,
        )
        uach.config_json = config_json
        uach.enabled = True
        uach.auto_publish = True
        uach.validated_revision = uach.revision
        snapshot = db.get(SourceVersion, (uach.id, uach.revision))
        snapshot.snapshot_json = source_config(db, uach).model_dump(mode="json")
        # Disable the harness's unrelated uni.example source for this run.
        db.get(Source, 1).enabled = False
        db.commit()
        uach_id, uach_revision = uach.id, uach.revision

    png_bytes = _large_test_png()
    png_sha256 = hashlib.sha256(png_bytes).hexdigest()
    article_html = (
        "<article><h1>Estudio sobre glaciares</h1>"
        '<time datetime="2026-10-15">2026-10-15</time>'
        '<img data-src="https://www.uach.cl/fotos/glaciar.jpg" alt="Glaciar estudiado">'
        "<p>Investigadores de la UACH estudian glaciares y conservación del agua. "
        "Este texto original documenta el estudio científico y sus resultados principales.</p></article>"
    )
    listing = '<article><a href="/detalle/101">Primera noticia</a></article>'
    image_redirect = "https://i0.wp.com/diario.uach.cl/glaciar.jpg"
    collector_openrouter_payloads: list[dict] = []

    def transport_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        parsed = request.url
        if "openrouter.ai" in url:
            if request.method == "POST":
                collector_openrouter_payloads.append(json.loads(request.content))
            return harness._handle_request(request)
        if url.startswith(harness.api_url):
            return harness._handle_request(request)
        if parsed.host in {"uninews.datoslab.cl", "diario.uach.cl", "www.uach.cl", "i0.wp.com"}:
            if parsed.path == "/robots.txt":
                return httpx.Response(200, text="User-agent: *\nAllow: /\n")
            if parsed.host == "uninews.datoslab.cl" and parsed.path == "/universidad/UACH":
                return httpx.Response(200, text=listing, headers={"content-type": "text/html"})
            if parsed.host == "uninews.datoslab.cl" and parsed.path == "/detalle/101":
                return httpx.Response(302, headers={"location": "https://diario.uach.cl/2026/10/estudio-glaciares"})
            if parsed.host == "uninews.datoslab.cl" and parsed.path == "/detalle/102":
                return httpx.Response(302, headers={"location": "https://diario.uach.cl/2026/10/monitoreo-glaciares"})
            if parsed.host == "diario.uach.cl" and parsed.path == "/2026/10/estudio-glaciares":
                return httpx.Response(200, text=article_html, headers={"content-type": "text/html"})
            if parsed.host == "www.uach.cl" and parsed.path == "/fotos/glaciar.jpg":
                return httpx.Response(302, headers={"location": image_redirect})
            if parsed.host == "i0.wp.com" and parsed.path == "/diario.uach.cl/glaciar.jpg":
                return httpx.Response(200, content=png_bytes, headers={"content-type": "image/png"})
        return httpx.Response(404, text="Not Found")

    harness.transport = httpx.MockTransport(transport_handler)
    harness.llm_returns_selection(category="Investigación", summary="Estudio de glaciares")
    harness.run()

    with harness.app.state.session_factory() as db:
        first = db.query(News).filter(News.title == "Estudio sobre glaciares").one()
        first_id = first.id
        assert first.publication_status == "published"
        assert first.source_url == "https://diario.uach.cl/2026/10/estudio-glaciares"
        assert first.image_sha256 == png_sha256
        assert first.image_original_url == image_redirect
        assert first.image_url == f"/api/media/{png_sha256}"
        status = db.get(CollectorStatus, "windows-collector-1")
        assert status is not None and status.status_json["version"] == "2.0.0"

    assert collector_openrouter_payloads
    assert all(payload["model"] == FREE_MODEL for payload in collector_openrouter_payloads)
    assert all(payload["provider"]["max_price"] == {"prompt": 0, "completion": 0} for payload in collector_openrouter_payloads)

    public = harness.api_client.get("/api/news/", params={"university": "Universidad Austral de Chile"})
    assert public.status_code == 200 and len(public.json()) == 1
    assert public.json()[0]["image_url"] == f"/api/media/{png_sha256}"

    # The media route must serve DB bytes after the local media directory is gone.
    shutil.rmtree(media_root)
    media = harness.api_client.get(f"/api/media/{png_sha256}")
    assert media.status_code == 200 and media.content == png_bytes
    assert media.headers["etag"] == f'"{png_sha256}"'
    assert media.headers["x-content-type-options"] == "nosniff"

    # Ingest a second related article through the same authenticated API contract.
    second_title = "Nuevo monitoreo de glaciares"
    second_body = (
        "Un equipo de investigación de la UACH amplía el monitoreo de glaciares. "
        "El reporte institucional describe observaciones recientes y conservación del agua."
    )
    second_blocks = [
        TextBlock(id=0, kind="title", text=second_title),
        TextBlock(id=1, kind="date", text="2026-10-16"),
        TextBlock(id=2, kind="body", text=second_body),
    ]
    second_document = Document(
        source_id=uach_id,
        source_revision=uach_revision,
        canonical_url="https://diario.uach.cl/2026/10/monitoreo-glaciares",
        fetched_at=datetime(2026, 10, 30, tzinfo=timezone.utc),
        document_hash=document_digest(second_blocks, [2]),
        html_sha256=hashlib.sha256(second_body.encode()).hexdigest(),
        blocks=second_blocks,
        expected_body_ids=[2],
        trusted_container=True,
    )
    second_delivery = Delivery(
        delivery_id=uuid4(),
        run_id=uuid4(),
        document=second_document,
        selection=Selection(title_id=0, date_id=1, body_ids=[2], category="Investigación"),
        fields=ArticleFields(
            title=second_title,
            content=second_body,
            category="Investigación",
            summary="Monitoreo institucional de glaciares",
            published_at=datetime(2026, 10, 16, tzinfo=timezone.utc),
            published_on=date(2026, 10, 16),
            date_precision="day",
            original_date_text="2026-10-16",
        ),
        issues=[],
        model=FREE_MODEL,
    )
    ingested = harness.api_client.post(
        "/api/collector/articles",
        json=second_delivery.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {harness.api_token}"},
    )
    assert ingested.status_code == 200
    with harness.app.state.session_factory() as db:
        second = db.query(News).filter(News.title == second_title).one()
        assert second.publication_status == "published"

    chat_payloads: list[dict] = []

    def chat_transport(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        chat_payloads.append(payload)
        return httpx.Response(200, json={"choices": [{"message": {"content": "Contexto respaldado por ambas noticias."}}]})

    assistant_client = httpx.Client(transport=httpx.MockTransport(chat_transport))
    llm = OpenRouterClient(api_key="offline-test-key", model=FREE_MODEL, client=assistant_client)
    harness.app.state.assistant = NewsAssistant(llm)
    harness.app.state.chat_guard = ChatGuard(ip_rpm=1, daily_budget=20)

    question = "¿Qué contexto hay sobre investigaciones en la UACH?"
    chat_request = {"question": question, "news_id": first_id}
    first_chat = harness.api_client.post("/api/chat/", json=chat_request)
    assert first_chat.status_code == 200
    assert {item["title"] for item in first_chat.json()["sources"]} == {
        "Estudio sobre glaciares", "Nuevo monitoreo de glaciares"
    }
    prompt = chat_payloads[0]["messages"][1]["content"]
    assert "[NOTICIA EN FOCO]" in prompt
    assert "[ANTECEDENTES RELACIONADOS DEL ARCHIVO]" in prompt
    assert "[CATÁLOGO RECIENTE DEL PORTAL]" in prompt
    assert all(payload["model"] == FREE_MODEL for payload in chat_payloads)
    assert all(payload["provider"]["max_price"] == {"prompt": 0, "completion": 0} for payload in chat_payloads)

    cached_chat = harness.api_client.post("/api/chat/", json=chat_request)
    assert cached_chat.status_code == 200 and cached_chat.json() == first_chat.json()
    assert len(chat_payloads) == 1, "identical request should be served from cache"

    rate_limited = harness.api_client.post(
        "/api/chat/", json={"question": "¿Qué otros resultados reporta esta noticia?", "news_id": first_id}
    )
    assert rate_limited.status_code == 429
    assert len(chat_payloads) == 1, "rate-limited request must not call OpenRouter"

    # Railway documents X-Real-IP for the originating address. X-Forwarded-For
    # may contain client-supplied values and its ordering is not a contract, so
    # the API must ignore it and key production limits only by validated X-Real-IP.
    harness.app.state.settings.app_env = "production"
    edited = harness.api_client.put(
        f"/api/news/{first_id}",
        json={"title": "Estudio actualizado sobre glaciares"},
        headers={"Authorization": "Bearer admin-test"},
    )
    assert edited.status_code == 200
    changed_title_question = {"question": question, "news_id": first_id}
    refreshed = harness.api_client.post(
        "/api/chat/",
        json=changed_title_question,
        headers={"X-Real-IP": "190.45.1.10", "X-Forwarded-For": "1.1.1.1"},
    )
    assert refreshed.status_code == 200
    assert len(chat_payloads) == 2, "editing a published news item must invalidate the chat cache"
    assert any(item["title"] == "Estudio actualizado sobre glaciares" for item in refreshed.json()["sources"])

    other_visitor = harness.api_client.post(
        "/api/chat/",
        json={"question": "¿Qué nuevos antecedentes aparecen?", "news_id": first_id},
        headers={"X-Real-IP": "190.45.1.11", "X-Forwarded-For": "190.45.1.10"},
    )
    assert other_visitor.status_code == 200, "distinct Railway X-Real-IP values must have independent limits"
    spoof_attempt = harness.api_client.post(
        "/api/chat/",
        json={"question": "¿Qué otro detalle se menciona?", "news_id": first_id},
        headers={"X-Real-IP": "190.45.1.10", "X-Forwarded-For": "8.8.8.8"},
    )
    assert spoof_attempt.status_code == 429, "X-Forwarded-For must not bypass the trusted X-Real-IP bucket"

    with harness.app.state.session_factory() as db:
        first = db.get(News, first_id)
        first.publication_status = "pending"
        db.commit()
    remaining_public = harness.api_client.get("/api/news/").json()
    assert [item["title"] for item in remaining_public] == ["Nuevo monitoreo de glaciares"]
