"""Authentication API Routes"""
from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from app.models.users import (
    Token,
    OAuthURL,
    OAuthCallback,
    User,
    LoginRequest,
    RegisterRequest,
    MessageResponse,
)
from app.services.auth import AuthService, GoogleOAuthService
from app.api.deps import get_current_user, require_active_user
from app.core.config import settings
from app.core.errors import AuthenticationError, ValidationError, NotFoundError
from app.core.logging import get_logger

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(require_active_user)):
    """Get the current authenticated user's information"""
    return current_user


@router.post("/login", response_model=Token)
async def login_with_password(credentials: LoginRequest):
    """Login with email and password (not implemented yet)"""
    # TODO: Implement email/password authentication
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email/password authentication not yet implemented",
    )


@router.post("/register", response_model=Token)
async def register_with_password(data: RegisterRequest):
    """Register with email and password (not implemented yet)"""
    # TODO: Implement email/password registration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email/password registration not yet implemented",
    )


@router.get("/oauth/google", response_model=OAuthURL)
async def get_google_oauth_url(
    redirect_uri: Optional[str] = Query(
        None, description="Override the default redirect URI (for development)"
    )
):
    """Get the Google OAuth authorization URL"""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
    if not redirect_uri:
        raise ValidationError("redirect_uri", "Must provide redirect_uri or set GOOGLE_REDIRECT_URI")

    url, state = GoogleOAuthService.get_authorization_url(redirect_uri)

    return OAuthURL(url=url, state=state)


@router.post("/oauth/google/callback", response_model=Token)
async def google_oauth_callback(callback: OAuthCallback):
    """Handle Google OAuth callback"""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )

    try:
        # Authenticate with Google
        user = await GoogleOAuthService.authenticate(
            callback.code,
            callback.redirect_uri or settings.GOOGLE_REDIRECT_URI,
        )

        # Create tokens
        tokens = await AuthService.create_tokens(user.id)

        logger.info("User authenticated via Google OAuth", extra={"user_id": user.id})

        return tokens

    except Exception as e:
        logger.error("Google OAuth failed", extra={"error": str(e)})
        raise AuthenticationError("Failed to authenticate with Google")


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh an access token using a refresh token"""
    try:
        tokens = await AuthService.refresh_tokens(refresh_token)
        return tokens
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Token refresh failed", extra={"error": str(e)})
        raise AuthenticationError("Failed to refresh token")


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(require_active_user)):
    """Logout the current user"""
    try:
        await AuthService.logout(current_user.id)
        return MessageResponse(message="Successfully logged out")
    except Exception as e:
        logger.error("Logout failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )


@router.get("/providers", response_model=list[str])
async def get_available_providers():
    """Get list of available authentication providers"""
    providers = ["google"]

    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        return providers
    else:
        return []
