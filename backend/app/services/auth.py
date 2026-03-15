"""Authentication Service"""
from typing import Optional, Dict, Any
from datetime import datetime
import secrets
import httpx

from app.core.errors import NotFoundError, AuthenticationError, ExternalServiceError
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.config import settings
from app.models.users import User, UserCreate, Provider
from app.db.database import db
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service for managing users and tokens"""

    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        """Get a user by ID"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user_data = cursor.fetchone()
                if user_data:
                    return User(**user_data)
                return None
        except Exception as e:
            logger.error("Failed to get user", extra={"error": str(e), "user_id": user_id})
            return None

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """Get a user by email"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user_data = cursor.fetchone()
                if user_data:
                    return User(**user_data)
                return None
        except Exception as e:
            logger.error("Failed to get user by email", extra={"error": str(e), "email": email})
            return None

    @staticmethod
    async def get_user_by_provider(provider: Provider, provider_id: str) -> Optional[User]:
        """Get a user by OAuth provider and provider ID"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE provider = %s AND provider_id = %s",
                    (provider.value, provider_id),
                )
                user_data = cursor.fetchone()
                if user_data:
                    return User(**user_data)
                return None
        except Exception as e:
            logger.error(
                "Failed to get user by provider",
                extra={"error": str(e), "provider": provider, "provider_id": provider_id},
            )
            return None

    @staticmethod
    async def create_user(user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            with db.get_cursor() as cursor:
                query = """
                    INSERT INTO users (email, name, avatar_url, provider, provider_id)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    query,
                    (
                        user_data.email,
                        user_data.name,
                        user_data.avatar_url,
                        user_data.provider.value,
                        user_data.provider_id,
                    ),
                )

                # Get the created user
                cursor.execute("SELECT * FROM users WHERE id = %s", (cursor.lastrowid,))
                return User(**cursor.fetchone())
        except Exception as e:
            logger.error("Failed to create user", extra={"error": str(e), "user": user_data.dict()})
            raise ExternalServiceError("database", "Failed to create user")

    @staticmethod
    async def update_last_login(user_id: int) -> None:
        """Update the user's last login timestamp"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user_id,),
                )
        except Exception as e:
            logger.error("Failed to update last login", extra={"error": str(e), "user_id": user_id})

    @staticmethod
    async def create_tokens(user_id: int) -> Dict[str, Any]:
        """Create access and refresh tokens for a user"""
        access_token = create_access_token(data={"sub": str(user_id), "type": "access"})
        refresh_token = create_refresh_token(user_id)

        # Store refresh token in database
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET refresh_token = %s
                    WHERE id = %s
                    """,
                    (refresh_token, user_id),
                )
        except Exception as e:
            logger.error("Failed to store refresh token", extra={"error": str(e), "user_id": user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def refresh_tokens(refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        user_id = verify_token(refresh_token)
        if not user_id:
            raise AuthenticationError("Invalid refresh token")

        # Verify refresh token is still valid in database
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE id = %s AND refresh_token = %s",
                    (user_id, refresh_token),
                )
                if not cursor.fetchone():
                    raise AuthenticationError("Invalid refresh token")
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Failed to verify refresh token", extra={"error": str(e)})
            raise AuthenticationError("Invalid refresh token")

        return await AuthService.create_tokens(user_id)

    @staticmethod
    async def logout(user_id: int) -> None:
        """Logout user by invalidating refresh token"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET refresh_token = NULL WHERE id = %s",
                    (user_id,),
                )
        except Exception as e:
            logger.error("Failed to logout user", extra={"error": str(e), "user_id": user_id})


class GoogleOAuthService:
    """Google OAuth 2.0 integration service"""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    SCOPES = [
        "openid",
        "email",
        "profile",
    ]

    @classmethod
    def get_authorization_url(cls, redirect_uri: str, state: Optional[str] = None) -> tuple[str, str]:
        """Generate Google OAuth authorization URL"""
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
        """Exchange authorization code for access token"""
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
                    "Failed to exchange code for token",
                    extra={"status": response.status_code, "body": response.text},
                )
                raise ExternalServiceError("Google", "Failed to exchange authorization code")

            return response.json()

    @classmethod
    async def get_user_info(cls, access_token: str) -> Dict[str, Any]:
        """Get user information from Google using access token"""
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(cls.USER_INFO_URL, headers=headers)

            if response.status_code != 200:
                logger.error(
                    "Failed to get user info",
                    extra={"status": response.status_code, "body": response.text},
                )
                raise ExternalServiceError("Google", "Failed to get user information")

            return response.json()

    @classmethod
    async def authenticate(cls, code: str, redirect_uri: str) -> User:
        """Complete OAuth flow and return user"""
        # Exchange code for token
        token_data = await cls.exchange_code_for_token(code, redirect_uri)

        # Get user info
        user_info = await cls.get_user_info(token_data["access_token"])

        # Check if user exists
        user = await AuthService.get_user_by_provider(Provider.GOOGLE, user_info["id"])

        if not user:
            # Create new user
            user_data = UserCreate(
                email=user_info["email"],
                name=user_info["name"],
                avatar_url=user_info.get("picture"),
                provider=Provider.GOOGLE,
                provider_id=user_info["id"],
            )
            user = await AuthService.create_user(user_data)
            logger.info("Created new user via Google OAuth", extra={"user_id": user.id})
        else:
            # Update user info
            logger.info("User logged in via Google OAuth", extra={"user_id": user.id})

        # Update last login
        await AuthService.update_last_login(user.id)

        return user
