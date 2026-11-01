from datetime import datetime, timezone
import pytest
from starlette.requests import Request
from rag.chat_guard import ChatGuard, ChatRateLimitError, extract_client_ip


def _make_request(client_host: str, headers: dict[str, str] | None = None) -> Request:
    raw_headers = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    return Request({"type": "http", "client": (client_host, 12345), "headers": raw_headers})


def test_extract_client_ip_uses_validated_railway_real_ip_only_when_proxy_trusted():
    req = _make_request("100.64.0.5", {"X-Real-IP": "190.45.10.22", "X-Forwarded-For": "1.1.1.1, 8.8.8.8"})
    assert extract_client_ip(req, trust_proxy_headers=True) == "190.45.10.22"
    assert extract_client_ip(req, trust_proxy_headers=False) == "100.64.0.5"


def test_extract_client_ip_ignores_invalid_proxy_headers():
    req = _make_request("100.64.0.5", {"X-Real-IP": "1.1.1.1, 190.45.10.22", "X-Forwarded-For": "190.45.10.22"})
    assert extract_client_ip(req, trust_proxy_headers=True) == "100.64.0.5"


def test_extract_client_ip_prefers_global_envoy_external_address_when_real_ip_is_internal_or_missing():
    req_envoy = _make_request(
        "100.64.0.5",
        {"X-Envoy-External-Address": "190.45.10.33", "X-Real-IP": "10.12.0.4"},
    )
    assert extract_client_ip(req_envoy, trust_proxy_headers=True) == "190.45.10.33"

    req_envoy_only = _make_request(
        "100.64.0.5",
        {"X-Envoy-External-Address": "190.45.10.44"},
    )
    assert extract_client_ip(req_envoy_only, trust_proxy_headers=True) == "190.45.10.44"


def test_ip_rate_limit_and_daily_budget_enforced():
    guard = ChatGuard(ip_rpm=2, daily_budget=3)
    now = datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc)
    guard.reserve_live_call("203.0.113.10", now)
    guard.reserve_live_call("203.0.113.10", now)
    with pytest.raises(ChatRateLimitError):
        guard.reserve_live_call("203.0.113.10", now)
    guard.reserve_live_call("198.51.100.7", now)
    with pytest.raises(ChatRateLimitError):
        guard.reserve_live_call("198.51.100.99", now)


def test_published_editorial_edit_invalidates_marker_when_updated_at_advances(tmp_path):
    from datetime import datetime, timezone
    from pathlib import Path
    import sys
    sys.path.insert(0, "backend")
    from database import make_engine, make_session_factory
    from models import News
    from scripts.bootstrap_db import bootstrap_database

    url = "sqlite:///" + (tmp_path / "marker.db").as_posix()
    bootstrap_database(url)
    db = make_session_factory(make_engine(url))()
    stamp = datetime(2026, 11, 1, tzinfo=timezone.utc)
    news = News(id=1, title="Título original", content="Texto original", category="General", university="UPLA", publication_status="published", created_at=stamp, updated_at=stamp)
    db.add(news)
    db.commit()
    guard = ChatGuard()
    marker_before = guard.snapshot_marker(db)
    guard.put_cached(1, "pregunta", marker_before, {"answer": "respuesta vieja", "sources": []}, 1.0)
    news.title = "Título corregido"
    news.content = "Texto corregido"
    news.updated_at = stamp.replace(minute=1)
    db.commit()
    marker_after = guard.snapshot_marker(db)
    assert marker_after != marker_before
    assert guard.get_cached(1, "pregunta", marker_after, 2.0) is None
    db.close()
