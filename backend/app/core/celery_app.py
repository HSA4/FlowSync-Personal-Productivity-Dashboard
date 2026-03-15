"""Celery Application for Background Tasks"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Build broker and backend URLs
def get_broker_url() -> str:
    """Get Celery broker URL"""
    if settings.CELERY_BROKER_URL:
        return settings.CELERY_BROKER_URL

    if settings.REDIS_URL:
        return f"{settings.REDIS_URL}/1"

    redis_auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{redis_auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"


def get_result_backend() -> str:
    """Get Celery result backend URL"""
    if settings.CELERY_RESULT_BACKEND:
        return settings.CELERY_RESULT_BACKEND

    if settings.REDIS_URL:
        return f"{settings.REDIS_URL}/2"

    redis_auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{redis_auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/2"


# Create Celery app
celery_app = Celery(
    "flowsync",
    broker=get_broker_url(),
    backend=get_result_backend(),
    include=[
        "app.tasks.sync_tasks",
        "app.tasks.integration_tasks",
        "app.tasks.ai_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_acks_late=True,  # Acknowledge task after execution
    task_reject_on_worker_lost=True,  # Re-queue task if worker dies
    task_send_sent_event=True,  # Track sent events
    # Worker settings
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Use extended result format
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Beat scheduler settings
    beat_schedule={
        # Sync all enabled integrations every 15 minutes
        "sync-all-integrations": {
            "task": "app.tasks.sync_tasks.sync_all_integrations",
            "schedule": 15.0,  # Every 15 minutes
        },
        # Sync Google Calendar every 30 minutes
        "sync-google-calendar": {
            "task": "app.tasks.sync_tasks.sync_provider_integrations",
            "schedule": 30.0,  # Every 30 minutes
            "kwargs": {"provider": "google_calendar"},
        },
        # Sync Todoist every 20 minutes
        "sync-todoist": {
            "task": "app.tasks.sync_tasks.sync_provider_integrations",
            "schedule": 20.0,  # Every 20 minutes
            "kwargs": {"provider": "todoist"},
        },
        # Cleanup old task results daily at 2 AM
        "cleanup-old-results": {
            "task": "app.tasks.sync_tasks.cleanup_old_results",
            "schedule": crontab(hour=2, minute=0),
        },
        # Retry failed syncs every hour
        "retry-failed-syncs": {
            "task": "app.tasks.sync_tasks.retry_failed_syncs",
            "schedule": crontab(minute=0),  # Every hour
        },
    },
)


def get_celery_app() -> Celery:
    """Get the Celery application instance"""
    return celery_app
