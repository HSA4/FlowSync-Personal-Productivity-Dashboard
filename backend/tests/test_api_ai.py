"""AI API Tests"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.unit
class TestAIAPI:
    """Test AI API endpoints"""

    def test_parse_task_success(
        self,
        client,
        mock_auth_required,
    ):
        """Test natural language task parsing"""
        with patch("app.api.ai.OpenRouterService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            mock_instance.chat.return_value = {
                "content": """```json
{
    "title": "Complete project report",
    "description": "Write and submit the quarterly project report",
    "priority": 3,
    "due_date": "2025-01-20"
}
```"""
            }

            response = client.post(
                "/api/v1/ai/parse-task",
                json={"text": "I need to complete my project report by Friday"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "title" in data
            assert "priority" in data

    def test_parse_task_empty_text(
        self,
        client,
        mock_auth_required,
    ):
        """Test parsing with empty text"""
        response = client.post(
            "/api/v1/ai/parse-task",
            json={"text": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_suggest_tasks(
        self,
        client,
        mock_auth_required,
    ):
        """Test task suggestions"""
        with patch("app.api.ai.OpenRouterService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            mock_instance.chat.return_value = {
                "content": """```json
[
    {"title": "Review quarterly goals", "description": "Assess progress on Q1 objectives"},
    {"title": "Schedule team meeting", "description": "Organize weekly sync"},
    {"title": "Update documentation", "description": "Add new API endpoints to docs"}
]
```"""
            }

            response = client.post(
                "/api/v1/ai/suggest-tasks",
                json={"max_suggestions": 3},
            )

            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data
            assert isinstance(data["suggestions"], list)

    def test_prioritize_tasks(
        self,
        client,
        mock_auth_required,
    ):
        """Test task prioritization"""
        with patch("app.api.ai.OpenRouterService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            mock_instance.chat.return_value = {
                "content": """```json
[1, 3, 2]
```"""
            }

            response = client.post(
                "/api/v1/ai/prioritize-tasks",
                json={"task_ids": [1, 2, 3]},
            )

            assert response.status_code == 200
            data = response.json()
            assert "priorities" in data

    def test_get_ai_status_enabled(
        self,
        client,
        mock_auth_required,
    ):
        """Test AI status when enabled"""
        with patch("app.api.ai.OpenRouterService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.is_configured.return_value = True

            response = client.get("/api/v1/ai/status")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True

    def test_get_ai_status_disabled(
        self,
        client,
        mock_auth_required,
    ):
        """Test AI status when disabled"""
        with patch("app.api.ai.OpenRouterService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.is_configured.return_value = False

            response = client.get("/api/v1/ai/status")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is False

    def test_get_ai_models(
        self,
        client,
        mock_auth_required,
    ):
        """Test getting available AI models"""
        with patch("app.api.ai.OpenRouterService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            mock_instance.get_available_models.return_value = [
                {"id": "model1", "name": "Model 1"},
                {"id": "model2", "name": "Model 2"},
            ]

            response = client.get("/api/v1/ai/models")

            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert isinstance(data["models"], list)

    def test_parse_task_ai_error(
        self,
        client,
        mock_auth_required,
    ):
        """Test parsing when AI service fails"""
        with patch("app.api.ai.OpenRouterService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            mock_instance.chat.side_effect = Exception("AI service unavailable")

            response = client.post(
                "/api/v1/ai/parse-task",
                json={"text": "Test task"},
            )

            assert response.status_code == 500


@pytest.mark.integration
class TestAIIntegration:
    """Integration tests for AI API"""

    def test_real_ai_call(self, client):
        """Test actual AI service call (requires API key)"""
        pytest.skip("Requires OpenRouter API key")

    def test_end_to_end_task_creation(self, client):
        """Test complete flow from parsing to task creation"""
        pytest.skip("Requires full system setup")
