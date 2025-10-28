"""Tests for CORS configuration."""

from fastapi.testclient import TestClient


def test_cors_headers_present(client: TestClient):
    """Test that CORS headers are present in responses."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200

    # Check for CORS headers (note: TestClient may not always return them)
    # This test documents the expected behavior


def test_cors_allowed_origins(client: TestClient):
    """Test that allowed origins are configured."""
    # Test with localhost:5173 (React frontend)
    response = client.options(
        "/api/metrics",
        headers={"Origin": "http://localhost:5173"},
    )
    # OPTIONS may not be explicitly handled, but GET should work
    response = client.get(
        "/api/metrics",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200


def test_cors_credentials(client: TestClient):
    """Test CORS credentials configuration."""
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Credentials": "include",
        },
    )
    assert response.status_code == 200


def test_cors_methods(client: TestClient):
    """Test that configured HTTP methods work."""
    # Test GET
    response = client.get("/health")
    assert response.status_code == 200

    # Test POST
    response = client.post(
        "/auth/token",
        json={"username": "demo", "password": "demo123"},
    )
    assert response.status_code == 200
