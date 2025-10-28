"""Tests for metrics endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_get_metrics_no_auth(client: TestClient):
    """Test getting metrics without authentication."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()

    # Verify metrics structure
    assert "ai_interaction_velocity" in data
    assert "acceptance_rate" in data
    assert "model_selection_accuracy" in data
    assert "error_rate" in data
    assert "token_efficiency" in data
    assert "pr_throughput" in data
    assert "commit_frequency" in data
    assert "pr_merge_time_hours" in data
    assert "rework_rate" in data
    assert "timestamp" in data

    # Verify metric value structure
    metric = data["ai_interaction_velocity"]
    assert "value" in metric
    assert "unit" in metric or metric["unit"] is None


def test_get_metrics_with_auth(client: TestClient, auth_headers):
    """Test getting metrics with authentication."""
    response = client.get("/api/metrics", headers=auth_headers)
    assert response.status_code == 200


def test_get_metrics_with_custom_since(client: TestClient):
    """Test getting metrics with custom time window."""
    response = client.get("/api/metrics?since=14")
    assert response.status_code == 200
    data = response.json()
    assert "ai_interaction_velocity" in data


def test_get_metrics_with_invalid_since(client: TestClient):
    """Test getting metrics with invalid since value."""
    # Should default to 7 days
    response = client.get("/api/metrics?since=invalid")
    assert response.status_code == 200


def test_get_raw_metrics(client: TestClient):
    """Test getting raw metrics data."""
    response = client.get("/api/metrics/raw")
    assert response.status_code == 200
    data = response.json()

    # Should be a dictionary with metric keys
    assert isinstance(data, dict)


def test_get_raw_metrics_with_since(client: TestClient):
    """Test getting raw metrics with custom time window."""
    response = client.get("/api/metrics/raw?since=30")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_metrics_response_structure(client: TestClient):
    """Test that metrics response has proper structure."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()

    # Check each metric has proper structure
    metrics_to_check = [
        "ai_interaction_velocity",
        "acceptance_rate",
        "model_selection_accuracy",
        "error_rate",
        "token_efficiency",
        "pr_throughput",
        "commit_frequency",
        "pr_merge_time_hours",
        "rework_rate",
    ]

    for metric_name in metrics_to_check:
        assert metric_name in data
        metric_data = data[metric_name]
        assert "value" in metric_data
        assert isinstance(metric_data["value"], (int, float))
