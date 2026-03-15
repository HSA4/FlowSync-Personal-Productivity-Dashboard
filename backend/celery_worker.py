"""Celery Worker - Standalone entry point for running Celery workers"""
from celery.bin import worker
from app.core.celery_app import celery_app
from app.core.logging import setup_logging
from app.core.config import settings

# Set up logging
logger = setup_logging()


def main():
    """Start the Celery worker"""
    logger.info("Starting Celery worker")

    worker = worker.worker(
        app=celery_app,
        broker=getattr(celery_app, 'broker_url', None),
        loglevel=settings.LOG_LEVEL.lower(),
        concurrency=4,  # Number of worker processes
        max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
        prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    )

    worker.start()


if __name__ == "__main__":
    main()
