from datetime import date, datetime, timezone
from uuid import uuid4
from backend.scripts.bootstrap_db import bootstrap_database
from backend.main import create_app
from backend.config import BackendSettings
from models import Source
from shared.contracts import Delivery,Document,TextBlock,Selection,ArticleFields
from fastapi.testclient import TestClient
from pathlib import Path
from alembic import command
from alembic.config import Config
from shared.contracts import FREE_MODEL
from shared.validation import materialize
def test_repeated_delivery_has_one_revision_and_one_news(tmp_path):
    url='sqlite:///'+(tmp_path/'api.db').as_posix();bootstrap_database(url);app=create_app(BackendSettings(database_url=url));c=TestClient(app);a={'Authorization':'Bearer admin-test'};w={'Authorization':'Bearer worker-test'}
    c.post('/api/admin/universities',json={'name':'U'},headers=a);c.post('/api/admin/sources',json={'university_id':1,'start_url':'https://u.test/a','allowed_hosts':['u.test']},headers=a)
    db=app.state.session_factory();s=db.get(Source,1);s.enabled=s.auto_publish=True;s.validated_revision=1;db.commit();db.close();now=datetime.now(timezone.utc)
    d=Delivery(delivery_id=uuid4(),run_id=uuid4(),document=Document(source_id=1,source_revision=1,canonical_url='https://u.test/a',fetched_at=now,document_hash='a'*64,html_sha256='b'*64,blocks=[TextBlock(id=0,kind='title',text='T'),TextBlock(id=1,kind='date',text='D'),TextBlock(id=2,kind='body',text='Body')],expected_body_ids=[2]),selection=Selection(title_id=0,date_id=1,body_ids=[2],category='General'),fields=ArticleFields(title='T',content='Body',category='General',published_at=now,published_on=date.today(),date_precision='day'),issues=[],model='minimax/minimax-m3:free')
    first=c.post('/api/collector/articles',json=d.model_dump(mode='json'),headers=w);assert first.status_code==200
    for _ in range(100):assert c.post('/api/collector/articles',json=d.model_dump(mode='json'),headers=w).json()==first.json()
    assert len(c.get('/api/news/').json())==1


def test_manual_publication_from_alembic_schema_is_visible(tmp_path, document, selection):
    url='sqlite:///'+(tmp_path/'api-migrated.db').as_posix()
    config=Config(str(Path('backend/alembic.ini').resolve()))
    config.set_main_option('sqlalchemy.url',url)
    command.upgrade(config,'head')
    app=create_app(BackendSettings(database_url=url))
    client=TestClient(app)
    admin={'Authorization':'Bearer admin-test'}
    collector={'Authorization':'Bearer worker-test'}
    assert client.post('/api/admin/universities',json={'name':'Universidad de Prueba'},headers=admin).status_code==201
    assert client.post('/api/admin/sources',json={'university_id':1,'start_url':'https://uni.example/noticias/','allowed_hosts':['uni.example']},headers=admin).status_code==200
    fields=materialize(document,selection,'America/Santiago')
    delivery=Delivery(delivery_id=uuid4(),run_id=uuid4(),document=document,selection=selection,fields=fields,issues=[],model=FREE_MODEL,prompt_version='extract-v2')
    receipt=client.post('/api/collector/articles',json=delivery.model_dump(mode='json'),headers=collector)
    assert receipt.status_code==200 and receipt.json()['outcome']=='pending'
    revision_id=receipt.json()['revision_id']
    published=client.post(f'/api/admin/revisions/{revision_id}/publish',json={'fields':fields.model_dump(mode='json'),'editorial_lock':True},headers=admin)
    assert published.status_code==200
    response=client.get('/api/news/')
    assert response.status_code==200
    assert len(response.json())==1
    assert response.json()[0]['created_at'] is not None
