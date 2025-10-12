import datetime as dt

from prodlens.trace_normalizer import normalize_records


def test_normalize_records_handles_multiple_formats():
    records = [
        {
            "timestamp": "2024-01-01T12:00:00Z",
            "usage": {"input_tokens": 30, "output_tokens": 70, "total_tokens": 100},
            "metadata": {
                "user_id": "_session_alpha",
                "developer_id": "dev-123",
            },
            "attributes": {
                "llm.model_name": "anthropic/claude-3-sonnet",
                "latency_ms": 1500,
                "status_code": 200,
                "prod_lens.accepted": True,
            },
        },
        {
            "timestamp": "2024-01-02T13:00:00+00:00",
            "usage": {"total_tokens": 50},
            "attributes.metadata": {
                "user_api_key_end_user_id": "session_beta",
            },
            "attributes": {
                "llm.model_name": "anthropic/claude-3-haiku",
                "request.latency_ms": 900,
                "http.status_code": 429,
            },
        },
    ]

    normalized = normalize_records(records)

    assert normalized[0].session_id == "alpha"
    assert normalized[0].developer_id == "dev-123"
    assert normalized[0].tokens_in == 30
    assert normalized[0].tokens_out == 70
    assert normalized[0].latency_ms == 1500
    assert normalized[0].status_code == 200
    assert normalized[0].accepted_flag is True
    assert normalized[0].timestamp == dt.datetime(2024, 1, 1, 12, 0, tzinfo=dt.timezone.utc)

    assert normalized[1].session_id == "beta"
    assert normalized[1].developer_id is None
    assert normalized[1].tokens_in == 50  # falls back to total tokens when splits absent
    assert normalized[1].tokens_out == 0
    assert normalized[1].latency_ms == 900
    assert normalized[1].status_code == 429
    assert normalized[1].accepted_flag is False
    assert normalized[1].timestamp == dt.datetime(2024, 1, 2, 13, 0, tzinfo=dt.timezone.utc)
