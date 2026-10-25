from fastapi import APIRouter, HTTPException
router=APIRouter(prefix="/api/scrape",tags=["Scraping"])
@router.post("/upla",status_code=410)
def retired_importer(): raise HTTPException(410,"Usa las fuentes configuradas en el panel")
