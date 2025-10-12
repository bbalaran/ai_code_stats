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

            cur = self.conn.execute("PRAGMA table_info(sessions)")
            columns = {row[1] for row in cur.fetchall()}
            if "trace_hash" not in columns:
                self.conn.execute("ALTER TABLE sessions ADD COLUMN trace_hash TEXT")
                rows = self.conn.execute(
                    "SELECT id, session_id, developer_id, timestamp, model, tokens_in, tokens_out, latency_ms, status_code, accepted_flag FROM sessions"
                ).fetchall()
                for row in rows:
                    record = dict(row)
                    record["trace_hash"] = self._compute_trace_hash(record)
                    self.conn.execute(
                        "UPDATE sessions SET trace_hash = :trace_hash WHERE id = :id",
                        {"trace_hash": record["trace_hash"], "id": record["id"]},
                    )
                self.conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_trace_hash ON sessions(trace_hash)"
                )

    # ------------------------------------------------------------------
    # Session operations
    # ------------------------------------------------------------------
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

            record["trace_hash"] = self._compute_trace_hash(record)

            rows.append(record)

        if not rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO sessions (
                    session_id, developer_id, timestamp, model,
                    tokens_in, tokens_out, latency_ms, status_code, accepted_flag, trace_hash
                ) VALUES (
                    :session_id, :developer_id, :timestamp, :model,
                    :tokens_in, :tokens_out, :latency_ms, :status_code, :accepted_flag, :trace_hash
                )
                ON CONFLICT(trace_hash)
                DO UPDATE SET
                    developer_id=excluded.developer_id,
                    model=excluded.model,
                    tokens_in=excluded.tokens_in,
                    tokens_out=excluded.tokens_out,
                    latency_ms=excluded.latency_ms,
                    status_code=excluded.status_code,
                    accepted_flag=excluded.accepted_flag
                """,
                rows,
            )
        return len(rows)

    def fetch_sessions(self) -> List[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT session_id, developer_id, timestamp, model, tokens_in, tokens_out, latency_ms, status_code, accepted_flag FROM sessions"
        )
        return cur.fetchall()

    def sessions_dataframe(self) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT session_id, developer_id, timestamp, model, tokens_in, tokens_out, latency_ms, status_code, accepted_flag FROM sessions",
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
