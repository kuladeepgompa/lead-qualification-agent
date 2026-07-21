"""Typed application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LEAD_",
        extra="ignore",
    )

    app_name: str = Field(default="lead-qualification-agent", min_length=1)
    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    llm_provider: Literal["openai"] = "openai"
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "LEAD_OPENAI_API_KEY"),
    )
    openai_model: str = Field(default="gpt-4o-mini", min_length=1, max_length=120)
    llm_timeout_seconds: float = Field(default=20, gt=0, le=120)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    llm_retry_base_delay_seconds: float = Field(default=0.25, gt=0, le=10)
    hot_lead_min_score: int = Field(default=75, ge=0, le=100)
    warm_lead_min_score: int = Field(default=40, ge=0, le=100)
    cache_enabled: bool = False
    cache_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = Field(default="redis://localhost:6379/0", min_length=1)
    cache_ttl_seconds: int = Field(default=3600, ge=1, le=864000)

    @model_validator(mode="after")
    def validate_priority_bands(self) -> "Settings":
        """Require ordered score bands for deterministic priority reconciliation."""

        if self.warm_lead_min_score > self.hot_lead_min_score:
            raise ValueError("warm_lead_min_score must not exceed hot_lead_min_score.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object for the current process."""

    return Settings()
