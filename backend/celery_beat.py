"""Celery Beat Scheduler - Standalone entry point for running the Celery beat scheduler"""
from celery.beat import Beat
from app.core.celery_app import celery_app
from app.core.logging import setup_logging
from app.core.config import settings

# Set up logging
logger = setup_logging()


def main():
    """Start the Celery beat scheduler"""
    logger.info("Starting Celery beat scheduler")

    beat = Beat(
        app=celery_app,
        loglevel=settings.LOG_LEVEL.lower(),
        scheduler="celery.beat.PersistentScheduler",  # Use persistent scheduler
        pidfile="celerybeat.pid",
        schedulefile="celerybeat-schedule",  # Store schedule state
    )

    beat.start()


if __name__ == "__main__":
    main()
