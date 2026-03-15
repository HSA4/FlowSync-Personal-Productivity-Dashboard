"""Webhook Processing Services"""
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import hmac

from app.core.config import settings
from app.core.errors import ValidationError, ExternalServiceError
from app.core.logging import get_logger
from app.db.database import db

logger = get_logger(__name__)


class WebhookProcessor:
    """Base class for processing webhook events"""

    @classmethod
    def verify_signature(
        cls,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify webhook signature"""
        if not secret:
            return True  # Skip verification if no secret configured

        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        # Check signature with and without prefix
        sig_to_check = signature.replace("sha256=", "").replace("SHA256=", "")
        return hmac.compare_digest(expected_signature, sig_to_check)

    @classmethod
    async def process_event(
        cls,
        provider: str,
        event_data: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process webhook event - to be implemented by subclasses"""
        raise NotImplementedError

    @classmethod
    def _find_user_by_integration(cls, provider: str, external_id: str) -> Optional[int]:
        """Find user ID by external integration ID"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id FROM integrations
                    WHERE provider = %s AND settings->>'external_user_id' = %s
                    LIMIT 1
                    """,
                    (provider, external_id),
                )
                result = cursor.fetchone()
                return result["user_id"] if result else None
        except Exception as e:
            logger.error("Failed to find user by integration", extra={"error": str(e)})
            return None


class TodoistWebhookProcessor(WebhookProcessor):
    """Process Todoist webhook events"""

    # Todoist webhook signature header
    SIGNATURE_HEADER = "X-Todoist-Hmac-SHA256"
    TODOIST_WEBHOOK_SECRET = None  # Set from config

    @classmethod
    async def process_event(
        cls,
        event_data: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process Todoist webhook event"""
        try:
            event_type = event_data.get("event_name")
            event_id = event_data.get("event_id")

            logger.info(
                "Processing Todoist webhook",
                extra={"event_type": event_type, "event_id": event_id},
            )

            result = {"processed": False, "action": None}

            # Find user by integration
            if not user_id:
                # Todoist webhooks include user_id in the event
                todoist_user_id = event_data.get("user_id")
                if todoist_user_id:
                    user_id = cls._find_user_by_integration("todoist", str(todoist_user_id))

            if not user_id:
                logger.warning("No user found for Todoist webhook")
                return result

            # Process different event types
            if event_type == "item:added":
                result = await cls._handle_item_added(event_data, user_id)

            elif event_type == "item:updated":
                result = await cls._handle_item_updated(event_data, user_id)

            elif event_type == "item:completed":
                result = await cls._handle_item_completed(event_data, user_id)

            elif event_type == "item:deleted":
                result = await cls._handle_item_deleted(event_data, user_id)

            else:
                logger.info(f"Unhandled Todoist event type: {event_type}")

            return result

        except Exception as e:
            logger.error("Failed to process Todoist webhook", extra={"error": str(e)})
            raise

    @classmethod
    async def _handle_item_added(cls, event_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Handle new task added in Todoist"""
        item_data = event_data.get("event_data", {})

        with db.get_cursor() as cursor:
            # Check if task already exists
            cursor.execute(
                "SELECT id FROM tasks WHERE user_id = %s AND external_id = %s",
                (user_id, str(item_data.get("id"))),
            )
            existing = cursor.fetchone()

            if existing:
                # Already exists, mark as processed
                return {"processed": True, "action": "already_exists"}

            # Create new task
            due_info = item_data.get("due", {})
            due_date = due_info.get("date") if due_info else None

            cursor.execute(
                """
                INSERT INTO tasks (user_id, title, description, status, priority, due_date, external_id, external_provider)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user_id,
                    item_data.get("content"),
                    item_data.get("description"),
                    "completed" if item_data.get("is_completed") else "pending",
                    item_data.get("priority", 1),
                    due_date,
                    str(item_data.get("id")),
                    "todoist",
                ),
            )

            logger.info(
                "Created task from Todoist webhook",
                extra={"task_id": cursor.fetchone()["id"], "todoist_id": item_data.get("id")},
            )

            return {"processed": True, "action": "created"}

    @classmethod
    async def _handle_item_updated(cls, event_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Handle task updated in Todoist"""
        item_data = event_data.get("event_data", {})

        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM tasks WHERE user_id = %s AND external_id = %s",
                (user_id, str(item_data.get("id"))),
            )
            existing = cursor.fetchone()

            if not existing:
                # Task doesn't exist locally, create it
                return await cls._handle_item_added(event_data, user_id)

            # Update existing task
            due_info = item_data.get("due", {})
            due_date = due_info.get("date") if due_info else None

            cursor.execute(
                """
                UPDATE tasks
                SET title = %s, description = %s, status = %s, priority = %s, due_date = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    item_data.get("content"),
                    item_data.get("description"),
                    "completed" if item_data.get("is_completed") else "pending",
                    item_data.get("priority", 1),
                    due_date,
                    existing["id"],
                ),
            )

            logger.info(
                "Updated task from Todoist webhook",
                extra={"task_id": existing["id"], "todoist_id": item_data.get("id")},
            )

            return {"processed": True, "action": "updated"}

    @classmethod
    async def _handle_item_completed(cls, event_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Handle task completed in Todoist"""
        item_data = event_data.get("event_data", {})

        with db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE tasks SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE user_id = %s AND external_id = %s",
                (user_id, str(item_data.get("id"))),
            )

            return {"processed": True, "action": "completed"}

    @classmethod
    async def _handle_item_deleted(cls, event_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Handle task deleted in Todoist"""
        item_data = event_data.get("event_data", {})

        with db.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM tasks WHERE user_id = %s AND external_id = %s",
                (user_id, str(item_data.get("id"))),
            )

            return {"processed": True, "action": "deleted"}


class GoogleCalendarWebhookProcessor(WebhookProcessor):
    """Process Google Calendar webhook events"""

    # Google uses channel ID matching
    @classmethod
    async def process_event(
        cls,
        event_data: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process Google Calendar notification

        Note: Google Calendar notifications don't include event details.
        They just signal that something changed. We need to sync.
        """
        try:
            # Google Calendar push notifications contain:
            # - channel_id: The ID we set when watching
            # - resource_id: Unique ID for this notification
            # - resource_state: "exists" (sync) or "not_exists" (deleted)

            channel_id = event_data.get("channel_id", "")
            resource_state = event_data.get("resource_state", "")

            logger.info(
                "Processing Google Calendar webhook",
                extra={"channel_id": channel_id, "resource_state": resource_state},
            )

            result = {"processed": False, "action": None}

            # Find integration by channel ID (stored in settings)
            if not user_id:
                user_id = cls._find_user_by_channel(channel_id)

            if not user_id:
                logger.warning("No user found for Google Calendar webhook")
                return result

            if resource_state == "not_exists":
                # Event was deleted
                result = await cls._handle_event_deleted(event_data, user_id)
            else:
                # Event was created or updated - trigger sync
                result = await cls._handle_event_changed(event_data, user_id)

            return result

        except Exception as e:
            logger.error("Failed to process Google Calendar webhook", extra={"error": str(e)})
            raise

    @classmethod
    def _find_user_by_channel(cls, channel_id: str) -> Optional[int]:
        """Find user ID by Google Calendar watch channel ID"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id FROM integrations
                    WHERE provider = 'google_calendar' AND settings->>'watch_channel_id' = %s
                    LIMIT 1
                    """,
                    (channel_id,),
                )
                result = cursor.fetchone()
                return result["user_id"] if result else None
        except Exception as e:
            logger.error("Failed to find user by channel", extra={"error": str(e)})
            return None

    @classmethod
    async def _handle_event_deleted(cls, event_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Handle event deleted in Google Calendar"""
        resource_id = event_data.get("resource_id", "")

        # Store the deletion notification
        with db.get_cursor() as cursor:
            # Find event by resource_id (sync ID)
            cursor.execute(
                """
                DELETE FROM events WHERE user_id = %s AND settings->>'sync_resource_id' = %s
                """,
                (user_id, resource_id),
            )

            return {"processed": True, "action": "deleted"}

    @classmethod
    async def _handle_event_changed(cls, event_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Handle event changed in Google Calendar

        Since Google notifications don't include event details,
        we just mark for sync and let the background sync handle it.
        """
        with db.get_cursor() as cursor:
            # Mark integration for sync
            cursor.execute(
                """
                UPDATE integrations
                SET settings = jsonb_set(settings, '{pending_sync}', 'true')
                WHERE user_id = %s AND provider = 'google_calendar'
                """,
                (user_id,),
            )

            return {"processed": True, "action": "marked_for_sync"}
