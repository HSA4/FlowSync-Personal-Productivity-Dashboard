"""Common Response Models"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")
    timestamp: str = Field(..., description="Current timestamp")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: Dict[str, Any] = Field(..., description="Error details")


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str = Field(..., description="Response message")


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: list[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
