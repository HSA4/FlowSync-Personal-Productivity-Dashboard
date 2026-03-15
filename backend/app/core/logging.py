"""Structured Logging Configuration"""
import logging
import sys
from typing import Any
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Set up structured logging for the application"""
    logger = logging.getLogger("flowsync")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == "json":
        # JSON formatted logs for production
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            timestamp=True,
        )
    else:
        # Text formatted logs for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"flowsync.{name}")


# Initialize logging on import
logger = setup_logging()
