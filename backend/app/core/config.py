import os
from typing import Any, Dict, List, Literal, Optional
from pydantic import (
    PostgresDsn,
    RedisDsn,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
        ),
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "FastAPI Production Boilerplate"
    ENVIRONMENT: Literal["dev", "stage", "prod"] = "dev"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "securepassword"
    POSTGRES_DB: str = "fastapi_db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        return f"postgresql+asyncpg://{info.data.get('POSTGRES_USER')}:{info.data.get('POSTGRES_PASSWORD')}@{info.data.get('POSTGRES_SERVER')}:{info.data.get('POSTGRES_PORT')}/{info.data.get('POSTGRES_DB')}"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        password_part = ""
        if info.data.get("REDIS_PASSWORD"):
            password_part = f":{info.data.get('REDIS_PASSWORD')}@"
        return f"redis://{password_part}{info.data.get('REDIS_HOST')}:{info.data.get('REDIS_PORT')}/0"

    # JWT Security
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Observability
    OTEL_SERVICE_NAME: str = "fastapi-boilerplate"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    PROMETHEUS_METRICS_PATH: str = "/metrics"


settings = Settings()
