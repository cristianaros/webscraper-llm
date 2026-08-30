import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

UPLA_NEWS_URL = "https://upla.cl/noticias/"
_ARTICLE_PATH = re.compile(r"^/noticias/\d{4}/\d{2}/\d{2}/[^/]+/?$")

_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


class ScrapeGraphError(RuntimeError):
    """Error controlado de la API de ScrapeGraphAI."""


@dataclass
class UplaArticleLink:
    title: str
    url: str
    published_at: Optional[datetime] = None
    category: str = "General"
    image_url: Optional[str] = None


@dataclass
class UplaArticle:
    title: str
    content: str
    published_at: Optional[datetime]
    category: str
    author: Optional[str]
    image_url: Optional[str]
    source_url: str


class UplaScraper:
    """Extrae el listado y el cuerpo de noticias UPLA con ScrapeGraphAI v2."""

    def __init__(self) -> None:
        # API_SCRAPEGRAPHAI mantiene compatibilidad con la variable ya usada
        # por el proyecto; SGAI_API_KEY es el nombre oficial del proveedor.
        self.api_key = (
            os.getenv("SGAI_API_KEY") or os.getenv("API_SCRAPEGRAPHAI") or ""
        ).strip()
        self.base_url = os.getenv(
            "SGAI_API_URL", "https://v2-api.scrapegraphai.com/api"
        ).rstrip("/")
        self.timeout = float(os.getenv("SGAI_TIMEOUT", "120"))

        if not self.api_key:
            raise ValueError(
                "Configura API_SCRAPEGRAPHAI o SGAI_API_KEY en backend/.env"
            )

    def latest_links(self, limit: int) -> list[UplaArticleLink]:
        schema = {
            "type": "object",
            "properties": {
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                            "published_at": {
                                "type": ["string", "null"],
                                "description": "Fecha de publicacion visible",
                            },
                            "category": {"type": ["string", "null"]},
                            "image_url": {"type": ["string", "null"]},
                        },
                        "required": ["title", "url"],
                    },
                }
            },
            "required": ["articles"],
        }
        payload = self._extract(
            url=UPLA_NEWS_URL,
            prompt=(
                f"Extrae las {limit} noticias mas recientes del listado principal. "
                "Para cada noticia entrega titulo, URL canonica absoluta, fecha visible, "
                "categoria e imagen principal si aparece. Incluye solo articulos de noticias "
                "individuales con rutas que contienen ano, mes y dia. Excluye menu, agenda, "
                "entrevistas laterales, avisos, enlaces de categorias y paginacion."
            ),
            schema=schema,
            mode="normal",
        )

        links: list[UplaArticleLink] = []
        seen: set[str] = set()
        for raw in payload.get("articles", []):
            if not isinstance(raw, dict):
                continue
            url = _canonical_article_url(str(raw.get("url") or ""))
            title = _clean_text(raw.get("title"))
            if not url or not title or url in seen:
                continue
            seen.add(url)
            links.append(
                UplaArticleLink(
                    title=title,
                    url=url,
                    published_at=_parse_date(raw.get("published_at"), url),
                    category=_normalize_category(raw.get("category")),
                    image_url=_absolute_url(raw.get("image_url")),
                )
            )
            if len(links) >= limit:
                break
        return links

    def article(self, item: UplaArticleLink) -> UplaArticle:
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {
                    "type": "string",
                    "description": (
                        "Texto completo del cuerpo del articulo en parrafos, sin menu, "
                        "pie de pagina, noticias relacionadas ni etiquetas HTML"
                    ),
                },
                "published_at": {"type": ["string", "null"]},
                "category": {"type": ["string", "null"]},
                "author": {"type": ["string", "null"]},
                "image_url": {"type": ["string", "null"]},
            },
            "required": ["title", "content"],
        }
        payload = self._extract(
            url=item.url,
            prompt=(
                "Extrae exclusivamente la noticia principal de esta pagina: titulo, cuerpo "
                "completo en texto plano conservando saltos entre parrafos, fecha de publicacion, "
                "categoria, autor si esta explicitamente indicado y URL absoluta de la imagen "
                "principal. No incluyas navegacion, banners, noticias relacionadas ni comentarios."
            ),
            schema=schema,
            mode="reader",
        )

        content = _clean_content(payload.get("content"))
        if len(content) < 120:
            raise ScrapeGraphError("ScrapeGraphAI devolvio un cuerpo de noticia incompleto")

        return UplaArticle(
            title=_clean_text(payload.get("title")) or item.title,
            content=content,
            published_at=(
                _parse_date(payload.get("published_at"), item.url) or item.published_at
            ),
            category=_normalize_category(payload.get("category") or item.category),
            author=_optional_text(payload.get("author")),
            image_url=_absolute_url(payload.get("image_url")) or item.image_url,
            source_url=item.url,
        )

    def _extract(
        self,
        *,
        url: str,
        prompt: str,
        schema: dict[str, Any],
        mode: str,
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "SGAI-APIKEY": self.api_key,
        }
        body = {
            "url": url,
            "prompt": prompt,
            "schema": schema,
            "mode": mode,
            "fetchConfig": {
                "mode": "auto",
                "timeout": 30000,
            },
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/extract", headers=headers, json=body
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _api_error(exc.response)
            logger.error(
                "ScrapeGraphAI respondio %s para %s: %s",
                exc.response.status_code,
                url,
                detail,
            )
            raise ScrapeGraphError(f"ScrapeGraphAI rechazo la solicitud: {detail}") from exc
        except httpx.HTTPError as exc:
            logger.error("No se pudo conectar con ScrapeGraphAI para %s: %s", url, exc)
            raise ScrapeGraphError("No se pudo conectar con ScrapeGraphAI") from exc

        data = response.json().get("json")
        if not isinstance(data, dict):
            raise ScrapeGraphError("ScrapeGraphAI no devolvio datos estructurados")
        return data


def _canonical_article_url(value: str) -> Optional[str]:
    absolute = urljoin(UPLA_NEWS_URL, value.strip())
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.hostname not in {"upla.cl", "www.upla.cl"}:
        return None
    if not _ARTICLE_PATH.match(parsed.path):
        return None
    path = parsed.path if parsed.path.endswith("/") else f"{parsed.path}/"
    return urlunparse(("https", "upla.cl", path, "", "", ""))


def _parse_date(value: Any, url: str) -> Optional[datetime]:
    raw = _clean_text(value).lower()
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("z", "+00:00"))
        except ValueError:
            pass

        match = re.search(
            r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", raw
        )
        if match:
            month = _MONTHS.get(match.group(2))
            if month:
                return datetime(int(match.group(3)), month, int(match.group(1)))

    match = re.search(r"/noticias/(\d{4})/(\d{2})/(\d{2})/", url)
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def _normalize_category(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return "General"
    aliases = {
        "academia": "Academia",
        "cultura": "Cultura",
        "deportes": "Deportes",
        "entrevista": "Entrevistas",
        "entrevistas": "Entrevistas",
        "genero": "Género",
        "género": "Género",
        "investigacion": "Investigación",
        "investigación": "Investigación",
        "opinion": "Opinión",
        "opinión": "Opinión",
        "en los medios": "En los medios",
        "destacados": "Destacados",
    }
    return aliases.get(text.lower(), text[:100])


def _absolute_url(value: Any) -> Optional[str]:
    text = _clean_text(value)
    if not text:
        return None
    url = urljoin(UPLA_NEWS_URL, text)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    return url


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _optional_text(value: Any) -> Optional[str]:
    text = _clean_text(value)
    return text or None


def _clean_content(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _api_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:300] or f"HTTP {response.status_code}"
    error = payload.get("error", payload)
    if isinstance(error, dict):
        return str(error.get("message") or error.get("type") or error)[:300]
    return str(error)[:300]
