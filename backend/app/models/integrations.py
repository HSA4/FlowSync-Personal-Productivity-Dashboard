"""Integration Models"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class IntegrationBase(BaseModel):
    """Base integration model"""
    name: str = Field(..., description="Integration name")
    provider: str = Field(..., description="Provider identifier")
    enabled: bool = Field(default=False, description="Is integration enabled")


class IntegrationCreate(IntegrationBase):
    """Model for creating an integration"""
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Integration-specific settings")


class IntegrationUpdate(BaseModel):
    """Model for updating an integration"""
    enabled: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class Integration(IntegrationBase):
    """Complete integration model"""
    id: int = Field(..., description="Integration ID")
    user_id: int = Field(..., description="User ID")
    access_token: str = Field(..., description="Encrypted access token")
    settings: Dict[str, Any] = Field(default_factory=dict)
    last_sync: Optional[datetime] = Field(None, description="Last successful sync")
    created_at: datetime = Field(..., description="Integration creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class SyncStatus(BaseModel):
    """Sync status model"""
    integration_id: int = Field(..., description="Integration ID")
    status: str = Field(..., description="Sync status: pending, in_progress, success, error")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    next_sync: Optional[datetime] = Field(None, description="Next scheduled sync")
    error_message: Optional[str] = Field(None, description="Error message if status is error")


class WebhookEvent(BaseModel):
    """Webhook event model"""
    provider: str = Field(..., description="Integration provider")
    event_type: str = Field(..., description="Event type")
    event_id: str = Field(..., description="Unique event identifier")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(..., description="Event timestamp")


class TodoistTaskSchema(BaseModel):
    """Todoist task schema for mapping"""
    id: str = Field(..., description="Todoist task ID")
    content: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: int = Field(..., description="Task priority (1-4)")
    due: Optional[Dict[str, Any]] = Field(None, description="Due date info")
    is_completed: bool = Field(..., description="Task completion status")
    created_at: str = Field(..., description="Creation timestamp")


class GoogleCalendarEventSchema(BaseModel):
    """Google Calendar event schema for mapping"""
    id: str = Field(..., description="Event ID")
    summary: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start: Dict[str, str] = Field(..., description="Event start time")
    end: Dict[str, str] = Field(..., description="Event end time")
    created: str = Field(..., description="Creation timestamp")
