from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from config import BackendSettings
from main import create_app


@pytest.mark.parametrize(
    "admin,collector,origins",
    [
        ("admin-test", "secure-worker-token-12345", ["https://uninews.vercel.app"]),
        ("secure-admin-token-12345", "worker-test", ["https://uninews.vercel.app"]),
        ("short", "secure-worker-token-12345", ["https://uninews.vercel.app"]),
        ("secure-admin-token-12345", "secure-worker-token-12345", []),
        ("same-secret-token-123456", "same-secret-token-123456", ["https://uninews.vercel.app"]),
    ],
)
def test_production_rejects_weak_or_missing_auth_configuration(admin, collector, origins):
    with pytest.raises(ValidationError):
        BackendSettings(
            app_env="production",
            admin_token=SecretStr(admin),
            collector_token=SecretStr(collector),
            allowed_origins=origins,
        )


def test_normalize_database_url_supports_railway_and_preserves_encoded_password():
    from database import normalize_database_url
    raw = "postgres://postgres:p%40ss%2Fword@db.example:5432/railway"
    assert normalize_database_url(raw) == (
        "postgresql+psycopg2://postgres:p%40ss%2Fword@db.example:5432/railway"
    )
    assert normalize_database_url("postgresql://u:p%25@db.example/db") == (
        "postgresql+psycopg2://u:p%25@db.example/db"
    )
    assert normalize_database_url("sqlite:///./local.db") == "sqlite:///./local.db"


def test_non_sqlite_engine_uses_production_pool_options(monkeypatch):
    import database

    captured = {}
    monkeypatch.setattr(database, "create_engine", lambda url, **kwargs: captured.update(url=url, **kwargs) or object())
    database.make_engine("postgres://u:p%40ss@localhost:5432/db")
    assert captured == {
        "url": "postgresql+psycopg2://u:p%40ss@localhost:5432/db",
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 5,
        "future": True,
    }


def test_migration_url_percent_is_escaped_for_alembic_config(monkeypatch):
    from alembic.config import Config

    from database import normalize_database_url

    cfg = Config("backend/alembic.ini")
    cfg.set_main_option(
        "sqlalchemy.url",
        normalize_database_url("postgres://u:p%40ss@localhost:5432/db").replace("%", "%%"),
    )
    assert cfg.get_main_option("sqlalchemy.url") == (
        "postgresql+psycopg2://u:p%40ss@localhost:5432/db"
    )


def test_collector_status_uses_configured_collector_id_and_news_filter(tmp_path):
    from scripts.bootstrap_db import bootstrap_database

    db_url = f"sqlite:///{(tmp_path / 'news.db').as_posix()}"
    bootstrap_database(db_url)
    settings = BackendSettings(
        database_url=db_url,
        admin_token=SecretStr("admin-secret-12345678"),
        collector_token=SecretStr("worker-secret-12345678"),
        collector_id="configured-worker",
    )
    with TestClient(create_app(settings)) as client:
        heartbeat = {
            "collector_id": "configured-worker",
            "queue_size": 2,
            "llm_status": "ok",
            "disk_free_bytes": 10_000_000,
            "version": "2.0.0",
        }
        assert client.put(
            "/api/collector/status",
            json=heartbeat,
            headers={"Authorization": "Bearer worker-secret-12345678"},
        ).status_code == 204
        status = client.get(
            "/api/admin/collector/status",
            headers={"Authorization": "Bearer admin-secret-12345678"},
        )
        assert status.status_code == 200
        assert status.json()["stale"] is False

        for university in ("Universidad Austral de Chile", "Universidad de Playa Ancha"):
            response = client.post(
                "/api/news/",
                json={"title": f"Beca {university}", "content": "Texto", "category": "Becas", "university": university},
                headers={"Authorization": "Bearer admin-secret-12345678"},
            )
            assert response.status_code == 201
        filtered = client.get(
            "/api/news/", params={"university": "Universidad Austral de Chile"}
        )
        assert [row["university"] for row in filtered.json()] == ["Universidad Austral de Chile"]


def test_news_response_exposes_publication_day_as_date():
    from schemas import NewsResponse

    assert NewsResponse.model_fields["published_on"].annotation == date | None
