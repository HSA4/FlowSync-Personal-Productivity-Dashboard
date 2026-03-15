"""Integration API Tests"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.mark.unit
class TestIntegrationsAPI:
    """Test integration API endpoints"""

    def test_get_integrations(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
    ):
        """Test getting all integrations"""
        # Mock database response
        test_db_cursor.return_value.__enter__.return_value.fetchall.return_value = [
            sample_integration
        ]

        response = client.get("/api/v1/integrations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == sample_integration["id"]
        assert data[0]["provider"] == sample_integration["provider"]

    def test_get_integration_by_id(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
    ):
        """Test getting a specific integration"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration

        response = client.get(f"/api/v1/integrations/{sample_integration['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_integration["id"]
        assert data["name"] == sample_integration["name"]

    def test_get_integration_not_found(
        self,
        client,
        mock_auth_required,
        test_db_cursor,
    ):
        """Test getting a non-existent integration"""
        test_db_cursor.return_value.__enter__.return_value.fetchone.return_value = None

        response = client.get("/api/v1/integrations/999")

        assert response.status_code == 404

    def test_create_integration(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
    ):
        """Test creating a new integration"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration

        integration_data = {
            "name": "Test Integration",
            "provider": "todoist",
            "access_token": "test_token",
            "enabled": True,
            "settings": {},
        }

        response = client.post("/api/v1/integrations", json=integration_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    def test_update_integration(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
    ):
        """Test updating an integration"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration
        cursor_mock.execute.return_value = None

        response = client.patch(
            f"/api/v1/integrations/{sample_integration['id']}",
            params={"enabled": False},
        )

        assert response.status_code == 200

    def test_delete_integration(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
    ):
        """Test deleting an integration"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration
        cursor_mock.execute.return_value = None

        response = client.delete(f"/api/v1/integrations/{sample_integration['id']}")

        assert response.status_code == 204

    def test_sync_integration(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
        mock_external_services,
    ):
        """Test syncing an integration"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration
        cursor_mock.fetchall.return_value = []
        cursor_mock.execute.return_value = None

        response = client.post(f"/api/v1/integrations/{sample_integration['id']}/sync")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "last_sync" in data

    def test_get_available_providers(self, client):
        """Test getting available integration providers"""
        response = client.get("/api/v1/integrations/providers/available")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(p["id"] == "todoist" for p in data)
        assert any(p["id"] == "google-calendar" for p in data)

    def test_get_oauth_url_todoist(
        self,
        client,
        mock_auth_required,
    ):
        """Test getting Todoist OAuth URL"""
        with patch(
            "app.api.integrations.TodoistOAuthService.get_authorization_url"
        ) as mock_oauth:
            mock_oauth.return_value = (
                "https://todoist.com/oauth?code=test",
                "test_state",
            )

            response = client.get("/api/v1/integrations/oauth/todoist")

            assert response.status_code == 200
            data = response.json()
            assert "url" in data
            assert "state" in data

    def test_get_oauth_url_google_calendar(
        self,
        client,
        mock_auth_required,
    ):
        """Test getting Google Calendar OAuth URL"""
        with patch(
            "app.api.integrations.GoogleCalendarOAuthService.get_authorization_url"
        ) as mock_oauth:
            mock_oauth.return_value = (
                "https://accounts.google.com/oauth?code=test",
                "test_state",
            )

            response = client.get("/api/v1/integrations/oauth/google-calendar")

            assert response.status_code == 200
            data = response.json()
            assert "url" in data

    def test_oauth_callback_todoist(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
    ):
        """Test Todoist OAuth callback"""
        with patch(
            "app.api.integrations.TodoistOAuthService.exchange_code_for_token"
        ) as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "test_access_token",
            }

            cursor_mock = test_db_cursor.return_value.__enter__.return_value
            cursor_mock.fetchone.return_value = sample_integration
            cursor_mock.execute.return_value = None

            callback_data = {
                "code": "test_code",
                "redirect_uri": "http://localhost:5173/integrations/callback",
            }

            response = client.post(
                "/api/v1/integrations/oauth/todoist/callback",
                json=callback_data,
            )

            assert response.status_code == 200

    def test_webhook_todoist(
        self,
        client,
        test_db_cursor,
    ):
        """Test Todoist webhook handler"""
        webhook_data = {
            "event_name": "item:added",
            "event_id": "test_event_123",
            "user_id": "12345",
            "event_data": {
                "id": "todoist_task_1",
                "content": "Test Task",
                "description": "Test Description",
                "priority": 2,
                "is_completed": False,
            },
        }

        with patch(
            "app.api.integrations.TodoistWebhookProcessor.process_event"
        ) as mock_process:
            mock_process.return_value = {"processed": True, "action": "created"}

            response = client.post(
                "/api/v1/integrations/webhook/todoist",
                json=webhook_data,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "received"

    def test_get_sync_status(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
    ):
        """Test getting sync status"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchall.return_value = [
            {
                **sample_integration,
                "webhook_registered": "true",
                "pending_sync": "false",
            }
        ]

        response = client.get("/api/v1/integrations/sync/status")

        assert response.status_code == 200
        data = response.json()
        assert "integrations" in data
        assert "overall_status" in data

    def test_register_webhook(
        self,
        client,
        mock_auth_required,
        sample_integration,
        test_db_cursor,
        mock_external_services,
    ):
        """Test registering a webhook"""
        cursor_mock = test_db_cursor.return_value.__enter__.return_value
        cursor_mock.fetchone.return_value = sample_integration
        cursor_mock.execute.return_value = None

        with patch(
            "app.api.integrations.TodoistIntegration.create_webhook"
        ) as mock_webhook:
            mock_webhook.return_value = {"id": "webhook_123"}

            response = client.post(
                f"/api/v1/integrations/{sample_integration['id']}/webhooks/register"
            )

            assert response.status_code == 200
            data = response.json()
            assert "webhook_registered" in data


@pytest.mark.integration
class TestIntegrationsIntegration:
    """Integration tests for integrations API"""

    def test_full_oauth_flow(self, client, sample_user):
        """Test complete OAuth flow"""
        # This would require actual OAuth provider interaction
        # Marked as integration test for manual testing or with test providers
        pytest.skip("Requires actual OAuth provider")

    def test_real_sync_operation(self, client, sample_integration):
        """Test real sync with external service"""
        # This would require actual external service credentials
        pytest.skip("Requires external service credentials")
