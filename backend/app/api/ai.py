"""AI API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.ai import OpenRouterService
from app.models.users import User
from app.api.deps import require_active_user, standard_rate_limit
from app.db.database import db
from app.core.logging import get_logger
from app.core.errors import ExternalServiceError

router = APIRouter(prefix="/ai", tags=["ai"])
logger = get_logger(__name__)


# Request/Response Models
class TaskParseRequest(BaseModel):
    """Request model for parsing tasks from natural language"""
    text: str = Field(..., min_length=1, max_length=500, description="Natural language task description")


class TaskParseResponse(BaseModel):
    """Response model for parsed task"""
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: int = Field(default=2, ge=1, le=4)
    estimated_duration: Optional[int] = None


class TaskSuggestionRequest(BaseModel):
    """Request model for generating task suggestions"""
    max_suggestions: int = Field(default=5, ge=1, le=10)


class TaskSuggestion(BaseModel):
    """Individual task suggestion"""
    title: str
    reason: str
    priority: int = Field(default=2, ge=1, le=4)


class TaskSuggestionResponse(BaseModel):
    """Response model for task suggestions"""
    suggestions: List[TaskSuggestion]


class TaskPrioritizeRequest(BaseModel):
    """Request model for prioritizing tasks"""
    task_ids: Optional[List[int]] = Field(None, description="Specific task IDs to prioritize (empty = all)")


class PrioritizedTask(BaseModel):
    """Model for a prioritized task"""
    id: int
    title: str
    current_priority: int
    new_priority: int


# Endpoints

@router.post("/parse-task", response_model=TaskParseResponse)
async def parse_task_from_text(
    request: TaskParseRequest,
    current_user: User = Depends(require_active_user),
):
    """
    Parse natural language text into a structured task

    Examples:
    - "Schedule meeting tomorrow at 2pm" -> title, due_date
    - "Urgent: Submit report by Friday" -> title, due_date, priority=4
    - "Call mom about birthday party" -> title, estimated_duration
    """
    try:
        result = await OpenRouterService.parse_task_from_text(request.text)

        logger.info(
            "Task parsed from natural language",
            extra={"user_id": current_user.id, "original_text": request.text[:50]},
        )

        return TaskParseResponse(**result)

    except ExternalServiceError as e:
        logger.error("Failed to parse task via AI", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error parsing task", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse task",
        )


@router.post("/suggest-tasks", response_model=TaskSuggestionResponse)
async def generate_task_suggestions(
    request: TaskSuggestionRequest,
    current_user: User = Depends(require_active_user),
):
    """
    Generate task suggestions based on user's current context

    Analyzes:
    - Current pending tasks
    - Upcoming calendar events
    - Recently completed tasks
    - User's productivity patterns
    """
    try:
        # Gather user context
        with db.get_cursor() as cursor:
            # Get pending tasks
            cursor.execute(
                """
                SELECT id, title, description, priority, due_date
                FROM tasks
                WHERE user_id = %s AND status != 'completed'
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (current_user.id,),
            )
            tasks = cursor.fetchall()

            # Get upcoming events
            cursor.execute(
                """
                SELECT id, title, start_time
                FROM events
                WHERE user_id = %s AND start_time > CURRENT_TIMESTAMP
                ORDER BY start_time ASC
                LIMIT 5
                """,
                (current_user.id,),
            )
            events = cursor.fetchall()

            # Get recently completed tasks
            cursor.execute(
                """
                SELECT title, completed_at
                FROM (
                    SELECT title, updated_at as completed_at
                    FROM tasks
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY updated_at DESC
                    LIMIT 5
                ) recent
                """,
                (current_user.id,),
            )
            completed = cursor.fetchall()

        user_context = {
            "tasks": [dict(t) for t in tasks],
            "events": [dict(e) for e in events],
            "completed": [dict(c) for c in completed],
        }

        suggestions = await OpenRouterService.generate_task_suggestions(user_context)

        logger.info(
            "Generated task suggestions",
            extra={"user_id": current_user.id, "count": len(suggestions)},
        )

        return TaskSuggestionResponse(
            suggestions=[TaskSuggestion(**s) for s in suggestions[: request.max_suggestions]]
        )

    except ExternalServiceError as e:
        logger.error("Failed to generate suggestions via AI", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error generating suggestions", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        )


@router.post("/prioritize-tasks", response_model=List[PrioritizedTask])
async def prioritize_tasks(
    request: TaskPrioritizeRequest,
    current_user: User = Depends(require_active_user),
):
    """
    Re-prioritize tasks using AI analysis

    Considers:
    - Due dates and deadlines
    - Task dependencies
    - Importance and impact
    - Current workload
    """
    try:
        # Get tasks to prioritize
        with db.get_cursor() as cursor:
            if request.task_ids:
                placeholders = ",".join(["%s"] * len(request.task_ids))
                query = f"""
                    SELECT id, title, description, priority, due_date, status
                    FROM tasks
                    WHERE user_id = %s AND id IN ({placeholders})
                    ORDER BY due_date ASC NULLS LAST, priority DESC
                """
                params = [current_user.id] + request.task_ids
            else:
                query = """
                    SELECT id, title, description, priority, due_date, status
                    FROM tasks
                    WHERE user_id = %s AND status != 'completed'
                    ORDER BY due_date ASC NULLS LAST, priority DESC
                """
                params = [current_user.id]

            cursor.execute(query, params)
            tasks = [dict(t) for t in cursor.fetchall()]

        if not tasks:
            return []

        # Store original priorities for response
        original_priorities = {t["id"]: t["priority"] for t in tasks}

        # Re-prioritize using AI
        prioritized = await OpenRouterService.prioritize_tasks(tasks)

        # Update database with new priorities
        with db.get_cursor() as cursor:
            for task in prioritized:
                if task["priority"] != original_priorities[task["id"]]:
                    cursor.execute(
                        "UPDATE tasks SET priority = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (task["priority"], task["id"]),
                    )

        response = [
            PrioritizedTask(
                id=t["id"],
                title=t["title"],
                current_priority=original_priorities[t["id"]],
                new_priority=t["priority"],
            )
            for t in prioritized
        ]

        logger.info(
            "Tasks re-prioritized via AI",
            extra={"user_id": current_user.id, "task_count": len(prioritized)},
        )

        return response

    except ExternalServiceError as e:
        logger.error("Failed to prioritize tasks via AI", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error prioritizing tasks", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prioritize tasks",
        )


@router.get("/models")
async def list_available_models(current_user: User = Depends(require_active_user)):
    """
    List available AI models via OpenRouter

    Returns a curated list of recommended models for different use cases.
    """
    # Recommended models for different use cases
    return {
        "task_parsing": [
            {"id": "anthropic/claude-3-haiku:beta", "name": "Claude 3 Haiku", "description": "Fast, cost-effective"},
            {"id": "anthropic/claude-3.5-sonnet:beta", "name": "Claude 3.5 Sonnet", "description": "Balanced performance"},
        ],
        "suggestions": [
            {"id": "anthropic/claude-3.5-sonnet:beta", "name": "Claude 3.5 Sonnet", "description": "Creative and helpful"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "description": "Fast and capable"},
        ],
        "prioritization": [
            {"id": "anthropic/claude-3.5-sonnet:beta", "name": "Claude 3.5 Sonnet", "description": "Analytical and thorough"},
        ],
        "default": settings.OPENROUTER_MODEL,
    }


@router.get("/status")
async def get_ai_status(current_user: User = Depends(require_active_user)):
    """
    Check if AI service is available and configured
    """
    return {
        "enabled": bool(settings.OPENROUTER_API_KEY),
        "provider": "OpenRouter",
        "default_model": settings.OPENROUTER_MODEL,
    }
