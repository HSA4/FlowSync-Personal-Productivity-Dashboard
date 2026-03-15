"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "FlowSync API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_BASE_URL: str = "http://localhost:8000"  # Base URL for webhook callbacks

    # Database (PostgreSQL)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DATABASE: str = "flowsync"
    POSTGRES_SSL_MODE: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full

    # Redis (Caching & Message Broker)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None  # Alternative to individual REDIS_* settings
    REDIS_MAX_CONNECTIONS: int = 50

    # Celery (Background Tasks)
    CELERY_BROKER_URL: Optional[str] = None  # Defaults to redis://localhost:6379/1
    CELERY_RESULT_BACKEND: Optional[str] = None  # Defaults to redis://localhost:6379/2
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000

    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # OAuth (Google)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    # External APIs
    TODOIST_CLIENT_ID: Optional[str] = None
    TODOIST_CLIENT_SECRET: Optional[str] = None
    TODOIST_API_KEY: Optional[str] = None
    TODOIST_WEBHOOK_SECRET: Optional[str] = None  # For webhook signature verification
    GOOGLE_CALENDAR_API_KEY: Optional[str] = None

    # AI / OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "anthropic/claude-3-haiku:beta"  # Default model
    OPENROUTER_SITE_URL: Optional[str] = None  # For OpenRouter ranking
    OPENROUTER_APP_NAME: Optional[str] = "FlowSync"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "text"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
