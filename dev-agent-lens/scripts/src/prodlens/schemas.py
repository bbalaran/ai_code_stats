from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class CanonicalTrace:
    """Canonical representation of a single LiteLLM span or session event."""

    session_id: Optional[str]
    developer_id: Optional[str]
    timestamp: datetime
    model: Optional[str]
    tokens_in: int
    tokens_out: int
    latency_ms: float
    status_code: Optional[int]
    accepted_flag: bool
    repo_slug: Optional[str] = None
    diff_ratio: Optional[float] = None
    accepted_lines: Optional[int] = None

    def to_record(self) -> dict:
        """Return a SQLite-friendly dictionary representation."""

        return {
            "session_id": self.session_id,
            "developer_id": self.developer_id,
            "timestamp": self.timestamp,
            "model": self.model,
            "tokens_in": int(self.tokens_in),
            "tokens_out": int(self.tokens_out),
            "latency_ms": float(self.latency_ms),
            "status_code": None if self.status_code is None else int(self.status_code),
            "accepted_flag": bool(self.accepted_flag),
            "repo_slug": self.repo_slug,
            "diff_ratio": None if self.diff_ratio is None else float(self.diff_ratio),
            "accepted_lines": None if self.accepted_lines is None else int(self.accepted_lines),
        }
