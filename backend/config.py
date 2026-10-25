from pathlib import Path
from typing import Literal
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from shared.contracts import FREE_MODEL
class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./university_news.db"
    admin_token: SecretStr = SecretStr("admin-test")
    collector_token: SecretStr = SecretStr("worker-test")
    allowed_origins: list[str] = []
    rag_enabled: bool = False
    openrouter_api_key: SecretStr | None = None
    openrouter_model: Literal[FREE_MODEL] = FREE_MODEL
    chroma_path: Path = Path("./chroma_db")
    media_root: Path = Path("./media")
    collector_id: str = "windows-collector-1"
