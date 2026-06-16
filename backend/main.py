import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import engine
import models
import app_state
from rag.engine import RAGEngine
from routers import news, chat

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos al arrancar y los limpia al cerrar."""
    # Crear tablas en la base de datos
    models.Base.metadata.create_all(bind=engine)
    logger.info("Base de datos inicializada.")

    # Inicializar motor RAG
    try:
        app_state.rag_engine = RAGEngine()
        count = app_state.rag_engine.get_index_count()
        logger.info(f"Motor RAG listo. Documentos indexados: {count}")
        if count == 0:
            logger.info("El índice RAG está vacío. Indexando noticias de la base de datos SQLite...")
            from database import SessionLocal
            db = SessionLocal()
            try:
                db_news = db.query(models.News).all()
                for news in db_news:
                    app_state.rag_engine.add_news(
                        news_id=news.id,
                        title=news.title,
                        content=news.content,
                        category=news.category,
                        university=news.university,
                        summary=news.summary,
                    )
                logger.info(f"Indexación inicial completada. {len(db_news)} noticias indexadas.")
            finally:
                db.close()
    except Exception as e:
        logger.error(f"Error al inicializar RAG: {e}")
        logger.warning("El sistema funcionará sin IA. Verifica tu GEMINI_API_KEY en .env")
        app_state.rag_engine = None

    yield

    logger.info("Servidor apagado.")


app = FastAPI(
    title="🎓 UniNews — Sistema de Noticias Universitarias",
    description=(
        "API REST con IA (Google Gemini + RAG) para gestión de noticias universitarias. "
        "Permite crear, editar y consultar noticias con un asistente inteligente."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — permite conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(news.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {
        "message": "UniNews — Sistema de Noticias Universitarias con IA",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "rag_active": app_state.rag_engine is not None,
    }


@app.get("/health")
def health():
    rag_ok = app_state.rag_engine is not None
    indexed = app_state.rag_engine.get_index_count() if rag_ok else 0
    return {
        "status": "healthy",
        "rag_enabled": rag_ok,
        "indexed_documents": indexed,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
