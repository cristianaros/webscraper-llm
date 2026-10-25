from fastapi.testclient import TestClient

from backend.config import BackendSettings
from backend.main import create_app
from backend.scripts.bootstrap_db import bootstrap_database


def test_public_news_search_matches_title_and_body_case_insensitively(tmp_path):
    url = "sqlite:///" + (tmp_path / "news.db").as_posix()
    bootstrap_database(url)
    client = TestClient(create_app(BackendSettings(database_url=url)))
    admin = {"Authorization": "Bearer admin-test"}
    assert client.post("/api/news/", json={"title": "Quantum Campus", "content": "Noticias de laboratorio", "category": "Investigación", "university": "U"}, headers=admin).status_code == 201
    assert client.post("/api/news/", json={"title": "Otra noticia", "content": "El QUANTUM se probó hoy", "category": "General", "university": "U"}, headers=admin).status_code == 201
    response = client.get("/api/news/", params={"search": "quantum"})
    assert response.status_code == 200
    assert {item["title"] for item in response.json()} == {"Quantum Campus", "Otra noticia"}
