"""Reindex published news into the vector database without altering news rows."""
from __future__ import annotations

import logging
from database import SessionLocal
from models import News

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reindex_published() -> int:
    try:
        from rag.engine import RAGEngine
        engine = RAGEngine()
    except Exception as exc:
        logger.warning("RAG engine not available or disabled: %s", exc)
        return 0

    db = SessionLocal()
    try:
        published_items = (
            db.query(News)
            .filter(News.publication_status == "published")
            .order_by(News.id)
            .all()
        )
        count = 0
        for item in published_items:
            engine.add_news(
                news_id=item.id,
                title=item.title,
                content=item.content,
                category=item.category,
                university=item.university,
                summary=item.summary,
                source_url=item.source_url,
                published_at=item.published_at,
            )
            count += 1
        logger.info("Reindexed %d published news items into RAG engine.", count)
        return count
    finally:
        db.close()


def main() -> None:
    reindex_published()


if __name__ == "__main__":
    main()
