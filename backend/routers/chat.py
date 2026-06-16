from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse
import app_state

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint RAG: recibe una pregunta, busca noticias relevantes
    en ChromaDB y genera una respuesta con Google Gemini.
    """
    if not app_state.rag_engine:
        raise HTTPException(
            status_code=503,
            detail="El motor RAG no está disponible. Verifica tu GEMINI_API_KEY en el archivo .env."
        )

    result = app_state.rag_engine.query(question=request.question)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )


@router.get("/status")
def rag_status():
    """Retorna el estado del motor RAG (cuántos documentos indexados)."""
    if not app_state.rag_engine:
        return {"status": "error", "message": "Motor RAG no inicializado. Configura GEMINI_API_KEY."}
    try:
        count = app_state.rag_engine.get_index_count()
        return {"status": "ok", "indexed_documents": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
