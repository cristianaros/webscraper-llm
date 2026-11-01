from pathlib import Path
from typing import Literal
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from shared.contracts import FREE_MODEL

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = REPO_ROOT / ".env"
LEGACY_BACKEND_ENV_FILE = Path(__file__).resolve().parent / ".env"


def default_env_path() -> Path:
    if DEFAULT_ENV_FILE.is_file() or not LEGACY_BACKEND_ENV_FILE.is_file():
        return DEFAULT_ENV_FILE
    return LEGACY_BACKEND_ENV_FILE


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    database_url: str = "sqlite:///./university_news.db"
    admin_token: SecretStr = SecretStr("admin-test")
    collector_token: SecretStr = SecretStr("worker-test")
    allowed_origins: list[str] = []
    rag_enabled: bool = False
    openrouter_api_key: SecretStr | None = None
    openrouter_model: Literal[FREE_MODEL] = FREE_MODEL
    media_root: Path = Path("./media")
    collector_id: str = "windows-collector-1"
    app_env: Literal["development", "production"] = "development"
    chat_daily_budget: int = Field(default=100, ge=0)
    chat_ip_rpm: int = Field(default=6, ge=1)

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.app_env == "production":
            admin = self.admin_token.get_secret_value()
            collector = self.collector_token.get_secret_value()
            if (
                len(admin) < 16
                or len(collector) < 16
                or admin == "admin-test"
                or collector == "worker-test"
                or admin == collector
                or not self.allowed_origins
            ):
                raise ValueError("production requires distinct strong tokens and allowed_origins")
        return self


def load_backend_settings(env_file: Path | None = None) -> BackendSettings:
    target = env_file.resolve() if env_file is not None else default_env_path()
    return BackendSettings(
        _env_file=str(target) if target.is_file() else None,
        _env_file_encoding="utf-8",
    )
