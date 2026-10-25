from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from security import require_admin, require_collector
from shared.contracts import SourceInput
from models import Source
from services.sources import create_source, patch_source, source_config
router=APIRouter(prefix="/api",tags=["Sources"])
@router.post("/admin/sources",dependencies=[Depends(require_admin)])
def create(payload:SourceInput,db=Depends(get_db)): return create_source(db,payload)
@router.get("/admin/sources",dependencies=[Depends(require_admin)])
def list_admin(db=Depends(get_db)): return [source_config(db,x) for x in db.query(Source).all()]
@router.patch("/admin/sources/{source_id}",dependencies=[Depends(require_admin)])
def patch(source_id:int,payload:dict,db=Depends(get_db)):
    expected=payload.pop("expected_revision",None)
    if not isinstance(expected,int):raise HTTPException(422,"expected_revision_required")
    return patch_source(db,source_id,payload,expected)
@router.delete("/admin/sources/{source_id}",status_code=204,dependencies=[Depends(require_admin)])
def disable(source_id:int,db=Depends(get_db)):
    s=db.get(Source,source_id)
    if not s:raise HTTPException(404,"source_not_found")
    s.enabled=False;s.auto_publish=False;db.commit()
@router.get("/collector/sources",dependencies=[Depends(require_collector)])
def collector_sources(db=Depends(get_db)):
    from datetime import datetime,timezone
    return {"generated_at":datetime.now(timezone.utc),"sources":[source_config(db,x) for x in db.query(Source).all()]}
