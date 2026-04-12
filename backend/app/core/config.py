"""Application Configuration"""
from dotenv import load_dotenv
import os
from typing import Optional, List

# Load environment variables from .env file
load_dotenv(override=True)

class Settings:
    """Application settings - Simple class with environment variables"""

    def __init__(self):
        # Application
        self.APP_NAME = os.getenv("APP_NAME", "FlowSync API")
        self.APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")

        # Server
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
        self.API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

        # Database (PostgreSQL)
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        self.POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "flowsync")
        self.POSTGRES_SSL_MODE = os.getenv("POSTGRES_SSL_MODE", "prefer")

        # Redis
        self.REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_DB = int(os.getenv("REDIS_DB", "0"))
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
        self.REDIS_URL = os.getenv("REDIS_URL", None)
        self.REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))

        # Celery
        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
        self.CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
        self.CELERY_TASK_TRACK_STARTED = os.getenv("CELERY_TASK_TRACK_STARTED", "True").lower() == "true"
        self.CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "1800"))
        self.CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "1500"))
        self.CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "4"))
        self.CELERY_WORKER_MAX_TASKS_PER_CHILD = int(os.getenv("CELERY_WORKER_MAX_TASKS_PER_CHILD", "1000"))

        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-use-openssl-rand-hex-32")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

        # CORS
        cors_origins_env = os.getenv("CORS_ORIGINS", "")
        if cors_origins_env:
            self.CORS_ORIGINS = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        else:
            self.CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000", "http://5.189.181.109:8080"]

        # OAuth (Google)
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
        self.GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

        # External APIs
        self.TODOIST_CLIENT_ID = os.getenv("TODOIST_CLIENT_ID")
        self.TODOIST_CLIENT_SECRET = os.getenv("TODOIST_CLIENT_SECRET")
        self.TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
        self.TODOIST_WEBHOOK_SECRET = os.getenv("TODOIST_WEBHOOK_SECRET")
        self.GOOGLE_CALENDAR_API_KEY = os.getenv("GOOGLE_CALENDAR_API_KEY")

        # AI / OpenRouter
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        self.OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku:beta")
        self.OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL")
        self.OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "FlowSync")

        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json")


# Global settings instance
settings = Settings()
