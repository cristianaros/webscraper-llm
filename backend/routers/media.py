from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from database import get_db
from models import MediaAsset, News
from security import require_collector
from services.media import receive_media
from shared.contracts import ImageDelivery, MediaReceipt
router=APIRouter(prefix="/api",tags=["Media"])

@router.post("/collector/media", response_model=MediaReceipt, dependencies=[Depends(require_collector)])
async def upload_media(request: Request, delivery: str = Form(...), file: UploadFile = File(...), db=Depends(get_db)):
    try: media_delivery = ImageDelivery.model_validate_json(delivery)
    except Exception as exc: raise HTTPException(422, "invalid_media_delivery") from exc
    content = await file.read(5 * 1024 * 1024 + 1)
    try: return receive_media(db, request.app.state.settings, media_delivery, content, file.content_type, datetime.now(timezone.utc))
    finally: await file.close()

@router.get("/media/{sha256}")
def get_media(sha256:str,db=Depends(get_db)):
    asset=db.get(MediaAsset,sha256)
    if not asset or not db.query(News).filter(News.image_sha256==sha256,News.publication_status=="published").first():raise HTTPException(404,"media_not_found")
    return FileResponse(asset.storage_key,media_type=asset.content_type,headers={"X-Content-Type-Options":"nosniff"})
