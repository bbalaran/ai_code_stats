import datetime as dt
from pathlib import Path

import pytest

from prodlens.metrics import ReportGenerator
from prodlens.storage import ProdLensStore


def insert_sample_data(store: ProdLensStore):
    store.insert_sessions(
        [
            {
                "session_id": "alpha",
                "developer_id": "dev-1",
                "timestamp": dt.datetime(2024, 1, 1, 12, tzinfo=dt.timezone.utc),
                "model": "anthropic/claude-3-sonnet",
                "tokens_in": 30,
                "tokens_out": 70,
                "latency_ms": 1200,
                "status_code": 200,
                "accepted_flag": True,
            },
            {
                "session_id": "beta",
                "developer_id": "dev-1",
                "timestamp": dt.datetime(2024, 1, 1, 13, tzinfo=dt.timezone.utc),
                "model": "anthropic/claude-3-sonnet",
                "tokens_in": 20,
                "tokens_out": 30,
                "latency_ms": 1800,
                "status_code": 200,
                "accepted_flag": False,
            },
            {
                "session_id": "gamma",
                "developer_id": "dev-2",
                "timestamp": dt.datetime(2024, 1, 2, 15, tzinfo=dt.timezone.utc),
                "model": "anthropic/claude-3-haiku",
                "tokens_in": 40,
                "tokens_out": 10,
                "latency_ms": 1500,
                "status_code": 500,
                "accepted_flag": False,
            },
        ]
    )

    store.insert_pull_requests(
        [
            {
                "id": 1,
                "number": 10,
                "title": "Add feature",
                "author": "dev-1",
                "state": "closed",
                "created_at": dt.datetime(2024, 1, 1, 10, tzinfo=dt.timezone.utc),
                "merged_at": dt.datetime(2024, 1, 1, 20, tzinfo=dt.timezone.utc),
                "updated_at": dt.datetime(2024, 1, 1, 20, tzinfo=dt.timezone.utc),
                "reopened": False,
            },
            {
                "id": 2,
                "number": 11,
                "title": "Fix bug",
                "author": "dev-2",
                "state": "closed",
                "created_at": dt.datetime(2024, 1, 2, 9, tzinfo=dt.timezone.utc),
                "merged_at": dt.datetime(2024, 1, 5, 9, tzinfo=dt.timezone.utc),
                "updated_at": dt.datetime(2024, 1, 5, 9, tzinfo=dt.timezone.utc),
                "reopened": True,
            },
        ]
    )

    store.insert_commits(
        [
            {
                "sha": "a" * 40,
                "author": "dev-1",
                "timestamp": dt.datetime(2024, 1, 2, 11, tzinfo=dt.timezone.utc),
            },
            {
                "sha": "b" * 40,
                "author": "dev-2",
                "timestamp": dt.datetime(2024, 1, 2, 12, tzinfo=dt.timezone.utc),
            },
        ]
    )


def test_report_generator_computes_metrics(tmp_path: Path):
    store = ProdLensStore(tmp_path / "cache.db")
    insert_sample_data(store)

    generator = ReportGenerator(store)
    report = generator.generate_report(
        repo="openai/dev-agent-lens",
        since=dt.date(2024, 1, 1),
        lag_days=1,
        policy_models={"anthropic/claude-3-sonnet", "anthropic/claude-3-haiku"},
    )

    velocity = report["ai_interaction_velocity"]
    assert velocity["median_latency_ms"] == 1500
    assert pytest.approx(velocity["sessions_per_hour"], rel=1e-2) == 0.11

    assert report["acceptance_rate"] == 1 / 3
    assert report["model_selection_accuracy"] == 1.0
    assert report["error_rate"] == pytest.approx(1 / 3, rel=1e-6)
    assert report["token_efficiency"]["tokens_per_accept"] == 100

    throughput = report["pr_throughput"]
    assert throughput["weekly_merged_prs"] == 2

    assert report["commit_frequency"]["daily_commits"] == 2
    assert report["pr_merge_time_hours"] == [10.0, 72.0]
    assert report["rework_rate"] == 0.5

    correlation = report["ai_outcome_association"]
    assert correlation["pearson"]["count"] == 1
