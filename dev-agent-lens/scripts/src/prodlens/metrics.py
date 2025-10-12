from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, List, Optional, Set

import pandas as pd

try:  # pragma: no cover - optional dependency
    from scipy import stats  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback path
    class _StatsFallback:
        @staticmethod
        def pearsonr(x: pd.Series, y: pd.Series) -> SimpleNamespace:
            return SimpleNamespace(statistic=float(x.corr(y, method="pearson")), pvalue=None)

        @staticmethod
        def spearmanr(x: pd.Series, y: pd.Series) -> SimpleNamespace:
            return SimpleNamespace(statistic=float(x.corr(y, method="spearman")), pvalue=None)

    stats = _StatsFallback()  # type: ignore

from .storage import ProdLensStore


@dataclass
class CorrelationResult:
    r: Optional[float]
    p_value: Optional[float]
    count: int

    def to_dict(self) -> Dict[str, Optional[float]]:
        return {"r": self.r, "p_value": self.p_value, "count": self.count}


class ReportGenerator:
    """Compute ProdLens pilot metrics from the normalized data store."""

    def __init__(self, store: ProdLensStore):
        self.store = store

    def _filter_since(self, df: pd.DataFrame, column: str, since: dt.date | dt.datetime) -> pd.DataFrame:
        if df.empty:
            return df
        since_ts = self._normalize_since(since)
        return df[df[column] >= since_ts]

    @staticmethod
    def _normalize_since(since: dt.date | dt.datetime | pd.Timestamp) -> pd.Timestamp:
        if isinstance(since, pd.Timestamp):
            if since.tzinfo is None:
                return since.tz_localize("UTC")
            return since.tz_convert("UTC")
        if isinstance(since, dt.datetime):
            if since.tzinfo is None:
                return pd.Timestamp(since, tz="UTC")
            return pd.Timestamp(since).tz_convert("UTC")
        return pd.Timestamp(since, tz="UTC")

    def generate_report(
        self,
        *,
        repo: str,
        since: dt.date | dt.datetime,
        lag_days: int = 1,
        policy_models: Optional[Set[str]] = None,
    ) -> Dict[str, object]:
        sessions = self.store.sessions_dataframe()
        if not sessions.empty:
            sessions["timestamp"] = pd.to_datetime(sessions["timestamp"], utc=True)
            sessions = self._filter_since(sessions, "timestamp", since)
            if "total_tokens" not in sessions.columns:
                sessions["total_tokens"] = sessions["tokens_in"].fillna(0) + sessions["tokens_out"].fillna(0)
            if "cost_usd" not in sessions.columns:
                sessions["cost_usd"] = 0.0

        pull_requests = self.store.pull_requests_dataframe()
        if not pull_requests.empty:
            for column in ("created_at", "merged_at", "updated_at"):
                pull_requests[column] = pd.to_datetime(pull_requests[column], utc=True)
            pull_requests = self._filter_since(pull_requests, "created_at", since)

        commits = self.store.commits_dataframe()
        if not commits.empty:
            commits["timestamp"] = pd.to_datetime(commits["timestamp"], utc=True)
            commits = self._filter_since(commits, "timestamp", since)

        report: Dict[str, object] = {}

        report["ai_interaction_velocity"] = self._compute_velocity(sessions)
        report["acceptance_rate"] = self._compute_acceptance_rate(sessions)
        report["model_selection_accuracy"] = self._compute_model_accuracy(sessions, policy_models)
        report["error_rate"] = self._compute_error_rate(sessions)
        report["token_efficiency"] = self._compute_token_efficiency(sessions)
        report["acceptance_quality"] = self._compute_acceptance_quality(sessions)
        report["pr_throughput"] = self._compute_pr_throughput(pull_requests)
        report["commit_frequency"] = self._compute_commit_frequency(commits)
        report["pr_merge_time_hours"] = self._compute_merge_times(pull_requests)
        report["rework_rate"] = self._compute_rework_rate(pull_requests)
        report["cost_metrics"] = self._compute_cost_metrics(sessions, pull_requests)
        report["ai_outcome_association"] = self._compute_correlations(sessions, commits, lag_days)
        report["multiple_comparison_adjustment"] = self._adjust_p_values(report)
        report["metadata"] = {"repo": repo, "since": str(since), "lag_days": lag_days}
        return report

    # Metric helpers -----------------------------------------------------------------
    def _compute_velocity(self, sessions: pd.DataFrame) -> Dict[str, float]:
        if sessions.empty:
            return {"median_latency_ms": 0.0, "sessions_per_hour": 0.0}

        median_latency = float(sessions["latency_ms"].median())
        time_range = sessions["timestamp"].max() - sessions["timestamp"].min()
        total_hours = max(time_range.total_seconds() / 3600, 1.0)
        sessions_per_hour = float(len(sessions) / total_hours)
        return {
            "median_latency_ms": median_latency,
            "sessions_per_hour": sessions_per_hour,
            "total_sessions": int(len(sessions)),
        }

    def _compute_acceptance_rate(self, sessions: pd.DataFrame) -> float:
        if sessions.empty:
            return 0.0
        return float(sessions["accepted_flag"].mean())

    def _compute_model_accuracy(self, sessions: pd.DataFrame, policy_models: Optional[Set[str]]) -> Optional[float]:
        if not policy_models:
            return None
        if sessions.empty:
            return None
        mask = sessions["model"].isin(policy_models)
        return float(mask.mean())

    def _compute_error_rate(self, sessions: pd.DataFrame) -> float:
        if sessions.empty:
            return 0.0
        statuses = sessions["status_code"].fillna(0)
        error_mask = statuses.astype(int) >= 400
        return float(error_mask.mean())

    def _compute_token_efficiency(self, sessions: pd.DataFrame) -> Dict[str, float]:
        accepted = sessions[sessions["accepted_flag"] == 1]
        if accepted.empty:
            return {
                "tokens_per_accept": 0.0,
                "accepted_sessions": 0,
                "total_tokens": 0.0,
                "tokens_per_accepted_line": 0.0,
            }
        if "total_tokens" in accepted.columns:
            total_tokens_series = accepted["total_tokens"].fillna(0)
        else:
            total_tokens_series = (accepted["tokens_in"].fillna(0) + accepted["tokens_out"].fillna(0))
        total_tokens = total_tokens_series.sum()
        tokens_per_accept = float(total_tokens / len(accepted))
        accepted_lines = accepted["accepted_lines"] if "accepted_lines" in accepted.columns else None
        if accepted_lines is not None and not accepted_lines.dropna().empty:
            total_lines = accepted_lines.fillna(0).astype(int).sum() or 1
            tokens_per_line = float(total_tokens / total_lines)
        else:
            tokens_per_line = 0.0
        return {
            "tokens_per_accept": tokens_per_accept,
            "accepted_sessions": int(len(accepted)),
            "total_tokens": float(total_tokens),
            "tokens_per_accepted_line": tokens_per_line,
        }

    def _compute_acceptance_quality(self, sessions: pd.DataFrame) -> Dict[str, Optional[float]]:
        if sessions.empty or "diff_ratio" not in sessions.columns:
            return {"avg_diff_ratio": None, "share_above_threshold": None, "threshold": 0.7, "sample": 0}
        ratios = sessions["diff_ratio"].dropna().astype(float)
        if ratios.empty:
            return {"avg_diff_ratio": None, "share_above_threshold": None, "threshold": 0.7, "sample": 0}
        threshold = 0.7
        share = float((ratios >= threshold).mean())
        return {
            "avg_diff_ratio": float(ratios.mean()),
            "share_above_threshold": share,
            "threshold": threshold,
            "sample": int(len(ratios)),
        }

    def _compute_pr_throughput(self, pull_requests: pd.DataFrame) -> Dict[str, int]:
        if pull_requests.empty:
            return {"weekly_merged_prs": 0, "total_merged": 0}
        merged = pull_requests[pull_requests["merged_at"].notna()]
        return {"weekly_merged_prs": int(len(merged)), "total_merged": int(len(merged))}

    def _compute_commit_frequency(self, commits: pd.DataFrame) -> Dict[str, float]:
        if commits.empty:
            return {"daily_commits": 0.0, "total_commits": 0}
        commits["day"] = commits["timestamp"].dt.date
        active_days = commits["day"].nunique() or 1
        daily = float(len(commits) / active_days)
        return {"daily_commits": daily, "total_commits": int(len(commits))}

    def _compute_merge_times(self, pull_requests: pd.DataFrame) -> list:
        if pull_requests.empty:
            return []
        merged = pull_requests[pull_requests["merged_at"].notna()]
        durations = ((merged["merged_at"] - merged["created_at"]).dt.total_seconds() / 3600).round(2)
        return sorted(durations.tolist())

    def _compute_rework_rate(self, pull_requests: pd.DataFrame) -> float:
        if pull_requests.empty:
            return 0.0
        closed = pull_requests[pull_requests["state"] == "closed"]
        if closed.empty:
            return 0.0
        reopened = closed["reopened"].astype(bool)
        return float(reopened.mean())

    def _compute_correlations(self, sessions: pd.DataFrame, commits: pd.DataFrame, lag_days: int) -> Dict[str, Dict[str, Optional[float]]]:
        if sessions.empty or commits.empty:
            return {
                "pearson": CorrelationResult(None, None, 0).to_dict(),
                "spearman": CorrelationResult(None, None, 0).to_dict(),
                "lag_days": lag_days,
            }

        session_daily = sessions.groupby(sessions["timestamp"].dt.date).size()
        commit_daily = commits.groupby(commits["timestamp"].dt.date).size()

        commit_shifted = commit_daily.copy()
        if lag_days:
            commit_shifted.index = [day - dt.timedelta(days=lag_days) for day in commit_shifted.index]

        merged = (
            pd.DataFrame({"sessions": session_daily})
            .join(pd.DataFrame({"commits": commit_shifted}), how="inner")
            .dropna()
        )

        count = int(len(merged))
        if count < 2:
            return {
                "pearson": CorrelationResult(None, None, count).to_dict(),
                "spearman": CorrelationResult(None, None, count).to_dict(),
                "lag_days": lag_days,
            }

        pearson = stats.pearsonr(merged["sessions"], merged["commits"])
        spearman = stats.spearmanr(merged["sessions"], merged["commits"])
        return {
            "pearson": CorrelationResult(float(pearson.statistic), float(pearson.pvalue), count).to_dict(),
            "spearman": CorrelationResult(float(spearman.statistic), float(spearman.pvalue), count).to_dict(),
            "lag_days": lag_days,
        }

    def _compute_cost_metrics(self, sessions: pd.DataFrame, pull_requests: pd.DataFrame) -> Dict[str, float]:
        if sessions.empty:
            total_cost = 0.0
        else:
            total_cost = float(sessions.get("cost_usd", pd.Series(dtype=float)).fillna(0).sum())

        merged = pull_requests[pull_requests["merged_at"].notna()] if not pull_requests.empty else pd.DataFrame()
        merged_count = int(len(merged)) if not merged.empty else 0
        cost_per_pr = float(total_cost / merged_count) if merged_count else 0.0
        return {
            "total_session_cost_usd": total_cost,
            "merged_pr_count": merged_count,
            "cost_per_merged_pr_usd": cost_per_pr,
        }

    @staticmethod
    def _adjust_p_values(report: Dict[str, object]) -> Dict[str, object]:
        p_values: List[float] = []
        labels: List[str] = []

        association = report.get("ai_outcome_association", {})
        for key in ("pearson", "spearman"):
            metric = association.get(key, {})
            p = metric.get("p_value")
            if p is not None:
                p_values.append(p)
                labels.append(f"ai_outcome_{key}")

        acceptance_quality = report.get("acceptance_quality", {})
        if acceptance_quality.get("sample"):
            # Use binomial approximation for threshold exceedance
            share = acceptance_quality.get("share_above_threshold")
            if share is not None:
                p_values.append(1 - share)
                labels.append("acceptance_threshold")

        if not p_values:
            return {"method": "benjamini-hochberg", "adjusted": {}}

        indexed = sorted(enumerate(p_values), key=lambda item: item[1])
        total = len(p_values)
        adjusted = {}
        for rank, (idx, p_value) in enumerate(indexed, start=1):
            adjusted_value = min(p_value * total / rank, 1.0)
            label = labels[idx]
            adjusted[label] = adjusted_value

        return {"method": "benjamini-hochberg", "adjusted": adjusted}
