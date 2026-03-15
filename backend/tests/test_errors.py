"""Error Handling Tests"""
import pytest
from fastapi import status

from app.core.errors import (
    FlowSyncException,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ExternalServiceError,
    DatabaseError,
)


class TestErrorClasses:
    """Test custom error classes"""

    def test_base_exception(self):
        """Test base FlowSyncException"""
        exc = FlowSyncException("Test error", status_code=500)
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_base_exception_with_details(self):
        """Test base exception with details"""
        details = {"field": "value"}
        exc = FlowSyncException("Test error", status_code=400, details=details)
        assert exc.details == details

    def test_validation_error(self):
        """Test ValidationError"""
        exc = ValidationError("Invalid input")
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.message == "Invalid input"

    def test_not_found_error(self):
        """Test NotFoundError"""
        exc = NotFoundError("Task", "123")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "Task" in exc.message
        assert "123" in exc.message

    def test_not_found_error_without_identifier(self):
        """Test NotFoundError without identifier"""
        exc = NotFoundError("Task")
        assert "Task not found" in exc.message

    def test_conflict_error(self):
        """Test ConflictError"""
        exc = ConflictError("Duplicate resource")
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_authentication_error(self):
        """Test AuthenticationError"""
        exc = AuthenticationError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication failed" in exc.message

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message"""
        exc = AuthenticationError("Invalid token")
        assert exc.message == "Invalid token"

    def test_authorization_error(self):
        """Test AuthorizationError"""
        exc = AuthorizationError()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_rate_limit_error(self):
        """Test RateLimitError"""
        exc = RateLimitError(retry_after=60)
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.details == {"retry_after": 60}

    def test_rate_limit_error_without_retry(self):
        """Test RateLimitError without retry_after"""
        exc = RateLimitError()
        assert exc.details == {}

    def test_external_service_error(self):
        """Test ExternalServiceError"""
        exc = ExternalServiceError("Todoist", "Service unavailable")
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Todoist" in exc.message

    def test_database_error(self):
        """Test DatabaseError"""
        exc = DatabaseError("Connection lost")
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
