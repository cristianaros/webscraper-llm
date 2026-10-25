from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db
from security import require_admin
from models import News, NewsRevision, University
from models import ScrapeRun, Source, CollectorStatus
from services.sources import create_university
from services.ingestion import approve_revision
from shared.contracts import ArticleFields
import schemas
router=APIRouter(prefix="/api/admin",tags=["Admin"],dependencies=[Depends(require_admin)])
@router.post("/universities",status_code=201)
def university(payload:dict,db=Depends(get_db)):
    row=create_university(db,payload.get("name", ""));return {"id":row.id,"name":row.name}
@router.get("/universities")
def universities(db=Depends(get_db)): return [{"id":x.id,"name":x.name} for x in db.query(University).order_by(University.name)]
@router.get("/news")
def all_news(skip:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=100),publication_status:str|None=None,db=Depends(get_db)):
    q=db.query(News)
    if publication_status:q=q.filter(News.publication_status==publication_status)
    return q.order_by(News.id.desc()).offset(skip).limit(limit).all()
@router.get("/news/{news_id}")
def one_news(news_id:int,db=Depends(get_db)):
    n=db.get(News,news_id)
    if not n:raise HTTPException(404,"news_not_found")
    return n
@router.get("/revisions")
def revisions(status:str|None=None,skip:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=100),db=Depends(get_db)):
    q=db.query(NewsRevision)
    if status:q=q.filter(NewsRevision.review_status==status)
    rows=q.order_by(NewsRevision.id.desc()).offset(skip).limit(limit).all()
    return {"items":[revision_view(x,db) for x in rows],"total":q.count()}
@router.get("/revisions/{revision_id}")
def revision(revision_id:int,db=Depends(get_db)):
    x=db.get(NewsRevision,revision_id)
    if not x:raise HTTPException(404,"revision_not_found")
    return revision_view(x,db)
def revision_view(x,db):
    p=x.payload_json; return {"id":x.id,"news_id":x.news_id,"source_id":x.source_id,"document":p.get("document"),"fields":p.get("fields"),"issues":x.issues_json,"review_status":x.review_status,"fetched_at":x.fetched_at}
@router.post("/revisions/{revision_id}/publish")
def publish(revision_id:int,payload:dict,db=Depends(get_db)): return approve_revision(db,revision_id,ArticleFields.model_validate(payload["fields"]),editorial_lock=bool(payload.get("editorial_lock",True)),now=datetime.now(timezone.utc))
@router.post("/revisions/{revision_id}/reject",status_code=204)
def reject(revision_id:int,payload:dict,db=Depends(get_db)):
    x=db.get(NewsRevision,revision_id)
    if not x:raise HTTPException(404,"revision_not_found")
    x.review_status="rejected"; x.issues_json=[*x.issues_json, payload.get("reason","rejected")];db.commit()
@router.patch("/news/{news_id}/publication")
def publication(news_id:int,payload:dict,db=Depends(get_db)):
    n=db.get(News,news_id)
    if not n:raise HTTPException(404,"news_not_found")
    if payload.get("status") not in {"published","archived"}:raise HTTPException(422,"invalid_status")
    n.publication_status=payload["status"];n.editorial_lock=bool(payload.get("editorial_lock",n.editorial_lock));db.commit();db.refresh(n);return n
@router.post("/sources/{source_id}/runs",status_code=202)
def request_run(source_id:int,payload:dict,db=Depends(get_db)):
    source=db.get(Source,source_id)
    if not source: raise HTTPException(404,"source_not_found")
    kind=payload.get("kind")
    if kind not in {"manual","preview"}: raise HTTPException(422,"invalid_run_kind")
    active=db.query(ScrapeRun).filter(ScrapeRun.source_id==source_id,ScrapeRun.status.in_(["requested","running"])).first()
    if active:return {"run_id":active.id,"status":active.status}
    now=datetime.now(timezone.utc); row=ScrapeRun(id=str(__import__('uuid').uuid4()),source_id=source_id,source_revision=source.revision,trigger=kind,status="requested",requested_at=now);db.add(row);db.commit();return {"run_id":row.id,"status":row.status}
@router.post("/sources/{source_id}/validate")
def validate_source(source_id:int,payload:dict,db=Depends(get_db)):
    source=db.get(Source,source_id); run=db.get(ScrapeRun,str(payload.get("run_id")))
    if not source or not run:raise HTTPException(404,"source_or_run_not_found")
    if payload.get("expected_revision")!=source.revision or run.source_revision!=source.revision or run.status!="success" or not run.preview_json:raise HTTPException(409,"preview_not_validated")
    source.validated_revision=source.revision;db.commit()
    from services.sources import source_config
    return source_config(db,source)
@router.get("/runs")
def runs(skip:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=100),db=Depends(get_db)):
    q=db.query(ScrapeRun);return {"items":[r.report_json or {"run_id":r.id,"status":r.status} for r in q.order_by(ScrapeRun.requested_at.desc()).offset(skip).limit(limit)],"total":q.count()}
@router.get("/runs/{run_id}")
def run(run_id:str,db=Depends(get_db)):
    r=db.get(ScrapeRun,run_id)
    if not r:raise HTTPException(404,"run_not_found")
    return {"run_id":r.id,"status":r.status,"source_id":r.source_id,"source_revision":r.source_revision,"report":r.report_json,"preview":r.preview_json,"error_code":r.error_code}
@router.get("/collector/status")
def collector_status(db=Depends(get_db)):
    row=db.get(CollectorStatus,"windows-collector-1")
    if not row:return {"stale":True}
    return {**row.status_json,"last_seen_at":row.last_seen_at,"stale":(datetime.now(timezone.utc)-row.last_seen_at).total_seconds()>2700}
