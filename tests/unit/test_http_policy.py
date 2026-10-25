from datetime import UTC, datetime

import httpx
import pytest

from collector.http import FetchError, HttpFetcher
from shared.contracts import SourceConfig


@pytest.fixture
def source():
    return SourceConfig(id=1, university_id=1, university_name='Universidad', revision=1,
        validated_revision=1, start_url='https://uni.example/news/', allowed_hosts=['uni.example'])


def _dns(*_args, **_kwargs):
    return [(2, 1, 6, '', ('8.8.8.8', 0))]


def test_robots_denial_blocks_before_article_request(source, monkeypatch):
    monkeypatch.setattr('collector.http.socket.getaddrinfo', _dns)
    seen = []
    def reply(request):
        seen.append(str(request.url))
        if request.url.path == '/robots.txt':
            return httpx.Response(200, text='User-agent: UniNewsResearchBot/1.0\nDisallow: /private')
        return httpx.Response(200, text='<article/>', headers={'content-type': 'text/html'})
    fetcher = HttpFetcher(httpx.Client(transport=httpx.MockTransport(reply)))
    with pytest.raises(FetchError, match='robots_denied'):
        fetcher.fetch('https://uni.example/private', source)
    assert seen == ['https://uni.example/robots.txt']


def test_missing_robots_permits_article_and_is_cached(source, monkeypatch):
    monkeypatch.setattr('collector.http.socket.getaddrinfo', _dns)
    calls = []
    def reply(request):
        calls.append(request.url.path)
        return httpx.Response(404 if request.url.path == '/robots.txt' else 200, text='<article/>', headers={'content-type': 'text/html'})
    fetcher = HttpFetcher(httpx.Client(transport=httpx.MockTransport(reply)))
    result = fetcher.fetch('https://uni.example/a', source)
    assert result.status == 200 and calls == ['/robots.txt', '/a']
