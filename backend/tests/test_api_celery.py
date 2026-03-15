"""Celery Tasks API Tests"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime


@pytest.mark.unit
class TestCeleryTasksAPI:
    """Test Celery task management API endpoints"""

    def test_get_celery_status(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test getting Celery worker status"""
        inspector_mock = MagicMock()
        inspector_mock.active.return_value = {
            "worker1@host": [
                {
                    "id": "task-1",
                    "name": "app.tasks.sync_tasks.sync_integration",
                    "args": [1],
                }
            ]
        }
        inspector_mock.scheduled.return_value = {}
        inspector_mock.reserved.return_value = {}

        with patch("app.api.celery.celery_app.control.inspect") as mock_inspect:
            mock_inspect.return_value = inspector_mock

            response = client.get("/api/v1/tasks/status")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "workers" in data
            assert "active_tasks" in data

    def test_get_running_syncs(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test getting currently running sync tasks"""
        inspector_mock = MagicMock()
        inspector_mock.active.return_value = {
            "worker1@host": [
                {
                    "id": "task-1",
                    "name": "app.tasks.sync_tasks.sync_integration",
                    "args": [1],
                }
            ]
        }

        with patch("app.api.celery.celery_app.control.inspect") as mock_inspect:
            mock_inspect.return_value = inspector_mock

            response = client.get("/api/v1/tasks/sync/running")

            assert response.status_code == 200
            data = response.json()
            assert "running_syncs" in data
            assert "count" in data

    def test_trigger_sync_background(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
        mock_celery,
        mock_redis,
    ):
        """Test triggering a sync in background"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration

        response = client.post(
            f"/api/v1/tasks/sync/{sample_integration['id']}",
            params={"background": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data

    def test_trigger_sync_foreground(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
        mock_celery,
        mock_redis,
        mock_external_services,
    ):
        """Test triggering a sync synchronously"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration
        cursor_mock.fetchall.return_value = []
        cursor_mock.execute.return_value = None

        response = client.post(
            f"/api/v1/tasks/sync/{sample_integration['id']}",
            params={"background": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_get_sync_result_cached(
        self,
        client,
        mock_auth_required,
        mock_redis,
    ):
        """Test getting cached sync result"""
        mock_redis.get.return_value = {
            "status": "success",
            "items_synced": 5,
            "completed_at": "2025-01-15T10:00:00",
        }

        response = client.get("/api/v1/tasks/sync/result/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_sync_result_running(
        self,
        client,
        mock_auth_required,
        mock_redis,
    ):
        """Test getting sync result when running"""
        mock_redis.get.side_effect = lambda k: {"running": True} if "running" in k else None

        response = client.get("/api/v1/tasks/sync/result/1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_trigger_sync_all(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test triggering sync for all integrations"""
        response = client.post("/api/v1/tasks/sync/all")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "task_id" in data

    def test_trigger_provider_sync(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test triggering sync for a specific provider"""
        response = client.post("/api/v1/tasks/sync/provider/todoist")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["provider"] == "todoist"

    def test_trigger_provider_sync_invalid(
        self,
        client,
        mock_auth_required,
    ):
        """Test triggering sync for invalid provider"""
        response = client.post("/api/v1/tasks/sync/provider/invalid")

        assert response.status_code == 400

    def test_trigger_retry_failed(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test triggering retry for failed syncs"""
        response = client.post("/api/v1/tasks/sync/retry-failed")

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

    def test_trigger_daily_digest(
        self,
        client,
        mock_auth_required,
        mock_celery,
        mock_redis,
    ):
        """Test triggering daily digest generation"""
        mock_redis.get.return_value = None

        response = client.post("/api/v1/tasks/ai/daily-digest")

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

    def test_trigger_daily_digest_cached(
        self,
        client,
        mock_auth_required,
        mock_redis,
    ):
        """Test daily digest with cached result"""
        mock_redis.get.return_value = "Cached digest content"

        response = client.post("/api/v1/tasks/ai/daily-digest")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cached"
        assert "digest" in data

    def test_trigger_prioritize(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test triggering task prioritization"""
        response = client.post(
            "/api/v1/tasks/ai/prioritize",
            json={"task_ids": [1, 2, 3]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

    def test_trigger_suggest(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test triggering task suggestions"""
        response = client.post(
            "/api/v1/tasks/ai/suggest",
            params={"max_suggestions": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

    def test_get_task_result_ready(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test getting result of a completed task"""
        async_result_mock = MagicMock()
        async_result_mock.state = "SUCCESS"
        async_result_mock.ready.return_value = True
        async_result_mock.result = {"status": "success"}

        with patch("app.api.celery.celery_app.AsyncResult") as mock_result:
            mock_result.return_value = async_result_mock

            response = client.get("/api/v1/tasks/task/test-task-id/result")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "SUCCESS"
            assert data["ready"] is True

    def test_cancel_task(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test cancelling a Celery task"""
        async_result_mock = MagicMock()
        async_result_mock.ready.return_value = False

        with patch("app.api.celery.celery_app.AsyncResult") as mock_result:
            mock_result.return_value = async_result_mock

            response = client.post("/api/v1/tasks/task/test-task-id/cancel")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"

    def test_cancel_completed_task(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test cancelling an already completed task"""
        async_result_mock = MagicMock()
        async_result_mock.ready.return_value = True

        with patch("app.api.celery.celery_app.AsyncResult") as mock_result:
            mock_result.return_value = async_result_mock

            response = client.post("/api/v1/tasks/task/test-task-id/cancel")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "already_completed"

    def test_get_queue_stats(
        self,
        client,
        mock_auth_required,
        mock_celery,
    ):
        """Test getting queue statistics"""
        inspector_mock = MagicMock()
        inspector_mock.active.return_value = {
            "worker1@host": [
                {"id": "task-1", "name": "task1"},
                {"id": "task-2", "name": "task2"},
            ]
        }
        inspector_mock.scheduled.return_value = {}
        inspector_mock.reserved.return_value = {}

        with patch("app.api.celery.celery_app.control.inspect") as mock_inspect:
            mock_inspect.return_value = inspector_mock

            response = client.get("/api/v1/tasks/stats")

            assert response.status_code == 200
            data = response.json()
            assert "active_tasks" in data
            assert "scheduled_tasks" in data
            assert "reserved_tasks" in data


@pytest.mark.integration
class TestCeleryIntegration:
    """Integration tests for Celery tasks"""

    def test_real_celery_task_execution(self):
        """Test actual Celery task execution"""
        pytest.skip("Requires running Celery worker")

    def test_task_persistence(self):
        """Test task result persistence in Redis"""
        pytest.skip("Requires Redis instance")
