"""Retrieval over published operational news followed by a grounded LLM answer."""

from __future__ import annotations

import heapq
import re
import unicodedata

from models import News

_STOP_WORDS = {
    "como", "cual", "cuales", "dame", "dime", "esta", "estas", "este", "estos",
    "hay", "las", "los", "mas", "noticia", "noticias", "para", "por", "que",
    "reciente", "recientes", "resumen", "resume", "sobre", "una", "ultima", "ultimas",
}
_NO_MATCH = "No encontré noticias publicadas relacionadas con tu pregunta."


def _normalized(value: str | None) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def _terms(question: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]{3,}", _normalized(question)) if term not in _STOP_WORDS}


def _score(news: News, terms: set[str]) -> int:
    title = _normalized(news.title)
    category = _normalized(news.category)
    university = _normalized(news.university)
    summary = _normalized(news.summary)
    content = _normalized(news.content)
    return sum(
        5 * (term in title) + 3 * (term in category) + 2 * (term in university)
        + 2 * (term in summary) + (term in content)
        for term in terms
    )


class NewsAssistant:
    def __init__(self, llm, max_results: int = 4):
        self.llm = llm
        self.max_results = max_results

    @property
    def model_name(self) -> str:
        return self.llm.model

    def get_index_count(self, db) -> int:
        return db.query(News).filter(News.publication_status == "published").count()

    def query(self, db, question: str, news_id: int | None = None) -> dict:
        published = db.query(News).filter(News.publication_status == "published")
        if news_id is not None:
            selected = published.filter(News.id == news_id).first()
            if selected is None:
                return {"answer": "La noticia seleccionada no está publicada o no existe.", "sources": []}
            relevant = [selected]
        else:
            terms = _terms(question)
            candidates = (
                (_score(news, terms), news.published_at.timestamp() if news.published_at else 0, news.id, news)
                for news in published.yield_per(100)
            )
            relevant = [news for score, _, _, news in heapq.nlargest(
                self.max_results,
                (candidate for candidate in candidates if not terms or candidate[0] > 0),
                key=lambda candidate: candidate[:3],
            )]
        if not relevant:
            return {"answer": _NO_MATCH, "sources": []}
        context = []
        sources = []
        for index, news in enumerate(relevant, 1):
            context.append(
                f"[Noticia {index}]\nTítulo: {news.title}\nUniversidad: {news.university}"
                f"\nCategoría: {news.category}\nFecha: {news.published_on or 'No indicada'}"
                f"\nContenido: {news.content[:12000]}"
            )
            sources.append({
                "news_id": news.id, "title": news.title, "category": news.category,
                "university": news.university, "source_url": news.source_url,
            })
        answer = self.llm.answer_from_news(question, "\n\n".join(context))
        return {"answer": answer, "sources": sources}
