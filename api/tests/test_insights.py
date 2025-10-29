"""Tests for insights endpoints."""

from fastapi.testclient import TestClient


def test_get_insights(client: TestClient):
    """Test getting insights."""
    response = client.get("/api/insights")
    assert response.status_code == 200
    data = response.json()

    assert "key_findings" in data
    assert "correlations" in data
    assert "recommendations" in data
    assert "anomalies" in data
    assert "generated_at" in data


def test_get_insights_response_structure(client: TestClient):
    """Test insights response structure."""
    response = client.get("/api/insights")
    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert isinstance(data["key_findings"], list)
    assert isinstance(data["correlations"], list)
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["anomalies"], list)

    # Check correlation structure if any exist
    for correlation in data["correlations"]:
        assert "variable1" in correlation
        assert "variable2" in correlation
        assert "r" in correlation
        assert "p_value" in correlation
        assert "count" in correlation
        assert "lag_days" in correlation
        assert "significant" in correlation


def test_get_insights_with_custom_since(client: TestClient):
    """Test getting insights with custom time window."""
    response = client.get("/api/insights?since=14")
    assert response.status_code == 200
    data = response.json()
    assert "key_findings" in data


def test_get_insights_with_lag_days(client: TestClient):
    """Test getting insights with custom lag days."""
    response = client.get("/api/insights?lag_days=2")
    assert response.status_code == 200
    data = response.json()
    assert "correlations" in data


def test_get_insights_findings(client: TestClient):
    """Test that findings are generated."""
    response = client.get("/api/insights")
    assert response.status_code == 200
    data = response.json()

    # Should have at least default message or findings
    assert isinstance(data["key_findings"], list)


def test_get_insights_recommendations(client: TestClient):
    """Test that recommendations are generated."""
    response = client.get("/api/insights")
    assert response.status_code == 200
    data = response.json()

    # Should have recommendations
    assert isinstance(data["recommendations"], list)


def test_get_insights_with_auth(client: TestClient, auth_headers):
    """Test getting insights with authentication."""
    response = client.get("/api/insights", headers=auth_headers)
    assert response.status_code == 200
    assert "key_findings" in response.json()


def test_get_insights_invalid_lag_days(client: TestClient):
    """Test insights with invalid lag_days."""
    # Values outside range should be clamped
    response = client.get("/api/insights?lag_days=10")
    # Should still work, value will be clamped to 7
    assert response.status_code == 200
