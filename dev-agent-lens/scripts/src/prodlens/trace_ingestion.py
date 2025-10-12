from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .storage import ProdLensStore
from .trace_normalizer import normalize_records


class TraceIngestor:
    """Ingest LiteLLM proxy JSONL traces into the ProdLens store."""

    def __init__(self, store: ProdLensStore):
        self.store = store

    def ingest_file(self, path: Path | str) -> int:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("r", encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle if line.strip()]

        normalized = normalize_records(records)
        return self.store.insert_sessions(record.to_record() for record in normalized)
