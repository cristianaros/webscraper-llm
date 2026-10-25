from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import BackendSettings
from database import make_engine, make_session_factory
from rag.news_assistant import NewsAssistant
from rag.openrouter import OpenRouterClient
from routers import news, sources, admin, collector, media, scraper, chat
def create_app(settings: BackendSettings | None = None):
    settings=settings or BackendSettings(_env_file=str(Path(__file__).resolve().parent / ".env")); engine=make_engine(settings.database_url)
    @asynccontextmanager
    async def lifespan(app): yield
    app=FastAPI(title="UniNews API",version="2.0.0",lifespan=lifespan); app.state.settings=settings; app.state.engine=engine; app.state.session_factory=make_session_factory(engine)
    key=settings.openrouter_api_key.get_secret_value() if settings.openrouter_api_key else ""
    app.state.assistant=NewsAssistant(OpenRouterClient(api_key=key,model=settings.openrouter_model)) if settings.rag_enabled and key else None
    app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=False,allow_methods=["GET","POST","PATCH","PUT","DELETE"],allow_headers=["Authorization","Content-Type","X-Lease-Token"])
    for r in (news.router,sources.router,admin.router,collector.router,media.router,scraper.router,chat.router): app.include_router(r)
    @app.get("/api/info")
    def info(): return {"status":"running","rag_enabled":app.state.assistant is not None}
    @app.get("/health")
    def health(): return {"status":"healthy","rag_enabled":app.state.assistant is not None}
    return app
app=create_app()
