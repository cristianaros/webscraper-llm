"""Bounded HTTP retrieval for explicitly configured university sources."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import socket
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from collector.config import CollectorSettings
from shared.contracts import SourceConfig
from shared.urls import normalize_url, validate_destination


@dataclass(frozen=True)
class FetchResult:
    url: str
    html: str | None
    status: int
    etag: str | None
    last_modified: str | None
    fetched_at: datetime
    content: bytes = b""
    content_type: str | None = None


class FetchError(RuntimeError):
    def __init__(self, code: str, retry_at: datetime | None = None) -> None:
        super().__init__(code)
        self.code, self.retry_at = code, retry_at


class HttpFetcher:
    def __init__(self, client: httpx.Client | None = None, *, allow_test_hosts: bool = False) -> None:
        self.client = client or httpx.Client(timeout=httpx.Timeout(30, connect=10), trust_env=False)
        self.allow_test_hosts = allow_test_hosts
        self._robots: dict[str, tuple[datetime, RobotFileParser, float]] = {}
        self._last_request: dict[str, float] = {}

    def _validate(self, url: str, source: SourceConfig, *, image: bool = False) -> str:
        value = normalize_url(url)
        host = httpx.URL(value).host
        if self.allow_test_hosts and (host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".example") or host.endswith(".test") or host.endswith(".local")):
            allowed = {item.lower().rstrip('.') for item in (source.allowed_hosts + source.allowed_image_hosts if image else source.allowed_hosts)}
            if host.lower().rstrip('.') not in allowed:
                raise FetchError("destination_host_not_allowed")
            return value
        try:
            addresses = [entry[4][0] for entry in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)]
        except socket.gaierror as exc:
            raise FetchError("dns_failed") from exc
        try:
            if image and host in {item.lower().rstrip('.') for item in source.allowed_image_hosts}:
                import ipaddress
                if not addresses or not all(ipaddress.ip_address(item).is_global for item in addresses):
                    raise ValueError('private_destination')
            else:
                validate_destination(value, source, addresses)
        except ValueError as exc:
            raise FetchError(str(exc)) from exc
        return value

    def _robots_for(self, url: str, source: SourceConfig, *, image: bool = False) -> tuple[RobotFileParser, float]:
        """Return a cached robots policy.  A missing robots file permits normal crawling."""
        parts = urlsplit(url)
        key = f"{parts.scheme}://{parts.netloc}"
        cached = self._robots.get(key)
        if cached and cached[0] > datetime.now(UTC):
            return cached[1], cached[2]
        robots_url = self._validate(f"{key}/robots.txt", source, image=image)
        parser = RobotFileParser(robots_url)
        try:
            response = self.client.get(robots_url, headers={"User-Agent": "UniNewsResearchBot/1.0"}, follow_redirects=False)
        except httpx.TimeoutException as exc:
            raise FetchError("robots_unavailable", datetime.now(UTC) + timedelta(minutes=5)) from exc
        except httpx.HTTPError as exc:
            raise FetchError("robots_unavailable", datetime.now(UTC) + timedelta(minutes=5)) from exc
        if response.status_code in {401, 403}:
            raise FetchError("robots_denied")
        if response.status_code >= 500:
            raise FetchError("robots_unavailable", datetime.now(UTC) + timedelta(minutes=5))
        parser.parse(response.text.splitlines() if response.status_code != 404 else [])
        delay = parser.crawl_delay("UniNewsResearchBot/1.0") or parser.crawl_delay("*") or 2
        self._robots[key] = (datetime.now(UTC) + timedelta(hours=24), parser, max(2.0, float(delay)))
        return parser, max(2.0, float(delay))

    def _respect_robots(self, url: str, source: SourceConfig, *, image: bool = False) -> None:
        parser, delay = self._robots_for(url, source, image=image)
        if not parser.can_fetch("UniNewsResearchBot/1.0", url):
            raise FetchError("robots_denied")
        if self.allow_test_hosts:
            return
        host = urlsplit(url).netloc.lower()
        elapsed = time.monotonic() - self._last_request.get(host, float("-inf"))
        if elapsed < delay:
            wait_time = delay - elapsed
            if wait_time <= 10.0:
                time.sleep(wait_time)
            else:
                raise FetchError("crawl_delay", datetime.now(UTC) + timedelta(seconds=wait_time))

    def fetch(self, url: str, source: SourceConfig, *, etag: str | None = None, modified: str | None = None, binary: bool = False) -> FetchResult:
        current = self._validate(url, source, image=binary)
        headers = {"User-Agent": "UniNewsResearchBot/1.0", "Accept": "text/html,application/xhtml+xml,application/xml,text/xml"}
        if etag: headers["If-None-Match"] = etag
        if modified: headers["If-Modified-Since"] = modified
        for _ in range(6):
            self._respect_robots(current, source, image=binary)
            try:
                response = self.client.get(current, headers=headers, follow_redirects=False)
            except httpx.TimeoutException as exc:
                raise FetchError("timeout") from exc
            except httpx.HTTPError as exc:
                raise FetchError("network_error") from exc
            if response.is_redirect:
                target = response.headers.get("location")
                if not target: raise FetchError("invalid_redirect")
                current = self._validate(normalize_url(target, current), source, image=binary)
                continue
            self._last_request[urlsplit(current).netloc.lower()] = time.monotonic()
            raw = response.content
            if len(raw) > 2 * 1024 * 1024: raise FetchError("response_too_large")
            content_type = response.headers.get("content-type", "").lower()
            if not binary and response.status_code not in {304} and response.status_code < 400 and not any(x in content_type for x in ("html", "xml", "text/")):
                raise FetchError("unsupported_content_type")
            return FetchResult(current, response.text if response.status_code != 304 else None, response.status_code,
                response.headers.get("etag"), response.headers.get("last-modified"), datetime.now(UTC), raw, content_type)
        raise FetchError("too_many_redirects")
