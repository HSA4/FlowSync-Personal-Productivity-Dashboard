"""Integration API Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.models.integrations import Integration, IntegrationCreate, SyncStatus, WebhookEvent
from app.models.users import User, OAuthURL, OAuthCallback
from app.api.deps import require_active_user, standard_rate_limit
from app.db.database import db
from app.core.logging import get_logger
from app.core.config import settings
from app.services.integrations_oauth import TodoistOAuthService, GoogleCalendarOAuthService
from app.services.integrations import TodoistIntegration, GoogleCalendarIntegration
from app.services.webhooks import TodoistWebhookProcessor, GoogleCalendarWebhookProcessor

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = get_logger(__name__)


@router.get("", response_model=List[Integration])
async def get_integrations(
    current_user: User = Depends(require_active_user),
):
    """Get all integrations for the current user"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM integrations WHERE user_id = %s",
                (current_user.id,),
            )
            integrations = cursor.fetchall()
            return integrations
    except Exception as e:
        logger.error("Failed to get integrations", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve integrations")


@router.post("", response_model=Integration, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration: IntegrationCreate,
    current_user: User = Depends(require_active_user),
):
    """Create a new integration"""
    try:
        with db.get_cursor() as cursor:
            query = """
                INSERT INTO integrations (user_id, name, provider, access_token, enabled, settings)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            cursor.execute(
                query,
                (
                    current_user.id,
                    integration.name,
                    integration.provider,
                    integration.access_token,
                    integration.enabled,
                    integration.settings,
                ),
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error("Failed to create integration", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to create integration")


@router.get("/{integration_id}", response_model=Integration)
async def get_integration(
    integration_id: int,
    current_user: User = Depends(require_active_user),
):
    """Get a specific integration"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM integrations WHERE id = %s AND user_id = %s",
                (integration_id, current_user.id),
            )
            integration = cursor.fetchone()

            if not integration:
                raise HTTPException(status_code=404, detail="Integration not found")

            return integration
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get integration", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve integration")


@router.patch("/{integration_id}", response_model=Integration)
async def update_integration(
    integration_id: int,
    enabled: Optional[bool] = None,
    current_user: User = Depends(require_active_user),
):
    """Update an integration (enable/disable)"""
    try:
        with db.get_cursor() as cursor:
            # Check ownership
            cursor.execute(
                "SELECT id FROM integrations WHERE id = %s AND user_id = %s",
                (integration_id, current_user.id),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Integration not found")

            # Update
            cursor.execute(
                "UPDATE integrations SET enabled = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (enabled, integration_id),
            )

            cursor.execute("SELECT * FROM integrations WHERE id = %s", (integration_id,))
            return cursor.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update integration", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to update integration")


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(require_active_user),
):
    """Delete an integration"""
    try:
        with db.get_cursor() as cursor:
            # Check ownership
            cursor.execute(
                "SELECT id FROM integrations WHERE id = %s AND user_id = %s",
                (integration_id, current_user.id),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Integration not found")

            cursor.execute("DELETE FROM integrations WHERE id = %s", (integration_id,))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete integration", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to delete integration")


@router.post("/{integration_id}/sync", response_model=SyncStatus)
async def sync_integration(
    integration_id: int,
    current_user: User = Depends(require_active_user),
):
    """Trigger a sync for an integration"""
    try:
        # Get integration details
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM integrations WHERE id = %s AND user_id = %s",
                (integration_id, current_user.id),
            )
            integration = cursor.fetchone()

            if not integration:
                raise HTTPException(status_code=404, detail="Integration not found")

            if not integration.get("enabled"):
                raise HTTPException(status_code=400, detail="Integration is disabled")

            provider = integration.get("provider")
            access_token = integration.get("access_token")

            # Perform sync based on provider
            sync_result = {"status": "success", "items_synced": 0}

            if provider == "todoist":
                # Sync tasks from Todoist
                tasks = await TodoistIntegration.get_tasks(access_token)

                for task in tasks:
                    # Check if task already exists
                    cursor.execute(
                        "SELECT id FROM tasks WHERE user_id = %s AND external_id = %s",
                        (current_user.id, str(task.get("id"))),
                    )
                    existing = cursor.fetchone()

                    task_data = {
                        "user_id": current_user.id,
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

                sync_result["items_synced"] = len(tasks)

            elif provider == "google_calendar":
                # Sync events from Google Calendar
                start_date = datetime.utcnow()
                events = await GoogleCalendarIntegration.get_events(access_token, start_date=start_date)

                for event in events:
                    # Check if event already exists
                    cursor.execute(
                        "SELECT id FROM events WHERE user_id = %s AND external_id = %s",
                        (current_user.id, event.get("id")),
                    )
                    existing = cursor.fetchone()

                    # Parse event times
                    start_info = event.get("start", {})
                    end_info = event.get("end", {})

                    start_time = start_info.get("dateTime") or start_info.get("date")
                    end_time = end_info.get("dateTime") or end_info.get("date")

                    event_data = {
                        "user_id": current_user.id,
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

                sync_result["items_synced"] = len(events)

            # Update last sync time
            cursor.execute(
                "UPDATE integrations SET last_sync = CURRENT_TIMESTAMP WHERE id = %s",
                (integration_id,),
            )

        logger.info(
            "Integration sync completed",
            extra={"integration_id": integration_id, "provider": provider, **sync_result},
        )

        return SyncStatus(
            integration_id=integration_id,
            status="success",
            last_sync=datetime.utcnow(),
            next_sync=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to sync integration", extra={"error": str(e), "integration_id": integration_id})
        return SyncStatus(
            integration_id=integration_id,
            status="error",
            last_sync=None,
            next_sync=None,
            error_message=str(e),
        )


@router.post("/webhook/{provider}")
async def handle_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Handle webhook events from external services"""
    try:
        # Get raw payload and headers
        payload = await request.body()

        # Verify signature for Todoist
        if provider == "todoist":
            signature = request.headers.get(TodoistWebhookProcessor.SIGNATURE_HEADER, "")
            webhook_secret = settings.TODOIST_WEBHOOK_SECRET

            if webhook_secret:
                if not TodoistWebhookProcessor.verify_signature(payload, signature, webhook_secret):
                    logger.warning("Invalid Todoist webhook signature")
                    raise HTTPException(status_code=401, detail="Invalid signature")

            # Parse JSON payload
            try:
                event_data = json.loads(payload)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload")

            # Process in background
            background_tasks.add_task(
                TodoistWebhookProcessor.process_event,
                event_data=event_data,
            )

            logger.info(
                "Todoist webhook received",
                extra={"event_type": event_data.get("event_name"), "event_id": event_data.get("event_id")},
            )

            return {"status": "received", "message": "Webhook processing in background"}

        elif provider == "google-calendar":
            # Google Calendar webhooks are simple notifications
            try:
                event_data = json.loads(payload)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload")

            # Process in background
            background_tasks.add_task(
                GoogleCalendarWebhookProcessor.process_event,
                event_data=event_data,
            )

            logger.info(
                "Google Calendar webhook received",
                extra={"channel_id": event_data.get("channel_id")},
            )

            return {"status": "received", "message": "Webhook processing in background"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to handle webhook", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/{integration_id}/webhooks/register")
async def register_webhook(
    integration_id: int,
    current_user: User = Depends(require_active_user),
):
    """Register webhook for an integration"""
    try:
        # Get integration
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM integrations WHERE id = %s AND user_id = %s",
                (integration_id, current_user.id),
            )
            integration = cursor.fetchone()

            if not integration:
                raise HTTPException(status_code=404, detail="Integration not found")

            if not integration.get("enabled"):
                raise HTTPException(status_code=400, detail="Integration is disabled")

            provider = integration.get("provider")
            access_token = integration.get("access_token")

            # Build webhook URL
            webhook_url = f"{settings.API_BASE_URL}/api/integrations/webhook/{provider}"

            result = {"webhook_registered": False, "webhook_url": webhook_url}

            if provider == "todoist":
                # Register webhook with Todoist
                webhook_response = await TodoistIntegration.create_webhook(access_token, webhook_url)

                # Store webhook info in integration settings
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

                result["webhook_registered"] = True
                result["provider_webhook_id"] = webhook_response.get("id")

                logger.info("Registered Todoist webhook", extra={"integration_id": integration_id})

            elif provider == "google_calendar":
                # Set up watch for Google Calendar
                watch_response = await GoogleCalendarIntegration.watch_calendar(access_token, webhook_url)

                # Store watch info in integration settings
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

                result["webhook_registered"] = True
                result["channel_id"] = watch_response.get("id")
                result["expiration"] = watch_response.get("expiration")

                logger.info("Registered Google Calendar watch", extra={"integration_id": integration_id})

            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to register webhook", extra={"error": str(e), "integration_id": integration_id})
        raise HTTPException(status_code=500, detail="Failed to register webhook")


@router.get("/providers/available", response_model=List[dict])
async def get_available_providers():
    """Get list of available integration providers"""
    return [
        {
            "id": "todoist",
            "name": "Todoist",
            "description": "Sync tasks from Todoist",
            "features": ["tasks", "webhooks"],
            "auth_type": "oauth",
        },
        {
            "id": "google_calendar",
            "name": "Google Calendar",
            "description": "Sync events with Google Calendar",
            "features": ["events", "webhooks"],
            "auth_type": "oauth",
        },
        {
            "id": "gmail",
            "name": "Gmail",
            "description": "Get email summaries and task suggestions",
            "features": ["email", "summaries"],
            "auth_type": "oauth",
        },
    ]


# OAuth Endpoints for Integrations

@router.get("/oauth/{provider}", response_model=OAuthURL)
async def get_integration_oauth_url(
    provider: str,
    redirect_uri: Optional[str] = Query(None, description="Override the default redirect URI"),
    current_user: User = Depends(require_active_user),
):
    """Get OAuth authorization URL for an integration provider"""
    if provider == "todoist":
        if not settings.TODOIST_CLIENT_ID or not settings.TODOIST_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Todoist integration is not configured. Set TODOIST_CLIENT_ID and TODOIST_CLIENT_SECRET.",
            )
        url, state = TodoistOAuthService.get_authorization_url(
            redirect_uri or f"{settings.CORS_ORIGINS[0]}/integrations/callback" if settings.CORS_ORIGINS else "http://localhost:5173/integrations/callback"
        )
        return OAuthURL(url=url, state=state)

    elif provider == "google-calendar":
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google Calendar integration is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
            )
        url, state = GoogleCalendarOAuthService.get_authorization_url(
            redirect_uri or f"{settings.CORS_ORIGINS[0]}/integrations/callback" if settings.CORS_ORIGINS else "http://localhost:5173/integrations/callback"
        )
        return OAuthURL(url=url, state=state)

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown provider: {provider}",
        )


@router.post("/oauth/{provider}/callback", response_model=Integration)
async def integration_oauth_callback(
    provider: str,
    callback: OAuthCallback,
    current_user: User = Depends(require_active_user),
):
    """Handle OAuth callback for an integration provider"""
    try:
        redirect_uri = callback.redirect_uri or f"{settings.CORS_ORIGINS[0]}/integrations/callback" if settings.CORS_ORIGINS else "http://localhost:5173/integrations/callback"

        # Exchange code for token
        if provider == "todoist":
            token_data = await TodoistOAuthService.exchange_code_for_token(callback.code, redirect_uri)
            integration_name = "Todoist"
            provider_id = "todoist"

        elif provider == "google-calendar":
            token_data = await GoogleCalendarOAuthService.exchange_code_for_token(callback.code, redirect_uri)
            integration_name = "Google Calendar"
            provider_id = "google_calendar"

        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown provider: {provider}",
            )

        # Check if integration already exists
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM integrations WHERE user_id = %s AND provider = %s",
                (current_user.id, provider_id),
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing integration
                cursor.execute(
                    """
                    UPDATE integrations
                    SET access_token = %s, enabled = true, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (token_data.get("access_token"), existing["id"]),
                )
                cursor.execute("SELECT * FROM integrations WHERE id = %s", (existing["id"],))
                integration = cursor.fetchone()
                logger.info("Updated integration via OAuth", extra={"integration_id": existing["id"], "provider": provider})

            else:
                # Create new integration
                cursor.execute(
                    """
                    INSERT INTO integrations (user_id, name, provider, access_token, enabled, settings)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        current_user.id,
                        integration_name,
                        provider_id,
                        token_data.get("access_token"),
                        True,
                        {},
                    ),
                )
                integration = cursor.fetchone()
                logger.info("Created integration via OAuth", extra={"integration_id": integration["id"], "provider": provider})

        return integration

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Integration OAuth callback failed", extra={"error": str(e), "provider": provider})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete integration authorization",
        )


@router.get("/sync/status", response_model=Dict[str, Any])
async def get_sync_status(
    current_user: User = Depends(require_active_user),
):
    """Get sync status for all user integrations"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, provider, enabled, last_sync,
                       settings->>'webhook_registered' as webhook_registered,
                       settings->>'pending_sync' as pending_sync
                FROM integrations
                WHERE user_id = %s
                ORDER BY last_sync DESC NULLS LAST
                """,
                (current_user.id,),
            )
            integrations = cursor.fetchall()

        # Build status response
        integration_statuses = []
        for integration in integrations:
            status_info = {
                "id": integration["id"],
                "name": integration["name"],
                "provider": integration["provider"],
                "enabled": integration["enabled"],
                "last_sync": integration["last_sync"].isoformat() if integration.get("last_sync") else None,
                "webhook_registered": integration.get("webhook_registered") == "true",
                "pending_sync": integration.get("pending_sync") == "true",
                "status": "idle",
            }

            # Determine sync status
            if not integration["enabled"]:
                status_info["status"] = "disabled"
            elif integration.get("pending_sync") == "true":
                status_info["status"] = "pending_sync"
            elif integration.get("last_sync"):
                # Check if sync is recent (within 5 minutes)
                last_sync = integration["last_sync"]
                if (datetime.utcnow() - last_sync).total_seconds() < 300:
                    status_info["status"] = "synced"

            integration_statuses.append(status_info)

        return {
            "integrations": integration_statuses,
            "overall_status": _get_overall_sync_status(integration_statuses),
        }

    except Exception as e:
        logger.error("Failed to get sync status", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve sync status")


@router.get("/sync/stats", response_model=Dict[str, Any])
async def get_sync_stats(
    current_user: User = Depends(require_active_user),
):
    """Get sync statistics for monitoring"""
    try:
        from app.core.retry import sync_tracker

        stats = sync_tracker.get_all_stats()

        return {
            "operations": stats,
            "summary": {
                "total_operations": len(stats),
                "successful_operations": sum(1 for s in stats.values() if s["successes"] > 0),
            },
        }

    except Exception as e:
        logger.error("Failed to get sync stats", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve sync stats")


def _get_overall_sync_status(integrations: list) -> str:
    """Determine overall sync status from individual integration statuses"""
    if not integrations:
        return "no_integrations"

    enabled_count = sum(1 for i in integrations if i["enabled"])
    if enabled_count == 0:
        return "no_enabled_integrations"

    has_pending = any(i["pending_sync"] for i in integrations if i["enabled"])
    if has_pending:
        return "syncing"

    recently_synced = any(
        i.get("last_sync") and
        (datetime.utcnow() - datetime.fromisoformat(i["last_sync"])).total_seconds() < 300
        for i in integrations if i["enabled"]
    )
    if recently_synced:
        return "synced"

    return "idle"
