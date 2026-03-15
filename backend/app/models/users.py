"""User Models"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class Provider(str, Enum):
    """OAuth providers"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    EMAIL = "email"


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr = Field(..., description="User email")
    name: str = Field(..., min_length=1, max_length=255, description="User display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")


class UserCreate(UserBase):
    """Model for creating a new user (internal)"""
    provider: Provider = Field(..., description="Authentication provider")
    provider_id: str = Field(..., description="Provider-specific user ID")


class UserUpdate(BaseModel):
    """Model for updating user profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class User(UserBase):
    """Complete user model"""
    id: int = Field(..., description="User ID")
    provider: Provider = Field(..., description="Authentication provider")
    provider_id: str = Field(..., description="Provider-specific user ID")
    is_active: bool = Field(default=True, description="User account status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class UserInDB(User):
    """User model with sensitive data (for internal use)"""
    refresh_token: Optional[str] = Field(None, description="Current refresh token")


class Token(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenPayload(BaseModel):
    """Token payload model"""
    sub: str = Field(..., description="User ID")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: Optional[str] = Field(None, description="Token type (access/refresh)")


class OAuthCallback(BaseModel):
    """OAuth callback request model"""
    code: str = Field(..., description="OAuth authorization code")
    state: Optional[str] = Field(None, description="OAuth state parameter")
    redirect_uri: Optional[str] = Field(None, description="OAuth redirect URI")


class OAuthURL(BaseModel):
    """OAuth URL response model"""
    url: str = Field(..., description="OAuth authorization URL")
    state: str = Field(..., description="OAuth state parameter")


class LoginRequest(BaseModel):
    """Email/password login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """Email/password registration request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    name: str = Field(..., min_length=1, max_length=255, description="User display name")

    @validator("password")
    def password_strength(cls, v):
        """Ensure password has minimum complexity"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
