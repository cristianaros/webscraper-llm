from backend.scripts.bootstrap_db import bootstrap_database
from backend.main import create_app
from backend.config import BackendSettings
from fastapi.testclient import TestClient
def test_admin_and_collector_tokens_are_separate(tmp_path):
    url='sqlite:///'+(tmp_path/'api.db').as_posix();bootstrap_database(url); c=TestClient(create_app(BackendSettings(database_url=url)))
    assert c.post('/api/admin/universities',json={'name':'U'}).status_code==401
    assert c.post('/api/admin/universities',json={'name':'U'},headers={'Authorization':'Bearer worker-test'}).status_code==403
    assert c.post('/api/admin/universities',json={'name':'U'},headers={'Authorization':'Bearer admin-test'}).status_code==201
