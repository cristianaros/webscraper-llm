import httpx
import pytest

from collector.discovery import discover
from collector.documents import build_document
from collector.http import FetchError, HttpFetcher
from scripts.audit_datoslab_sources import audit_source
from scripts.datoslab_catalog import DATOSLAB_PROFILES, build_source_input
from shared.contracts import SourceConfig


def test_directory_link_reaches_only_the_assigned_university(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("93.184.216.34", 443))],
    )
    profile = next(item for item in DATOSLAB_PROFILES if item.slug == "UPLA")
    source = SourceConfig.model_validate({
        **build_source_input(profile, university_id=1).model_dump(),
        "id": 1, "university_name": profile.name, "revision": 1,
        "validated_revision": 1, "enabled": True, "auto_publish": True,
    })

    def respond(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("/robots.txt"):
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if url == source.start_url:
            return httpx.Response(
                200, text='<div class="album py-5">'
                '<p class="card-text"><a href="/detalle/123">UPLA</a></p>'
                '<p class="card-text"><a href="/detalle/456">Ajena</a></p></div>',
                headers={"content-type": "text/html"},
            )
        if url.endswith("/detalle/123"):
            return httpx.Response(302, headers={"location": "https://upla.cl/noticias/actividad"})
        if url.endswith("/detalle/456"):
            return httpx.Response(302, headers={"location": "https://uchile.cl/noticias/ajena"})
        if url == "https://upla.cl/noticias/actividad":
            return httpx.Response(200, text=(
                '<meta property="article:published_time" content="2026-10-14T13:13:39-03:00">'
                '<h1>Actividad de la Universidad de Playa Ancha</h1>'
                '<article><div class="entry"><p>' + "Texto original de la universidad. " * 12
                + "</p></div></article>"
            ), headers={"content-type": "text/html"})
        raise AssertionError(f"unexpected request: {url}")

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        fetcher = HttpFetcher(client, allow_test_hosts=True)
        urls = discover(source, fetcher, None, set()).urls
        document = build_document(fetcher.fetch(urls[0], source), source)
        with pytest.raises(FetchError, match="destination_host_not_allowed"):
            fetcher.fetch(urls[1], source)

    assert len(urls) == 2
    assert document.canonical_url == "https://upla.cl/noticias/actividad"
    assert next(block.text for block in document.blocks if block.kind == "date") == "2026-10-14T13:13:39-03:00"
    assert document.trusted_container is True


def test_audit_checks_later_article_when_first_lacks_publication_date(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("93.184.216.34", 443))],
    )
    profile = next(item for item in DATOSLAB_PROFILES if item.slug == "UPLA")
    source = SourceConfig.model_validate({
        **build_source_input(profile, university_id=1).model_dump(),
        "id": 1, "university_name": profile.name, "revision": 1,
    })

    def respond(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("/robots.txt"):
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if url == source.start_url:
            return httpx.Response(200, text=(
                '<div class="album py-5"><p class="card-text"><a href="/detalle/111">Sin fecha</a></p>'
                '<p class="card-text"><a href="/detalle/222">Con fecha</a></p></div>'
            ))
        if url.endswith("/detalle/111"):
            return httpx.Response(302, headers={"location": "https://upla.cl/noticias/sin-fecha"})
        if url.endswith("/detalle/222"):
            return httpx.Response(302, headers={"location": "https://upla.cl/noticias/con-fecha"})
        if url.startswith("https://upla.cl/noticias/"):
            date = '<meta property="article:published_time" content="2026-10-14T13:13:39-03:00">' if url.endswith("con-fecha") else ""
            return httpx.Response(200, text=(
                date + '<h1>Actividad de la Universidad de Playa Ancha</h1>'
                '<article><div class="entry"><p>' + "Texto original de la universidad. " * 12
                + "</p></div></article>"
            ))
        raise AssertionError(f"unexpected request: {url}")

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = audit_source(source, HttpFetcher(client, allow_test_hosts=True))
    assert result["status"] == "sample_ok"
    assert result["url"] == "https://upla.cl/noticias/con-fecha"
    assert result["published_on"] == "2026-10-14"
    assert len(result["rejected_candidates"]) == 1
    assert result["rejected_candidates"][0]["status"] == "incomplete_evidence"
