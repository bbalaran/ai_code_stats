import json
from pathlib import Path

import pandas as pd

from prodlens.storage import ProdLensStore
from prodlens.trace_ingestion import TraceIngestor


def test_trace_ingestor_handles_dead_letters_and_parquet(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    store = ProdLensStore(cache_path)

    trace_file = tmp_path / "trace.jsonl"
    valid_payload = {
        "timestamp": "2024-01-01T00:00:00Z",
        "usage": {"input_tokens": 10, "output_tokens": 5},
        "metadata": {"session_id": "session_alpha"},
        "attributes": {"diff_ratio": 0.95},
    }
    with trace_file.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(valid_payload) + "\n")
        handle.write("not-json\n")
        handle.write(json.dumps({"timestamp": "2024-01-01T00:00:00Z"}) + "\n")

    ingestor = TraceIngestor(
        store,
        dead_letter_dir=tmp_path / "dead",
        parquet_dir=tmp_path / "parquet",
    )

    inserted = ingestor.ingest_file(trace_file, repo_slug="openai/dev-agent-lens")

    assert inserted == 1

    parquet_path = tmp_path / "parquet" / "openai/dev-agent-lens" / "2024-01-01.parquet"
    assert parquet_path.exists()
    frame = pd.read_parquet(parquet_path)
    assert frame.iloc[0]["repo_slug"] == "openai/dev-agent-lens"
    assert frame.iloc[0]["tokens_in"] == 10

    dead_letter_path = tmp_path / "dead" / "trace.deadletter.jsonl"
    assert dead_letter_path.exists()
    with dead_letter_path.open("r", encoding="utf-8") as handle:
        contents = handle.read().strip().splitlines()
    assert len(contents) == 2

    sessions = store.fetch_sessions()
    assert len(sessions) == 1
    stored = dict(sessions[0])
    assert stored["repo_slug"] == "openai/dev-agent-lens"
    assert stored["event_date"] == "2024-01-01"
