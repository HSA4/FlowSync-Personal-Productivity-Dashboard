"""Integration API Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional

from app.models.integrations import Integration, IntegrationCreate, SyncStatus, WebhookEvent
from app.models.users import User
from app.api.deps import require_active_user, standard_rate_limit
from app.db.database import db
from app.core.logging import get_logger

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

            cursor.execute("SELECT * FROM integrations WHERE id = %s", (cursor.lastrowid,))
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
        # TODO: Implement actual sync logic
        return SyncStatus(
            integration_id=integration_id,
            status="pending",
            last_sync=None,
            next_sync=None,
        )
    except Exception as e:
        logger.error("Failed to sync integration", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to sync integration")


@router.post("/webhook/{provider}")
async def handle_webhook(
    provider: str,
    event: WebhookEvent,
):
    """Handle webhook events from external services"""
    try:
        logger.info(
            "Received webhook event",
            extra={
                "provider": provider,
                "event_type": event.event_type,
                "event_id": event.event_id,
            },
        )

        # TODO: Process webhook event and update local data

        return {"status": "received"}
    except Exception as e:
        logger.error("Failed to handle webhook", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to process webhook")


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
