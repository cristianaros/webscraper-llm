from datetime import UTC, datetime
import hashlib, json, httpx, pytest
from pydantic import SecretStr
from collector.config import CollectorSettings
from collector.openrouter import LLMDeferred, MiniMaxExtractor
from shared.contracts import Document, FREE_MODEL, TextBlock
from shared.validation import document_digest

def test_quota_keeps_exact_free_model(tmp_path):
    blocks=[TextBlock(id=0,kind='title',text='Titulo correcto'),TextBlock(id=1,kind='date',text='5 septiembre 2026'),TextBlock(id=2,kind='body',text='Texto de evidencia suficiente.')]
    document=Document(source_id=1,source_revision=1,canonical_url='https://uni.example/a',fetched_at=datetime.now(UTC),document_hash=document_digest(blocks,[2]),html_sha256=hashlib.sha256(b'a').hexdigest(),blocks=blocks,expected_body_ids=[2],trusted_container=True)
    settings=CollectorSettings(data_dir=tmp_path,api_url='https://api.example',collector_token=SecretStr('x'),openrouter_api_key=SecretStr('x'))
    calls=[]
    def reply(request): calls.append(json.loads(request.content)); return httpx.Response(429,headers={'Retry-After':'120'},json={'error':{'message':'limit'}})
    extractor=MiniMaxExtractor(settings,httpx.Client(transport=httpx.MockTransport(reply)))
    with pytest.raises(LLMDeferred) as exc: extractor.extract(document)
    assert exc.value.retry_after_seconds==120 and calls[0]['model']==FREE_MODEL
    assert calls[0]['provider']['max_price']=={'prompt':0,'completion':0}
    assert calls[0]['reasoning']=={'enabled':False}

def test_unavailable_model_keeps_document_for_retry(tmp_path):
    blocks=[TextBlock(id=0,kind='title',text='Titulo correcto'),TextBlock(id=1,kind='date',text='5 septiembre 2026'),TextBlock(id=2,kind='body',text='Texto de evidencia suficiente.')]
    document=Document(source_id=1,source_revision=1,canonical_url='https://uni.example/a',fetched_at=datetime.now(UTC),document_hash=document_digest(blocks,[2]),html_sha256=hashlib.sha256(b'a').hexdigest(),blocks=blocks,expected_body_ids=[2],trusted_container=True)
    settings=CollectorSettings(data_dir=tmp_path,api_url='https://api.example',collector_token=SecretStr('x'),openrouter_api_key=SecretStr('x'))
    client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(404,json={'error':{'message':'model unavailable'}})))
    with pytest.raises(LLMDeferred) as exc: MiniMaxExtractor(settings,client).extract(document)
    assert exc.value.code=='credentials_or_model_unavailable'
