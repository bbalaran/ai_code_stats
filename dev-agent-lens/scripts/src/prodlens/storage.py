from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Iterable, List, Mapping, Optional

import pandas as pd

from .schemas import CanonicalTrace


class ProdLensStore:
    """SQLite-backed storage for ProdLens pilot data."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ProdLensStore":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    developer_id TEXT,
                    timestamp TEXT NOT NULL,
                    model TEXT,
                    tokens_in INTEGER NOT NULL,
                    tokens_out INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    status_code INTEGER,
                    accepted_flag INTEGER NOT NULL,
                    repo_slug TEXT,
                    event_date TEXT,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    cost_usd REAL NOT NULL DEFAULT 0,
                    diff_ratio REAL,
                    accepted_lines INTEGER,
                    trace_hash TEXT UNIQUE
                );

                CREATE TABLE IF NOT EXISTS pull_requests (
                    id INTEGER PRIMARY KEY,
                    number INTEGER NOT NULL,
                    title TEXT,
                    author TEXT,
                    state TEXT,
                    created_at TEXT,
                    merged_at TEXT,
                    updated_at TEXT,
                    reopened INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS commits (
                    sha TEXT PRIMARY KEY,
                    author TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS etag_state (
                    endpoint TEXT PRIMARY KEY,
                    etag TEXT,
                    last_modified TEXT,
                    last_synced TEXT
                );

                CREATE TABLE IF NOT EXISTS etl_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    row_count INTEGER DEFAULT 0,
                    details TEXT
                );
                """
            )

        # Initialize aggregation tables
        self._init_aggregation_schema()

        with self.conn:
            cur = self.conn.execute("PRAGMA table_info(sessions)")
            columns = {row[1] for row in cur.fetchall()}
            migrations: List[str] = []
            if "trace_hash" not in columns:
                migrations.append("ALTER TABLE sessions ADD COLUMN trace_hash TEXT")
            if "repo_slug" not in columns:
                migrations.append("ALTER TABLE sessions ADD COLUMN repo_slug TEXT")
            if "event_date" not in columns:
                migrations.append("ALTER TABLE sessions ADD COLUMN event_date TEXT")
            if "total_tokens" not in columns:
                migrations.append("ALTER TABLE sessions ADD COLUMN total_tokens INTEGER NOT NULL DEFAULT 0")
            if "cost_usd" not in columns:
                migrations.append("ALTER TABLE sessions ADD COLUMN cost_usd REAL NOT NULL DEFAULT 0")
            if "diff_ratio" not in columns:
                migrations.append("ALTER TABLE sessions ADD COLUMN diff_ratio REAL")
            if "accepted_lines" not in columns:
                migrations.append("ALTER TABLE sessions ADD COLUMN accepted_lines INTEGER")

            for statement in migrations:
                self.conn.execute(statement)

            if migrations:
                rows = self.conn.execute(
                    "SELECT id, session_id, developer_id, timestamp, model, tokens_in, tokens_out, latency_ms, status_code, accepted_flag, repo_slug, event_date, total_tokens, cost_usd, diff_ratio, accepted_lines FROM sessions"
                ).fetchall()
                for row in rows:
                    record = dict(row)
                    if not record.get("event_date"):
                        record["event_date"] = self._derive_event_date(record)
                    if not record.get("total_tokens"):
                        record["total_tokens"] = int(record.get("tokens_in", 0)) + int(record.get("tokens_out", 0))
                    if record.get("cost_usd") is None:
                        record["cost_usd"] = 0.0
                    record["trace_hash"] = self._compute_trace_hash(record)
                    self.conn.execute(
                        "UPDATE sessions SET trace_hash = :trace_hash WHERE id = :id",
                        {"trace_hash": record["trace_hash"], "id": record["id"]},
                    )
                self.conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_trace_hash ON sessions(trace_hash)"
                )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_repo_date ON sessions(repo_slug, event_date)"
            )

    # ------------------------------------------------------------------
    # Session operations
    # ------------------------------------------------------------------
    @staticmethod
    def _derive_event_date(record: Mapping[str, object]) -> str:
        timestamp = record.get("timestamp")
        if isinstance(timestamp, dt.datetime):
            return timestamp.astimezone(dt.timezone.utc).date().isoformat()
        try:
            parsed = dt.datetime.fromisoformat(str(timestamp))
        except (TypeError, ValueError):
            return dt.datetime.now(tz=dt.timezone.utc).date().isoformat()
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc).date().isoformat()

    @staticmethod
    def _compute_trace_hash(record: Mapping[str, object]) -> str:
        payload = {
            "session_id": record.get("session_id"),
            "developer_id": record.get("developer_id"),
            "timestamp": record.get("timestamp"),
            "model": record.get("model"),
            "tokens_in": int(record.get("tokens_in", 0)),
            "tokens_out": int(record.get("tokens_out", 0)),
            "latency_ms": float(record.get("latency_ms", 0.0)),
            "status_code": record.get("status_code"),
            "accepted_flag": 1 if record.get("accepted_flag") else 0,
            "repo_slug": record.get("repo_slug"),
            "event_date": record.get("event_date") or ProdLensStore._derive_event_date(record),
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha1(encoded).hexdigest()

    def insert_sessions(self, sessions: Iterable[CanonicalTrace | Mapping[str, object]]) -> int:
        rows: List[dict] = []
        for session in sessions:
            if isinstance(session, CanonicalTrace):
                record = session.to_record()
            else:
                record = dict(session)

            timestamp = record["timestamp"]
            if isinstance(timestamp, dt.datetime):
                record["timestamp"] = timestamp.astimezone(dt.timezone.utc).isoformat()
            else:
                record["timestamp"] = str(timestamp)

            record["accepted_flag"] = 1 if record.get("accepted_flag") else 0
            record.setdefault("tokens_out", 0)
            record.setdefault("tokens_in", 0)
            record.setdefault("repo_slug", None)
            record.setdefault("event_date", self._derive_event_date(record))
            record["total_tokens"] = int(record.get("total_tokens") or (int(record.get("tokens_in", 0)) + int(record.get("tokens_out", 0))))
            record["cost_usd"] = float(record.get("cost_usd") or 0.0)
            record.setdefault("diff_ratio", None)
            record.setdefault("accepted_lines", None)

            record["trace_hash"] = self._compute_trace_hash(record)

            rows.append(record)

        if not rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO sessions (
                    session_id, developer_id, timestamp, model,
                    tokens_in, tokens_out, latency_ms, status_code, accepted_flag,
                    repo_slug, event_date, total_tokens, cost_usd, diff_ratio, accepted_lines, trace_hash
                ) VALUES (
                    :session_id, :developer_id, :timestamp, :model,
                    :tokens_in, :tokens_out, :latency_ms, :status_code, :accepted_flag,
                    :repo_slug, :event_date, :total_tokens, :cost_usd, :diff_ratio, :accepted_lines, :trace_hash
                )
                ON CONFLICT(trace_hash)
                DO UPDATE SET
                    developer_id=excluded.developer_id,
                    model=excluded.model,
                    tokens_in=excluded.tokens_in,
                    tokens_out=excluded.tokens_out,
                    latency_ms=excluded.latency_ms,
                    status_code=excluded.status_code,
                    accepted_flag=excluded.accepted_flag,
                    repo_slug=excluded.repo_slug,
                    event_date=excluded.event_date,
                    total_tokens=excluded.total_tokens,
                    cost_usd=excluded.cost_usd,
                    diff_ratio=excluded.diff_ratio,
                    accepted_lines=excluded.accepted_lines
                """,
                rows,
            )
        return len(rows)

    def fetch_sessions(self) -> List[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT session_id, developer_id, timestamp, model, tokens_in, tokens_out, latency_ms, status_code, accepted_flag, repo_slug, event_date, total_tokens, cost_usd, diff_ratio, accepted_lines FROM sessions"
        )
        return cur.fetchall()

    def sessions_dataframe(self) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT session_id, developer_id, timestamp, model, tokens_in, tokens_out, latency_ms, status_code, accepted_flag, repo_slug, event_date, total_tokens, cost_usd, diff_ratio, accepted_lines FROM sessions",
            self.conn,
            parse_dates=["timestamp"],
        )

    # ------------------------------------------------------------------
    # Pull request operations
    # ------------------------------------------------------------------
    def insert_pull_requests(self, pull_requests: Iterable[Mapping[str, object]]) -> int:
        rows = []
        for pr in pull_requests:
            record = dict(pr)
            for key in ("created_at", "merged_at", "updated_at"):
                value = record.get(key)
                if isinstance(value, dt.datetime):
                    record[key] = value.astimezone(dt.timezone.utc).isoformat()
                elif value is None:
                    record[key] = None
                else:
                    record[key] = str(value)
            record["reopened"] = 1 if record.get("reopened") else 0
            rows.append(record)

        if not rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO pull_requests (
                    id, number, title, author, state, created_at, merged_at, updated_at, reopened
                ) VALUES (
                    :id, :number, :title, :author, :state, :created_at, :merged_at, :updated_at, :reopened
                )
                ON CONFLICT(id) DO UPDATE SET
                    number=excluded.number,
                    title=excluded.title,
                    author=excluded.author,
                    state=excluded.state,
                    created_at=excluded.created_at,
                    merged_at=excluded.merged_at,
                    updated_at=excluded.updated_at,
                    reopened=excluded.reopened
                """,
                rows,
            )
        return len(rows)

    def fetch_pull_requests(self) -> List[dict]:
        cur = self.conn.execute(
            "SELECT id, number, title, author, state, created_at, merged_at, updated_at, reopened FROM pull_requests ORDER BY number"
        )
        rows: List[dict] = []
        for row in cur.fetchall():
            record = dict(row)
            record["reopened"] = bool(record.get("reopened"))
            rows.append(record)
        return rows

    def pull_requests_dataframe(self) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT id, number, title, author, state, created_at, merged_at, updated_at, reopened FROM pull_requests",
            self.conn,
            parse_dates=["created_at", "merged_at", "updated_at"],
        )

    # ------------------------------------------------------------------
    # Commit operations
    # ------------------------------------------------------------------
    def insert_commits(self, commits: Iterable[Mapping[str, object]]) -> int:
        rows = []
        for commit in commits:
            record = dict(commit)
            timestamp = record.get("timestamp")
            if isinstance(timestamp, dt.datetime):
                record["timestamp"] = timestamp.astimezone(dt.timezone.utc).isoformat()
            else:
                record["timestamp"] = str(timestamp)
            rows.append(record)

        if not rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO commits (sha, author, timestamp)
                VALUES (:sha, :author, :timestamp)
                ON CONFLICT(sha) DO UPDATE SET
                    author=excluded.author,
                    timestamp=excluded.timestamp
                """,
                rows,
            )
        return len(rows)

    def fetch_commits(self) -> List[sqlite3.Row]:
        cur = self.conn.execute("SELECT sha, author, timestamp FROM commits")
        return cur.fetchall()

    def commits_dataframe(self) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT sha, author, timestamp FROM commits",
            self.conn,
            parse_dates=["timestamp"],
        )

    # ------------------------------------------------------------------
    # ETag tracking
    # ------------------------------------------------------------------
    def get_etag(self, endpoint: str) -> Optional[str]:
        cur = self.conn.execute("SELECT etag FROM etag_state WHERE endpoint = ?", (endpoint,))
        row = cur.fetchone()
        return row[0] if row else None

    def set_etag(self, endpoint: str, etag: Optional[str]) -> None:
        now = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO etag_state (endpoint, etag, last_synced)
                VALUES (?, ?, ?)
                ON CONFLICT(endpoint) DO UPDATE SET
                    etag=excluded.etag,
                    last_synced=excluded.last_synced
                """,
                (endpoint, etag, now),
            )

    def record_etl_run(self, job: str, row_count: int, details: Optional[str] = None) -> None:
        now = dt.datetime.now(tz=dt.timezone.utc)
        with self.conn:
            self.conn.execute(
                "INSERT INTO etl_runs (job, started_at, finished_at, row_count, details) VALUES (?, ?, ?, ?, ?)",
                (
                    job,
                    now.isoformat(),
                    now.isoformat(),
                    row_count,
                    details,
                ),
            )

    # ------------------------------------------------------------------
    # Checkpoint management for incremental exports
    # ------------------------------------------------------------------
    def get_last_checkpoint(self, job_name: str) -> Optional[dt.datetime]:
        """Get the last successful checkpoint timestamp for a given job."""
        cur = self.conn.execute(
            "SELECT finished_at FROM etl_runs WHERE job = ? ORDER BY finished_at DESC LIMIT 1",
            (job_name,),
        )
        row = cur.fetchone()
        if row and row[0]:
            try:
                return dt.datetime.fromisoformat(row[0])
            except (ValueError, TypeError):
                return None
        return None

    def set_checkpoint(self, job_name: str, checkpoint_timestamp: dt.datetime) -> None:
        """Record a successful checkpoint for incremental processing."""
        # Convert to UTC if needed
        if checkpoint_timestamp.tzinfo is None:
            checkpoint_timestamp = checkpoint_timestamp.replace(tzinfo=dt.timezone.utc)
        elif checkpoint_timestamp.tzinfo != dt.timezone.utc:
            checkpoint_timestamp = checkpoint_timestamp.astimezone(dt.timezone.utc)

        with self.conn:
            self.conn.execute(
                "INSERT INTO etl_runs (job, started_at, finished_at, row_count, details) VALUES (?, ?, ?, ?, ?)",
                (
                    job_name,
                    checkpoint_timestamp.isoformat(),
                    checkpoint_timestamp.isoformat(),
                    0,
                    f"Checkpoint at {checkpoint_timestamp.isoformat()}",
                ),
            )

    # ------------------------------------------------------------------
    # Daily aggregation tables
    # ------------------------------------------------------------------
    def _init_aggregation_schema(self) -> None:
        """Initialize tables for daily metric aggregation."""
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS daily_session_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date TEXT NOT NULL UNIQUE,
                    developer_id TEXT,
                    session_count INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    accepted_count INTEGER NOT NULL DEFAULT 0,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    median_latency_ms REAL NOT NULL DEFAULT 0.0,
                    cost_usd REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS daily_github_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date TEXT NOT NULL UNIQUE,
                    merged_pr_count INTEGER NOT NULL DEFAULT 0,
                    commit_count INTEGER NOT NULL DEFAULT 0,
                    reopened_pr_count INTEGER NOT NULL DEFAULT 0,
                    avg_merge_hours REAL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS correlation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correlation_date TEXT NOT NULL,
                    lag_days INTEGER NOT NULL,
                    pearson_r REAL,
                    pearson_p REAL,
                    spearman_r REAL,
                    spearman_p REAL,
                    sample_size INTEGER,
                    created_at TEXT NOT NULL,
                    UNIQUE(correlation_date, lag_days)
                );

                CREATE INDEX IF NOT EXISTS idx_daily_session_metrics_date ON daily_session_metrics(event_date);
                CREATE INDEX IF NOT EXISTS idx_daily_github_metrics_date ON daily_github_metrics(event_date);
                CREATE INDEX IF NOT EXISTS idx_correlation_cache_date_lag ON correlation_cache(correlation_date, lag_days);
                """
            )

    def insert_daily_session_metrics(self, metrics: Iterable[Mapping[str, object]]) -> int:
        """Insert or update daily session metrics."""
        rows = []
        for metric in metrics:
            record = dict(metric)
            # Validate required fields
            if "event_date" not in record:
                raise ValueError("Missing required field: event_date")
            # Set defaults for optional fields
            record.setdefault("developer_id", None)
            record.setdefault("created_at", dt.datetime.now(tz=dt.timezone.utc).isoformat())
            rows.append(record)

        if not rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO daily_session_metrics (
                    event_date, developer_id, session_count, total_tokens,
                    accepted_count, error_count, median_latency_ms, cost_usd, created_at
                ) VALUES (
                    :event_date, :developer_id, :session_count, :total_tokens,
                    :accepted_count, :error_count, :median_latency_ms, :cost_usd, :created_at
                )
                ON CONFLICT(event_date) DO UPDATE SET
                    session_count=excluded.session_count,
                    total_tokens=excluded.total_tokens,
                    accepted_count=excluded.accepted_count,
                    error_count=excluded.error_count,
                    median_latency_ms=excluded.median_latency_ms,
                    cost_usd=excluded.cost_usd
                """,
                rows,
            )
        return len(rows)

    def insert_daily_github_metrics(self, metrics: Iterable[Mapping[str, object]]) -> int:
        """Insert or update daily GitHub metrics."""
        rows = []
        for metric in metrics:
            record = dict(metric)
            record.setdefault("created_at", dt.datetime.now(tz=dt.timezone.utc).isoformat())
            rows.append(record)

        if not rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO daily_github_metrics (
                    event_date, merged_pr_count, commit_count, reopened_pr_count, avg_merge_hours, created_at
                ) VALUES (
                    :event_date, :merged_pr_count, :commit_count, :reopened_pr_count, :avg_merge_hours, :created_at
                )
                ON CONFLICT(event_date) DO UPDATE SET
                    merged_pr_count=excluded.merged_pr_count,
                    commit_count=excluded.commit_count,
                    reopened_pr_count=excluded.reopened_pr_count,
                    avg_merge_hours=excluded.avg_merge_hours
                """,
                rows,
            )
        return len(rows)

    def fetch_daily_session_metrics(self, since: Optional[dt.date] = None) -> List[dict]:
        """Fetch daily session metrics, optionally since a given date."""
        query = "SELECT * FROM daily_session_metrics"
        params: List[object] = []
        if since:
            query += " WHERE event_date >= ?"
            params.append(since.isoformat())
        query += " ORDER BY event_date"

        cur = self.conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def fetch_daily_github_metrics(self, since: Optional[dt.date] = None) -> List[dict]:
        """Fetch daily GitHub metrics, optionally since a given date."""
        query = "SELECT * FROM daily_github_metrics"
        params: List[object] = []
        if since:
            query += " WHERE event_date >= ?"
            params.append(since.isoformat())
        query += " ORDER BY event_date"

        cur = self.conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

    def insert_correlation_cache(self, correlations: Iterable[Mapping[str, object]]) -> int:
        """Cache computed correlations for reuse."""
        rows = []
        for corr in correlations:
            record = dict(corr)
            record.setdefault("created_at", dt.datetime.now(tz=dt.timezone.utc).isoformat())
            rows.append(record)

        if not rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO correlation_cache (
                    correlation_date, lag_days, pearson_r, pearson_p,
                    spearman_r, spearman_p, sample_size, created_at
                ) VALUES (
                    :correlation_date, :lag_days, :pearson_r, :pearson_p,
                    :spearman_r, :spearman_p, :sample_size, :created_at
                )
                ON CONFLICT(correlation_date, lag_days) DO UPDATE SET
                    pearson_r=excluded.pearson_r,
                    pearson_p=excluded.pearson_p,
                    spearman_r=excluded.spearman_r,
                    spearman_p=excluded.spearman_p,
                    sample_size=excluded.sample_size
                """,
                rows,
            )
        return len(rows)
