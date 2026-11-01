import pytest
from collector.browser import BrowserFetcher
from collector.http import HttpFetcher
from shared.contracts import SourceConfig
import httpx


@pytest.mark.browser
def test_browser_fetcher_requires_wait_selector():
    source = SourceConfig(
        id=1, university_id=1, university_name="U", revision=1, validated_revision=1,
        start_url="https://uni.example/", allowed_hosts=["uni.example"],
        render_mode="browser", wait_selector=None,
    )
    fetcher = BrowserFetcher(HttpFetcher(httpx.Client()))
    with pytest.raises(Exception):
        fetcher.fetch("https://uni.example/", source)


@pytest.mark.browser
def test_browser_fetcher_accepts_article_wait_selector():
    source = SourceConfig(
        id=1, university_id=1, university_name="U", revision=1, validated_revision=1,
        start_url="https://uni.example/", allowed_hosts=["uni.example"],
        render_mode="browser", wait_selector="article",
    )
    fetcher = BrowserFetcher(HttpFetcher(httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(404))), allow_test_hosts=True))
    assert source.wait_selector == "article"


def test_browser_fetcher_rejects_private_remote_ip(monkeypatch):
    import sys
    import types
    from collector.http import FetchError

    source = SourceConfig(id=1, university_id=1, university_name="U", revision=1, validated_revision=1, start_url="https://uni.example/", allowed_hosts=["uni.example"], render_mode="browser", wait_selector="article")
    class Response:
        status = 200
        def server_addr(self): return {"ipAddress": "169.254.169.254", "port": 443}
    class Locator:
        def wait_for(self, **kwargs): pass
    class Page:
        url = "https://uni.example/"
        def goto(self, *args, **kwargs): return Response()
        def locator(self, *args): return Locator()
        def content(self): raise AssertionError("DOM must not be read")
    class Context:
        def route(self, *args): pass
        def new_page(self): return Page()
    class Browser:
        def new_context(self, **kwargs): return Context()
        def close(self): pass
    class Chromium:
        def launch(self, **kwargs): return Browser()
    class Playwright:
        chromium = Chromium()
        def __enter__(self): return self
        def __exit__(self, *args): pass
    fake = types.SimpleNamespace(sync_api=types.SimpleNamespace(Error=type("PlaywrightError", (Exception,), {}), sync_playwright=lambda: Playwright()))
    monkeypatch.setitem(sys.modules, "playwright", fake)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake.sync_api)
    http = HttpFetcher(httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200))), allow_test_hosts=False)
    monkeypatch.setattr(http, "_validate", lambda url, source: url)
    monkeypatch.setattr("collector.browser.socket.getaddrinfo", lambda host, port, **kw: [(2, 1, 6, "", ("93.184.216.34", port))])
    with pytest.raises(FetchError, match="private_destination"):
        BrowserFetcher(http).fetch(source.start_url, source)


@pytest.mark.browser
def test_browser_launch_pins_every_allowed_host_before_navigation(monkeypatch):
    import sys
    import types

    source = SourceConfig(
        id=1, university_id=1, university_name="U", revision=1, validated_revision=1,
        start_url="https://uni.example/", allowed_hosts=["uni.example", "cdn.uni.example"],
        render_mode="browser", wait_selector="article",
    )
    monkeypatch.setattr("collector.browser.socket.getaddrinfo", lambda host, port, **kw: [(2, 1, 6, "", (("93.184.216.34" if host == "uni.example" else "1.1.1.1"), port or 443))])
    state = {}
    class Response:
        status = 200
        def server_addr(self): return {"ipAddress": "93.184.216.34", "port": 443}
    class Locator:
        def wait_for(self, **kwargs): pass
    class Page:
        url = source.start_url
        def goto(self, *args, **kwargs):
            assert "--host-resolver-rules=MAP uni.example 93.184.216.34, MAP cdn.uni.example 1.1.1.1" in state["args"]
            return Response()
        def locator(self, *args): return Locator()
        def content(self): return "<article/>"
    class Context:
        def route(self, *args): pass
        def new_page(self): return Page()
    class Browser:
        def new_context(self, **kwargs): return Context()
        def close(self): pass
    class Chromium:
        def launch(self, **kwargs): state["args"] = kwargs.get("args", []); return Browser()
    class Playwright:
        chromium = Chromium()
        def __enter__(self): return self
        def __exit__(self, *args): pass
    fake = types.SimpleNamespace(sync_api=types.SimpleNamespace(Error=type("PlaywrightError", (Exception,), {}), sync_playwright=lambda: Playwright()))
    monkeypatch.setitem(sys.modules, "playwright", fake)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake.sync_api)
    http = HttpFetcher(httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(404))), allow_test_hosts=False)
    monkeypatch.setattr(http, "_validate", lambda url, source: url)
    result = BrowserFetcher(http).fetch(source.start_url, source)
    assert result.html == "<article/>"
