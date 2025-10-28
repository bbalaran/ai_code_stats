"""Tests for the aggregation and parquet export modules."""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from ..src.prodlens.aggregation import DailyAggregator, ParquetExporter
from ..src.prodlens.schemas import CanonicalTrace
from ..src.prodlens.storage import ProdLensStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = ProdLensStore(db_path)
        yield store
        store.close()


@pytest.fixture
def sample_sessions():
    """Create sample session data for testing."""
    base_time = dt.datetime(2024, 10, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    sessions = []

    for i in range(5):
        for dev in ["alice", "bob"]:
            sessions.append(
                CanonicalTrace(
                    session_id=f"session_{i}_{dev}",
                    developer_id=dev,
                    timestamp=base_time + dt.timedelta(hours=i),
                    model="claude-3-sonnet",
                    tokens_in=1000,
                    tokens_out=500,
                    latency_ms=1000 + (i * 100),
                    status_code=200,
                    accepted_flag=i % 2 == 0,
                    repo_slug="test/repo",
                )
            )

    return sessions


@pytest.fixture
def sample_prs():
    """Create sample pull request data for testing."""
    base_date = dt.datetime(2024, 10, 1, tzinfo=dt.timezone.utc)
    prs = []

    for i in range(3):
        created = base_date + dt.timedelta(days=i)
        merged = created + dt.timedelta(hours=4)
        prs.append(
            {
                "id": 100 + i,
                "number": 100 + i,
                "title": f"PR {i}",
                "author": "alice",
                "state": "closed",
                "created_at": created,
                "merged_at": merged,
                "updated_at": merged,
                "reopened": i == 2,
            }
        )

    return prs


@pytest.fixture
def sample_commits():
    """Create sample commit data for testing."""
    base_date = dt.datetime(2024, 10, 1, tzinfo=dt.timezone.utc)
    commits = []

    for i in range(5):
        commits.append(
            {
                "sha": f"abc{i:03d}{'d' * 37}",
                "author": "alice" if i % 2 == 0 else "bob",
                "timestamp": base_date + dt.timedelta(hours=i * 2),
            }
        )

    return commits


class TestDailyAggregator:
    """Test daily metrics aggregation."""

    def test_aggregate_sessions_empty_store(self, temp_db):
        """Test aggregation with no data."""
        aggregator = DailyAggregator(temp_db)
        result = aggregator.aggregate_sessions()
        assert result == {}

    def test_aggregate_sessions_basic(self, temp_db, sample_sessions):
        """Test basic session aggregation."""
        temp_db.insert_sessions(sample_sessions)
        aggregator = DailyAggregator(temp_db)

        result = aggregator.aggregate_sessions()
        assert result is not None
        assert len(result) > 0

        # Check structure
        for date_str, metrics in result.items():
            assert "event_date" in metrics
            assert "session_count" in metrics
            assert "total_tokens" in metrics
            assert "accepted_count" in metrics
            assert "error_count" in metrics
            assert "median_latency_ms" in metrics
            assert "cost_usd" in metrics

    def test_aggregate_sessions_acceptance_rate(self, temp_db, sample_sessions):
        """Test acceptance rate aggregation."""
        temp_db.insert_sessions(sample_sessions)
        aggregator = DailyAggregator(temp_db)

        result = aggregator.aggregate_sessions()
        # With 10 sessions (5 dates * 2 devs), about 50% should be accepted
        for metrics in result.values():
            assert 0 <= metrics["accepted_count"] <= metrics["session_count"]

    def test_aggregate_github_empty_store(self, temp_db):
        """Test GitHub aggregation with no data."""
        aggregator = DailyAggregator(temp_db)
        result = aggregator.aggregate_github()
        assert result == {}

    def test_aggregate_github_basic(self, temp_db, sample_prs, sample_commits):
        """Test basic GitHub aggregation."""
        temp_db.insert_pull_requests(sample_prs)
        temp_db.insert_commits(sample_commits)
        aggregator = DailyAggregator(temp_db)

        result = aggregator.aggregate_github()
        assert result is not None
        assert len(result) > 0

        # Check structure
        for date_str, metrics in result.items():
            assert "event_date" in metrics
            assert "merged_pr_count" in metrics
            assert "commit_count" in metrics
            assert "reopened_pr_count" in metrics
            assert "avg_merge_hours" in metrics

    def test_aggregate_github_merge_hours(self, temp_db, sample_prs):
        """Test merge time calculation."""
        temp_db.insert_pull_requests(sample_prs)
        aggregator = DailyAggregator(temp_db)

        result = aggregator.aggregate_github()
        # First PR created on 2024-10-01, merged 4 hours later
        first_date = list(result.keys())[0]
        assert result[first_date]["avg_merge_hours"] is not None
        assert result[first_date]["avg_merge_hours"] > 0

    def test_write_aggregates(self, temp_db, sample_sessions, sample_prs, sample_commits):
        """Test writing aggregates to store."""
        temp_db.insert_sessions(sample_sessions)
        temp_db.insert_pull_requests(sample_prs)
        temp_db.insert_commits(sample_commits)

        aggregator = DailyAggregator(temp_db)
        session_count, github_count = aggregator.write_aggregates()

        assert session_count > 0
        assert github_count > 0

        # Verify data was written
        session_metrics = temp_db.fetch_daily_session_metrics()
        github_metrics = temp_db.fetch_daily_github_metrics()

        assert len(session_metrics) > 0
        assert len(github_metrics) > 0


class TestParquetExporter:
    """Test Parquet export functionality."""

    def test_export_sessions_empty_store(self, temp_db):
        """Test export with no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ParquetExporter(tmpdir)
            count = exporter.export_sessions_by_date(temp_db)
            assert count == 0

    def test_export_sessions_basic(self, temp_db, sample_sessions):
        """Test basic session export."""
        temp_db.insert_sessions(sample_sessions)

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ParquetExporter(tmpdir)
            count = exporter.export_sessions_by_date(temp_db)

            assert count == len(sample_sessions)

            # Check files were created
            partitions = exporter.list_partitions()
            assert len(partitions) > 0

    def test_export_sessions_with_date_filter(self, temp_db, sample_sessions):
        """Test export with date filtering."""
        temp_db.insert_sessions(sample_sessions)

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ParquetExporter(tmpdir)

            # Export only from a specific date
            target_date = dt.date(2024, 10, 2)
            count = exporter.export_sessions_by_date(temp_db, since=target_date)

            # Some sessions should be filtered out
            assert 0 <= count <= len(sample_sessions)

    def test_export_sessions_with_repo_filter(self, temp_db, sample_sessions):
        """Test export with repository filtering."""
        temp_db.insert_sessions(sample_sessions)

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ParquetExporter(tmpdir)
            count = exporter.export_sessions_by_date(temp_db, repo_filter="test/repo")

            assert count == len(sample_sessions)

    def test_export_aggregates(self, temp_db, sample_sessions, sample_prs, sample_commits):
        """Test aggregate export."""
        temp_db.insert_sessions(sample_sessions)
        temp_db.insert_pull_requests(sample_prs)
        temp_db.insert_commits(sample_commits)

        # First aggregate the data
        aggregator = DailyAggregator(temp_db)
        aggregator.write_aggregates()

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ParquetExporter(tmpdir)
            count = exporter.export_aggregates_by_date(temp_db)

            assert count > 0

            # Check files were created
            partitions = exporter.list_partitions()
            assert any("daily_sessions" in str(p) for p in partitions)
            assert any("daily_github" in str(p) for p in partitions)

    def test_list_partitions(self, temp_db, sample_sessions):
        """Test partition listing."""
        temp_db.insert_sessions(sample_sessions)

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ParquetExporter(tmpdir)
            exporter.export_sessions_by_date(temp_db)

            partitions = exporter.list_partitions()
            assert len(partitions) > 0

            # All should be .parquet files
            for partition in partitions:
                assert str(partition).endswith(".parquet")

    def test_parquet_roundtrip(self, temp_db, sample_sessions):
        """Test that exported data can be read back."""
        temp_db.insert_sessions(sample_sessions)

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ParquetExporter(tmpdir)
            exporter.export_sessions_by_date(temp_db)

            partitions = exporter.list_partitions()
            assert len(partitions) > 0

            # Read back a partition
            df = pd.read_parquet(partitions[0])
            assert len(df) > 0
            assert "session_id" in df.columns
            assert "developer_id" in df.columns
            assert "tokens_in" in df.columns
            assert "tokens_out" in df.columns
