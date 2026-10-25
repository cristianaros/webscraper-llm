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
