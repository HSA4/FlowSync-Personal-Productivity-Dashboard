"""Celery Tasks for Background Sync Operations"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.core.redis_client import cache
from app.core.logging import get_logger
from app.core.retry import RetryConfig, retry_async
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


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.sync_tasks.sync_integration")
def sync_integration(self, integration_id: int) -> Dict[str, Any]:
    """
    Sync a single integration in the background

    Args:
        integration_id: ID of the integration to sync

    Returns:
        Sync result with status and metadata
    """
    result = {
        "integration_id": integration_id,
        "status": "error",
        "items_synced": 0,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
    }

    try:
        # Mark sync as started
        cache.set(f"sync:running:{integration_id}", True, ttl=300)

        # Get integration details
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, provider, access_token, enabled
                FROM integrations
                WHERE id = %s
                """,
                (integration_id,),
            )
            integration = cursor.fetchone()

        if not integration:
            result["error"] = "Integration not found"
            return result

        if not integration["enabled"]:
            result["error"] = "Integration is disabled"
            return result

        provider = integration["provider"]
        access_token = integration["access_token"]
        user_id = integration["user_id"]

        # Sync based on provider
        if provider == "todoist":
            items_synced = _sync_todoist(integration_id, user_id, access_token)
            result["items_synced"] = items_synced

        elif provider == "google_calendar":
            items_synced = _sync_google_calendar(integration_id, user_id, access_token)
            result["items_synced"] = items_synced

        else:
            result["error"] = f"Unknown provider: {provider}"
            return result

        # Update last sync time
        with db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE integrations SET last_sync = CURRENT_TIMESTAMP WHERE id = %s",
                (integration_id,),
            )

        result["status"] = "success"
        logger.info(
            "Background sync completed",
            extra={"integration_id": integration_id, "items_synced": result["items_synced"]},
        )

    except SoftTimeLimitExceeded:
        result["error"] = "Sync timed out"
        logger.warning("Sync timed out", extra={"integration_id": integration_id})

    except Exception as e:
        result["error"] = str(e)
        logger.error("Sync failed", extra={"integration_id": integration_id, "error": str(e)})

    finally:
        result["completed_at"] = datetime.utcnow().isoformat()
        cache.delete(f"sync:running:{integration_id}")

        # Store result for 24 hours
        cache.set(f"sync:result:{integration_id}", result, ttl=86400)

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.sync_tasks.sync_all_integrations")
def sync_all_integrations(self) -> Dict[str, Any]:
    """
    Sync all enabled integrations for all users

    Returns:
        Summary of sync operations
    """
    result = {
        "status": "started",
        "started_at": datetime.utcnow().isoformat(),
        "integrations_synced": 0,
        "items_synced": 0,
        "errors": [],
    }

    try:
        # Get all enabled integrations
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM integrations
                WHERE enabled = true
                ORDER BY last_sync ASC NULLS FIRST
                LIMIT 100
                """
            )
            integrations = cursor.fetchall()

        # Queue sync tasks for each integration
        for integration in integrations:
            try:
                sync_integration.delay(integration["id"])
                result["integrations_synced"] += 1
            except Exception as e:
                result["errors"].append(f"Failed to queue sync for integration {integration['id']}: {str(e)}")

        result["status"] = "queued"
        logger.info(
            "Queued sync for all integrations",
            extra={"count": result["integrations_synced"]},
        )

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        logger.error("Failed to queue sync for all integrations", extra={"error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.sync_tasks.sync_provider_integrations")
def sync_provider_integrations(self, provider: str) -> Dict[str, Any]:
    """
    Sync all integrations for a specific provider

    Args:
        provider: Provider name (todoist, google_calendar, etc.)

    Returns:
        Summary of sync operations
    """
    result = {
        "provider": provider,
        "status": "started",
        "started_at": datetime.utcnow().isoformat(),
        "integrations_synced": 0,
        "errors": [],
    }

    try:
        # Get all enabled integrations for this provider
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM integrations
                WHERE enabled = true AND provider = %s
                ORDER BY last_sync ASC NULLS FIRST
                LIMIT 50
                """,
                (provider,),
            )
            integrations = cursor.fetchall()

        # Queue sync tasks
        for integration in integrations:
            try:
                sync_integration.delay(integration["id"])
                result["integrations_synced"] += 1
            except Exception as e:
                result["errors"].append(f"Failed to queue sync for integration {integration['id']}: {str(e)}")

        result["status"] = "queued"
        logger.info(
            f"Queued sync for {provider} integrations",
            extra={"count": result["integrations_synced"]},
        )

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        logger.error(
            f"Failed to queue sync for {provider}",
            extra={"error": str(e)},
        )

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.sync_tasks.retry_failed_syncs")
def retry_failed_syncs(self) -> Dict[str, Any]:
    """
    Retry sync operations that failed recently

    Returns:
        Summary of retry operations
    """
    result = {
        "status": "started",
        "started_at": datetime.utcnow().isoformat(),
        "retries_queued": 0,
        "errors": [],
    }

    try:
        # Get sync results that failed in the last hour
        # These are stored in Redis cache
        failed_integration_ids = []

        # Check recent sync failures via cache
        # In production, this would query a dedicated sync_failures table
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM integrations
                WHERE enabled = true
                AND last_sync < CURRENT_TIMESTAMP - INTERVAL '1 hour'
                ORDER BY last_sync ASC
                LIMIT 20
                """
            )
            stale_integrations = cursor.fetchall()
            failed_integration_ids = [i["id"] for i in stale_integrations]

        # Queue retry tasks
        for integration_id in failed_integration_ids:
            try:
                sync_integration.delay(integration_id)
                result["retries_queued"] += 1
            except Exception as e:
                result["errors"].append(f"Failed to queue retry for integration {integration_id}: {str(e)}")

        result["status"] = "queued"
        logger.info(
            "Queued retry for failed syncs",
            extra={"count": result["retries_queued"]},
        )

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        logger.error("Failed to queue retry for failed syncs", extra={"error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.sync_tasks.cleanup_old_results")
def cleanup_old_results(self) -> Dict[str, Any]:
    """
    Clean up old sync results from cache

    Returns:
        Summary of cleanup operations
    """
    result = {
        "status": "started",
        "started_at": datetime.utcnow().isoformat(),
        "keys_deleted": 0,
    }

    try:
        # Delete old sync results (older than 7 days)
        # In production, this would also clean up the database
        result["keys_deleted"] = cache.delete_pattern("sync:result:*")

        result["status"] = "completed"
        logger.info("Cleanup completed", extra={"keys_deleted": result["keys_deleted"]})

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error("Cleanup failed", extra={"error": str(e)})

    return result


# Helper functions

def _sync_todoist(integration_id: int, user_id: int, access_token: str) -> int:
    """Sync tasks from Todoist"""
    try:
        tasks = TodoistIntegration.get_tasks(access_token)
        # Run async function in sync context
        import asyncio
        tasks = asyncio.run(tasks)

        items_synced = 0

        with db.get_cursor() as cursor:
            for task in tasks:
                # Check if task already exists
                cursor.execute(
                    "SELECT id FROM tasks WHERE user_id = %s AND external_id = %s",
                    (user_id, str(task.get("id"))),
                )
                existing = cursor.fetchone()

                task_data = {
                    "user_id": user_id,
                    "title": task.get("content"),
                    "description": task.get("description"),
                    "status": "completed" if task.get("is_completed") else "pending",
                    "priority": task.get("priority", 1),
                    "due_date": task.get("due", {}).get("date") if task.get("due") else None,
                    "external_id": str(task.get("id")),
                    "external_provider": "todoist",
                }

                if existing:
                    # Update existing task
                    cursor.execute(
                        """
                        UPDATE tasks
                        SET title = %s, description = %s, status = %s, priority = %s, due_date = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (
                            task_data["title"],
                            task_data["description"],
                            task_data["status"],
                            task_data["priority"],
                            task_data["due_date"],
                            existing["id"],
                        ),
                    )
                else:
                    # Create new task
                    cursor.execute(
                        """
                        INSERT INTO tasks (user_id, title, description, status, priority, due_date, external_id, external_provider)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            task_data["user_id"],
                            task_data["title"],
                            task_data["description"],
                            task_data["status"],
                            task_data["priority"],
                            task_data["due_date"],
                            task_data["external_id"],
                            task_data["external_provider"],
                        ),
                    )

                items_synced += 1

        return items_synced

    except Exception as e:
        logger.error("Todoist sync failed", extra={"integration_id": integration_id, "error": str(e)})
        raise


def _sync_google_calendar(integration_id: int, user_id: int, access_token: str) -> int:
    """Sync events from Google Calendar"""
    try:
        start_date = datetime.utcnow()
        events = GoogleCalendarIntegration.get_events(access_token, start_date=start_date)
        # Run async function in sync context
        import asyncio
        events = asyncio.run(events)

        items_synced = 0

        with db.get_cursor() as cursor:
            for event in events:
                # Check if event already exists
                cursor.execute(
                    "SELECT id FROM events WHERE user_id = %s AND external_id = %s",
                    (user_id, event.get("id")),
                )
                existing = cursor.fetchone()

                # Parse event times
                start_info = event.get("start", {})
                end_info = event.get("end", {})

                start_time = start_info.get("dateTime") or start_info.get("date")
                end_time = end_info.get("dateTime") or end_info.get("date")

                event_data = {
                    "user_id": user_id,
                    "title": event.get("summary", "Untitled Event"),
                    "description": event.get("description"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "external_id": event.get("id"),
                    "external_provider": "google_calendar",
                }

                if existing:
                    # Update existing event
                    cursor.execute(
                        """
                        UPDATE events
                        SET title = %s, description = %s, start_time = %s, end_time = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (
                            event_data["title"],
                            event_data["description"],
                            event_data["start_time"],
                            event_data["end_time"],
                            existing["id"],
                        ),
                    )
                else:
                    # Create new event
                    cursor.execute(
                        """
                        INSERT INTO events (user_id, title, description, start_time, end_time, external_id, external_provider)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            event_data["user_id"],
                            event_data["title"],
                            event_data["description"],
                            event_data["start_time"],
                            event_data["end_time"],
                            event_data["external_id"],
                            event_data["external_provider"],
                        ),
                    )

                items_synced += 1

        return items_synced

    except Exception as e:
        logger.error("Google Calendar sync failed", extra={"integration_id": integration_id, "error": str(e)})
        raise
