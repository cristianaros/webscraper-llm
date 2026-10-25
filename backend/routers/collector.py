from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, Header, HTTPException
from database import get_db
from security import require_collector
from shared.contracts import Delivery, RunReport, PreviewResult, CollectorHeartbeat
from services.ingestion import ingest
from models import CollectorStatus, ScrapeRun, Source
router=APIRouter(prefix="/api/collector",tags=["Collector"],dependencies=[Depends(require_collector)])
@router.post("/articles")
def article(delivery:Delivery,db=Depends(get_db)): return ingest(db,delivery,datetime.now(timezone.utc))
@router.post("/runs/claim")
def claim(payload:dict,db=Depends(get_db)):
    if payload.get("collector_id")!="windows-collector-1":raise HTTPException(422,"unknown_collector")
    now=datetime.now(timezone.utc); rows=db.query(ScrapeRun).filter(ScrapeRun.status=="requested").order_by(ScrapeRun.requested_at).limit(3).all();result=[]
    for r in rows:
        r.status="running";r.started_at=now;r.lease_until=now+timedelta(minutes=15);r.lease_token=str(uuid4()); result.append({"run_id":r.id,"source":db.get(Source,r.source_id) and source_payload(db,r.source_id),"trigger":r.trigger,"lease_token":r.lease_token,"lease_until":r.lease_until})
    db.commit();return result
@router.post("/runs/{run_id}/renew")
def renew(run_id:str,payload:dict,db=Depends(get_db)):
    r=db.get(ScrapeRun,run_id)
    if not r or r.status!="running" or r.lease_token!=payload.get("lease_token"):raise HTTPException(409,"invalid_lease")
    r.lease_until=datetime.now(timezone.utc)+timedelta(minutes=15);db.commit();return {"lease_until":r.lease_until}
def source_payload(db,source_id):
    from services.sources import source_config
    return source_config(db,db.get(Source,source_id)).model_dump(mode="json")
@router.put("/runs/{run_id}",status_code=204)
def report(run_id:str,payload:RunReport,x_lease_token:str|None=Header(default=None),db=Depends(get_db)):
    r=db.get(ScrapeRun,run_id)
    if not r:raise HTTPException(404,"run_not_found")
    if r.lease_token and r.lease_token!=x_lease_token:raise HTTPException(409,"invalid_lease")
    if r.status in {"success","partial","failed","blocked"}:return
    r.status=payload.status;r.finished_at=payload.finished_at;r.report_json=payload.model_dump(mode="json");r.error_code=payload.error_code;db.commit()
@router.put("/runs/{run_id}/preview",status_code=204)
def preview(run_id:str,payload:PreviewResult,db=Depends(get_db)):
    r=db.get(ScrapeRun,run_id)
    if not r:raise HTTPException(404,"run_not_found")
    r.preview_json=payload.model_dump(mode="json");r.status="success";r.finished_at=datetime.now(timezone.utc);db.commit()
@router.put("/status",status_code=204)
def status(payload:CollectorHeartbeat,db=Depends(get_db)):
    if payload.collector_id!="windows-collector-1":raise HTTPException(422,"unknown_collector")
    row=db.get(CollectorStatus,payload.collector_id)
    if row:row.last_seen_at=datetime.now(timezone.utc);row.status_json=payload.model_dump(mode="json")
    else:db.add(CollectorStatus(collector_id=payload.collector_id,last_seen_at=datetime.now(timezone.utc),status_json=payload.model_dump(mode="json")))
    db.commit()
