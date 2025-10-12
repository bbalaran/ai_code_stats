from __future__ import annotations

import json
import datetime as dt
from pathlib import Path
from typing import Iterable, List, Mapping

import pandas as pd

from .storage import ProdLensStore
from .trace_normalizer import normalize_records


MODEL_PRICING_PER_MILLION = {
    "anthropic/claude-3-sonnet": {"input": 15.0, "output": 75.0},
    "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
    "anthropic/claude-3-haiku": {"input": 1.0, "output": 5.0},
    "openai/gpt-4o": {"input": 5.0, "output": 15.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
}

DEFAULT_PRICING = {"input": 10.0, "output": 10.0}


def _estimate_cost(model: str | None, tokens_in: int, tokens_out: int) -> float:
    if tokens_in < 0 or tokens_out < 0:
        return 0.0
    pricing = MODEL_PRICING_PER_MILLION.get(model or "", DEFAULT_PRICING)
    return (
        (tokens_in / 1_000_000) * pricing["input"]
        + (tokens_out / 1_000_000) * pricing["output"]
    )


def _event_date(timestamp: dt.datetime) -> str:
    return timestamp.astimezone(dt.timezone.utc).date().isoformat()


def _validate_record(record: Mapping[str, object]) -> bool:
    required_keys = ("timestamp", "usage")
    for key in required_keys:
        if key not in record:
            return False
    usage = record.get("usage")
    return isinstance(usage, Mapping)


class TraceIngestor:
    """Ingest LiteLLM proxy JSONL traces into the ProdLens store."""

    def __init__(
        self,
        store: ProdLensStore,
        *,
        dead_letter_dir: Path | str = Path(".prod-lens/dead-letter"),
        parquet_dir: Path | str = Path(".prod-lens/parquet"),
    ) -> None:
        self.store = store
        self.dead_letter_dir = Path(dead_letter_dir)
        self.parquet_dir = Path(parquet_dir)
        self.dead_letter_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)

    def ingest_file(self, path: Path | str, *, repo_slug: str | None = None) -> int:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)

        raw_records: List[Mapping[str, object]] = []
        invalid_lines: List[str] = []

        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    invalid_lines.append(stripped)
                    continue
                if not isinstance(payload, dict) or not _validate_record(payload):
                    invalid_lines.append(stripped)
                    continue
                raw_records.append(payload)

        normalized = normalize_records(raw_records)

        prepared_rows: List[dict] = []
        for record in normalized:
            if repo_slug and not record.repo_slug:
                record.repo_slug = repo_slug
            rec_dict = record.to_record()
            rec_dict["repo_slug"] = rec_dict.get("repo_slug") or repo_slug or "unknown"
            rec_dict["total_tokens"] = rec_dict["tokens_in"] + rec_dict["tokens_out"]
            rec_dict["event_date"] = _event_date(rec_dict["timestamp"])
            rec_dict["cost_usd"] = _estimate_cost(
                rec_dict.get("model"),
                rec_dict["tokens_in"],
                rec_dict["tokens_out"],
            )
            prepared_rows.append(rec_dict)

        if prepared_rows:
            self._write_parquet(prepared_rows)

        inserted = self.store.insert_sessions(prepared_rows)

        if invalid_lines:
            self._write_dead_letters(path, invalid_lines)
            print(
                f"[WARN] {len(invalid_lines)} records written to dead-letter queue at {self.dead_letter_dir}"
            )

        return inserted

    def _write_parquet(self, rows: List[dict]) -> None:
        frame = pd.DataFrame(rows)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)

        for (repo, event_date), group in frame.groupby(["repo_slug", "event_date"], dropna=False):
            repo_dir = self.parquet_dir / (repo or "unknown")
            repo_dir.mkdir(parents=True, exist_ok=True)
            parquet_path = repo_dir / f"{event_date}.parquet"
            if parquet_path.exists():
                existing = pd.read_parquet(parquet_path)
                combined = pd.concat([existing, group], ignore_index=True)
                combined = combined.drop_duplicates(
                    subset=["session_id", "timestamp", "model"], keep="last"
                )
            else:
                combined = group
            combined.to_parquet(parquet_path, index=False)

    def _write_dead_letters(self, source_path: Path, invalid_lines: Iterable[str]) -> None:
        filename = source_path.with_suffix("").name + ".deadletter.jsonl"
        dead_letter_path = self.dead_letter_dir / filename
        with dead_letter_path.open("a", encoding="utf-8") as handle:
            for line in invalid_lines:
                handle.write(line + "\n")
