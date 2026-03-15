"""Event API Routes"""
from fastapi import APIRouter, Query, status
from typing import Optional
from datetime import datetime, date

from app.models.events import Event, EventCreate, EventUpdate, EventList
from app.db.database import db
from app.core.errors import NotFoundError, DatabaseError
from app.core.logging import get_logger

router = APIRouter(prefix="/events", tags=["events"])
logger = get_logger(__name__)


@router.get("", response_model=EventList)
async def get_events(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
):
    """Get all events with optional date filtering"""
    try:
        conditions = []
        params = []

        if start_date:
            conditions.append("DATE(start_time) >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("DATE(end_time) <= %s")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        with db.get_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM events
                {where_clause}
                ORDER BY start_time ASC
                LIMIT %s
                """,
                params,
            )
            events = cursor.fetchall()

            # Get total count
            count_params = params[:-1]  # Remove limit
            cursor.execute(
                f"SELECT COUNT(*) as total FROM events {where_clause}",
                count_params,
            )
            counts = cursor.fetchone()

        return EventList(
            events=events,
            total=counts["total"] or 0,
        )

    except Exception as e:
        logger.error("Failed to get events", extra={"error": str(e)})
        raise DatabaseError("Failed to retrieve events")


@router.get("/{event_id}", response_model=Event)
async def get_event(event_id: int):
    """Get a specific event by ID"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
            event = cursor.fetchone()

            if not event:
                raise NotFoundError("Event", str(event_id))

            return event

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get event", extra={"error": str(e), "event_id": event_id})
        raise DatabaseError("Failed to retrieve event")


@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate):
    """Create a new event"""
    try:
        with db.get_cursor() as cursor:
            query = """
                INSERT INTO events (title, description, start_time, end_time, all_day)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (event.title, event.description, event.start_time, event.end_time, event.all_day),
            )

            # Get the created event
            cursor.execute("SELECT * FROM events WHERE id = %s", (cursor.lastrowid,))
            return cursor.fetchone()

    except Exception as e:
        logger.error("Failed to create event", extra={"error": str(e), "event": event.dict()})
        raise DatabaseError("Failed to create event")


@router.put("/{event_id}", response_model=Event)
async def update_event(event_id: int, event: EventUpdate):
    """Update an existing event"""
    try:
        # Check if event exists
        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM events WHERE id = %s", (event_id,))
            if not cursor.fetchone():
                raise NotFoundError("Event", str(event_id))

        # Build update query dynamically
        update_fields = []
        params = []

        if event.title is not None:
            update_fields.append("title = %s")
            params.append(event.title)

        if event.description is not None:
            update_fields.append("description = %s")
            params.append(event.description)

        if event.start_time is not None:
            update_fields.append("start_time = %s")
            params.append(event.start_time)

        if event.end_time is not None:
            update_fields.append("end_time = %s")
            params.append(event.end_time)

        if event.all_day is not None:
            update_fields.append("all_day = %s")
            params.append(event.all_day)

        if not update_fields:
            # No updates, return existing event
            cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
            return cursor.fetchone()

        params.append(event_id)

        with db.get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE events
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                params,
            )

            # Get updated event
            cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
            return cursor.fetchone()

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to update event", extra={"error": str(e), "event_id": event_id})
        raise DatabaseError("Failed to update event")


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int):
    """Delete an event"""
    try:
        # Check if event exists
        with db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM events WHERE id = %s", (event_id,))
            if not cursor.fetchone():
                raise NotFoundError("Event", str(event_id))

            cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))

        return None

    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to delete event", extra={"error": str(e), "event_id": event_id})
        raise DatabaseError("Failed to delete event")
