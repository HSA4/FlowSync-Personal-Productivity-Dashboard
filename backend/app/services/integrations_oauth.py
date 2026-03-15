"""Integration OAuth Services"""
from typing import Optional, Dict, Any
import secrets
import httpx

from app.core.config import settings
from app.core.errors import ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class IntegrationOAuthService:
    """Base class for integration OAuth services"""

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: Optional[str] = None) -> tuple[str, str]:
        """Generate OAuth authorization URL - to be implemented by subclasses"""
        raise NotImplementedError

    @classmethod
    async def exchange_code_for_token(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token - to be implemented by subclasses"""
        raise NotImplementedError


class TodoistOAuthService(IntegrationOAuthService):
    """Todoist OAuth 2.0 integration service"""

    AUTH_URL = "https://todoist.com/oauth/authorize"
    TOKEN_URL = "https://todoist.com/oauth/access_token"
    SCOPES = ["task:add", "task:read", "task:write", "project:read"]

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: Optional[str] = None) -> tuple[str, str]:
        """Generate Todoist OAuth authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": settings.TODOIST_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": " ".join(cls.SCOPES),
            "state": state,
        }

        url = f"{cls.AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return url, state

    @classmethod
    async def exchange_code_for_token(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Todoist authorization code for access token"""
        data = {
            "client_id": settings.TODOIST_CLIENT_ID,
            "client_secret": settings.TODOIST_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(cls.TOKEN_URL, data=data)

            if response.status_code != 200:
                logger.error(
                    "Todoist token exchange failed",
                    extra={"status": response.status_code, "body": response.text},
                )
                raise ExternalServiceError("Todoist", "Failed to exchange authorization code")

            return response.json()


class GoogleCalendarOAuthService(IntegrationOAuthService):
    """Google Calendar OAuth 2.0 integration service"""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SCOPES = [
        "openid",
        "email",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: Optional[str] = None) -> tuple[str, str]:
        """Generate Google Calendar OAuth authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": " ".join(cls.SCOPES),
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        url = f"{cls.AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return url, state

    @classmethod
    async def exchange_code_for_token(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Google Calendar authorization code for access token"""
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(cls.TOKEN_URL, data=data)

            if response.status_code != 200:
                logger.error(
                    "Google Calendar token exchange failed",
                    extra={"status": response.status_code, "body": response.text},
                )
                raise ExternalServiceError("Google Calendar", "Failed to exchange authorization code")

            return response.json()
