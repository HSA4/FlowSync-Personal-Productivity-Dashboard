"""Celery Tasks for AI Operations"""
from datetime import datetime
from typing import Dict, Any, List
import json

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.core.redis_client import cache
from app.core.logging import get_logger
from app.db.database import db
from app.services.ai import OpenRouterService

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Base task with database connection management"""

    _db = None

    def after_return(self, *args, **kwargs):
        """Close database connection after task completes"""
        if self._db:
            self._db.close_all()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_tasks.generate_daily_digest")
def generate_daily_digest(self, user_id: int) -> Dict[str, Any]:
    """
    Generate a daily digest of tasks and events using AI

    Returns:
        Generated digest content
    """
    result = {
        "user_id": user_id,
        "status": "error",
        "digest": None,
        "error": None,
    }

    try:
        # Get user's tasks and events for today
        with db.get_cursor() as cursor:
            # Get pending tasks
            cursor.execute(
                """
                SELECT id, title, description, priority, due_date
                FROM tasks
                WHERE user_id = %s AND status = 'pending'
                AND (due_date >= CURRENT_DATE OR due_date IS NULL)
                ORDER BY priority DESC, due_date ASC
                LIMIT 20
                """,
                (user_id,),
            )
            tasks = cursor.fetchall()

            # Get today's events
            cursor.execute(
                """
                SELECT id, title, description, start_time, end_time
                FROM events
                WHERE user_id = %s
                AND DATE(start_time) = CURRENT_DATE
                ORDER BY start_time ASC
                """,
                (user_id,),
            )
            events = cursor.fetchall()

        # Generate digest using AI
        ai_service = OpenRouterService()

        prompt = f"""Generate a concise daily productivity digest for a user with the following tasks and events:

Tasks ({len(tasks)} pending):
{json.dumps([{t['title']: t.get('description')} for t in tasks[:10]], indent=2)}

Events Today ({len(events)}):
{json.dumps([{e['title']: e['start_time']} for e in events], indent=2)}

Please provide:
1. A brief summary of the day
2. Top 3 priority tasks to focus on
3. Any scheduling conflicts or concerns
4. An encouraging closing note

Keep it under 200 words and format in Markdown."""

        response = ai_service.chat(prompt)
        digest_content = response.get("content", "")

        # Cache the digest for 24 hours
        cache.set(f"daily_digest:{user_id}", digest_content, ttl=86400)

        result["status"] = "success"
        result["digest"] = digest_content

        logger.info(
            "Generated daily digest",
            extra={"user_id": user_id, "digest_length": len(digest_content)},
        )

    except SoftTimeLimitExceeded:
        result["error"] = "AI generation timed out"
        logger.warning("Daily digest generation timed out", extra={"user_id": user_id})

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to generate daily digest", extra={"user_id": user_id, "error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_tasks.prioritize_tasks")
def prioritize_tasks(
    self,
    user_id: int,
    task_ids: List[int] = None,
) -> Dict[str, Any]:
    """
    Use AI to prioritize tasks

    Returns:
        Task priorities mapping
    """
    result = {
        "user_id": user_id,
        "status": "error",
        "priorities": {},
        "error": None,
    }

    try:
        # Get tasks to prioritize
        with db.get_cursor() as cursor:
            if task_ids:
                placeholders = ",".join(["%s"] * len(task_ids))
                cursor.execute(
                    f"""
                    SELECT id, title, description, priority, due_date
                    FROM tasks
                    WHERE user_id = %s AND id IN ({placeholders})
                    AND status = 'pending'
                    """,
                    [user_id] + task_ids,
                )
            else:
                cursor.execute(
                    """
                    SELECT id, title, description, priority, due_date
                    FROM tasks
                    WHERE user_id = %s AND status = 'pending'
                    AND (due_date >= CURRENT_DATE OR due_date IS NULL)
                    ORDER BY created_at DESC
                    LIMIT 15
                    """,
                    (user_id,),
                )
            tasks = cursor.fetchall()

        if not tasks:
            result["status"] = "success"
            result["priorities"] = {}
            return result

        # Generate priorities using AI
        ai_service = OpenRouterService()

        prompt = f"""Prioritize these tasks based on importance and urgency. Return a JSON array of task IDs in priority order (highest first).

Tasks:
{json.dumps([{t['id']: t['title']} for t in tasks], indent=2)}

Consider:
1. Due dates and deadlines
2. Task complexity
3. Dependencies between tasks
4. User's stated priorities

Return ONLY the JSON array, no other text."""

        response = ai_service.chat(prompt)
        content = response.get("content", "")

        # Parse the AI response
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                priority_order = json.loads(json_match.group())
            else:
                # Fallback: use current priority order
                priority_order = [t["id"] for t in sorted(tasks, key=lambda x: -x["priority"])]

            # Assign priorities (4=urgent, 3=high, 2=medium, 1=low)
            priorities = {}
            for i, task_id in enumerate(priority_order[:15]):
                if len(priority_order) <= 5:
                    priority = 4 if i == 0 else (3 if i <= 2 else 2)
                else:
                    priority = 4 if i < 2 else (3 if i < 5 else (2 if i < 10 else 1))
                priorities[task_id] = priority

            # Update tasks in database
            with db.get_cursor() as cursor:
                for task_id, priority in priorities.items():
                    cursor.execute(
                        "UPDATE tasks SET priority = %s WHERE id = %s",
                        (priority, task_id),
                    )

            result["status"] = "success"
            result["priorities"] = priorities

            logger.info(
                "Prioritized tasks",
                extra={"user_id": user_id, "count": len(priorities)},
            )

        except json.JSONDecodeError:
            result["error"] = "Failed to parse AI response"

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to prioritize tasks", extra={"user_id": user_id, "error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_tasks.suggest_tasks")
def suggest_tasks(
    self,
    user_id: int,
    max_suggestions: int = 5,
) -> Dict[str, Any]:
    """
    Generate task suggestions based on user's patterns

    Returns:
        List of suggested tasks
    """
    result = {
        "user_id": user_id,
        "status": "error",
        "suggestions": [],
        "error": None,
    }

    try:
        # Get user's recent tasks to understand patterns
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT title, description, created_at, completed_at
                FROM tasks
                WHERE user_id = %s
                AND created_at > CURRENT_DATE - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            )
            recent_tasks = cursor.fetchall()

            # Get pending tasks
            cursor.execute(
                """
                SELECT title, description
                FROM tasks
                WHERE user_id = %s AND status = 'pending'
                LIMIT 10
                """,
                (user_id,),
            )
            pending_tasks = cursor.fetchall()

        # Generate suggestions using AI
        ai_service = OpenRouterService()

        prompt = f"""Based on the user's recent and pending tasks, suggest {max_suggestions} actionable tasks they should consider adding.

Recent tasks (last 30 days):
{json.dumps([t['title'] for t in recent_tasks], indent=2)}

Pending tasks:
{json.dumps([t['title'] for t in pending_tasks], indent=2)}

Return a JSON array of objects with 'title' and optional 'description' fields. Keep suggestions practical and actionable."""

        response = ai_service.chat(prompt)
        content = response.get("content", "")

        # Parse the AI response
        try:
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                result["suggestions"] = suggestions[:max_suggestions]
            else:
                result["suggestions"] = []

            result["status"] = "success"

            logger.info(
                "Generated task suggestions",
                extra={"user_id": user_id, "count": len(result["suggestions"])},
            )

        except json.JSONDecodeError:
            result["error"] = "Failed to parse AI response"

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to generate task suggestions", extra={"user_id": user_id, "error": str(e)})

    return result


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_tasks.smart_time_blocking")
def smart_time_blocking(
    self,
    user_id: int,
    date: str = None,
) -> Dict[str, Any]:
    """
    Generate a time-blocked schedule for the day using AI

    Returns:
        Scheduled time blocks
    """
    result = {
        "user_id": user_id,
        "date": date or datetime.utcnow().date().isoformat(),
        "status": "error",
        "schedule": [],
        "error": None,
    }

    try:
        # Get user's tasks and events for the day
        with db.get_cursor() as cursor:
            # Get events
            cursor.execute(
                """
                SELECT id, title, start_time, end_time
                FROM events
                WHERE user_id = %s AND DATE(start_time) = %s
                ORDER BY start_time ASC
                """,
                (user_id, result["date"]),
            )
            events = cursor.fetchall()

            # Get pending tasks
            cursor.execute(
                """
                SELECT id, title, description, priority, estimated_minutes
                FROM tasks
                WHERE user_id = %s AND status = 'pending'
                AND (due_date >= %s OR due_date IS NULL)
                ORDER BY priority DESC
                LIMIT 10
                """,
                (user_id, result["date"]),
            )
            tasks = cursor.fetchall()

        # Generate schedule using AI
        ai_service = OpenRouterService()

        prompt = f"""Create a time-blocked schedule for the day starting at 9:00 AM.

Existing events:
{json.dumps([{'title': e['title'], 'start': e['start_time'], 'end': e['end_time']} for e in events], indent=2)}

Tasks to schedule:
{json.dumps([{'title': t['title'], 'priority': t['priority']} for t in tasks], indent=2)}

Return a JSON array of time blocks with 'start', 'end', 'title', and 'type' (work/break/event) fields."""

        response = ai_service.chat(prompt)
        content = response.get("content", "")

        # Parse the AI response
        try:
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                schedule = json.loads(json_match.group())
                result["schedule"] = schedule
            else:
                result["schedule"] = []

            result["status"] = "success"

            logger.info(
                "Generated time-blocking schedule",
                extra={"user_id": user_id, "blocks": len(result["schedule"])},
            )

        except json.JSONDecodeError:
            result["error"] = "Failed to parse AI response"

    except Exception as e:
        result["error"] = str(e)
        logger.error("Failed to generate time-blocking schedule", extra={"user_id": user_id, "error": str(e)})

    return result
