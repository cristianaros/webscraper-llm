"""Integration harness for collection pipeline testing."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.config import BackendSettings
from backend.main import create_app
from backend.scripts.bootstrap_db import bootstrap_database
from collector.config import CollectorSettings
from collector.pipeline import run_once
from models import Source, SourceVersion, University


DEFAULT_ARTICLE_HTML = (
    "<article>"
    "<h1>Investigación sobre el agua</h1>"
    '<time datetime="2026-09-05">2026-09-05</time>'
    "<p>La universidad presentó una investigación sobre conservación del agua. "
    "Texto original con suficiente longitud para superar el umbral de caracteres mínimos exigidos por el contrato.</p>"
    "</article>"
)


class PipelineHarness:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.data_dir = tmp_path / "collector_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.api_db_path = tmp_path / "api.db"
        self.api_url = "http://127.0.0.1:8000"
        self.api_token = "worker-test"

        url = "sqlite:///" + self.api_db_path.as_posix()
        bootstrap_database(url)
        self.backend_settings = BackendSettings(database_url=url, collector_token=SecretStr(self.api_token))
        self.app = create_app(self.backend_settings)
        self.api_client = TestClient(self.app)

        self._seed_source()

        self.collector_settings = CollectorSettings(
            data_dir=self.data_dir,
            api_url=self.api_url,
            collector_token=SecretStr(self.api_token),
            openrouter_api_key=SecretStr("test-key"),
            collector_id="windows-collector-1",
            allow_test_hosts=True,
            run_budget_seconds=720,
        )

        self.current_time = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
        self.monotonic_time = 1000.0

        self.is_api_available = True
        self.llm_status = 200
        self.llm_retry_after: int | None = None
        self.llm_selection: dict | None = {
            "title_id": 0,
            "date_id": 1,
            "body_ids": [2],
            "category": "Investigación",
            "summary": "Resumen de prueba",
        }

        self.portal_pages: dict[str, str] = {
            "https://uni.example/robots.txt": "User-agent: *\nAllow: /\n",
            "https://uni.example/noticias/": '<article><a href="/noticias/agua">Agua</a></article>',
            "https://uni.example/noticias/agua": DEFAULT_ARTICLE_HTML,
        }

        self.transport = httpx.MockTransport(self._handle_request)

    def _seed_source(self) -> None:
        db = self.app.state.session_factory()
        u = University(id=1, name="Universidad de Prueba", normalized_name="universidad de prueba")
        db.add(u)
        db.flush()
        s = Source(
            id=1,
            university_id=1,
            start_url="https://uni.example/noticias/",
            revision=1,
            validated_revision=1,
            enabled=True,
            auto_publish=True,
            config_json={
                "allowed_hosts": ["uni.example"],
                "content_selector": "article",
                "title_selector": "h1",
                "date_selector": "time",
                "link_selector": "article a[href]",
                "min_body_chars": 50,
            },
        )
        db.add(s)
        db.flush()
        from services.sources import source_config
        cfg = source_config(db, s)
        sv = SourceVersion(
            source_id=1,
            revision=1,
            snapshot_json=cfg.model_dump(mode="json"),
            created_at=datetime.now(UTC),
        )
        db.add(sv)
        db.commit()
        db.close()

    def portal_article(self, path: str, fixture: str | None = None, html: str | None = None) -> None:
        full_url = f"https://uni.example{path}"
        content = html or DEFAULT_ARTICLE_HTML
        self.portal_pages[full_url] = content
        self.portal_pages["https://uni.example/noticias/"] = f'<article><a href="{path}">Noticia</a></article>'

    def llm_returns(self, status: int, retry_after: int | None = None) -> None:
        self.llm_status = status
        self.llm_retry_after = retry_after
        self.llm_selection = None

    def llm_returns_selection(self, title_id: int = 0, date_id: int | None = 1, body_ids: list[int] | None = None, category: str = "Investigación", summary: str | None = None) -> None:
        self.llm_status = 200
        self.llm_retry_after = None
        self.llm_selection = {
            "title_id": title_id,
            "date_id": date_id,
            "body_ids": body_ids if body_ids is not None else [2],
            "category": category,
            "summary": summary,
        }

    def advance(self, seconds: int) -> None:
        self.current_time += timedelta(seconds=seconds)
        self.monotonic_time += seconds

    def api_available(self, available: bool) -> None:
        self.is_api_available = available

    def restart_collector(self) -> None:
        self.advance(300)

    def run(self) -> None:
        run_once(
            self.collector_settings,
            clock=lambda: self.current_time,
            monotonic=lambda: self.monotonic_time,
            http_transport=self.transport,
        )

    def count_local_documents(self) -> int:
        db_file = self.data_dir / "collector.db"
        if not db_file.exists():
            return 0
        with sqlite3.connect(db_file) as db:
            row = db.execute("SELECT COUNT(*) FROM work_items WHERE document_json IS NOT NULL").fetchone()
            return row[0] if row else 0

    def count_public_news(self) -> int:
        with sqlite3.connect(self.api_db_path) as db:
            row = db.execute("SELECT COUNT(*) FROM news WHERE publication_status = 'published'").fetchone()
            return row[0] if row else 0

    def count_outbox_pending(self) -> int:
        db_file = self.data_dir / "collector.db"
        if not db_file.exists():
            return 0
        with sqlite3.connect(db_file) as db:
            row = db.execute("SELECT COUNT(*) FROM outbox WHERE receipt_json IS NULL").fetchone()
            return row[0] if row else 0

    def _handle_request(self, request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)

        # 1. OpenRouter API
        if "openrouter.ai" in url_str:
            if url_str.endswith("/models"):
                return httpx.Response(
                    200,
                    json={
                        "data": [
                            {
                                "id": "minimax/minimax-m3:free",
                                "pricing": {"prompt": "0", "completion": "0"},
                            }
                        ]
                    },
                )
            if self.llm_status != 200:
                headers = {}
                if self.llm_retry_after is not None:
                    headers["Retry-After"] = str(self.llm_retry_after)
                return httpx.Response(
                    self.llm_status,
                    headers=headers,
                    json={"error": {"message": "Rate limit exceeded"}},
                )
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(self.llm_selection),
                            }
                        }
                    ]
                },
            )

        # 2. Central API
        if url_str.startswith(self.api_url):
            if not self.is_api_available:
                raise httpx.ConnectError("API server is currently unavailable")
            # Forward to TestClient
            path = request.url.path
            if request.url.query:
                path = f"{path}?{request.url.query.decode('utf-8')}"
            headers = dict(request.headers)
            content = request.content
            resp = self.api_client.request(
                method=request.method,
                url=path,
                headers=headers,
                content=content,
            )
            return httpx.Response(
                status_code=resp.status_code,
                headers=resp.headers,
                content=resp.content,
            )

        # 3. Portal Pages
        clean_url = url_str.split("#")[0]
        if clean_url in self.portal_pages:
            body = self.portal_pages[clean_url]
            ct = "text/plain" if clean_url.endswith("robots.txt") else "text/html"
            return httpx.Response(200, text=body, headers={"content-type": ct})

        return httpx.Response(404, text="Not Found")
