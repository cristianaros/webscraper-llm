from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
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
def get_media(sha256: str, if_none_match: str | None = Header(default=None), db=Depends(get_db)):
    asset=db.get(MediaAsset,sha256)
    if not asset or not db.query(News).filter(News.image_sha256==sha256,News.publication_status=="published").first():raise HTTPException(404,"media_not_found")
    etag = f'"{sha256}"'
    headers = {"X-Content-Type-Options":"nosniff", "Cache-Control":"public, max-age=31536000, immutable", "ETag":etag}
    if if_none_match and (etag in if_none_match or sha256 in if_none_match):
        return Response(status_code=304, headers=headers)
    if asset.content_bytes is not None:
        return Response(content=asset.content_bytes, media_type=asset.content_type, headers=headers)
    return FileResponse(asset.storage_key,media_type=asset.content_type,headers=headers)
