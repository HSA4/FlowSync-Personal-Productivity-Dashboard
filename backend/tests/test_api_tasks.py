"""Tasks API Endpoint Tests"""
import pytest
from unittest.mock import Mock, patch, contextmanager
from fastapi.testclient import TestClient


@pytest.fixture
def mock_cursor():
    """Mock cursor fixture"""
    cursor = Mock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    cursor.lastrowid = 1
    return cursor


@pytest.fixture
def mock_db_connection(mock_cursor):
    """Mock database connection with context manager"""
    connection = Mock()
    connection.is_connected.return_value = True

    @contextmanager
    def get_cursor(dictionary=True):
        yield mock_cursor

    connection.cursor = get_cursor
    return connection


class TestTasksEndpoint:
    """Test tasks endpoints"""

    def test_get_tasks_empty(self, client: TestClient, mock_db):
        """Test getting tasks when none exist"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {"total": 0, "completed": None}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0

    def test_get_tasks_with_data(self, client: TestClient, mock_db):
        """Test getting tasks with existing data"""
        mock_tasks = [
            {
                "id": 1,
                "title": "Task 1",
                "description": "Description 1",
                "completed": False,
                "priority": 2,
                "due_date": None,
                "created_at": "2025-01-15T10:00:00",
            },
            {
                "id": 2,
                "title": "Task 2",
                "description": "Description 2",
                "completed": True,
                "priority": 1,
                "due_date": None,
                "created_at": "2025-01-15T09:00:00",
            },
        ]

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_tasks
        mock_cursor.fetchone.return_value = {"total": 2, "completed": 1}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 2
        assert data["completed"] == 1
        assert data["pending"] == 1

    def test_get_task_by_id(self, client: TestClient, mock_db):
        """Test getting a specific task"""
        task = {
            "id": 1,
            "title": "Test Task",
            "description": "Test description",
            "completed": False,
            "priority": 2,
            "due_date": None,
            "created_at": "2025-01-15T10:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [task]  # First call returns task

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/tasks/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Task"

    def test_get_task_not_found(self, client: TestClient, mock_db):
        """Test getting a non-existent task"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/tasks/999")
        assert response.status_code == 404

    def test_create_task(self, client: TestClient, mock_db):
        """Test creating a new task"""
        new_task = {
            "id": 1,
            "title": "New Task",
            "description": "New task description",
            "completed": False,
            "priority": 2,
            "due_date": None,
            "created_at": "2025-01-15T10:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [None, new_task]

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "New Task",
                "description": "New task description",
                "priority": 2,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["id"] == 1

    def test_create_task_validation_error(self, client: TestClient):
        """Test creating a task with invalid data"""
        response = client.post("/api/v1/tasks", json={"title": ""})
        assert response.status_code == 422

    def test_update_task(self, client: TestClient, mock_db):
        """Test updating an existing task"""
        existing_task = {"id": 1}
        updated_task = {
            "id": 1,
            "title": "Updated Task",
            "description": "Updated description",
            "completed": True,
            "priority": 3,
            "due_date": None,
            "created_at": "2025-01-15T10:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [existing_task, updated_task]

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.put(
            "/api/v1/tasks/1",
            json={
                "title": "Updated Task",
                "completed": True,
                "priority": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task"
        assert data["completed"] is True

    def test_delete_task(self, client: TestClient, mock_db):
        """Test deleting a task"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 1}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.delete("/api/v1/tasks/1")
        assert response.status_code == 204

    def test_toggle_task_completion(self, client: TestClient, mock_db):
        """Test toggling task completion"""
        task_before = {"id": 1, "completed": False}
        task_after = {
            "id": 1,
            "title": "Test Task",
            "completed": True,
            "priority": 2,
            "due_date": None,
            "created_at": "2025-01-15T10:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [task_before, task_after]

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.patch("/api/v1/tasks/1/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    def test_filter_tasks_by_completed(self, client: TestClient, mock_db):
        """Test filtering tasks by completion status"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {"total": 0, "completed": None}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/tasks?completed=true")
        assert response.status_code == 200

    def test_filter_tasks_by_priority(self, client: TestClient, mock_db):
        """Test filtering tasks by priority"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {"total": 0, "completed": None}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/tasks?priority=3")
        assert response.status_code == 200
