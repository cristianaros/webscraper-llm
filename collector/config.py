"""Configuración explícita del recolector Windows."""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.contracts import FREE_MODEL

OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = REPO_ROOT / ".env"
LEGACY_COLLECTOR_ENV_FILE = Path(__file__).resolve().parent / ".env"


class CollectorSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    data_dir: Path = Field(validation_alias="COLLECTOR_DATA_DIR")
    api_url: str = Field(validation_alias="COLLECTOR_API_URL")
    collector_token: SecretStr | None = Field(default=None, validation_alias="COLLECTOR_TOKEN")
    openrouter_api_key: SecretStr | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    openrouter_model: Literal[FREE_MODEL] = Field(default=FREE_MODEL, validation_alias="OPENROUTER_MODEL")
    collector_id: str = Field(default="windows-collector-1", validation_alias="COLLECTOR_ID")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    llm_daily_budget: int = Field(default=30, ge=0, validation_alias="LLM_DAILY_BUDGET")
    llm_rpm: int = Field(default=5, ge=0, validation_alias="LLM_RPM")
    run_budget_seconds: int = Field(default=720, ge=1, validation_alias="RUN_BUDGET_SECONDS")
    source_cache_ttl_hours: int = Field(default=24, ge=1, validation_alias="SOURCE_CACHE_TTL_HOURS")
    allow_test_hosts: bool = Field(default=False, validation_alias="ALLOW_TEST_HOSTS")

    @field_validator("data_dir")
    @classmethod
    def _absolute_data_dir(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("data_dir_must_be_absolute")
        return value

    @model_validator(mode="after")
    def _secure_api_url(self) -> "CollectorSettings":
        parsed = urlsplit(self.api_url)
        if not parsed.hostname or parsed.scheme not in {"http", "https"}:
            raise ValueError("invalid_api_url")
        host = parsed.hostname.lower()
        loopback = host == "localhost"
        if not loopback:
            try:
                loopback = ipaddress.ip_address(host).is_loopback
            except ValueError:
                pass
        if parsed.scheme != "https" and not (self.app_env == "development" and loopback):
            raise ValueError("api_https_required")
        return self

    def require_secrets(self) -> None:
        if self.collector_token is None or not self.collector_token.get_secret_value():
            raise ValueError("collector_token_missing")
        if self.openrouter_api_key is None or not self.openrouter_api_key.get_secret_value():
            raise ValueError("openrouter_api_key_missing")


def default_env_path() -> Path:
    if DEFAULT_ENV_FILE.is_file() or not LEGACY_COLLECTOR_ENV_FILE.is_file():
        return DEFAULT_ENV_FILE
    return LEGACY_COLLECTOR_ENV_FILE


def load_settings(env_file: Path | None = None) -> CollectorSettings:
    """Load the unified root dotenv file (or an explicit caller-selected path)."""
    target = env_file.resolve() if env_file is not None else default_env_path()
    return CollectorSettings(_env_file=str(target), _env_file_encoding="utf-8")
