"""Tests for storage layer aggregation functionality."""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path

import pytest

from ..src.prodlens.storage import ProdLensStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = ProdLensStore(db_path)
        yield store
        store.close()


class TestCheckpointManagement:
    """Test checkpoint management for incremental exports."""

    def test_get_last_checkpoint_empty(self, temp_db):
        """Test getting checkpoint from empty store."""
        checkpoint = temp_db.get_last_checkpoint("test_job")
        assert checkpoint is None

    def test_set_and_get_checkpoint(self, temp_db):
        """Test setting and retrieving a checkpoint."""
        now = dt.datetime.now(tz=dt.timezone.utc)
        temp_db.set_checkpoint("test_job", now)

        checkpoint = temp_db.get_last_checkpoint("test_job")
        assert checkpoint is not None
        # Allow small time difference due to precision
        assert abs((checkpoint - now).total_seconds()) < 1

    def test_multiple_checkpoints_returns_latest(self, temp_db):
        """Test that latest checkpoint is returned."""
        base = dt.datetime(2024, 10, 1, tzinfo=dt.timezone.utc)

        temp_db.set_checkpoint("job", base)
        later = base + dt.timedelta(hours=1)
        temp_db.set_checkpoint("job", later)

        checkpoint = temp_db.get_last_checkpoint("job")
        assert checkpoint is not None
        # Should return the later checkpoint
        assert checkpoint.day == later.day
        assert checkpoint.hour == later.hour

    def test_separate_jobs_have_separate_checkpoints(self, temp_db):
        """Test that different jobs have separate checkpoints."""
        now = dt.datetime.now(tz=dt.timezone.utc)
        later = now + dt.timedelta(hours=1)

        temp_db.set_checkpoint("job1", now)
        temp_db.set_checkpoint("job2", later)

        checkpoint1 = temp_db.get_last_checkpoint("job1")
        checkpoint2 = temp_db.get_last_checkpoint("job2")

        assert checkpoint1 is not None
        assert checkpoint2 is not None
        assert checkpoint1 != checkpoint2


class TestDailySessionMetrics:
    """Test daily session metrics storage and retrieval."""

    def test_insert_daily_session_metrics_empty(self, temp_db):
        """Test inserting empty metrics."""
        count = temp_db.insert_daily_session_metrics([])
        assert count == 0

    def test_insert_daily_session_metrics_single(self, temp_db):
        """Test inserting a single metric."""
        metrics = [
            {
                "event_date": "2024-10-01",
                "developer_id": "alice",
                "session_count": 10,
                "total_tokens": 5000,
                "accepted_count": 7,
                "error_count": 1,
                "median_latency_ms": 1200.0,
                "cost_usd": 0.05,
            }
        ]

        count = temp_db.insert_daily_session_metrics(metrics)
        assert count == 1

        # Retrieve and verify
        result = temp_db.fetch_daily_session_metrics()
        assert len(result) == 1
        assert result[0]["session_count"] == 10
        assert result[0]["developer_id"] == "alice"

    def test_insert_daily_session_metrics_multiple(self, temp_db):
        """Test inserting multiple metrics."""
        metrics = [
            {
                "event_date": f"2024-10-{i:02d}",
                "developer_id": "alice" if i % 2 == 0 else "bob",
                "session_count": 5 + i,
                "total_tokens": 2500 + (i * 100),
                "accepted_count": 3 + (i % 3),
                "error_count": i % 2,
                "median_latency_ms": 1000.0 + (i * 50),
                "cost_usd": 0.02 + (i * 0.01),
            }
            for i in range(1, 6)
        ]

        count = temp_db.insert_daily_session_metrics(metrics)
        assert count == 5

        result = temp_db.fetch_daily_session_metrics()
        assert len(result) == 5

    def test_update_daily_session_metrics(self, temp_db):
        """Test updating existing metrics."""
        metrics1 = [
            {
                "event_date": "2024-10-01",
                "session_count": 10,
                "total_tokens": 5000,
                "accepted_count": 7,
                "error_count": 1,
                "median_latency_ms": 1200.0,
                "cost_usd": 0.05,
            }
        ]

        temp_db.insert_daily_session_metrics(metrics1)

        # Update the same date with new data
        metrics2 = [
            {
                "event_date": "2024-10-01",
                "session_count": 12,
                "total_tokens": 6000,
                "accepted_count": 9,
                "error_count": 1,
                "median_latency_ms": 1100.0,
                "cost_usd": 0.06,
            }
        ]

        count = temp_db.insert_daily_session_metrics(metrics2)
        assert count == 1

        result = temp_db.fetch_daily_session_metrics()
        assert len(result) == 1
        assert result[0]["session_count"] == 12  # Should be updated
        assert result[0]["total_tokens"] == 6000

    def test_fetch_daily_session_metrics_with_since_filter(self, temp_db):
        """Test fetching metrics with date filter."""
        metrics = [
            {
                "event_date": f"2024-10-{i:02d}",
                "session_count": 5 + i,
                "total_tokens": 2500 + (i * 100),
                "accepted_count": 3,
                "error_count": 0,
                "median_latency_ms": 1000.0,
                "cost_usd": 0.02,
            }
            for i in range(1, 6)
        ]

        temp_db.insert_daily_session_metrics(metrics)

        # Fetch only from a specific date
        since = dt.date(2024, 10, 3)
        result = temp_db.fetch_daily_session_metrics(since=since)

        assert len(result) == 3  # Oct 3, 4, 5
        assert all(r["event_date"] >= "2024-10-03" for r in result)


class TestDailyGithubMetrics:
    """Test daily GitHub metrics storage and retrieval."""

    def test_insert_daily_github_metrics_empty(self, temp_db):
        """Test inserting empty metrics."""
        count = temp_db.insert_daily_github_metrics([])
        assert count == 0

    def test_insert_daily_github_metrics_single(self, temp_db):
        """Test inserting a single metric."""
        metrics = [
            {
                "event_date": "2024-10-01",
                "merged_pr_count": 3,
                "commit_count": 15,
                "reopened_pr_count": 0,
                "avg_merge_hours": 4.5,
            }
        ]

        count = temp_db.insert_daily_github_metrics(metrics)
        assert count == 1

        result = temp_db.fetch_daily_github_metrics()
        assert len(result) == 1
        assert result[0]["merged_pr_count"] == 3
        assert result[0]["commit_count"] == 15

    def test_insert_daily_github_metrics_multiple(self, temp_db):
        """Test inserting multiple metrics."""
        metrics = [
            {
                "event_date": f"2024-10-{i:02d}",
                "merged_pr_count": 2 + i,
                "commit_count": 10 + (i * 2),
                "reopened_pr_count": i % 2,
                "avg_merge_hours": 3.0 + (i * 0.5),
            }
            for i in range(1, 6)
        ]

        count = temp_db.insert_daily_github_metrics(metrics)
        assert count == 5

        result = temp_db.fetch_daily_github_metrics()
        assert len(result) == 5

    def test_update_daily_github_metrics(self, temp_db):
        """Test updating existing GitHub metrics."""
        metrics1 = [
            {
                "event_date": "2024-10-01",
                "merged_pr_count": 3,
                "commit_count": 15,
                "reopened_pr_count": 0,
                "avg_merge_hours": 4.5,
            }
        ]

        temp_db.insert_daily_github_metrics(metrics1)

        # Update with new data
        metrics2 = [
            {
                "event_date": "2024-10-01",
                "merged_pr_count": 4,
                "commit_count": 18,
                "reopened_pr_count": 1,
                "avg_merge_hours": 5.0,
            }
        ]

        count = temp_db.insert_daily_github_metrics(metrics2)
        assert count == 1

        result = temp_db.fetch_daily_github_metrics()
        assert len(result) == 1
        assert result[0]["merged_pr_count"] == 4
        assert result[0]["commit_count"] == 18


class TestCorrelationCache:
    """Test correlation caching functionality."""

    def test_insert_correlation_cache_empty(self, temp_db):
        """Test inserting empty correlations."""
        count = temp_db.insert_correlation_cache([])
        assert count == 0

    def test_insert_correlation_cache_single(self, temp_db):
        """Test inserting a single correlation."""
        correlations = [
            {
                "correlation_date": "2024-10-15",
                "lag_days": 1,
                "pearson_r": 0.45,
                "pearson_p": 0.05,
                "spearman_r": 0.48,
                "spearman_p": 0.04,
                "sample_size": 14,
            }
        ]

        count = temp_db.insert_correlation_cache(correlations)
        assert count == 1

    def test_insert_correlation_cache_multiple_lags(self, temp_db):
        """Test inserting correlations for multiple lag days."""
        correlations = [
            {
                "correlation_date": "2024-10-15",
                "lag_days": lag,
                "pearson_r": 0.40 + (lag * 0.05),
                "pearson_p": 0.08 - (lag * 0.02),
                "spearman_r": 0.42 + (lag * 0.05),
                "spearman_p": 0.07 - (lag * 0.02),
                "sample_size": 14 - lag,
            }
            for lag in range(1, 4)
        ]

        count = temp_db.insert_correlation_cache(correlations)
        assert count == 3

    def test_update_correlation_cache(self, temp_db):
        """Test updating cached correlations."""
        corr1 = [
            {
                "correlation_date": "2024-10-15",
                "lag_days": 1,
                "pearson_r": 0.45,
                "pearson_p": 0.05,
                "spearman_r": 0.48,
                "spearman_p": 0.04,
                "sample_size": 14,
            }
        ]

        temp_db.insert_correlation_cache(corr1)

        # Update with new values
        corr2 = [
            {
                "correlation_date": "2024-10-15",
                "lag_days": 1,
                "pearson_r": 0.50,
                "pearson_p": 0.03,
                "spearman_r": 0.52,
                "spearman_p": 0.02,
                "sample_size": 15,
            }
        ]

        count = temp_db.insert_correlation_cache(corr2)
        assert count == 1


class TestSchemaIntegration:
    """Test integration of all schema components."""

    def test_complete_workflow(self, temp_db):
        """Test a complete workflow using all aggregation features."""
        # Insert session metrics
        session_metrics = [
            {
                "event_date": "2024-10-01",
                "session_count": 10,
                "total_tokens": 5000,
                "accepted_count": 7,
                "error_count": 1,
                "median_latency_ms": 1200.0,
                "cost_usd": 0.05,
            }
        ]
        session_count = temp_db.insert_daily_session_metrics(session_metrics)
        assert session_count == 1

        # Insert GitHub metrics
        github_metrics = [
            {
                "event_date": "2024-10-01",
                "merged_pr_count": 3,
                "commit_count": 15,
                "reopened_pr_count": 0,
                "avg_merge_hours": 4.5,
            }
        ]
        github_count = temp_db.insert_daily_github_metrics(github_metrics)
        assert github_count == 1

        # Set a checkpoint
        checkpoint_time = dt.datetime(2024, 10, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
        temp_db.set_checkpoint("daily_aggregation", checkpoint_time)

        # Cache a correlation
        correlations = [
            {
                "correlation_date": "2024-10-01",
                "lag_days": 1,
                "pearson_r": 0.45,
                "pearson_p": 0.05,
                "spearman_r": 0.48,
                "spearman_p": 0.04,
                "sample_size": 1,
            }
        ]
        corr_count = temp_db.insert_correlation_cache(correlations)
        assert corr_count == 1

        # Verify all data persists
        assert len(temp_db.fetch_daily_session_metrics()) == 1
        assert len(temp_db.fetch_daily_github_metrics()) == 1
        assert temp_db.get_last_checkpoint("daily_aggregation") is not None
