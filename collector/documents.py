"""Turn fetched HTML into source-evidence blocks before any LLM call."""
from __future__ import annotations
import hashlib, json
from datetime import UTC
from bs4 import BeautifulSoup
from collector.http import FetchResult
from shared.contracts import ArticleFields, Document, SourceConfig, TextBlock
from shared.validation import document_digest

def _text(node) -> str:
    return " ".join(node.stripped_strings)

def build_document(result: FetchResult, source: SourceConfig) -> Document:
    soup = BeautifulSoup(result.html or "", "html.parser")
    root = soup.select_one(source.content_selector) if source.content_selector else (soup.select_one("article") or soup.select_one("main"))
    trusted = bool(source.content_selector and root)
    root = root or soup
    for node in root.select("script,style,noscript,nav,footer,form") : node.decompose()
    blocks: list[TextBlock] = []
    title = soup.select_one(source.title_selector) or soup.select_one("h1")
    if title and _text(title): blocks.append(TextBlock(id=len(blocks), kind="title", text=_text(title)))
    date = soup.select_one(source.date_selector) or soup.select_one("time[datetime]") or soup.select_one('meta[property="article:published_time"]')
    date_text = (date.get("datetime") or date.get("content") or _text(date)) if date else ""
    if date_text:
        blocks.append(TextBlock(id=len(blocks), kind="date", text=date_text))
    body_ids: list[int] = []
    for node in root.select("p,h2,h3,li,blockquote,figcaption"):
        text = _text(node)
        if text and text not in [b.text for b in blocks]:
            blocks.append(TextBlock(id=len(blocks), kind="body", text=text)); body_ids.append(blocks[-1].id)
    raw = result.content or (result.html or "").encode()
    return Document(source_id=source.id, source_revision=source.revision, canonical_url=result.url, fetched_at=result.fetched_at,
        document_hash=document_digest(blocks, body_ids), html_sha256=hashlib.sha256(raw).hexdigest(), blocks=blocks,
        expected_body_ids=body_ids, trusted_container=trusted)

def baseline_extract(doc: Document, source: SourceConfig) -> ArticleFields:
    title = next((b.text for b in doc.blocks if b.kind == "title"), None)
    body = "\n\n".join(b.text for b in doc.blocks if b.kind == "body") or None
    return ArticleFields(title=title, content=body)
