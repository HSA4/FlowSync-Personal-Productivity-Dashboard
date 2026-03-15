"""Task API Routes"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional

from app.models.tasks import Task, TaskCreate, TaskUpdate, TaskList, Priority
from app.models.common import MessageResponse
from app.db.database import db
from app.core.errors import NotFoundError, DatabaseError
from app.core.logging import get_logger

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = get_logger(__name__)


@router.get("", response_model=TaskList)
async def get_tasks(
    completed: Optional[bool] = None,
    priority: Optional[Priority] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get all tasks with optional filtering"""
    try:
        conditions = []
        params = []

        if completed is not None:
            conditions.append("completed = %s")
            params.append(completed)

        if priority is not None:
            conditions.append("priority = %s")
            params.append(priority)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])

        with db.get_cursor() as cursor:
            # Get tasks
            cursor.execute(
                f"""
                SELECT * FROM tasks
                {where_clause}
                ORDER BY priority DESC, created_at DESC
                LIMIT %s OFFSET %s
                """,
                params,
            )
            tasks = cursor.fetchall()

            # Get counts
            count_params = params[:-2]  # Remove limit and offset
            cursor.execute(
                f"SELECT COUNT(*) as total, SUM(completed) as completed FROM tasks {where_clause}",
                count_params,
            )
            counts = cursor.fetchone()

        return TaskList(
            tasks=tasks,
            total=counts["total"] or 0,
            completed=counts["completed"] or 0,
            pending=(counts["total"] or 0) - (counts["completed"] or 0),
        )

    except Exception as e:
        logger.error("Failed to get tasks", extra={"error": str(e)})
        raise DatabaseError("Failed to retrieve tasks")


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Get a specific task by ID"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cursor.fetchone()

            if not task:
                raise NotFoundError("Task", str(task_id))

            return task

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get task", extra={"error": str(e), "task_id": task_id})
        raise DatabaseError("Failed to retrieve task")


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    """Create a new task"""
    try:
        with db.get_cursor() as cursor:
            query = """
                INSERT INTO tasks (title, description, completed, priority, due_date)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (task.title, task.description, task.completed, task.priority, task.due_date),
            )

            # Get the created task
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (cursor.lastrowid,))
            return cursor.fetchone()

    except Exception as e:
        logger.error("Failed to create task", extra={"error": str(e), "task": task.dict()})
        raise DatabaseError("Failed to create task")


@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: int, task: TaskUpdate):
    """Update an existing task"""
    try:
        # Check if task exists
        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                raise NotFoundError("Task", str(task_id))

        # Build update query dynamically
        update_fields = []
        params = []

        if task.title is not None:
            update_fields.append("title = %s")
            params.append(task.title)

        if task.description is not None:
            update_fields.append("description = %s")
            params.append(task.description)

        if task.completed is not None:
            update_fields.append("completed = %s")
            params.append(task.completed)

        if task.priority is not None:
            update_fields.append("priority = %s")
            params.append(task.priority)

        if task.due_date is not None:
            update_fields.append("due_date = %s")
            params.append(task.due_date)

        if not update_fields:
            # No updates, return existing task
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            return cursor.fetchone()

        params.append(task_id)

        with db.get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE tasks
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                params,
            )

            # Get updated task
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            return cursor.fetchone()

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to update task", extra={"error": str(e), "task_id": task_id})
        raise DatabaseError("Failed to update task")


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    """Delete a task"""
    try:
        # Check if task exists
        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                raise NotFoundError("Task", str(task_id))

            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

        return None

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to delete task", extra={"error": str(e), "task_id": task_id})
        raise DatabaseError("Failed to delete task")


@router.patch("/{task_id}/toggle", response_model=Task)
async def toggle_task_completion(task_id: int):
    """Toggle task completion status"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT completed FROM tasks WHERE id = %s", (task_id,))
            result = cursor.fetchone()

            if not result:
                raise NotFoundError("Task", str(task_id))

            new_status = not result["completed"]

            cursor.execute(
                "UPDATE tasks SET completed = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_status, task_id),
            )

            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            return cursor.fetchone()

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to toggle task", extra={"error": str(e), "task_id": task_id})
        raise DatabaseError("Failed to toggle task completion")
