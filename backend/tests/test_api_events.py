"""Events API Endpoint Tests"""
import pytest
from unittest.mock import Mock, contextmanager
from fastapi.testclient import TestClient


class TestEventsEndpoint:
    """Test events endpoints"""

    def test_get_events_empty(self, client: TestClient, mock_db):
        """Test getting events when none exist"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {"total": 0}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0

    def test_get_events_with_data(self, client: TestClient, mock_db):
        """Test getting events with existing data"""
        mock_events = [
            {
                "id": 1,
                "title": "Event 1",
                "description": "Description 1",
                "start_time": "2025-01-15T10:00:00",
                "end_time": "2025-01-15T11:00:00",
                "all_day": False,
                "created_at": "2025-01-15T09:00:00",
            },
        ]

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_events
        mock_cursor.fetchone.return_value = {"total": 1}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["total"] == 1

    def test_get_event_by_id(self, client: TestClient, mock_db):
        """Test getting a specific event"""
        event = {
            "id": 1,
            "title": "Test Event",
            "description": "Test description",
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:00:00",
            "all_day": False,
            "created_at": "2025-01-15T09:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = event

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/events/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Event"

    def test_get_event_not_found(self, client: TestClient, mock_db):
        """Test getting a non-existent event"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get("/api/v1/events/999")
        assert response.status_code == 404

    def test_create_event(self, client: TestClient, mock_db):
        """Test creating a new event"""
        new_event = {
            "id": 1,
            "title": "New Event",
            "description": "New event description",
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:00:00",
            "all_day": False,
            "created_at": "2025-01-15T09:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [None, new_event]

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.post(
            "/api/v1/events",
            json={
                "title": "New Event",
                "description": "New event description",
                "start_time": "2025-01-15T10:00:00",
                "end_time": "2025-01-15T11:00:00",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Event"
        assert data["id"] == 1

    def test_create_event_validation_error_end_before_start(self, client: TestClient):
        """Test creating an event with end_time before start_time"""
        response = client.post(
            "/api/v1/events",
            json={
                "title": "Invalid Event",
                "start_time": "2025-01-15T11:00:00",
                "end_time": "2025-01-15T10:00:00",
            },
        )
        assert response.status_code == 422

    def test_update_event(self, client: TestClient, mock_db):
        """Test updating an existing event"""
        existing_event = {"id": 1}
        updated_event = {
            "id": 1,
            "title": "Updated Event",
            "description": "Updated description",
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T12:00:00",
            "all_day": False,
            "created_at": "2025-01-15T09:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [existing_event, updated_event]

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.put(
            "/api/v1/events/1",
            json={
                "title": "Updated Event",
                "end_time": "2025-01-15T12:00:00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Event"

    def test_delete_event(self, client: TestClient, mock_db):
        """Test deleting an event"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {"id": 1}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.delete("/api/v1/events/1")
        assert response.status_code == 204

    def test_filter_events_by_date_range(self, client: TestClient, mock_db):
        """Test filtering events by date range"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {"total": 0}

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.get(
            "/api/v1/events?start_date=2025-01-01&end_date=2025-01-31"
        )
        assert response.status_code == 200

    def test_create_all_day_event(self, client: TestClient, mock_db):
        """Test creating an all-day event"""
        new_event = {
            "id": 1,
            "title": "All Day Event",
            "description": None,
            "start_time": "2025-01-15T00:00:00",
            "end_time": "2025-01-16T00:00:00",
            "all_day": True,
            "created_at": "2025-01-15T09:00:00",
        }

        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_cursor.fetchone.side_effect = [None, new_event]

        @contextmanager
        def get_cursor(dictionary=True):
            yield mock_cursor

        mock_db.get_cursor = get_cursor

        response = client.post(
            "/api/v1/events",
            json={
                "title": "All Day Event",
                "start_time": "2025-01-15T00:00:00",
                "end_time": "2025-01-16T00:00:00",
                "all_day": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["all_day"] is True
