"""Test Configuration and Fixtures"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Generator
import tempfile
import os

from app.main import app
from app.core.config import settings
from app.db.database import db


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database fixture"""
    with patch("app.api.tasks.db") as mock:
        yield mock


@pytest.fixture
def sample_task():
    """Sample task data"""
    return {
        "id": 1,
        "user_id": 1,
        "title": "Test Task",
        "description": "Test task description",
        "completed": False,
        "priority": 2,
        "status": "pending",
        "due_date": None,
        "external_id": None,
        "external_provider": None,
        "created_at": "2025-01-15T10:00:00",
        "updated_at": None,
    }


@pytest.fixture
def sample_event():
    """Sample event data"""
    return {
        "id": 1,
        "user_id": 1,
        "title": "Test Event",
        "description": "Test event description",
        "start_time": "2025-01-15T10:00:00",
        "end_time": "2025-01-15T11:00:00",
        "external_id": None,
        "external_provider": None,
        "created_at": "2025-01-15T09:00:00",
        "updated_at": None,
    }


@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.jpg",
        "provider": "google",
        "provider_id": "123456789",
        "is_active": True,
        "created_at": "2025-01-15T00:00:00",
    }


@pytest.fixture
def sample_integration():
    """Sample integration data"""
    return {
        "id": 1,
        "user_id": 1,
        "name": "Todoist",
        "provider": "todoist",
        "access_token": "test_token_123",
        "enabled": True,
        "settings": {},
        "last_sync": None,
        "created_at": "2025-01-15T00:00:00",
        "updated_at": None,
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client fixture"""
    with patch("app.core.redis_client.get_redis_client") as mock:
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.delete.return_value = 1
        redis_mock.exists.return_value = False
        redis_mock.keys.return_value = []
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_celery():
    """Mock Celery app fixture"""
    with patch("app.core.celery_app.celery_app") as mock:
        # Mock task result
        async_result_mock = MagicMock()
        async_result_mock.id = "test-task-id"
        async_result_mock.state = "PENDING"
        async_result_mock.ready.return_value = False
        async_result_mock.result = None

        # Mock delay method
        task_mock = MagicMock()
        task_mock.delay.return_value = async_result_mock
        task_mock.apply_async.return_value = async_result_mock

        mock.send_task = task_mock
        mock.AsyncResult.return_value = async_result_mock

        yield mock


@pytest.fixture
def auth_headers(sample_user):
    """Mock authorization headers with valid JWT"""
    # Create a mock JWT token
    import jwt
    from app.core.config import settings

    token_data = {
        "sub": str(sample_user["id"]),
        "email": sample_user["email"],
        "provider": sample_user["provider"],
        "exp": datetime.utcnow() + timedelta(hours=24),
    }

    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_auth_required(sample_user):
    """Mock the require_active_user dependency"""
    with patch("app.api.deps.require_active_user") as mock:
        user_mock = MagicMock()
        user_mock.id = sample_user["id"]
        user_mock.email = sample_user["email"]
        user_mock.name = sample_user["name"]
        user_mock.provider = sample_user["provider"]
        mock.return_value = user_mock
        yield mock


@pytest.fixture
def mock_external_services():
    """Mock external service calls (Todoist, Google Calendar, OpenRouter)"""
    with patch("app.services.integrations.httpx.AsyncClient") as httpx_mock:
        # Mock HTTP response
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = []
        response_mock.text = "OK"

        client_mock = MagicMock()
        client_mock.get.return_value = response_mock
        client_mock.post.return_value = response_mock
        client_mock.patch.return_value = response_mock
        client_mock.delete.return_value = response_mock

        httpx_mock.return_value.__aenter__.return_value = client_mock
        yield httpx_mock


@pytest.fixture
def test_db_cursor():
    """Mock database cursor with context manager"""
    with patch("app.db.database.db.get_cursor") as mock:
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None
        cursor_mock.fetchall.return_value = []
        cursor_mock.execute.return_value = None
        mock.return_value.__enter__.return_value = cursor_mock
        mock.return_value.__exit__.return_value = None
        yield mock


class TestDatabase:
    """Test database helper class"""

    def __init__(self):
        self.test_data: Dict[str, Any] = {
            "users": [],
            "tasks": [],
            "events": [],
            "integrations": [],
        }

    def add_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Add a test user"""
        user["id"] = len(self.test_data["users"]) + 1
        self.test_data["users"].append(user)
        return user

    def add_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Add a test task"""
        task["id"] = len(self.test_data["tasks"]) + 1
        self.test_data["tasks"].append(task)
        return task

    def get_task(self, task_id: int) -> Dict[str, Any]:
        """Get a test task by ID"""
        for task in self.test_data["tasks"]:
            if task["id"] == task_id:
                return task
        return None

    def clear(self):
        """Clear all test data"""
        self.test_data = {
            "users": [],
            "tasks": [],
            "events": [],
            "integrations": [],
        }


@pytest.fixture
def test_db():
    """Test database fixture"""
    return TestDatabase()


# Async fixtures for testing async endpoints

@pytest_asyncio.fixture
async def async_client():
    """Async test client fixture"""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# Environment setup for tests

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before all tests"""
    # Set test environment variables
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"

    yield

    # Cleanup after tests
    pass


# Pytest configuration

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )
