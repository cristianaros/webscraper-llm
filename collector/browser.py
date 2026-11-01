"""Optional Playwright fetcher with the same allowlist boundary as HTTPX."""
from __future__ import annotations

from datetime import UTC, datetime
import ipaddress
import socket

from collector.http import FetchError, FetchResult, HttpFetcher
from shared.contracts import SourceConfig


class BrowserFetcher:
    def __init__(self, http: HttpFetcher) -> None:
        self.http = http

    def _resolver_rules(self, source: SourceConfig) -> str:
        rules = []
        hosts = list(dict.fromkeys(host.lower().rstrip(".") for host in source.allowed_hosts + source.allowed_image_hosts))
        for host in hosts:
            try:
                entries = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
                addresses = [entry[4][0] for entry in entries]
                if not addresses or not all(ipaddress.ip_address(address).is_global for address in addresses):
                    raise FetchError("private_destination")
            except socket.gaierror as exc:
                raise FetchError("dns_failed") from exc
            except ValueError as exc:
                if isinstance(exc, FetchError):
                    raise
                raise FetchError("private_destination") from exc
            rules.append(f"MAP {host} {addresses[0]}")
        if not rules:
            raise FetchError("destination_host_not_allowed")
        return ", ".join(rules)

    def _install_routes(self, context, source: SourceConfig) -> None:
        def route_request(route):
            request = route.request
            if request.resource_type in {"image", "font", "media", "websocket", "download"}:
                return route.abort()
            try:
                self.http._validate(request.url, source)
            except FetchError:
                return route.abort()
            return route.continue_()
        context.route("**/*", route_request)

    def fetch(self, url: str, source: SourceConfig, **_: object) -> FetchResult:
        if source.render_mode != "browser" or not source.wait_selector:
            raise FetchError("browser_selector_required")
        try:
            from playwright.sync_api import Error as PlaywrightError, sync_playwright
        except ImportError as exc:
            raise FetchError("browser_not_installed") from exc
        self.http._validate(url, source)
        try:
            with sync_playwright() as playwright:
                launch_options = {"headless": True}
                if not self.http.allow_test_hosts:
                    launch_options["args"] = [f"--host-resolver-rules={self._resolver_rules(source)}"]
                browser = playwright.chromium.launch(**launch_options)
                try:
                    context = browser.new_context(service_workers="block")
                    self._install_routes(context, source)
                    page = context.new_page()
                    response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                    if response is not None and not self.http.allow_test_hosts and hasattr(response, "server_addr"):
                        addr = response.server_addr()
                        if addr and addr.get("ipAddress"):
                            try:
                                is_global = ipaddress.ip_address(addr["ipAddress"]).is_global
                            except ValueError:
                                is_global = False
                            if not is_global:
                                raise FetchError("private_destination")
                    page.locator(source.wait_selector).wait_for(state="attached", timeout=15_000)
                    final_url = self.http._validate(page.url, source)
                    return FetchResult(final_url, page.content(), response.status if response else 200, None, None, datetime.now(UTC))
                finally:
                    browser.close()
        except PlaywrightError as exc:
            message = str(exc).lower()
            raise FetchError("browser_not_installed" if "executable doesn't exist" in message else "browser_failed") from exc
