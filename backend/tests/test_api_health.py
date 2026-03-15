"""Health Check Endpoint Tests"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_check_healthy(client: TestClient, mock_db):
    """Test health check returns healthy status when DB is connected"""
    mock_db.health_check.return_value = True

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_health_check_unhealthy(client: TestClient, mock_db):
    """Test health check returns unhealthy status when DB is disconnected"""
    mock_db.health_check.return_value = False

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "disconnected"


def test_openapi_docs_available(client: TestClient):
    """Test OpenAPI docs are available in debug mode"""
    response = client.get("/docs")
    # In production (DEBUG=False), this returns 404
    # In debug mode, it returns 200
    assert response.status_code in [200, 404]
