"""Default tests cannot open connections to production services."""

import ipaddress
import socket

import pytest


def _assert_local(address):
    if not isinstance(address, tuple):
        return  # Local Unix-domain sockets do not reach an external host.
    host = address[0]
    if host == "localhost":
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    raise AssertionError("External network disabled: use fixtures or MockTransport")


@pytest.fixture(autouse=True)
def deny_external_network(monkeypatch, request):
    if request.node.get_closest_marker("live"):
        return
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create = socket.create_connection

    def connect(sock, address):
        _assert_local(address)
        return original_connect(sock, address)

    def connect_ex(sock, address):
        _assert_local(address)
        return original_connect_ex(sock, address)

    def create_connection(address, *args, **kwargs):
        _assert_local(address)
        return original_create(address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "create_connection", create_connection)


from datetime import datetime, timezone
from uuid import UUID
from shared.contracts import SourceConfig, Document, Selection, ArticleFields, Delivery, TextBlock
from shared.validation import document_digest


@pytest.fixture
def source():
    return SourceConfig(
        id=1, university_id=1, university_name="Universidad de Prueba",
        start_url="https://uni.example/noticias/", allowed_hosts=["uni.example"],
        revision=1, validated_revision=1, enabled=True, auto_publish=True,
        content_selector="article .entry-content",
    )


@pytest.fixture
def document():
    body = "La universidad presentó una investigación sobre conservación del agua. " * 4
    blocks = [
        TextBlock(id=0, kind="title", text="Investigación sobre el agua"),
        TextBlock(id=1, kind="date", text="2026-09-05"),
        TextBlock(id=2, kind="body", text=body.strip()),
    ]
    return Document(
        source_id=1, source_revision=1,
        canonical_url="https://uni.example/noticias/agua",
        fetched_at=datetime(2026, 9, 6, 16, tzinfo=timezone.utc),
        document_hash=document_digest(blocks, [2]), html_sha256="a" * 64,
        trusted_container=True, expected_body_ids=[2], blocks=blocks,
    )


@pytest.fixture
def selection():
    return Selection(title_id=0, body_ids=[2], date_id=1, category="Investigación")


@pytest.fixture
def delivery(document, selection):
    return Delivery(
        delivery_id=UUID(int=1), run_id=UUID(int=2), document=document,
        selection=selection, fields=ArticleFields(), issues=[],
        model="minimax/minimax-m3:free",
    )


@pytest.fixture
def pipeline_harness(tmp_path):
    from tests.integration.pipeline_harness import PipelineHarness
    return PipelineHarness(tmp_path)


@pytest.fixture
def analytics_harness(tmp_path, pipeline_harness):
    from tests.integration.analytics_harness import AnalyticsHarness
    return AnalyticsHarness(pipeline_harness.app.state.session_factory(), tmp_path)

