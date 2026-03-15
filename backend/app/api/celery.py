"""Celery Task Queue API Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.users import User
from app.api.deps import require_active_user
from app.core.celery_app import celery_app
from app.core.redis_client import cache
from app.core.logging import get_logger
from app.tasks.sync_tasks import (
    sync_integration,
    sync_all_integrations,
    sync_provider_integrations,
    retry_failed_syncs,
    cleanup_old_results,
)
from app.tasks.integration_tasks import (
    push_task_to_todoist,
    update_todoist_task,
    delete_todoist_task,
    register_webhook,
)
from app.tasks.ai_tasks import (
    generate_daily_digest,
    prioritize_tasks,
    suggest_tasks,
    smart_time_blocking,
)

router = APIRouter(prefix="/tasks", tags=["celery-tasks"])
logger = get_logger(__name__)


@router.get("/status")
async def get_celery_status(
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Get Celery worker status"""
    try:
        # Get active workers
        inspector = celery_app.control.inspect()
        active = inspector.active() if inspector else {}
        scheduled = inspector.scheduled() if inspector else {}
        reserved = inspector.reserved() if inspector else {}

        # Count tasks
        active_count = sum(len(tasks) for tasks in active.values()) if active else 0
        scheduled_count = sum(len(tasks) for tasks in scheduled.values()) if scheduled else 0
        reserved_count = sum(len(tasks) for tasks in reserved.values()) if reserved else 0

        # Get worker info
        workers = []
        if active:
            for worker_name, tasks in active.items():
                workers.append({
                    "name": worker_name,
                    "active_tasks": len(tasks),
                })

        return {
            "status": "running" if workers else "no_workers",
            "workers": workers,
            "active_tasks": active_count,
            "scheduled_tasks": scheduled_count,
            "reserved_tasks": reserved_count,
        }

    except Exception as e:
        logger.error("Failed to get Celery status", extra={"error": str(e)})
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/sync/running")
async def get_running_syncs(
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Get currently running sync tasks"""
    try:
        # Get active sync tasks
        inspector = celery_app.control.inspect()
        active = inspector.active() if inspector else {}

        running_syncs = []
        if active:
            for worker_name, tasks in active.items():
                for task in tasks:
                    if "sync" in task.get("name", "").lower():
                        running_syncs.append({
                            "task_id": task["id"],
                            "task_name": task["name"],
                            "worker": worker_name,
                            "args": task.get("args", []),
                        })

        return {
            "running_syncs": running_syncs,
            "count": len(running_syncs),
        }

    except Exception as e:
        logger.error("Failed to get running syncs", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to get running syncs")


@router.post("/sync/{integration_id}")
async def trigger_sync(
    integration_id: int,
    background: bool = Query(True, description="Run in background"),
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Trigger a sync for an integration"""
    try:
        # Verify integration ownership
        from app.db.database import db
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM integrations WHERE id = %s AND user_id = %s",
                (integration_id, current_user.id),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Integration not found")

        if background:
            # Trigger async task
            task = sync_integration.delay(integration_id)
            return {
                "status": "queued",
                "task_id": task.id,
                "integration_id": integration_id,
            }
        else:
            # Run synchronously
            result = sync_integration(integration_id)
            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to trigger sync", extra={"error": str(e), "integration_id": integration_id})
        raise HTTPException(status_code=500, detail="Failed to trigger sync")


@router.get("/sync/result/{integration_id}")
async def get_sync_result(
    integration_id: int,
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Get the result of a sync operation"""
    try:
        # Check cache for recent sync result
        result = cache.get(f"sync:result:{integration_id}")

        if result:
            return result

        # Check if sync is currently running
        running = cache.get(f"sync:running:{integration_id}")

        return {
            "status": "running" if running else "no_recent_sync",
            "integration_id": integration_id,
        }

    except Exception as e:
        logger.error("Failed to get sync result", extra={"error": str(e), "integration_id": integration_id})
        raise HTTPException(status_code=500, detail="Failed to get sync result")


@router.post("/sync/all")
async def trigger_sync_all(
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Trigger sync for all integrations"""
    try:
        task = sync_all_integrations.delay()
        return {
            "status": "queued",
            "task_id": task.id,
        }

    except Exception as e:
        logger.error("Failed to trigger sync all", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to trigger sync all")


@router.post("/sync/provider/{provider}")
async def trigger_provider_sync(
    provider: str,
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Trigger sync for a specific provider"""
    try:
        if provider not in ["todoist", "google_calendar"]:
            raise HTTPException(status_code=400, detail="Invalid provider")

        task = sync_provider_integrations.delay(provider)
        return {
            "status": "queued",
            "task_id": task.id,
            "provider": provider,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to trigger provider sync", extra={"error": str(e), "provider": provider})
        raise HTTPException(status_code=500, detail="Failed to trigger provider sync")


@router.post("/sync/retry-failed")
async def trigger_retry_failed(
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Trigger retry for failed syncs"""
    try:
        task = retry_failed_syncs.delay()
        return {
            "status": "queued",
            "task_id": task.id,
        }

    except Exception as e:
        logger.error("Failed to trigger retry failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to trigger retry failed")


@router.post("/ai/daily-digest")
async def trigger_daily_digest(
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Trigger daily digest generation"""
    try:
        # Check cache first
        cached = cache.get(f"daily_digest:{current_user.id}")
        if cached:
            return {
                "status": "cached",
                "digest": cached,
            }

        task = generate_daily_digest.delay(current_user.id)
        return {
            "status": "queued",
            "task_id": task.id,
        }

    except Exception as e:
        logger.error("Failed to trigger daily digest", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to trigger daily digest")


@router.post("/ai/prioritize")
async def trigger_prioritize(
    task_ids: Optional[List[int]] = None,
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Trigger task prioritization"""
    try:
        task = prioritize_tasks.delay(current_user.id, task_ids)
        return {
            "status": "queued",
            "task_id": task.id,
        }

    except Exception as e:
        logger.error("Failed to trigger prioritize", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to trigger prioritize")


@router.post("/ai/suggest")
async def trigger_suggest(
    max_suggestions: int = Query(5, ge=1, le=10),
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Trigger task suggestions"""
    try:
        task = suggest_tasks.delay(current_user.id, max_suggestions)
        return {
            "status": "queued",
            "task_id": task.id,
        }

    except Exception as e:
        logger.error("Failed to trigger suggest", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to trigger suggest")


@router.get("/task/{task_id}/result")
async def get_task_result(
    task_id: str,
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Get the result of a Celery task"""
    try:
        result = celery_app.AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": result.state,
            "result": result.result if result.ready() else None,
            "ready": result.ready(),
        }

    except Exception as e:
        logger.error("Failed to get task result", extra={"error": str(e), "task_id": task_id})
        raise HTTPException(status_code=500, detail="Failed to get task result")


@router.post("/task/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Cancel a Celery task"""
    try:
        result = celery_app.AsyncResult(task_id)

        if not result.ready():
            result.revoke(terminate=True)
            return {
                "task_id": task_id,
                "status": "cancelled",
            }
        else:
            return {
                "task_id": task_id,
                "status": "already_completed",
            }

    except Exception as e:
        logger.error("Failed to cancel task", extra={"error": str(e), "task_id": task_id})
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/stats")
async def get_queue_stats(
    current_user: User = Depends(require_active_user),
) -> Dict[str, Any]:
    """Get queue statistics"""
    try:
        inspector = celery_app.control.inspect()

        # Get various stats
        stats = {
            "registered_tasks": list(celery_app.tasks.keys()),
            "active_tasks": inspector.active() or {},
            "scheduled_tasks": inspector.scheduled() or {},
            "reserved_tasks": inspector.reserved() or {},
        }

        # Count active tasks
        active_count = sum(len(tasks) for tasks in stats["active_tasks"].values())
        scheduled_count = sum(len(tasks) for tasks in stats["scheduled_tasks"].values())
        reserved_count = sum(len(tasks) for tasks in stats["reserved_tasks"].values())

        return {
            "active_tasks": active_count,
            "scheduled_tasks": scheduled_count,
            "reserved_tasks": reserved_count,
            "registered_tasks_count": len(stats["registered_tasks"]),
            "workers": list(stats["active_tasks"].keys()) if stats["active_tasks"] else [],
        }

    except Exception as e:
        logger.error("Failed to get queue stats", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to get queue stats")
