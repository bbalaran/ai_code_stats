"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    """Test successful login."""
    response = client.post(
        "/auth/token",
        json={"username": "demo", "password": "demo123"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_invalid_credentials(client: TestClient):
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/token",
        json={"username": "demo", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/token",
        json={"username": "nonexistent", "password": "password123"},
    )
    assert response.status_code == 401


def test_valid_users(client: TestClient):
    """Test that all valid users can login."""
    valid_users = {
        "demo": "demo123",
        "pilot": "pilot123",
        "admin": "admin123",
    }

    for username, password in valid_users.items():
        response = client.post(
            "/auth/token",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


def test_refresh_token(client: TestClient):
    """Test token refresh endpoint."""
    # Get initial token
    response = client.post(
        "/auth/token",
        json={"username": "demo", "password": "demo123"},
    )
    assert response.status_code == 200

    # Refresh token
    response = client.post(
        "/auth/refresh",
        json={"username": "demo", "password": "demo123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
