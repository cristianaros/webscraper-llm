import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app_state
import models
import schemas
from database import get_db
from rag.openrouter import OpenRouterClient, OpenRouterError
from scraping.upla import ScrapeGraphError, UplaScraper

router = APIRouter(prefix="/api/scrape", tags=["Scraping"])
logger = logging.getLogger(__name__)


@router.post("/upla", response_model=schemas.ScrapeUplaResponse)
def import_upla_news(
    request: schemas.ScrapeUplaRequest,
    db: Session = Depends(get_db),
):
    """Importa las noticias mas recientes de UPLA y evita URLs duplicadas."""
    try:
        scraper = UplaScraper()
        llm = OpenRouterClient()
        links = scraper.latest_links(request.limit)
    except (ValueError, ScrapeGraphError, OpenRouterError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not links:
        raise HTTPException(
            status_code=502,
            detail="ScrapeGraphAI no encontro URLs de noticias validas en UPLA.",
        )

    items: list[schemas.ScrapeItemResult] = []
    created = 0
    skipped = 0
    failed = 0

    for link in links:
        existing = (
            db.query(models.News)
            .filter(models.News.source_url == link.url)
            .first()
        )
        if existing:
            skipped += 1
            items.append(
                schemas.ScrapeItemResult(
                    title=existing.title,
                    source_url=link.url,
                    status="skipped",
                    news_id=existing.id,
                )
            )
            continue

        try:
            article = scraper.article(link)
            summary = llm.summarize_news(article.title, article.content)
            news = models.News(
                title=article.title,
                summary=summary,
                content=article.content,
                category=article.category,
                university="Universidad de Playa Ancha",
                author=article.author,
                image_url=article.image_url,
                source_url=article.source_url,
                published_at=article.published_at,
                is_featured=False,
            )
            db.add(news)
            db.commit()
            db.refresh(news)

            if app_state.rag_engine:
                try:
                    app_state.rag_engine.add_news(
                        news_id=news.id,
                        title=news.title,
                        content=news.content,
                        category=news.category,
                        university=news.university,
                        summary=news.summary,
                        source_url=news.source_url,
                        published_at=news.published_at,
                    )
                except Exception as exc:
                    logger.warning(
                        "La noticia %s se guardo, pero no se pudo indexar: %s",
                        news.id,
                        exc,
                    )

            created += 1
            items.append(
                schemas.ScrapeItemResult(
                    title=news.title,
                    source_url=news.source_url,
                    status="created",
                    news_id=news.id,
                )
            )
        except (ScrapeGraphError, OpenRouterError, ValueError) as exc:
            db.rollback()
            failed += 1
            items.append(
                schemas.ScrapeItemResult(
                    title=link.title,
                    source_url=link.url,
                    status="failed",
                    error=str(exc),
                )
            )
        except Exception as exc:
            db.rollback()
            failed += 1
            logger.exception("Error inesperado al importar %s", link.url)
            items.append(
                schemas.ScrapeItemResult(
                    title=link.title,
                    source_url=link.url,
                    status="failed",
                    error=f"Error inesperado: {type(exc).__name__}",
                )
            )

    return schemas.ScrapeUplaResponse(
        requested=request.limit,
        found=len(links),
        created=created,
        skipped=skipped,
        failed=failed,
        model=llm.model,
        items=items,
    )
