from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import event

from backend.config import BackendSettings
from backend.main import create_app
from backend.scripts.bootstrap_db import bootstrap_database
from models import News


class StubLLM:
    model = "nvidia/nemotron-3.5-super-vl:free"

    def __init__(self):
        self.calls = []

    def answer_from_news(self, question, context):
        self.calls.append((question, context))
        return "Respuesta basada en la noticia publicada."


def test_chat_status_route_reports_disabled_instead_of_404(tmp_path):
    url = "sqlite:///" + (tmp_path / "api.db").as_posix()
    bootstrap_database(url)
    client = TestClient(create_app(BackendSettings(database_url=url, rag_enabled=False)))
    response = client.get("/api/chat/status")
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert client.post("/api/chat/", json={"question": "Hola"}).status_code == 503


def test_chat_uses_only_published_news_and_scoped_article(tmp_path):
    url = "sqlite:///" + (tmp_path / "api.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=True, openrouter_api_key=SecretStr("test-key")))
    llm = StubLLM()
    app.state.assistant.llm = llm
    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        db.add_all([
            News(id=1, title="Investigación sobre agua", content="La universidad investiga la conservación del agua.", category="Investigación", university="Universidad A", source_url="https://uni.example/agua", published_at=now, published_on=date.today(), publication_status="published", created_at=now),
            News(id=2, title="Beca privada", content="Información reservada sobre becas.", category="Becas", university="Universidad B", publication_status="draft", created_at=now),
            News(id=3, title="Noticia archivada", content="La noticia archivada trata sobre agua.", category="Investigación", university="Universidad C", publication_status="archived", created_at=now),
        ])
        db.commit()
    client = TestClient(app)
    status = client.get("/api/chat/status")
    assert status.status_code == 200
    assert status.json()["indexed_documents"] == 1
    response = client.post("/api/chat/", json={"question": "¿Qué investigación hay sobre agua?"})
    assert response.status_code == 200
    assert [source["news_id"] for source in response.json()["sources"]] == [1]
    assert "conservación del agua" in llm.calls[0][1]
    assert "Beca privada" not in llm.calls[0][1]
    assert "Noticia archivada" not in llm.calls[0][1]
    scoped = client.post("/api/chat/", json={"question": "Resúmela", "news_id": 1})
    assert scoped.status_code == 200 and scoped.json()["sources"][0]["news_id"] == 1
    hidden = client.post("/api/chat/", json={"question": "Resúmela", "news_id": 2})
    assert hidden.status_code == 200 and hidden.json()["sources"] == []
    assert len(llm.calls) == 2


def test_chat_without_matching_news_does_not_call_provider(tmp_path):
    url = "sqlite:///" + (tmp_path / "api.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=True, openrouter_api_key=SecretStr("test-key")))
    llm = StubLLM()
    app.state.assistant.llm = llm
    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        db.add(News(title="Investigación sobre agua", content="Conservación del agua.", category="Investigación", university="Universidad A", publication_status="published", created_at=now))
        db.commit()
    response = TestClient(app).post("/api/chat/", json={"question": "¿Qué becas estudiantiles hay?"})
    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert llm.calls == []


def test_chat_cache_invalidates_when_selected_news_archived(tmp_path):
    url = "sqlite:///" + (tmp_path / "cache.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=True, openrouter_api_key=SecretStr("test-key")))
    llm = StubLLM()
    app.state.assistant.llm = llm
    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        db.add(News(id=1, title="Investigación sobre agua", content="Conservación del agua.", category="Investigación", university="Universidad A", source_url="https://uni.example/a", publication_status="published", created_at=now, published_at=now))
        db.commit()
    client = TestClient(app)
    payload = {"question": "Resume agua", "news_id": 1}
    first = client.post("/api/chat/", json=payload)
    second = client.post("/api/chat/", json=payload)
    assert first.status_code == second.status_code == 200
    assert len(llm.calls) == 1
    archived = client.patch(
        "/api/admin/news/1/publication",
        json={"status": "archived"},
        headers={"Authorization": "Bearer admin-test"},
    )
    assert archived.status_code == 200
    assert archived.json()["updated_at"] is not None
    hidden = client.post("/api/chat/", json=payload)
    assert hidden.json() == {"answer": "La noticia seleccionada no está publicada o no existe.", "sources": []}
    assert len(llm.calls) == 1


def test_global_chat_falls_back_to_recent_catalog_when_terms_do_not_match(tmp_path):
    url = "sqlite:///" + (tmp_path / "panorama.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=True, openrouter_api_key=SecretStr("test-key")))
    llm = StubLLM()
    app.state.assistant.llm = llm
    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        db.add_all([
            News(id=i, title=f"Noticia general {i}", content=f"Contenido publicado {i}", category="General", university="Universidad A", publication_status="published", created_at=now, published_at=now)
            for i in range(1, 4)
        ])
        db.commit()
    response = TestClient(app).post("/api/chat/", json={"question": "Dame un panorama general del portal"})
    assert response.status_code == 200
    assert [source["news_id"] for source in response.json()["sources"]] == [3, 2, 1]
    assert "[CATÁLOGO RECIENTE DEL PORTAL]" in llm.calls[0][1]


def test_chat_handles_conversational_greetings_and_general_blog_summary(tmp_path):
    url = "sqlite:///" + (tmp_path / "conversational.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=True, openrouter_api_key=SecretStr("test-key")))
    llm = StubLLM()
    app.state.assistant.llm = llm
    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        db.add_all([
            News(id=i, title=f"Innovación Tecnológica {i}", content=f"Detalle sobre ciencia {i}", category="Ciencia", university="Universidad A", publication_status="published", created_at=now, published_at=now)
            for i in range(1, 4)
        ])
        db.commit()
    client = TestClient(app)

    res_summary = client.post("/api/chat/", json={"question": "Hazme un resumen de lo que dicen las noticias publicadas en este blog"})
    assert res_summary.status_code == 200
    assert len(res_summary.json()["sources"]) == 3
    assert len(llm.calls) == 1

    res_greeting = client.post("/api/chat/", json={"question": "Hola"})
    assert res_greeting.status_code == 200
    assert len(res_greeting.json()["sources"]) == 3
    assert len(llm.calls) == 2


def test_editorial_edit_updates_marker_and_invalidates_chat_cache(tmp_path):
    url = "sqlite:///" + (tmp_path / "edit-cache.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=True, openrouter_api_key=SecretStr("test-key")))
    llm = StubLLM()
    app.state.assistant.llm = llm
    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        db.add(News(id=1, title="Investigación de agua", content="Texto original sobre conservación.", category="Investigación", university="Universidad A", publication_status="published", created_at=now, updated_at=now, published_at=now))
        db.commit()
    client = TestClient(app)
    payload = {"question": "investigación agua"}
    assert client.post("/api/chat/", json=payload).status_code == 200
    assert client.post("/api/chat/", json=payload).status_code == 200
    assert len(llm.calls) == 1
    headers = {"Authorization": "Bearer admin-test"}
    updated = client.put("/api/news/1", json={"title": "Investigación de agua editada", "content": "Texto editorial actualizado."}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["updated_at"] is not None
    assert client.post("/api/chat/", json=payload).status_code == 200
    assert len(llm.calls) == 2


def test_snapshot_marker_uses_only_one_aggregate_query_without_news_content(tmp_path):
    from backend.rag.chat_guard import ChatGuard

    url = "sqlite:///" + (tmp_path / "aggregate-marker.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=False))
    statements = []
    engine = app.state.engine
    event.listen(engine, "before_cursor_execute", lambda conn, cursor, statement, params, context, executemany: statements.append(statement))
    with app.state.session_factory() as db:
        ChatGuard().snapshot_marker(db)
    selects = [statement.lower() for statement in statements if "select" in statement.lower()]
    assert len(selects) == 1
    assert "count(" in selects[0] and "max(" in selects[0]
    assert "content" not in selects[0]


def test_news_assistant_bounds_candidate_pool_to_recent_200(tmp_path):
    from backend.rag.news_assistant import NewsAssistant

    url = "sqlite:///" + (tmp_path / "bounded-pool.db").as_posix()
    bootstrap_database(url)
    app = create_app(BackendSettings(database_url=url, rag_enabled=False))
    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        db.add_all([
            News(id=i, title=f"Noticia {i}", content="Texto publicado", category="General", university="Universidad A", publication_status="published", created_at=now, published_at=now)
            for i in range(1, 206)
        ])
        db.commit()
    statements = []
    event.listen(app.state.engine, "before_cursor_execute", lambda conn, cursor, statement, params, context, executemany: statements.append((statement.lower(), params)))
    with app.state.session_factory() as db:
        NewsAssistant(StubLLM()).prepare_context(db, "panorama general")
    candidates = [(sql, params) for sql, params in statements if "from news" in sql and "order by" in sql and "limit" in sql]
    assert any(200 in params for _, params in candidates)
    assert all(200 in params or 15 in params for _, params in candidates)
