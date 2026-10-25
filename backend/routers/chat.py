from fastapi import APIRouter, Depends, HTTPException, Request
from database import get_db
from schemas import ChatRequest, ChatResponse
from rag.openrouter import OpenRouterError

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, db=Depends(get_db)):
    """Answer using only currently published operational news."""
    assistant = request.app.state.assistant
    if assistant is None:
        raise HTTPException(status_code=503, detail="El asistente no está configurado.")

    try:
        result = assistant.query(db, question=payload.question, news_id=payload.news_id)
    except OpenRouterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )


@router.get("/status")
def rag_status(request: Request, db=Depends(get_db)):
    """Report availability and the count of published news available for retrieval."""
    assistant = request.app.state.assistant
    if assistant is None:
        return {
            "status": "error",
            "indexed_documents": 0,
            "message": "Configura RAG_ENABLED y OPENROUTER_API_KEY en el backend.",
        }
    try:
        count = assistant.get_index_count(db)
        return {
            "status": "ok",
            "indexed_documents": count,
            "model": assistant.model_name,
        }
    except Exception:
        return {"status": "error", "indexed_documents": 0, "message": "No se pudo consultar las noticias."}
