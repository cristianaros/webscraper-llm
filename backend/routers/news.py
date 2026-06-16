from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from database import get_db
import models
import schemas
import app_state

router = APIRouter(prefix="/api/news", tags=["News"])


# -----------------------------------------------------------------------
# GET /api/news/stats — Estadísticas generales
# -----------------------------------------------------------------------
@router.get("/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(models.News).count()
    featured = db.query(models.News).filter(models.News.is_featured == True).count()

    cats = db.query(models.News.category, func.count(models.News.id)).group_by(models.News.category).all()
    categories = {cat: count for cat, count in cats}

    unis = db.query(models.News.university).distinct().all()
    universities = [u[0] for u in unis]

    return schemas.StatsResponse(
        total_news=total,
        categories=categories,
        universities=universities,
        featured_count=featured,
    )


# -----------------------------------------------------------------------
# GET /api/news — Listar noticias con filtros
# -----------------------------------------------------------------------
@router.get("/", response_model=list[schemas.NewsResponse])
def list_news(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    university: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.News)

    if category:
        query = query.filter(models.News.category == category)
    if university:
        query = query.filter(models.News.university == university)
    if featured is not None:
        query = query.filter(models.News.is_featured == featured)
    if search:
        query = query.filter(
            models.News.title.contains(search) | models.News.content.contains(search)
        )

    return query.order_by(models.News.created_at.desc()).offset(skip).limit(limit).all()


# -----------------------------------------------------------------------
# GET /api/news/{id} — Obtener una noticia
# -----------------------------------------------------------------------
@router.get("/{news_id}", response_model=schemas.NewsResponse)
def get_news(news_id: int, db: Session = Depends(get_db)):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    return news


# -----------------------------------------------------------------------
# POST /api/news — Crear noticia
# -----------------------------------------------------------------------
@router.post("/", response_model=schemas.NewsResponse, status_code=201)
def create_news(news_in: schemas.NewsCreate, db: Session = Depends(get_db)):
    news = models.News(**news_in.model_dump())
    db.add(news)
    db.commit()
    db.refresh(news)

    # Indexar en RAG
    if app_state.rag_engine:
        try:
            app_state.rag_engine.add_news(
                news_id=news.id,
                title=news.title,
                content=news.content,
                category=news.category,
                university=news.university,
                summary=news.summary,
            )
        except Exception as e:
            print(f"[RAG] Warning: no se pudo indexar la noticia {news.id}: {e}")

    return news


# -----------------------------------------------------------------------
# PUT /api/news/{id} — Actualizar noticia
# -----------------------------------------------------------------------
@router.put("/{news_id}", response_model=schemas.NewsResponse)
def update_news(news_id: int, news_in: schemas.NewsUpdate, db: Session = Depends(get_db)):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")

    update_data = news_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(news, field, value)

    db.commit()
    db.refresh(news)

    # Re-indexar en RAG
    if app_state.rag_engine:
        try:
            app_state.rag_engine.add_news(
                news_id=news.id,
                title=news.title,
                content=news.content,
                category=news.category,
                university=news.university,
                summary=news.summary,
            )
        except Exception as e:
            print(f"[RAG] Warning: no se pudo re-indexar la noticia {news.id}: {e}")

    return news


# -----------------------------------------------------------------------
# DELETE /api/news/{id} — Eliminar noticia
# -----------------------------------------------------------------------
@router.delete("/{news_id}", status_code=204)
def delete_news(news_id: int, db: Session = Depends(get_db)):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")

    db.delete(news)
    db.commit()

    # Eliminar del índice RAG
    if app_state.rag_engine:
        try:
            app_state.rag_engine.remove_news(news_id)
        except Exception as e:
            print(f"[RAG] Warning: no se pudo eliminar noticia {news_id} del índice: {e}")
