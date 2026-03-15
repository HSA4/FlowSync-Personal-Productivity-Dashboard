"""Task API Routes"""
from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from typing import Optional

from app.models.tasks import Task, TaskCreate, TaskUpdate, TaskList, Priority
from app.models.users import User
from app.models.common import MessageResponse
from app.api.deps import require_active_user
from app.db.database import db
from app.core.errors import NotFoundError, DatabaseError
from app.core.logging import get_logger
from app.services.integrations import TodoistIntegration

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
async def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    sync_to_external: bool = Query(False, description="Sync task to external integrations"),
    current_user: User = Depends(require_active_user),
):
    """Create a new task"""
    try:
        with db.get_cursor() as cursor:
            query = """
                INSERT INTO tasks (user_id, title, description, completed, priority, due_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """
            cursor.execute(
                query,
                (
                    current_user.id,
                    task.title,
                    task.description,
                    task.completed,
                    task.priority,
                    task.due_date,
                    "completed" if task.completed else "pending",
                ),
            )
            new_task = cursor.fetchone()

            # Sync to external integrations if requested
            if sync_to_external:
                background_tasks.add_task(
                    _push_task_to_integrations,
                    current_user.id,
                    new_task["id"],
                )

            return new_task

    except Exception as e:
        logger.error("Failed to create task", extra={"error": str(e), "task": task.dict()})
        raise DatabaseError("Failed to create task")


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    background_tasks: BackgroundTasks,
    sync_to_external: bool = Query(False, description="Sync update to external integrations"),
    current_user: User = Depends(require_active_user),
):
    """Update an existing task"""
    try:
        # Check if task exists and get external info
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, external_id, external_provider FROM tasks WHERE id = %s AND user_id = %s",
                (task_id, current_user.id),
            )
            task_row = cursor.fetchone()
            if not task_row:
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
            update_fields.append("status = %s")
            params.append(task.completed)
            params.append("completed" if task.completed else "pending")

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
            updated_task = cursor.fetchone()

        # Sync to external integrations if requested
        if sync_to_external and task_row.get("external_id") and task_row.get("external_provider"):
            background_tasks.add_task(
                _update_task_in_integration,
                current_user.id,
                task_row["external_provider"],
                task_row["external_id"],
                task.dict(exclude_unset=True),
            )

        return updated_task

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to update task", extra={"error": str(e), "task_id": task_id})
        raise DatabaseError("Failed to update task")


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    sync_to_external: bool = Query(False, description="Delete from external integrations"),
    current_user: User = Depends(require_active_user),
):
    """Delete a task"""
    try:
        # Check if task exists and get external info
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, external_id, external_provider FROM tasks WHERE id = %s AND user_id = %s",
                (task_id, current_user.id),
            )
            task = cursor.fetchone()
            if not task:
                raise NotFoundError("Task", str(task_id))

            external_id = task.get("external_id")
            external_provider = task.get("external_provider")

            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))

            # Delete from external integrations if requested
            if sync_to_external and external_id and external_provider:
                background_tasks.add_task(
                    _delete_task_from_integration,
                    current_user.id,
                    external_provider,
                    external_id,
                )

        return None

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to delete task", extra={"error": str(e), "task_id": task_id})
        raise DatabaseError("Failed to delete task")


@router.patch("/{task_id}/toggle", response_model=Task)
async def toggle_task_completion(
    task_id: int,
    background_tasks: BackgroundTasks,
    sync_to_external: bool = Query(False, description="Sync toggle to external integrations"),
    current_user: User = Depends(require_active_user),
):
    """Toggle task completion status"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT completed, external_id, external_provider FROM tasks WHERE id = %s AND user_id = %s",
                (task_id, current_user.id),
            )
            result = cursor.fetchone()

            if not result:
                raise NotFoundError("Task", str(task_id))

            new_status = not result["completed"]

            cursor.execute(
                "UPDATE tasks SET completed = %s, status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_status, "completed" if new_status else "pending", task_id),
            )

            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            updated_task = cursor.fetchone()

        # Sync to external integrations if requested
        if sync_to_external and result.get("external_id") and result.get("external_provider"):
            background_tasks.add_task(
                _update_task_in_integration,
                current_user.id,
                result["external_provider"],
                result["external_id"],
                {"is_completed": new_status},
            )

        return updated_task

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to toggle task", extra={"error": str(e), "task_id": task_id})
        raise DatabaseError("Failed to toggle task completion")


# Helper functions for two-way sync

async def _push_task_to_integrations(user_id: int, task_id: int):
    """Push a newly created task to external integrations"""
    try:
        # Get user's enabled integrations
        with db.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM integrations WHERE user_id = %s AND provider = 'todoist' AND enabled = true",
                (user_id,),
            )
            integrations = cursor.fetchall()

            # Get task details
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cursor.fetchone()

        for integration in integrations:
            try:
                # Create task in Todoist
                todoist_task = await TodoistIntegration.create_task(
                    access_token=integration["access_token"],
                    title=task["title"],
                    description=task.get("description"),
                    due_date=str(task["due_date"]) if task.get("due_date") else None,
                    priority=task.get("priority", 1),
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

                logger.info(
                    "Pushed task to Todoist",
                    extra={"task_id": task_id, "todoist_id": todoist_task["id"]},
                )

            except Exception as e:
                logger.error(
                    "Failed to push task to Todoist",
                    extra={"error": str(e), "task_id": task_id},
                )

    except Exception as e:
        logger.error("Failed to push task to integrations", extra={"error": str(e), "task_id": task_id})


async def _update_task_in_integration(
    user_id: int,
    provider: str,
    external_id: str,
    update_data: dict,
):
    """Update a task in an external integration"""
    try:
        # Get user's integration
        with db.get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM integrations WHERE user_id = %s AND provider = %s AND enabled = true",
                (user_id, provider),
            )
            integration = cursor.fetchone()

        if not integration:
            logger.warning(f"No enabled {provider} integration found", extra={"user_id": user_id})
            return

        if provider == "todoist":
            # Update task in Todoist
            title = update_data.get("title")
            completed = update_data.get("completed") or update_data.get("is_completed")

            await TodoistIntegration.update_task(
                access_token=integration["access_token"],
                task_id=external_id,
                title=title,
                completed=completed,
            )

            logger.info(
                "Updated task in Todoist",
                extra={"external_id": external_id, "update_data": update_data},
            )

    except Exception as e:
        logger.error(
            "Failed to update task in integration",
            extra={"error": str(e), "provider": provider, "external_id": external_id},
        )


async def _delete_task_from_integration(
    user_id: int,
    provider: str,
    external_id: str,
):
    """Delete a task from an external integration"""
    try:
        # Get user's integration
        with db.get_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM integrations WHERE user_id = %s AND provider = %s AND enabled = true",
                (user_id, provider),
            )
            integration = cursor.fetchone()

        if not integration:
            logger.warning(f"No enabled {provider} integration found", extra={"user_id": user_id})
            return

        if provider == "todoist":
            # Delete task from Todoist
            await TodoistIntegration.delete_task(
                access_token=integration["access_token"],
                task_id=external_id,
            )

            logger.info(
                "Deleted task from Todoist",
                extra={"external_id": external_id},
            )

    except Exception as e:
        logger.error(
            "Failed to delete task from integration",
            extra={"error": str(e), "provider": provider, "external_id": external_id},
        )
