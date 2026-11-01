from datetime import UTC, datetime

import httpx
import httpcore
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


def test_public_backend_pins_public_ip(monkeypatch):
    from collector.http import PublicOnlyNetworkBackend

    lookups = []
    def resolve(host, port, **kwargs):
        lookups.append((host, port))
        return [(2, 1, 6, "", ("93.184.216.34", port))]
    monkeypatch.setattr("collector.http.socket.getaddrinfo", resolve)
    connected = {}
    monkeypatch.setattr("httpcore.SyncBackend.connect_tcp", lambda self, host, port, **kw: connected.update(host=host, port=port) or "stream")
    assert PublicOnlyNetworkBackend().connect_tcp("uni.example", 443, timeout=10) == "stream"
    assert connected == {"host": "93.184.216.34", "port": 443}
    assert lookups == [("uni.example", 443)]


def test_public_backend_rejects_rebound_private_addresses(monkeypatch):
    from collector.http import PublicDestinationError, PublicOnlyNetworkBackend
    monkeypatch.setattr("collector.http.socket.getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("93.184.216.34", 443)), (2, 1, 6, "", ("169.254.169.254", 443))])
    called = []
    monkeypatch.setattr("httpcore.SyncBackend.connect_tcp", lambda *a, **kw: called.append(True))
    with pytest.raises(PublicDestinationError, match="private_destination"):
        PublicOnlyNetworkBackend().connect_tcp("uni.example", 443)
    assert called == []


def test_public_backend_reports_dns_failure(monkeypatch):
    from collector.http import PublicDestinationError, PublicOnlyNetworkBackend
    monkeypatch.setattr("collector.http.socket.getaddrinfo", lambda *a, **kw: (_ for _ in ()).throw(__import__("socket").gaierror()))
    with pytest.raises(PublicDestinationError, match="dns_failed"):
        PublicOnlyNetworkBackend().connect_tcp("uni.example", 443)


def test_default_fetcher_installs_pinning_backend():
    from collector.http import PublicOnlyNetworkBackend
    fetcher = HttpFetcher()
    try:
        assert isinstance(fetcher.client._transport._pool._network_backend, PublicOnlyNetworkBackend)
    finally:
        fetcher.client.close()


def test_fetch_surfaces_wrapped_public_destination_error(source, monkeypatch):
    from collector.http import PublicDestinationError
    monkeypatch.setattr('collector.http.socket.getaddrinfo', _dns)
    class Client:
        def get(self, *args, **kwargs):
            try:
                raise PublicDestinationError('private_destination')
            except PublicDestinationError as err:
                raise httpx.ConnectError('connection failed') from err
    fetcher = HttpFetcher(Client())
    with pytest.raises(FetchError, match='private_destination'):
        fetcher.fetch('https://uni.example/a', source)
