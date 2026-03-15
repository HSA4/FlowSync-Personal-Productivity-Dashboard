"""Task Models"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from enum import IntEnum


class Priority(IntEnum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskBase(BaseModel):
    """Base task model"""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=5000, description="Task description")
    completed: bool = Field(default=False, description="Task completion status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Task priority")
    due_date: Optional[date] = Field(None, description="Task due date")


class TaskCreate(TaskBase):
    """Model for creating a new task"""
    pass


class TaskUpdate(BaseModel):
    """Model for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
    due_date: Optional[date] = None

    @field_validator('title', 'description', mode='before')
    def strip_whitespace(cls, v):
        """Strip whitespace from string fields"""
        if v is not None:
            return v.strip()
        return v


class Task(TaskBase):
    """Complete task model with ID"""
    id: int = Field(..., description="Task ID")
    user_id: Optional[int] = Field(None, description="User ID")
    status: Optional[str] = Field(None, description="Task status: pending or completed")
    external_id: Optional[str] = Field(None, description="External task ID from integration")
    external_provider: Optional[str] = Field(None, description="External provider: todoist, etc.")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Task update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class TaskList(BaseModel):
    """Response model for task list"""
    tasks: list[Task]
    total: int
    completed: int
    pending: int
