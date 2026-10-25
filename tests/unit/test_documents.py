from datetime import UTC, datetime
from collector.documents import build_document
from collector.http import FetchResult
from shared.contracts import SourceConfig

import pytest

@pytest.fixture
def source():
    return SourceConfig(id=1,university_id=1,university_name='Universidad',revision=1,validated_revision=1,start_url='https://uni.example/news/',allowed_hosts=['uni.example'],content_selector='article')

def test_document_keeps_evidence_blocks(source):
    html='<article><h1>Investigación de agua</h1><time datetime="2026-09-05">5 septiembre</time><p>Texto original suficientemente largo para formar evidencia del artículo universitario.</p></article>'
    result=FetchResult('https://uni.example/noticia',html,200,None,None,datetime.now(UTC),html.encode(),'text/html')
    document=build_document(result,source)
    assert [block.kind for block in document.blocks]==['title','date','body']
    assert document.expected_body_ids==[2]
