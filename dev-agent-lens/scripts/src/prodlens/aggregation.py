"""Daily metrics aggregation pipeline for ProdLens."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import pandas as pd

from .storage import ProdLensStore


class DailyAggregator:
    """Aggregate daily session and GitHub metrics for reporting."""

    def __init__(self, store: ProdLensStore):
        self.store = store

    def aggregate_sessions(self, event_date: dt.date | None = None) -> Dict[str, object]:
        """Compute daily session metrics aggregates."""
        sessions = self.store.sessions_dataframe()
        if sessions.empty:
            return {}

        sessions["timestamp"] = pd.to_datetime(sessions["timestamp"], utc=True)

        if event_date:
            target_date = pd.Timestamp(event_date, tz="UTC")
            daily_sessions = sessions[sessions["timestamp"].dt.date == event_date]
        else:
            # Compute for all available dates
            daily_sessions = sessions

        if daily_sessions.empty:
            return {}

        grouped = daily_sessions.groupby(daily_sessions["timestamp"].dt.date)
        metrics = {}

        for date, group in grouped:
            # Handle potential NaN values from median calculation
            median_val = group["latency_ms"].median()
            median_latency_ms = float(median_val) if pd.notna(median_val) else 0.0

            metrics[str(date)] = {
                "event_date": str(date),
                "session_count": len(group),
                "total_tokens": int(group["tokens_in"].fillna(0).sum() + group["tokens_out"].fillna(0).sum()),
                "accepted_count": int((group["accepted_flag"] == 1).sum()),
                "error_count": int((group["status_code"] >= 400).sum()),
                "median_latency_ms": median_latency_ms,
                "cost_usd": float(group.get("cost_usd", pd.Series(dtype=float)).fillna(0).sum()),
            }

        return metrics

    def aggregate_github(self, event_date: dt.date | None = None) -> Dict[str, object]:
        """Compute daily GitHub metrics aggregates."""
        pull_requests = self.store.pull_requests_dataframe()
        commits = self.store.commits_dataframe()

        if pull_requests.empty and commits.empty:
            return {}

        metrics = {}

        # Process PRs by date
        if not pull_requests.empty:
            for col in ("created_at", "merged_at", "updated_at"):
                pull_requests[col] = pd.to_datetime(pull_requests[col], utc=True)

            grouped_prs = pull_requests.groupby(pull_requests["created_at"].dt.date)
            for date, group in grouped_prs:
                merged = (group["state"] == "closed") & group["merged_at"].notna()
                reopened = group["reopened"].astype(bool)

                date_str = str(date)
                if date_str not in metrics:
                    metrics[date_str] = {
                        "event_date": date_str,
                        "merged_pr_count": 0,
                        "commit_count": 0,
                        "reopened_pr_count": 0,
                        "avg_merge_hours": None,
                    }

                metrics[date_str]["merged_pr_count"] = int(merged.sum())
                metrics[date_str]["reopened_pr_count"] = int(reopened.sum())

                # Calculate average merge time
                merged_group = group[merged]
                if not merged_group.empty:
                    merge_durations = (
                        (merged_group["merged_at"] - merged_group["created_at"]).dt.total_seconds() / 3600
                    )
                    metrics[date_str]["avg_merge_hours"] = float(merge_durations.mean())

        # Process commits by date
        if not commits.empty:
            commits["timestamp"] = pd.to_datetime(commits["timestamp"], utc=True)
            grouped_commits = commits.groupby(commits["timestamp"].dt.date)
            for date, group in grouped_commits:
                date_str = str(date)
                if date_str not in metrics:
                    metrics[date_str] = {
                        "event_date": date_str,
                        "merged_pr_count": 0,
                        "commit_count": 0,
                        "reopened_pr_count": 0,
                        "avg_merge_hours": None,
                    }
                metrics[date_str]["commit_count"] = len(group)

        return metrics

    def write_aggregates(self) -> tuple[int, int]:
        """Write computed aggregates to the store."""
        session_metrics = self.aggregate_sessions()
        github_metrics = self.aggregate_github()

        session_rows = list(session_metrics.values())
        github_rows = list(github_metrics.values())

        session_inserted = self.store.insert_daily_session_metrics(session_rows)
        github_inserted = self.store.insert_daily_github_metrics(github_rows)

        return session_inserted, github_inserted


class ParquetExporter:
    """Export trace data to Parquet with date-based partitioning."""

    def __init__(self, parquet_dir: Path | str = Path(".prod-lens/parquet")):
        self.parquet_dir = Path(parquet_dir)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)

    def export_sessions_by_date(
        self,
        store: ProdLensStore,
        since: Optional[dt.date] = None,
        repo_filter: Optional[str] = None,
    ) -> int:
        """Export session data partitioned by date and repository."""
        sessions = store.sessions_dataframe()
        if sessions.empty:
            return 0

        sessions["timestamp"] = pd.to_datetime(sessions["timestamp"], utc=True)

        if since:
            sessions = sessions[sessions["timestamp"].dt.date >= since]

        if sessions.empty:
            return 0

        if repo_filter:
            sessions = sessions[sessions["repo_slug"] == repo_filter]

        # Validate required columns exist before groupby
        required_columns = ["event_date", "repo_slug"]
        missing_columns = [col for col in required_columns if col not in sessions.columns]
        if missing_columns:
            raise KeyError(f"Missing required columns for export: {missing_columns}")

        # Group by date and repo_slug for partitioning
        export_count = 0
        for (event_date, repo), group in sessions.groupby(["event_date", "repo_slug"], dropna=False):
            # Sanitize repo_slug to prevent path traversal attacks
            safe_repo = str(repo or "unknown").replace("..", "_").replace("/", "-").replace("\\", "-")
            repo_dir = self.parquet_dir / safe_repo
            repo_dir.mkdir(parents=True, exist_ok=True)

            output_path = repo_dir / f"{event_date}.parquet"
            group_copy = group.drop(columns=["event_date"], errors="ignore")
            group_copy.to_parquet(output_path, index=False)
            export_count += len(group)

        return export_count

    def export_aggregates_by_date(
        self,
        store: ProdLensStore,
        since: Optional[dt.date] = None,
    ) -> int:
        """Export daily aggregated metrics by date."""
        metrics_dir = self.parquet_dir / "_aggregates"
        metrics_dir.mkdir(parents=True, exist_ok=True)

        session_metrics = store.fetch_daily_session_metrics(since=since)
        github_metrics = store.fetch_daily_github_metrics(since=since)

        export_count = 0

        if session_metrics:
            df_sessions = pd.DataFrame(session_metrics)
            output_path = metrics_dir / "daily_sessions.parquet"
            df_sessions.to_parquet(output_path, index=False)
            export_count += len(df_sessions)

        if github_metrics:
            df_github = pd.DataFrame(github_metrics)
            output_path = metrics_dir / "daily_github.parquet"
            df_github.to_parquet(output_path, index=False)
            export_count += len(df_github)

        return export_count

    def list_partitions(self) -> List[Path]:
        """List all exported Parquet partitions."""
        if not self.parquet_dir.exists():
            return []

        partitions = []
        for item in self.parquet_dir.rglob("*.parquet"):
            if not item.name.startswith("."):
                partitions.append(item)

        return sorted(partitions)
