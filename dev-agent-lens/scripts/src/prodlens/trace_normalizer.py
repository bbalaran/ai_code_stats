from __future__ import annotations

import datetime as dt
import json
import re
from typing import Iterable, List, Mapping, Optional

from .schemas import CanonicalTrace

_SESSION_PATTERN = re.compile(r"session[_-]([a-zA-Z0-9-]+)")


def _ensure_datetime(value: Optional[str]) -> dt.datetime:
    if value is None:
        return dt.datetime.now(tz=dt.timezone.utc)

    if isinstance(value, dt.datetime):
        return value.astimezone(dt.timezone.utc) if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)

    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)

    value = str(value)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return dt.datetime.fromisoformat(value).astimezone(dt.timezone.utc)


def _extract_metadata(record: Mapping[str, object]) -> Mapping[str, object]:
    metadata = record.get("metadata")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            return {"raw": metadata}
    if isinstance(metadata, Mapping):
        return metadata

    metadata_attr = record.get("attributes.metadata")
    if isinstance(metadata_attr, str):
        try:
            return json.loads(metadata_attr)
        except json.JSONDecodeError:
            return {"raw": metadata_attr}
    if isinstance(metadata_attr, Mapping):
        return metadata_attr

    attributes = record.get("attributes")
    if isinstance(attributes, Mapping):
        meta = attributes.get("metadata")
        if isinstance(meta, Mapping):
            return meta
    return {}


def _extract_session_id(metadata: Mapping[str, object]) -> Optional[str]:
    possible_values = []
    for key in ("session_id", "user_id", "developer_session", "user_api_key_end_user_id"):
        value = metadata.get(key)
        if value:
            possible_values.append(str(value))

    requester = metadata.get("requester_metadata")
    if isinstance(requester, Mapping):
        value = requester.get("user_id")
        if value:
            possible_values.append(str(value))

    raw = metadata.get("raw")
    if raw:
        possible_values.append(str(raw))

    for value in possible_values:
        match = _SESSION_PATTERN.search(value)
        if match:
            return match.group(1)

    return None


def _extract_developer_id(metadata: Mapping[str, object]) -> Optional[str]:
    for key in ("developer_id", "dev_id", "user", "user_id"):
        value = metadata.get(key)
        if value and "session" not in str(value):
            return str(value)

    requester = metadata.get("requester_metadata")
    if isinstance(requester, Mapping):
        user_id = requester.get("developer_id") or requester.get("user")
        if user_id and "session" not in str(user_id):
            return str(user_id)
    return None


def _extract_model(attributes: Mapping[str, object]) -> Optional[str]:
    for key in ("llm.model_name", "model", "llm.model", "model_name"):
        value = attributes.get(key)
        if value:
            return str(value)
    return None


def _extract_latency(attributes: Mapping[str, object], record: Mapping[str, object]) -> float:
    for key in ("latency_ms", "request.latency_ms", "response.latency_ms", "duration_ms"):
        value = attributes.get(key)
        if value is not None:
            return float(value)
    if "latency_ms" in record:
        return float(record["latency_ms"])
    return 0.0


def _extract_status(attributes: Mapping[str, object], record: Mapping[str, object]) -> Optional[int]:
    for key in ("status_code", "http.status_code", "response.status_code"):
        value = attributes.get(key)
        if value is not None:
            return int(value)
    value = record.get("status_code")
    return int(value) if value is not None else None


def _extract_accept_flag(attributes: Mapping[str, object]) -> bool:
    for key in ("prod_lens.accepted", "accepted", "accepted_flag"):
        value = attributes.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"true", "1", "yes"}
        if value is not None:
            return bool(value)
    return False


def normalize_records(records: Iterable[Mapping[str, object]]) -> List[CanonicalTrace]:
    """Normalize raw trace payloads into canonical ProdLens records."""

    normalized: List[CanonicalTrace] = []
    for record in records:
        attributes = record.get("attributes")
        if not isinstance(attributes, Mapping):
            attributes = {}

        metadata = _extract_metadata(record)
        session_id = _extract_session_id(metadata)
        developer_id = _extract_developer_id(metadata)

        usage = record.get("usage")
        if not isinstance(usage, Mapping):
            usage = {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")

        if input_tokens is None and total_tokens is not None and output_tokens is not None:
            input_tokens = int(total_tokens) - int(output_tokens)
        if input_tokens is None and total_tokens is not None:
            input_tokens = int(total_tokens)
        if input_tokens is None:
            input_tokens = 0

        if output_tokens is None:
            # When only total tokens are present, attribute them to input tokens
            output_tokens = max(int(total_tokens or 0) - int(input_tokens), 0)

        timestamp = _ensure_datetime(record.get("timestamp") or record.get("start_time"))
        model = _extract_model(attributes)
        latency = _extract_latency(attributes, record)
        status = _extract_status(attributes, record)
        accepted = _extract_accept_flag(attributes)

        normalized.append(
            CanonicalTrace(
                session_id=session_id,
                developer_id=developer_id,
                timestamp=timestamp,
                model=model,
                tokens_in=int(input_tokens),
                tokens_out=int(output_tokens),
                latency_ms=float(latency),
                status_code=status,
                accepted_flag=accepted,
            )
        )

    return normalized
