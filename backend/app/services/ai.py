"""AI Service using OpenRouter API"""
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings
from app.core.errors import ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenRouterService:
    """OpenRouter API integration for AI features"""

    API_BASE = "https://openrouter.ai/api/v1"

    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Get headers for OpenRouter API requests"""
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.OPENROUTER_SITE_URL or "https://flowsync.app",
            "X-Title": settings.OPENROUTER_APP_NAME or "FlowSync",
        }
        return headers

    @classmethod
    async def chat_completion(
        cls,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (defaults to settings.OPENROUTER_MODEL)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Response dict with 'content' and other metadata
        """
        if not settings.OPENROUTER_API_KEY:
            raise ExternalServiceError("OpenRouter", "API key not configured")

        model = model or settings.OPENROUTER_MODEL

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{cls.API_BASE}/chat/completions",
                    headers=cls.get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        "OpenRouter API error",
                        extra={"status": response.status_code, "body": response.text},
                    )
                    raise ExternalServiceError("OpenRouter", f"API request failed: {response.status_code}")

                data = response.json()

                if "choices" not in data or not data["choices"]:
                    raise ExternalServiceError("OpenRouter", "No response generated")

                return {
                    "content": data["choices"][0]["message"]["content"],
                    "model": data.get("model", model),
                    "usage": data.get("usage", {}),
                }

        except httpx.TimeoutException:
            logger.error("OpenRouter timeout")
            raise ExternalServiceError("OpenRouter", "Request timeout")
        except httpx.HTTPError as e:
            logger.error("OpenRouter HTTP error", extra={"error": str(e)})
            raise ExternalServiceError("OpenRouter", "Connection failed")

    @classmethod
    async def parse_task_from_text(cls, text: str) -> Dict[str, Any]:
        """
        Parse natural language text into a structured task

        Args:
            text: Natural language input like "Schedule meeting tomorrow at 2pm"

        Returns:
            Dict with parsed task fields: title, description, due_date, priority, etc.
        """
        system_prompt = """You are a task parsing assistant. Extract task information from natural language and return it as JSON.

Your response must be ONLY valid JSON with these fields:
- title: string (required) - The main task title
- description: string or null - Additional details
- due_date: string or null - ISO date format (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS) if time specified
- priority: integer (1-4) - 1=low, 2=medium, 3=high, 4=urgent
- estimated_duration: integer or null - Estimated minutes (if mentioned)

Rules:
- If no date is mentioned, due_date should be null
- If "tomorrow" is used, calculate the date from current date (assume current date is provided in context)
- If a time is mentioned (like "2pm", "14:00"), include it in due_date
- Default priority to 2 (medium) unless urgency is indicated
- Current date: {current_date}

Examples:
Input: "Finish the project report by Friday 5pm"
Output: {{"title": "Finish the project report", "description": null, "due_date": "2025-03-21T17:00:00", "priority": 3, "estimated_duration": null}}

Input: "Call mom about birthday party"
Output: {{"title": "Call mom about birthday party", "description": null, "due_date": null, "priority": 2, "estimated_duration": 15}}

Input: "Urgent: Submit tax documents before midnight"
Output: {{"title": "Submit tax documents", "description": "Urgent submission", "due_date": "2025-03-15T23:59:59", "priority": 4, "estimated_duration": null}}"""

        from datetime import datetime

        user_prompt = f'Parse this task request: "{text}"\n\nCurrent date: {datetime.now().strftime("%Y-%m-%d")}'

        messages = [
            {"role": "system", "content": system_prompt.format(current_date=datetime.now().strftime("%Y-%m-%d"))},
            {"role": "user", "content": user_prompt},
        ]

        try:
            result = await cls.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent parsing
                max_tokens=300,
            )

            import json

            # Extract JSON from the response
            content = result["content"].strip()
            # Handle markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            parsed = json.loads(content)

            # Validate required fields
            if not parsed.get("title"):
                parsed["title"] = text[:100]  # Fallback to truncated input

            return parsed

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON", extra={"error": str(e), "content": result.get("content")})
            # Return a basic fallback
            return {
                "title": text[:100],
                "description": text,
                "due_date": None,
                "priority": 2,
                "estimated_duration": None,
            }

    @classmethod
    async def generate_task_suggestions(cls, user_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate task suggestions based on user context and patterns

        Args:
            user_context: Dict with user's current tasks, calendar, etc.

        Returns:
            List of suggested tasks with title and reason
        """
        system_prompt = """You are a productivity assistant. Generate 3-5 task suggestions based on the user's context.

Return ONLY valid JSON array with objects having:
- title: string (suggested task)
- reason: string (why this task is suggested)
- priority: integer (1-4)

Consider:
- Tasks that might be forgotten
- Follow-up tasks from completed items
- Recurring responsibilities
- Upcoming deadlines
- Gaps in the user's schedule"""

        user_prompt = f"""Based on this context, suggest tasks:

Current tasks: {user_context.get('tasks', [])}
Upcoming events: {user_context.get('events', [])}
Recent completions: {user_context.get('completed', [])}

Generate 3-5 practical suggestions."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            result = await cls.chat_completion(
                messages=messages,
                temperature=0.8,  # Higher temperature for creativity
                max_tokens=500,
            )

            import json

            content = result["content"].strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            suggestions = json.loads(content)

            # Ensure we have a list
            if isinstance(suggestions, dict):
                suggestions = [suggestions]

            return suggestions[:5]  # Limit to 5 suggestions

        except (json.JSONDecodeError, Exception) as e:
            logger.error("Failed to generate suggestions", extra={"error": str(e)})
            return []

    @classmethod
    async def prioritize_tasks(cls, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Re-rank tasks by priority using AI

        Args:
            tasks: List of task dicts

        Returns:
            List of tasks with updated priority scores
        """
        system_prompt = """You are a prioritization assistant. Re-rank tasks based on urgency, importance, and dependencies.

Return ONLY valid JSON array of tasks with their IDs and new priority (1-4):
- 1 = Low priority (can wait)
- 2 = Medium priority (normal)
- 3 = High priority (important)
- 4 = Urgent (immediate action needed)

Consider:
- Due dates and deadlines
- Dependencies between tasks
- Impact and consequences
- Current date and time"""

        from datetime import datetime

        tasks_summary = "\n".join([
            f"- Task {i+1}: {t.get('title')} (Due: {t.get('due_date', 'None')}, Current priority: {t.get('priority', 2)})"
            for i, t in enumerate(tasks)
        ])

        user_prompt = f"""Prioritize these tasks:\n{tasks_summary}\n\nCurrent date: {datetime.now().strftime('%Y-%m-%d')}

Return the updated priorities as JSON with task indices and new priorities."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            result = await cls.chat_completion(
                messages=messages,
                temperature=0.5,
                max_tokens=500,
            )

            import json

            content = result["content"].strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            priorities = json.loads(content)

            # Apply new priorities to tasks
            updated_tasks = tasks.copy()
            for item in priorities:
                if "index" in item and 0 <= item["index"] < len(updated_tasks):
                    updated_tasks[item["index"]]["priority"] = item.get("priority", 2)
                elif "id" in item:
                    for task in updated_tasks:
                        if task.get("id") == item["id"]:
                            task["priority"] = item.get("priority", 2)
                            break

            return updated_tasks

        except (json.JSONDecodeError, Exception) as e:
            logger.error("Failed to prioritize tasks", extra={"error": str(e)})
            return tasks  # Return original on error
