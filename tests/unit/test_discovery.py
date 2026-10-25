from datetime import UTC, datetime
from collector.discovery import discover
from collector.http import FetchResult
from shared.contracts import SourceConfig
import pytest

@pytest.fixture
def source():
    return SourceConfig(id=1,university_id=1,university_name='Universidad',revision=1,validated_revision=1,start_url='https://uni.example/news/',allowed_hosts=['uni.example'])

class FakeFetcher:
    def fetch(self,url,source):
        pages={
          'https://uni.example/news/':'<article><a href="/a?utm_source=x">A</a></article><a rel="next" href="/news/2">next</a>',
          'https://uni.example/news/2':'<article><a href="/b">B</a></article><a rel="next" href="/news/">cycle</a>'}
        html=pages[url]; return FetchResult(url,html,200,None,None,datetime.now(UTC),html.encode(),'text/html')

def test_discovers_unique_links_and_stops_cycle(source):
    result=discover(source,FakeFetcher(),None,set())
    assert result.urls==['https://uni.example/a','https://uni.example/b']
    assert len(result.visited_pages)==2
