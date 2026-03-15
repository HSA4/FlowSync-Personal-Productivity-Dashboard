"""Test Configuration and Fixtures"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.config import settings


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
        "title": "Test Task",
        "description": "Test task description",
        "completed": False,
        "priority": 2,
        "due_date": None,
        "created_at": "2025-01-15T10:00:00",
    }


@pytest.fixture
def sample_event():
    """Sample event data"""
    return {
        "id": 1,
        "title": "Test Event",
        "description": "Test event description",
        "start_time": "2025-01-15T10:00:00",
        "end_time": "2025-01-15T11:00:00",
        "all_day": False,
        "created_at": "2025-01-15T09:00:00",
    }


@pytest.fixture
def auth_headers():
    """Mock authorization headers"""
    return {"Authorization": "Bearer test-token"}
