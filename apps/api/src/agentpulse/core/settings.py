"""Application settings and environment configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for AgentPulse."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AgentPulse"
    environment: str = "development"
    debug: bool = False

    # Database & Redis
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/agentpulse",
        description="Async PostgreSQL connection URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Streams and Pub/Sub",
    )

    # Auth
    auth_provider: Literal["dev", "entra"] = "dev"
    entra_tenant_id: str | None = None
    entra_client_id: str | None = None

    # LLM Judge & Guardrails
    judge_provider: Literal["fake", "azure_openai"] = "fake"
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_key: str | None = None
    content_safety_endpoint: str | None = None
    content_safety_api_key: str | None = None

    # Ingestion limits
    max_batch_size: int = 500
    rate_limit_per_minute: int = 1200


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()
