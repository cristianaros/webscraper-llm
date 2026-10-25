from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from pydantic import SecretStr

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
