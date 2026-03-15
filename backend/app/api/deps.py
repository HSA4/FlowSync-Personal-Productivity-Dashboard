"""API Dependencies - Auth and Common Dependencies"""
from typing import Optional
from fastapi import Header, HTTPException, status, Depends

from app.core.errors import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.services.auth import AuthService
from app.models.users import User

from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> User:
    """Get the current authenticated user from the Authorization header"""
    if not authorization:
        raise AuthenticationError("Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header format")

    token = authorization.split(" ")[1]

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", 0))

        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user = await AuthService.get_user_by_id(user_id)

        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Failed to get current user", extra={"error": str(e)})
        raise AuthenticationError("Failed to authenticate")


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None"""
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    try:
        return await get_current_user(authorization)
    except AuthenticationError:
        return None


async def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Require the current user to be active"""
    if not current_user.is_active:
        raise AuthorizationError("User account is inactive")
    return current_user


class RateLimitDependency:
    """Rate limiting dependency (placeholder for future implementation)"""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute

    async def __call__(self, current_user: User = Depends(get_current_user_optional)) -> None:
        """Check rate limit (placeholder)"""
        # TODO: Implement actual rate limiting with Redis
        pass


# Common rate limiters
standard_rate_limit = RateLimitDependency(requests_per_minute=60)
strict_rate_limit = RateLimitDependency(requests_per_minute=10)
