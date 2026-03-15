"""External Integration Services"""
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.errors import ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class TodoistIntegration:
    """Todoist API integration for task synchronization"""

    API_BASE = "https://api.todoist.com/rest/v2"
    SYNC_API = "https://api.todoist.com/sync/v9"

    @classmethod
    def get_headers(cls, access_token: str) -> Dict[str, str]:
        """Get headers for Todoist API requests"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def get_tasks(cls, access_token: str) -> List[Dict[str, Any]]:
        """Get all tasks from Todoist"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{cls.API_BASE}/tasks",
                    headers=cls.get_headers(access_token),
                )

                if response.status_code != 200:
                    logger.error(
                        "Todoist API error",
                        extra={"status": response.status_code, "body": response.text},
                    )
                    raise ExternalServiceError("Todoist", "Failed to fetch tasks")

                return response.json()
        except httpx.HTTPError as e:
            logger.error("Todoist HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Todoist", "Connection failed")

    @classmethod
    async def create_task(
        cls,
        access_token: str,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: int = 1,
    ) -> Dict[str, Any]:
        """Create a new task in Todoist"""
        try:
            data = {
                "content": title,
                "priority": priority,
            }

            if description:
                data["description"] = description

            if due_date:
                data["due_string"] = due_date

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{cls.API_BASE}/tasks",
                    headers=cls.get_headers(access_token),
                    json=data,
                )

                if response.status_code != 200:
                    logger.error(
                        "Todoist create task error",
                        extra={"status": response.status_code, "body": response.text},
                    )
                    raise ExternalServiceError("Todoist", "Failed to create task")

                return response.json()
        except httpx.HTTPError as e:
            logger.error("Todoist HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Todoist", "Connection failed")

    @classmethod
    async def update_task(
        cls,
        access_token: str,
        task_id: str,
        title: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update a task in Todoist"""
        try:
            data = {}

            if title:
                data["content"] = title

            if completed is not None:
                data["is_completed"] = completed

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{cls.API_BASE}/tasks/{task_id}",
                    headers=cls.get_headers(access_token),
                    json=data,
                )

                if response.status_code != 200:
                    raise ExternalServiceError("Todoist", "Failed to update task")

                return response.json()
        except httpx.HTTPError as e:
            logger.error("Todoist HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Todoist", "Connection failed")

    @classmethod
    async def delete_task(cls, access_token: str, task_id: str) -> None:
        """Delete a task from Todoist"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{cls.API_BASE}/tasks/{task_id}",
                    headers=cls.get_headers(access_token),
                )

                if response.status_code != 204:
                    raise ExternalServiceError("Todoist", "Failed to delete task")
        except httpx.HTTPError as e:
            logger.error("Todoist HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Todoist", "Connection failed")

    @classmethod
    async def get_webhook(cls, access_token: str) -> Optional[str]:
        """Get webhook URL for Todoist"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{cls.SYNC_API}/webhooks",
                    headers=cls.get_headers(access_token),
                )

                if response.status_code == 200 and response.json():
                    return response.json()[0].get("url")

                return None
        except Exception as e:
            logger.error("Todoist get webhook error", extra={"error": str(e)})
            return None

    @classmethod
    async def create_webhook(cls, access_token: str, webhook_url: str) -> Dict[str, Any]:
        """Create a webhook for Todoist"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{cls.SYNC_API}/webhooks",
                    headers=cls.get_headers(access_token),
                    json={"url": webhook_url},
                )

                if response.status_code != 200:
                    raise ExternalServiceError("Todoist", "Failed to create webhook")

                return response.json()
        except httpx.HTTPError as e:
            logger.error("Todoist HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Todoist", "Connection failed")


class GoogleCalendarIntegration:
    """Google Calendar API integration for event synchronization"""

    API_BASE = "https://www.googleapis.com/calendar/v3"
    CALENDAR_ID = "primary"

    @classmethod
    def get_headers(cls, access_token: str) -> Dict[str, str]:
        """Get headers for Google Calendar API requests"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def get_events(
        cls,
        access_token: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get events from Google Calendar"""
        try:
            params = {
                "calendarId": cls.CALENDAR_ID,
                "singleEvents": "true",
                "orderBy": "startTime",
            }

            if start_date:
                params["timeMin"] = start_date.isoformat()

            if end_date:
                params["timeMax"] = end_date.isoformat()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{cls.API_BASE}/calendars/{cls.CALENDAR_ID}/events",
                    headers=cls.get_headers(access_token),
                    params=params,
                )

                if response.status_code != 200:
                    logger.error(
                        "Google Calendar API error",
                        extra={"status": response.status_code, "body": response.text},
                    )
                    raise ExternalServiceError("Google Calendar", "Failed to fetch events")

                data = response.json()
                return data.get("items", [])
        except httpx.HTTPError as e:
            logger.error("Google Calendar HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Google Calendar", "Connection failed")

    @classmethod
    async def create_event(
        cls,
        access_token: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        all_day: bool = False,
    ) -> Dict[str, Any]:
        """Create an event in Google Calendar"""
        try:
            event_data = {
                "summary": title,
                "start": cls._format_datetime(start_time, all_day),
                "end": cls._format_datetime(end_time, all_day),
            }

            if description:
                event_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{cls.API_BASE}/calendars/{cls.CALENDAR_ID}/events",
                    headers=cls.get_headers(access_token),
                    json=event_data,
                )

                if response.status_code != 200:
                    logger.error(
                        "Google Calendar create event error",
                        extra={"status": response.status_code, "body": response.text},
                    )
                    raise ExternalServiceError("Google Calendar", "Failed to create event")

                return response.json()
        except httpx.HTTPError as e:
            logger.error("Google Calendar HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Google Calendar", "Connection failed")

    @classmethod
    def _format_datetime(cls, dt: datetime, all_day: bool) -> Dict[str, str]:
        """Format datetime for Google Calendar API"""
        if all_day:
            return {"date": dt.date().isoformat()}
        else:
            return {"dateTime": dt.isoformat()}

    @classmethod
    async def update_event(
        cls,
        access_token: str,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Update an event in Google Calendar"""
        try:
            event_data = {}

            if title:
                event_data["summary"] = title

            if start_time:
                event_data["start"] = cls._format_datetime(start_time, False)

            if end_time:
                event_data["end"] = cls._format_datetime(end_time, False)

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{cls.API_BASE}/calendars/{cls.CALENDAR_ID}/events/{event_id}",
                    headers=cls.get_headers(access_token),
                    json=event_data,
                )

                if response.status_code != 200:
                    raise ExternalServiceError("Google Calendar", "Failed to update event")

                return response.json()
        except httpx.HTTPError as e:
            logger.error("Google Calendar HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Google Calendar", "Connection failed")

    @classmethod
    async def delete_event(cls, access_token: str, event_id: str) -> None:
        """Delete an event from Google Calendar"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{cls.API_BASE}/calendars/{cls.CALENDAR_ID}/events/{event_id}",
                    headers=cls.get_headers(access_token),
                )

                if response.status_code != 204:
                    raise ExternalServiceError("Google Calendar", "Failed to delete event")
        except httpx.HTTPError as e:
            logger.error("Google Calendar HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Google Calendar", "Connection failed")

    @classmethod
    async def watch_calendar(cls, access_token: str, webhook_url: str) -> Dict[str, Any]:
        """Set up push notifications for calendar changes"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{cls.API_BASE}/calendars/{cls.CALENDAR_ID}/events/watch",
                    headers=cls.get_headers(access_token),
                    json={
                        "id": f"flowsync-{datetime.utcnow().timestamp()}",
                        "type": "web_hook",
                        "address": webhook_url,
                    },
                )

                if response.status_code != 200:
                    raise ExternalServiceError("Google Calendar", "Failed to set up watch")

                return response.json()
        except httpx.HTTPError as e:
            logger.error("Google Calendar HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("Google Calendar", "Connection failed")
