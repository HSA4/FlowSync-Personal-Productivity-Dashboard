"""Event Models"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class EventBase(BaseModel):
    """Base event model"""
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: Optional[str] = Field(None, max_length=5000, description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    all_day: bool = Field(default=False, description="Is this an all-day event?")

    @field_validator('end_time')
    def validate_end_time(cls, v, info):
        """Ensure end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class EventCreate(EventBase):
    """Model for creating a new event"""
    pass


class EventUpdate(BaseModel):
    """Model for updating an event"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None

    @field_validator('end_time')
    def validate_end_time(cls, v, info):
        """Ensure end_time is after start_time if both provided"""
        start_time = info.data.get('start_time')
        if start_time and v is not None and v <= start_time:
            raise ValueError('end_time must be after start_time')
        return v


class Event(EventBase):
    """Complete event model with ID"""
    id: int = Field(..., description="Event ID")
    created_at: datetime = Field(..., description="Event creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Event update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class EventList(BaseModel):
    """Response model for event list"""
    events: list[Event]
    total: int
