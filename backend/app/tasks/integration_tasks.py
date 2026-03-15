"""Celery Tasks for Integration Operations"""
from datetime import datetime
from typing import Dict, Any

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.core.redis_client import cache
from app.core.logging import get_logger
from app.db.database import db
from app.services.integrations import TodoistIntegration, GoogleCalendarIntegration

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Base task with database connection management"""

    _db = None

    def after_return(self, *args, **kwargs):
        """Close database connection after task completes"""
        if self._db:
            self._db.close_all()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.integration_tasks.push_task_to_todoist")
def push_task_to_todoist(
    self,
    user_id: int,
    task_id: int,
    title: str,
    description: str = None,
    due_date: str = None,
    priority: int = 1,
) -> Dict[str, Any]:
    """
    Push a task to Todoist in the background

    Returns:
        Result with external task ID
    """
    result = {
        "task_id": task_id,
        "status": "error",
        "external_id": None,
        "error": None,
    }

    try:
        # Get user's Todoist integration
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, access_token FROM integrations
                WHERE user_id = %s AND provider = 'todoist' AND enabled = true
                LIMIT 1
                """,
                (user_id,),
            )
            integration = cursor.fetchone()

        if not integration:
            result["error"] = "No enabled Todoist integration found"
            return result

        # Create task in Todoist
        import asyncio
        todoist_task = asyncio.run(
            TodoistIntegration.create_task(
                access_token=integration["access_token"],
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
            )
        )

        # Update task with external ID
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE tasks
                SET external_id = %s, external_provider = 'todoist'
                WHERE id = %s
                """,
                (str(todoist_task["id"]), task_id),
            )

        result["status"] = "success"
        result["external_id"] = str(todoist_task["id"])

        logger.info(
            "Pushed task to Todoist",
            extra={"task_id": task_id, "todoist_id": todoist_task["id"]},
        )

    except SoftTimeLimitExceeded:
        result["error"] = "Operation timed out"
        logger.warning("Push to Todoist timed out", extra={"task_id": task_id})

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to push task to Todoist", extra={"task_id": task_id, "error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.integration_tasks.update_todoist_task")
def update_todoist_task(
    self,
    user_id: int,
    external_id: str,
    title: str = None,
    completed: bool = None,
) -> Dict[str, Any]:
    """
    Update a task in Todoist in the background

    Returns:
        Result status
    """
    result = {
        "external_id": external_id,
        "status": "error",
        "error": None,
    }

    try:
        # Get user's Todoist integration
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT access_token FROM integrations
                WHERE user_id = %s AND provider = 'todoist' AND enabled = true
                LIMIT 1
                """,
                (user_id,),
            )
            integration = cursor.fetchone()

        if not integration:
            result["error"] = "No enabled Todoist integration found"
            return result

        # Update task in Todoist
        import asyncio
        asyncio.run(
            TodoistIntegration.update_task(
                access_token=integration["access_token"],
                task_id=external_id,
                title=title,
                completed=completed,
            )
        )

        result["status"] = "success"

        logger.info(
            "Updated task in Todoist",
            extra={"external_id": external_id},
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to update task in Todoist", extra={"external_id": external_id, "error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.integration_tasks.delete_todoist_task")
def delete_todoist_task(
    self,
    user_id: int,
    external_id: str,
) -> Dict[str, Any]:
    """
    Delete a task from Todoist in the background

    Returns:
        Result status
    """
    result = {
        "external_id": external_id,
        "status": "error",
        "error": None,
    }

    try:
        # Get user's Todoist integration
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT access_token FROM integrations
                WHERE user_id = %s AND provider = 'todoist' AND enabled = true
                LIMIT 1
                """,
                (user_id,),
            )
            integration = cursor.fetchone()

        if not integration:
            result["error"] = "No enabled Todoist integration found"
            return result

        # Delete task from Todoist
        import asyncio
        asyncio.run(
            TodoistIntegration.delete_task(
                access_token=integration["access_token"],
                task_id=external_id,
            )
        )

        result["status"] = "success"

        logger.info(
            "Deleted task from Todoist",
            extra={"external_id": external_id},
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to delete task from Todoist", extra={"external_id": external_id, "error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.integration_tasks.push_event_to_google_calendar")
def push_event_to_google_calendar(
    self,
    user_id: int,
    event_id: int,
    title: str,
    start_time: str,
    end_time: str,
    description: str = None,
) -> Dict[str, Any]:
    """
    Push an event to Google Calendar in the background

    Returns:
        Result with external event ID
    """
    result = {
        "event_id": event_id,
        "status": "error",
        "external_id": None,
        "error": None,
    }

    try:
        # Get user's Google Calendar integration
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, access_token FROM integrations
                WHERE user_id = %s AND provider = 'google_calendar' AND enabled = true
                LIMIT 1
                """,
                (user_id,),
            )
            integration = cursor.fetchone()

        if not integration:
            result["error"] = "No enabled Google Calendar integration found"
            return result

        # Create event in Google Calendar
        from datetime import datetime
        import asyncio

        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        gcal_event = asyncio.run(
            GoogleCalendarIntegration.create_event(
                access_token=integration["access_token"],
                title=title,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
            )
        )

        # Update event with external ID
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE events
                SET external_id = %s, external_provider = 'google_calendar'
                WHERE id = %s
                """,
                (gcal_event["id"], event_id),
            )

        result["status"] = "success"
        result["external_id"] = gcal_event["id"]

        logger.info(
            "Pushed event to Google Calendar",
            extra={"event_id": event_id, "gcal_id": gcal_event["id"]},
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to push event to Google Calendar", extra={"event_id": event_id, "error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.integration_tasks.register_webhook")
def register_webhook(
    self,
    integration_id: int,
    webhook_url: str,
) -> Dict[str, Any]:
    """
    Register webhook for an integration in the background

    Returns:
        Result with webhook registration status
    """
    result = {
        "integration_id": integration_id,
        "status": "error",
        "error": None,
    }

    try:
        # Get integration details
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, provider, access_token FROM integrations
                WHERE id = %s AND enabled = true
                """,
                (integration_id,),
            )
            integration = cursor.fetchone()

        if not integration:
            result["error"] = "Integration not found or disabled"
            return result

        provider = integration["provider"]
        access_token = integration["access_token"]

        if provider == "todoist":
            # Register webhook with Todoist
            import asyncio
            webhook_response = asyncio.run(
                TodoistIntegration.create_webhook(access_token, webhook_url)
            )

            # Store webhook info
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE integrations
                    SET settings = jsonb_set(
                        COALESCE(settings, '{}'),
                        '{webhook_registered}',
                        'true'
                    ) || jsonb_build_object('webhook_url', %s)
                    WHERE id = %s
                    """,
                    (webhook_url, integration_id),
                )

            result["status"] = "success"
            result["provider_webhook_id"] = webhook_response.get("id")

        elif provider == "google_calendar":
            # Set up watch for Google Calendar
            import asyncio
            watch_response = asyncio.run(
                GoogleCalendarIntegration.watch_calendar(access_token, webhook_url)
            )

            # Store watch info
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE integrations
                    SET settings = jsonb_set(
                        COALESCE(settings, '{}'),
                        '{watch_channel_id}',
                        %s
                    ) || jsonb_build_object('webhook_url', %s, 'watch_resource_id', %s, 'watch_expiration', %s)
                    WHERE id = %s
                    """,
                    (
                        watch_response.get("id"),
                        webhook_url,
                        watch_response.get("resourceId"),
                        watch_response.get("expiration"),
                        integration_id,
                    ),
                )

            result["status"] = "success"
            result["channel_id"] = watch_response.get("id")
            result["expiration"] = watch_response.get("expiration")

        logger.info(
            "Registered webhook",
            extra={"integration_id": integration_id, "provider": provider},
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to register webhook", extra={"integration_id": integration_id, "error": str(e)})

    return result
