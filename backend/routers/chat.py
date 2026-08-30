from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse
import app_state
from rag.openrouter import OpenRouterError

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint RAG: recibe una pregunta, busca noticias relevantes
    en ChromaDB y genera una respuesta con MiniMax mediante OpenRouter.
    """
    if not app_state.rag_engine:
        raise HTTPException(
            status_code=503,
            detail="El motor RAG no está disponible. Verifica OPENROUTER_API_KEY y OPENROUTER_MODEL."
        )

    try:
        result = app_state.rag_engine.query(question=request.question)
    except OpenRouterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )


@router.get("/status")
def rag_status():
    """Retorna el estado del motor RAG (cuántos documentos indexados)."""
    if not app_state.rag_engine:
        return {
            "status": "error",
            "message": "Motor RAG no inicializado. Configura OpenRouter.",
        }
    try:
        count = app_state.rag_engine.get_index_count()
        return {
            "status": "ok",
            "indexed_documents": count,
            "model": app_state.rag_engine.model_name,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
