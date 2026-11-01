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


def test_unified_root_env_loads_cleanly_for_backend_and_collector(tmp_path, monkeypatch):
    from config import BackendSettings, load_backend_settings
    from collector.config import load_settings as load_collector_settings
    from shared.contracts import FREE_MODEL

    collector_dir = tmp_path / "collector-data"
    unified_env = tmp_path / ".env"
    unified_env.write_text(
        "\n".join(
            [
                "APP_ENV=development",
                "PUBLIC_API_URL=http://127.0.0.1:8765",
                f"DATABASE_URL=sqlite:///{(tmp_path / 'news.db').as_posix()}",
                "ADMIN_TOKEN=admin-secret-token-0123456789abcdef",
                "COLLECTOR_TOKEN=collector-secret-token-0123456789abcdef",
                "COLLECTOR_ID=windows-collector-1",
                'ALLOWED_ORIGINS=["http://127.0.0.1:4321","http://localhost:4321"]',
                "RAG_ENABLED=true",
                "OPENROUTER_API_KEY=sk-or-v1-offline-fixture-key",
                f"OPENROUTER_MODEL={FREE_MODEL}",
                "OPENROUTER_SITE_URL=http://127.0.0.1:4321",
                "OPENROUTER_APP_NAME=UniNews",
                "CHAT_DAILY_BUDGET=100",
                "CHAT_IP_RPM=6",
                f"MEDIA_ROOT={(tmp_path / 'media').as_posix()}",
                f"COLLECTOR_DATA_DIR={collector_dir.as_posix()}",
                "COLLECTOR_API_URL=http://127.0.0.1:8765",
                "LLM_DAILY_BUDGET=30",
                "LLM_RPM=5",
                "RUN_BUDGET_SECONDS=720",
                "SOURCE_CACHE_TTL_HOURS=24",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    backend_cfg = load_backend_settings(unified_env)
    collector_cfg = load_collector_settings(unified_env)

    assert backend_cfg.admin_token.get_secret_value() == "admin-secret-token-0123456789abcdef"
    assert backend_cfg.collector_token.get_secret_value() == "collector-secret-token-0123456789abcdef"
    assert backend_cfg.rag_enabled is True
    assert backend_cfg.chat_daily_budget == 100
    assert backend_cfg.chat_ip_rpm == 6

    assert collector_cfg.data_dir == collector_dir
    assert collector_cfg.api_url == "http://127.0.0.1:8765"
    assert collector_cfg.collector_token.get_secret_value() == "collector-secret-token-0123456789abcdef"
    assert collector_cfg.openrouter_model == FREE_MODEL

    # Direct BackendSettings(...) construction in tests must stay isolated from cwd .env
    monkeypatch.chdir(tmp_path)
    isolated = BackendSettings(database_url="sqlite:///./isolated.db")
    assert isolated.admin_token.get_secret_value() == "admin-test"
    assert isolated.collector_token.get_secret_value() == "worker-test"


def test_collector_cli_defaults_to_root_env(tmp_path, monkeypatch):
    import collector.__main__ as collector_main

    collector_dir = tmp_path / "collector-data"
    unified_env = tmp_path / ".env"
    unified_env.write_text(
        "\n".join(
            [
                "APP_ENV=development",
                "PUBLIC_API_URL=http://127.0.0.1:8765",
                "ADMIN_TOKEN=admin-secret-token-0123456789abcdef",
                f"COLLECTOR_DATA_DIR={collector_dir.as_posix()}",
                "COLLECTOR_API_URL=http://127.0.0.1:8765",
                "COLLECTOR_TOKEN=collector-secret-token-0123456789abcdef",
                "OPENROUTER_API_KEY=sk-or-v1-offline-fixture-key",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(collector_main, "DEFAULT_ENV_FILE", unified_env)
    assert collector_main.main(["doctor"]) == 0
    assert collector_main.main(["--env", str(unified_env), "doctor"]) == 0
