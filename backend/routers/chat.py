from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from database import get_db
from schemas import ChatRequest, ChatResponse
from rag.openrouter import OpenRouterError
from rag.chat_guard import ChatRateLimitError, extract_client_ip

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, db=Depends(get_db)):
    """Answer using only currently published operational news."""
    assistant = request.app.state.assistant
    if assistant is None:
        raise HTTPException(status_code=503, detail="El asistente no está configurado.")

    guard = request.app.state.chat_guard
    try:
        context, sources, direct_answer = assistant.prepare_context(db, payload.question, payload.news_id)
        if direct_answer is not None:
            result = {"answer": direct_answer, "sources": sources}
        else:
            marker = guard.snapshot_marker(db)
            now = datetime.now(timezone.utc).timestamp()
            cached = guard.get_cached(payload.news_id, payload.question, marker, now)
            if cached is not None:
                result = cached
            else:
                ip = extract_client_ip(
                    request,
                    trust_proxy_headers=request.app.state.settings.app_env == "production",
                )
                guard.reserve_live_call(ip, datetime.now(timezone.utc))
                result = {"answer": assistant.llm.answer_from_news(payload.question, context), "sources": sources}
                guard.put_cached(payload.news_id, payload.question, marker, result, now)
    except ChatRateLimitError as exc:
        raise HTTPException(status_code=429, detail=exc.detail) from exc
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
