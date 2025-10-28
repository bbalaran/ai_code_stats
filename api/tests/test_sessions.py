"""Tests for session endpoints."""

from fastapi.testclient import TestClient


def test_list_sessions_empty(client: TestClient):
    """Test listing sessions when no data exists."""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 0
    assert data["sessions"] == []
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["has_more"] is False


def test_list_sessions_pagination(client: TestClient):
    """Test pagination parameters."""
    response = client.get("/api/sessions?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert "page" in data
    assert data["page"] == 1
    assert "page_size" in data
    assert data["page_size"] == 10


def test_list_sessions_filters(client: TestClient):
    """Test filtering sessions."""
    # Test with developer_id filter
    response = client.get("/api/sessions?developer_id=dev123")
    assert response.status_code == 200

    # Test with model filter
    response = client.get("/api/sessions?model=claude-3-sonnet")
    assert response.status_code == 200


def test_list_sessions_sorting(client: TestClient):
    """Test sorting sessions."""
    # Test different sort options
    sort_options = [
        ("timestamp", "asc"),
        ("timestamp", "desc"),
        ("cost_usd", "asc"),
        ("cost_usd", "desc"),
        ("tokens", "asc"),
        ("tokens", "desc"),
    ]

    for sort_by, sort_order in sort_options:
        response = client.get(f"/api/sessions?sort_by={sort_by}&sort_order={sort_order}")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data


def test_get_session_details_not_found(client: TestClient):
    """Test getting non-existent session."""
    response = client.get("/api/sessions/nonexistent-session")
    assert response.status_code == 404


def test_get_session_details_response_structure(client: TestClient):
    """Test session details response structure."""
    response = client.get("/api/sessions")
    data = response.json()

    # If we have sessions, test the structure
    if data["total_count"] > 0:
        session = data["sessions"][0]
        assert "session_id" in session
        assert "developer_id" in session
        assert "timestamp" in session
        assert "model" in session
        assert "tokens_in" in session
        assert "tokens_out" in session
        assert "total_tokens" in session
        assert "latency_ms" in session
        assert "accepted_flag" in session
        assert "cost_usd" in session


def test_list_sessions_with_auth(client: TestClient, auth_headers):
    """Test listing sessions with authentication."""
    response = client.get("/api/sessions", headers=auth_headers)
    assert response.status_code == 200


def test_list_sessions_without_auth(client: TestClient):
    """Test listing sessions without authentication (should work)."""
    response = client.get("/api/sessions")
    assert response.status_code == 200
