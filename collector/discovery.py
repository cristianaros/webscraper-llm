"""Discovery from configured feeds and listing selectors; never discovers sources."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
import re

from bs4 import BeautifulSoup
import feedparser

from collector.http import HttpFetcher
from shared.contracts import SourceConfig
from shared.urls import normalize_url

@dataclass(frozen=True)
class DiscoveryBatch:
    urls: list[str]
    next_cursor: str | None
    visited_pages: list[str]
    status: Literal["success", "partial", "no_links"]

def _accepted(url: str, source: SourceConfig) -> bool:
    if source.article_url_pattern and not re.search(source.article_url_pattern, url): return False
    return True

def discover(source: SourceConfig, fetcher: HttpFetcher, cursor: str | None, known_urls: set[str]) -> DiscoveryBatch:
    urls: list[str] = []
    visited: list[str] = []
    page = cursor or source.feed_url or source.start_url
    while page and len(visited) < source.max_pages and len(urls) < source.max_articles:
        page = normalize_url(page)
        if page in visited: break
        result = fetcher.fetch(page, source)
        visited.append(page)
        if result.status >= 400: break
        if "xml" in (result.content_type or "") or page == source.feed_url:
            parsed = feedparser.parse(result.content)
            candidates = [entry.get("link") for entry in parsed.entries]
            next_page = None
        else:
            soup = BeautifulSoup(result.html or "", "html.parser")
            candidates = [a.get("href") for a in soup.select(source.link_selector)]
            nxt = soup.select_one(source.next_selector)
            next_page = normalize_url(nxt.get("href"), page) if nxt and nxt.get("href") else None
        for candidate in candidates:
            if not candidate: continue
            try: value = normalize_url(candidate, page)
            except ValueError: continue
            if value not in known_urls and value not in urls and _accepted(value, source): urls.append(value)
            if len(urls) >= source.max_articles: break
        page = next_page
    status: Literal["success", "partial", "no_links"] = "partial" if page else ("success" if urls else "no_links")
    return DiscoveryBatch(urls, page, visited, status)
