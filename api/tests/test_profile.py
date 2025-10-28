"""Tests for profile endpoints."""

from fastapi.testclient import TestClient


def test_get_profile_no_data(client: TestClient):
    """Test getting profile when no data exists."""
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()

    assert data["total_sessions"] == 0
    assert data["total_tokens_used"] == 0
    assert data["total_cost_usd"] == 0.0
    assert data["avg_latency_ms"] == 0.0
    assert data["acceptance_rate"] == 0.0
    assert "most_used_models" in data
    assert "active_repos" in data
    assert "sessions_by_date" in data


def test_get_profile_response_structure(client: TestClient):
    """Test profile response structure."""
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()

    assert "developer_id" in data
    assert "total_sessions" in data
    assert "total_tokens_used" in data
    assert "total_cost_usd" in data
    assert "avg_latency_ms" in data
    assert "acceptance_rate" in data
    assert "most_used_models" in data
    assert "active_repos" in data
    assert "sessions_by_date" in data

    # Verify dimension structure
    assert isinstance(data["most_used_models"], list)
    assert isinstance(data["active_repos"], list)
    assert isinstance(data["sessions_by_date"], dict)


def test_get_profile_for_developer(client: TestClient):
    """Test getting profile for specific developer."""
    response = client.get("/api/profile?developer_id=dev123")
    assert response.status_code in [200, 404]


def test_get_profile_with_auth(client: TestClient, auth_headers):
    """Test getting profile with authentication."""
    response = client.get("/api/profile", headers=auth_headers)
    assert response.status_code == 200


def test_get_profile_dimensions(client: TestClient):
    """Test that dimension values have correct structure."""
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()

    # Check most_used_models structure
    for model in data["most_used_models"]:
        assert "value" in model
        assert "count" in model
        assert isinstance(model["count"], int)

    # Check active_repos structure
    for repo in data["active_repos"]:
        assert "value" in repo
        assert "count" in repo
        assert isinstance(repo["count"], int)
