"""Models Package"""
from app.models.tasks import Task, TaskCreate, TaskUpdate, TaskList, Priority
from app.models.events import Event, EventCreate, EventUpdate, EventList
from app.models.users import (
    User,
    UserCreate,
    UserUpdate,
    UserInDB,
    Token,
    TokenPayload,
    OAuthCallback,
    OAuthURL,
    LoginRequest,
    RegisterRequest,
    Provider,
)
from app.models.common import (
    HealthResponse,
    ErrorResponse,
    MessageResponse,
    PaginationParams,
    PaginatedResponse,
)

__all__ = [
    # Tasks
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskList",
    "Priority",
    # Events
    "Event",
    "EventCreate",
    "EventUpdate",
    "EventList",
    # Users
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "Token",
    "TokenPayload",
    "OAuthCallback",
    "OAuthURL",
    "LoginRequest",
    "RegisterRequest",
    "Provider",
    # Common
    "HealthResponse",
    "ErrorResponse",
    "MessageResponse",
    "PaginationParams",
    "PaginatedResponse",
]
