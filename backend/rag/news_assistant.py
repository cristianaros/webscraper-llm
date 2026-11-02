"""Hybrid retrieval over the published news archive."""

from __future__ import annotations

import heapq
import re
import unicodedata

from models import News

_STOP_WORDS = {
    "al", "con", "de", "del", "el", "en", "es", "la", "las", "lo", "los", "no", "se", "si", "su", "sus",
    "un", "una", "unos", "unas", "ya", "como", "cual", "cuales", "para", "por", "que", "sobre",
    "esta", "estas", "este", "estos", "esto", "mas", "menos", "mucho", "muchos", "muy",
    "hay", "dame", "dime", "cuenta", "cuentame", "explica", "explicame", "hazme", "haz",
    "dice", "dicen", "habla", "hablan", "trata", "tratan", "sabes", "puedes", "hacer",
    "quien", "quienes", "eres", "donde", "cuando", "cuanto", "cuanta", "cuantos", "cuantas",
    "queda", "quedan", "tal", "ayuda", "ayudame",
    "hola", "buenas", "buenos", "saludos", "gracias", "favor", "porfa", "tardes", "dias", "noches", "hello", "hi",
    "noticia", "noticias", "articulo", "articulos", "publicacion", "publicaciones",
    "publicada", "publicadas", "publicado", "publicados",
    "reciente", "recientes", "resumen", "resume", "resumir", "ultima", "ultimas",
    "blog", "sitio", "web", "pagina", "portal", "archivo", "general",
}
_PANORAMIC_TRIGGERS = ("panorama", "portal", "todas", "todos", "universidades", "archivo", "general")
_NO_MATCH = "No encontré noticias publicadas relacionadas con tu pregunta."
_HIDDEN = "La noticia seleccionada no está publicada o no existe."


def _normalized(value: str | None) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def _terms(question: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]{2,}", _normalized(question)) if term not in _STOP_WORDS}


def _score(news: News, terms: set[str]) -> int:
    fields = (_normalized(news.title), _normalized(news.category), _normalized(news.university), _normalized(news.summary), _normalized(news.content))
    return sum(5 * (term in fields[0]) + 3 * (term in fields[1]) + 2 * (term in fields[2]) + 2 * (term in fields[3]) + (term in fields[4]) for term in terms)


def _source(news: News) -> dict:
    return {"news_id": news.id, "title": news.title, "category": news.category, "university": news.university, "source_url": news.source_url}


def _catalog_line(news: News) -> str:
    date = news.published_on or (news.published_at.date() if news.published_at else None)
    return f"- [#{news.id} | {date.isoformat() if date else 'Sin fecha'} | {news.university} | {news.category}] {news.title}"


class NewsAssistant:
    def __init__(self, llm, max_results: int = 4, candidate_pool_limit: int = 200):
        self.llm = llm
        self.max_results = max_results
        self.candidate_pool_limit = candidate_pool_limit

    @property
    def model_name(self) -> str:
        return self.llm.model

    def get_index_count(self, db) -> int:
        return db.query(News).filter(News.publication_status == "published").count()

    def prepare_context(self, db, question: str, news_id: int | None = None) -> tuple[str | None, list[dict], str | None]:
        recent = db.query(News).filter(News.publication_status == "published").order_by(News.published_at.desc(), News.id.desc()).limit(15).all()
        if not recent and news_id is None:
            return None, [], _NO_MATCH
        catalog = "[CATÁLOGO RECIENTE DEL PORTAL]\n" + "\n".join(_catalog_line(n) for n in recent)
        base = db.query(News).filter(News.publication_status == "published")
        if news_id is not None:
            selected = base.filter(News.id == news_id).first()
            if selected is None:
                return None, [], _HIDDEN
            terms = _terms(question + " " + (selected.title or ""))
            pool = base.filter(News.id != news_id).order_by(News.published_at.desc(), News.id.desc()).limit(self.candidate_pool_limit).all()
            related = sorted(
                (( _score(n, terms) + 2 * (n.university == selected.university) + 2 * (n.category == selected.category), n.id, n) for n in pool),
                key=lambda row: (row[0], row[1]), reverse=True,
            )
            related = [row[2] for row in related if row[0] > 0][:3]
            chunks = [
                "[NOTICIA EN FOCO]\n" + _catalog_line(selected) + "\n" + (selected.content or "")[:4000],
            ]
            if related:
                chunks.append("[ANTECEDENTES RELACIONADOS DEL ARCHIVO]\n" + "\n\n".join(_catalog_line(n) + "\n" + (n.content or "")[:1500] for n in related))
            chunks.append(catalog)
            return "\n\n".join(chunks), [_source(selected), *(_source(n) for n in related)], None

        terms = _terms(question)
        pool = base.order_by(News.published_at.desc(), News.id.desc()).limit(self.candidate_pool_limit).all()
        scored = sorted((( _score(n, terms), n.published_at.timestamp() if n.published_at else 0, n.id, n) for n in pool), key=lambda row: (row[0], row[1], row[2]), reverse=True)
        relevant = [row[3] for row in scored if row[0] > 0][:self.max_results]
        if not relevant:
            panoramic = not terms or any(token in _normalized(question) for token in _PANORAMIC_TRIGGERS)
            if not panoramic:
                return None, [], _NO_MATCH
            relevant = recent[:self.max_results]
        detail = "[NOTICIAS RELEVANTES]\n" + "\n\n".join(_catalog_line(n) + "\n" + (n.content or "")[:2500] for n in relevant)
        return detail + "\n\n" + catalog, [_source(n) for n in relevant], None

    def query(self, db, question: str, news_id: int | None = None) -> dict:
        context, sources, direct_answer = self.prepare_context(db, question, news_id)
        if direct_answer is not None:
            return {"answer": direct_answer, "sources": sources}
        return {"answer": self.llm.answer_from_news(question, context), "sources": sources}
