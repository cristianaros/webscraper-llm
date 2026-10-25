from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from database import get_db
from security import require_admin
from services.ingestion import published_news
import models, schemas
router=APIRouter(prefix="/api/news",tags=["News"])
@router.get("/stats",response_model=schemas.StatsResponse)
def stats(db=Depends(get_db)):
    q=published_news(db);return schemas.StatsResponse(total_news=q.count(),categories=dict(q.with_entities(models.News.category,func.count(models.News.id)).group_by(models.News.category).all()),universities=[x[0] for x in q.with_entities(models.News.university).distinct().all()],featured_count=q.filter(models.News.is_featured==True).count())
@router.get("/",response_model=list[schemas.NewsResponse])
def list_news(skip:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=100),university_id:int|None=None,category:str|None=None,search:str|None=Query(None,min_length=1,max_length=200),db=Depends(get_db)):
    q=published_news(db)
    if university_id:q=q.filter(models.News.university_id==university_id)
    if category:q=q.filter(models.News.category==category)
    if search:
        pattern = f"%{search.strip().lower()}%"
        q=q.filter(func.lower(models.News.title).like(pattern) | func.lower(models.News.content).like(pattern))
    return q.order_by(models.News.published_at.desc(),models.News.id.desc()).offset(skip).limit(limit).all()
@router.get("/{news_id}",response_model=schemas.NewsResponse)
def get_news(news_id:int,db=Depends(get_db)):
    n=published_news(db).filter(models.News.id==news_id).first()
    if not n:raise HTTPException(404,"Noticia no encontrada")
    return n
@router.post("/",response_model=schemas.NewsResponse,status_code=201,dependencies=[Depends(require_admin)])
def create(news_in:schemas.NewsCreate,db=Depends(get_db)):
    n=models.News(**news_in.model_dump(),publication_status="published",editorial_lock=True);db.add(n);db.commit();db.refresh(n);return n
@router.put("/{news_id}",response_model=schemas.NewsResponse,dependencies=[Depends(require_admin)])
def update(news_id:int,news_in:schemas.NewsUpdate,db=Depends(get_db)):
    n=db.get(models.News,news_id)
    if not n:raise HTTPException(404,"Noticia no encontrada")
    for k,v in news_in.model_dump(exclude_unset=True).items():setattr(n,k,v)
    n.editorial_lock=True;db.commit();db.refresh(n);return n
@router.delete("/{news_id}",status_code=204,dependencies=[Depends(require_admin)])
def delete(news_id:int,db=Depends(get_db)):
    n=db.get(models.News,news_id)
    if not n:raise HTTPException(404,"Noticia no encontrada")
    n.publication_status="archived";db.commit()
