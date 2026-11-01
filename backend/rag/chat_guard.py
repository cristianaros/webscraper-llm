"""In-memory cache and per-process chat request limits."""

from __future__ import annotations

import re
import unicodedata
import ipaddress
from collections import OrderedDict, defaultdict, deque
from datetime import datetime

from sqlalchemy import func
from starlette.requests import Request

from models import News


def extract_client_ip(request: Request, *, trust_proxy_headers: bool) -> str:
    if trust_proxy_headers:
        fallback_valid: str | None = None
        for header_name in ("x-envoy-external-address", "x-real-ip"):
            candidate = request.headers.get(header_name, "").strip()
            if not candidate:
                continue
            try:
                parsed = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            if parsed.is_global:
                return str(parsed)
            if fallback_valid is None:
                fallback_valid = str(parsed)
        if fallback_valid is not None:
            return fallback_valid
    return request.client.host if request.client else "unknown"


class ChatRateLimitError(RuntimeError):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ChatGuard:
    def __init__(self, ip_rpm: int = 6, daily_budget: int = 100, max_entries: int = 256, ttl_seconds: int = 3600):
        self.ip_rpm, self.daily_budget = ip_rpm, daily_budget
        self.max_entries, self.ttl_seconds = max_entries, ttl_seconds
        self._cache: OrderedDict[tuple, tuple[float, dict]] = OrderedDict()
        self._ip_calls = defaultdict(deque)
        self._daily_calls: dict[str, int] = {}

    def snapshot_marker(self, db) -> tuple[int, int, str]:
        count, max_id, latest_updated, latest_created = db.query(
            func.count(News.id),
            func.max(News.id),
            func.max(News.updated_at),
            func.max(News.created_at),
        ).filter(News.publication_status == "published").one()
        updated = latest_updated.isoformat() if latest_updated else ""
        created = latest_created.isoformat() if latest_created else ""
        return int(count or 0), int(max_id or 0), f"{updated}|{created}"

    @staticmethod
    def _question(question: str) -> str:
        value = unicodedata.normalize("NFKD", question or "")
        value = "".join(c for c in value if not unicodedata.combining(c)).casefold()
        return re.sub(r"\s+", " ", value).strip()

    def get_cached(self, news_id, question, marker, now):
        key = (news_id, self._question(question), marker)
        item = self._cache.get(key)
        if item is None:
            return None
        inserted, value = item
        if now - inserted >= self.ttl_seconds:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return dict(value)

    def put_cached(self, news_id, question, marker, value, now):
        key = (news_id, self._question(question), marker)
        self._cache[key] = (now, dict(value))
        self._cache.move_to_end(key)
        while len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)

    def reserve_live_call(self, client_ip: str, now_utc: datetime) -> None:
        calls = self._ip_calls[client_ip]
        stamp = now_utc.timestamp()
        while calls and stamp - calls[0] >= 60:
            calls.popleft()
        if len(calls) >= self.ip_rpm:
            raise ChatRateLimitError("Has alcanzado el límite de consultas por minuto. Intenta nuevamente en unos segundos.")
        day = now_utc.strftime("%Y-%m-%d")
        if self._daily_calls.get(day, 0) >= self.daily_budget:
            raise ChatRateLimitError("La cuota diaria gratuita del asistente IA se agotó por hoy. Vuelve a intentarlo mañana.")
        calls.append(stamp)
        self._daily_calls[day] = self._daily_calls.get(day, 0) + 1
        for old_day in list(self._daily_calls):
            if old_day != day:
                del self._daily_calls[old_day]
