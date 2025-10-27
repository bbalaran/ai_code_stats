import datetime as dt

from prodlens.trace_normalizer import normalize_records, TraceFormat


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


def test_normalizer_preserves_session_ids_with_multiple_underscores():
    record = {
        "timestamp": "2024-01-01T00:00:00Z",
        "usage": {"total_tokens": 10},
        "metadata": {"session_id": "session_alpha_beta"},
        "attributes": {},
    }

    normalized = normalize_records([record])

    assert normalized[0].session_id == "alpha_beta"


def test_normalize_arize_format_basic():
    """Test normalization of Arize/Phoenix format traces."""
    records = [
        {
            "name": "Claude_Code_Internal_Prompt_0",
            "span_kind": "LLM",
            "start_time": 1760358608016,  # milliseconds since epoch
            "end_time": 1760358609516,
            "status_code": "OK",
            "context.span_id": "8f9deb95cdb11839",
            "context.trace_id": "e4501a776815cc466697b2595f6dd889",
            "attributes.llm.model_name": "claude-3-5-haiku-20241022",
            "attributes.llm.token_count.prompt": 50,
            "attributes.llm.token_count.completion": 150,
            "attributes.llm.token_count.total": 200,
            "attributes.metadata": '{"session_id": "session_gamma", "developer_id": "dev-456"}',
        },
        {
            "name": "api_request",
            "span_kind": "CLIENT",
            "start_time": 1760358610000,
            "end_time": 1760358611000,
            "status_code": "ERROR",
            "attributes.llm.model_name": "gpt-4",
            "attributes.llm.token_count.prompt": 100,
            "attributes.llm.token_count.completion": 0,  # Error case
            "attributes.metadata": {"user_id": "session-delta", "developer_id": "dev-789"},
        }
    ]
    
    normalized = normalize_records(records, format=TraceFormat.ARIZE)
    
    # First record
    assert normalized[0].session_id == "gamma"
    assert normalized[0].developer_id == "dev-456"
    assert normalized[0].tokens_in == 50
    assert normalized[0].tokens_out == 150
    assert normalized[0].latency_ms == 1500.0  # 1760358609516 - 1760358608016
    assert normalized[0].status_code == 200  # "OK" maps to 200
    assert normalized[0].model == "claude-3-5-haiku-20241022"
    
    # Second record
    assert normalized[1].session_id == "delta"
    assert normalized[1].developer_id == "dev-789"
    assert normalized[1].tokens_in == 100
    assert normalized[1].tokens_out == 0
    assert normalized[1].latency_ms == 1000.0
    assert normalized[1].status_code == 500  # "ERROR" maps to 500
    assert normalized[1].model == "gpt-4"


def test_normalize_arize_format_with_missing_fields():
    """Test Arize format normalization handles missing fields gracefully."""
    records = [
        {
            "start_time": 1760358608016,
            "end_time": 1760358608016,  # Same as start time
            "status_code": "UNSET",
            # No token counts
            # No model name
            # No metadata
        }
    ]
    
    normalized = normalize_records(records, format=TraceFormat.ARIZE)
    
    assert normalized[0].session_id is None
    assert normalized[0].developer_id is None
    assert normalized[0].tokens_in == 0
    assert normalized[0].tokens_out == 0
    assert normalized[0].latency_ms == 0.0
    assert normalized[0].status_code is None  # "UNSET" maps to None
    assert normalized[0].model is None
