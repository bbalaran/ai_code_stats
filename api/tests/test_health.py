"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "database_connected" in data
    assert "prodlens_cache_exists" in data


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"
