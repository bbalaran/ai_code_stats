# Phase 1 Data Infrastructure Implementation Guide

## Overview

This document details the Phase 1 implementation of the ProdLens data infrastructure and ETL pipeline, focusing on enhanced trace normalization, incremental export, database schema enhancements, Parquet partitioning, and metrics aggregation.

## Phase 1 Components

### 1. Enhanced Trace Normalization

**Module**: `scripts/src/prodlens/trace_normalizer.py`

The trace normalizer converts raw LiteLLM proxy JSON logs into canonical `CanonicalTrace` objects with the following fields:

- `session_id`: Unique session identifier (extracted from metadata with fallback patterns)
- `developer_id`: Developer identifier (extracted with "session" filtering)
- `timestamp`: UTC-normalized timestamp (supports ISO8601, Unix timestamps)
- `model`: Model name (extracted from various attribute keys)
- `tokens_in`: Input token count (coerced from usage data)
- `tokens_out`: Output token count (derived from total tokens if needed)
- `latency_ms`: Request latency in milliseconds
- `status_code`: HTTP status code (for error detection)
- `accepted_flag`: Boolean indicating whether the suggestion was accepted
- `repo_slug`: Repository slug with path traversal protection
- `diff_ratio`: Similarity ratio for accepted code (0.0-1.0)
- `accepted_lines`: Count of accepted lines of code

**Key Features**:
- Robust metadata extraction from nested structures
- Automatic coercion and fallback for missing fields
- UTC timestamp normalization
- Dead-letter queue for invalid records

**Usage Example**:
```python
from prodlens.trace_normalizer import normalize_records

raw_records = [
    {
        "timestamp": "2024-10-28T12:00:00Z",
        "usage": {"input_tokens": 1000, "output_tokens": 500},
        "attributes": {"llm.model_name": "claude-3-sonnet"},
        "metadata": {"session_id": "session_abc123"}
    }
]

normalized = normalize_records(raw_records)
# Returns list of CanonicalTrace objects
```

### 2. Checkpoint System for Incremental Exports

**Module**: `scripts/src/prodlens/storage.py` (new methods)

The checkpoint system enables safe, incremental data processing without re-processing or losing data:

**API**:
```python
store = ProdLensStore(".prod-lens/cache.db")

# Get last successful checkpoint for a job
checkpoint = store.get_last_checkpoint("trace_ingestion_job")
if checkpoint:
    # Resume from this point
    since = checkpoint

# After successful processing, mark a checkpoint
store.set_checkpoint("trace_ingestion_job", datetime.utcnow())
```

**Implementation Details**:
- Checkpoints are stored in the `etl_runs` table with job name and timestamp
- Supports multiple independent jobs with separate checkpoints
- Enables safe retries and failure recovery
- Used by CLI commands with `--since` parameter for delta processing

### 3. Database Schema Enhancements

**Module**: `scripts/src/prodlens/storage.py` (new tables)

#### Daily Session Metrics Table
```sql
CREATE TABLE daily_session_metrics (
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
```

**Indexes**:
- `idx_daily_session_metrics_date`: Fast date-based lookups for reporting

#### Daily GitHub Metrics Table
```sql
CREATE TABLE daily_github_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL UNIQUE,
    merged_pr_count INTEGER NOT NULL DEFAULT 0,
    commit_count INTEGER NOT NULL DEFAULT 0,
    reopened_pr_count INTEGER NOT NULL DEFAULT 0,
    avg_merge_hours REAL,
    created_at TEXT NOT NULL
);
```

#### Correlation Cache Table
```sql
CREATE TABLE correlation_cache (
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
```

**Purpose**:
- Pre-computed daily aggregates reduce repeated calculations
- Correlation cache prevents recomputation of expensive statistical operations
- Supports efficient incremental report generation

### 4. Parquet Partitioning Strategy

**Module**: `scripts/src/prodlens/aggregation.py` (ParquetExporter)

Data is exported to Apache Parquet format with hierarchical partitioning:

**Directory Structure**:
```
.prod-lens/parquet/
├── org-repo-1/
│   ├── 2024-10-01.parquet
│   ├── 2024-10-02.parquet
│   └── ...
├── org-repo-2/
│   ├── 2024-10-01.parquet
│   └── ...
└── _aggregates/
    ├── daily_sessions.parquet
    └── daily_github.parquet
```

**Benefits**:
- Date-based partitioning enables efficient time-range queries
- Repository-based partitioning isolates per-project analytics
- Aggregate tables provide pre-computed daily summaries
- Compatible with query engines (DuckDB, Pandas, Spark)

**Export API**:
```python
from prodlens.aggregation import ParquetExporter

exporter = ParquetExporter(".prod-lens/parquet")

# Export raw sessions
count = exporter.export_sessions_by_date(
    store,
    since=datetime.date(2024, 10, 1),
    repo_filter="org/repo"
)

# Export aggregates
agg_count = exporter.export_aggregates_by_date(store)

# List all partitions
partitions = exporter.list_partitions()
```

### 5. Daily Metrics Aggregation Pipeline

**Module**: `scripts/src/prodlens/aggregation.py` (DailyAggregator)

The aggregation pipeline computes daily summaries from raw trace and GitHub data:

**Session Aggregation**:
- Session count per day
- Total tokens consumed (input + output)
- Acceptance count (how many sessions had accepted suggestions)
- Error count (status_code >= 400)
- Median latency
- Estimated cost in USD

**GitHub Aggregation**:
- Merged PR count
- Commit count
- Reopened PR count (rework signal)
- Average merge time in hours

**Aggregation Workflow**:
```python
from prodlens.aggregation import DailyAggregator

aggregator = DailyAggregator(store)

# Get session metrics for a specific date
session_metrics = aggregator.aggregate_sessions(
    event_date=datetime.date(2024, 10, 28)
)

# Get GitHub metrics
github_metrics = aggregator.aggregate_github()

# Write both to database
session_count, github_count = aggregator.write_aggregates()
```

### 6. Enhanced Correlation Analysis with Effect Sizes

**Module**: `scripts/src/prodlens/metrics.py` (new methods)

#### New Methods in ReportGenerator

1. **compute_effect_sizes()**: Compute Cohen's d and efficiency ratios
```python
effect_sizes = generator.compute_effect_sizes(sessions, pull_requests)
# Returns:
# {
#     "latency_cohens_d": 0.35,
#     "token_efficiency_ratio": 0.92,
#     "model_acceptance_rates": {
#         "claude-3-sonnet": 0.75,
#         "claude-3-haiku": 0.65
#     }
# }
```

2. **get_correlations_with_effect_sizes()**: Combine correlation and effect size metrics
```python
result = generator.get_correlations_with_effect_sizes(
    sessions, commits, lag_days=1
)
# Includes:
# - Pearson and Spearman correlations with p-values
# - Effect size metrics
# - Session growth percentage
# - Benjamini-Hochberg adjusted p-values
```

**Effect Size Interpretations**:
- Cohen's d < 0.2: Negligible
- Cohen's d 0.2-0.5: Small
- Cohen's d 0.5-0.8: Medium
- Cohen's d > 0.8: Large

## Usage Workflows

### Workflow 1: Daily Ingestion with Incremental Checkpoint

```bash
#!/bin/bash
set -e

DB_PATH=".prod-lens/cache.db"
TRACE_FILE="/tmp/litellm_traces.jsonl"

# Get last checkpoint
CHECKPOINT=$(python3 << 'EOF'
from prodlens.storage import ProdLensStore
store = ProdLensStore("$DB_PATH")
cp = store.get_last_checkpoint("trace_ingestion")
if cp:
    print(cp.isoformat())
EOF
)

# Ingest traces
python3 -m prodlens.cli ingest-traces "$TRACE_FILE" \
    --db "$DB_PATH" \
    --repo "org/repo"

# Sync GitHub data (with ETag caching)
python3 -m prodlens.cli ingest-github \
    --repo "org/repo" \
    --db "$DB_PATH" \
    --token "$GITHUB_TOKEN"

# Aggregate daily metrics
python3 << 'EOF'
from prodlens.storage import ProdLensStore
from prodlens.aggregation import DailyAggregator

store = ProdLensStore("$DB_PATH")
aggregator = DailyAggregator(store)
session_count, github_count = aggregator.write_aggregates()
print(f"Aggregated {session_count} session metrics, {github_count} github metrics")
EOF

echo "Daily ingestion complete"
```

### Workflow 2: Generate Comprehensive Report

```bash
python3 -m prodlens.cli report \
    --repo "org/repo" \
    --db ".prod-lens/cache.db" \
    --since "2024-10-01" \
    --lag-days 1 \
    --policy-model "claude-3-sonnet" \
    --output "report.csv"
```

**Output Report Includes**:
- AI Interaction Velocity (median latency, sessions per hour)
- Acceptance Rate (% of suggested code accepted)
- Token Efficiency (tokens per accepted line, cost per PR)
- PR Throughput (merged PRs per week)
- Rework Rate (% of PRs reopened)
- AI-Outcome Association (Pearson/Spearman correlations with lagged commits)
- Effect Sizes (Cohen's d for latency, token efficiency ratios)
- Benjamini-Hochberg adjusted p-values
- Model-specific acceptance rates

### Workflow 3: Export Data to Parquet

```python
from pathlib import Path
from datetime import date
from prodlens.storage import ProdLensStore
from prodlens.aggregation import ParquetExporter

store = ProdLensStore(".prod-lens/cache.db")
exporter = ParquetExporter(".prod-lens/parquet")

# Export last 30 days of sessions
export_count = exporter.export_sessions_by_date(
    store,
    since=date(2024, 9, 28),
    repo_filter="org/repo"
)

# Export aggregates
agg_count = exporter.export_aggregates_by_date(
    store,
    since=date(2024, 9, 28)
)

print(f"Exported {export_count} session records, {agg_count} aggregate records")

# Use DuckDB or Pandas for analysis
import duckdb

result = duckdb.sql("""
    SELECT
        event_date,
        COUNT(*) as session_count,
        AVG(latency_ms) as avg_latency,
        SUM(tokens_in + tokens_out) as total_tokens
    FROM read_parquet('.prod-lens/parquet/org-repo/*.parquet')
    WHERE event_date >= '2024-10-01'
    GROUP BY event_date
    ORDER BY event_date
""").pl()

print(result)
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all Phase 1 tests
pytest scripts/tests/test_aggregation.py -v
pytest scripts/tests/test_storage_aggregation.py -v

# Run with coverage
pytest scripts/tests/ --cov=scripts/src/prodlens \
    --cov-report=html \
    --cov-report=term-missing
```

### Test Coverage

**test_aggregation.py** (38 test cases):
- DailyAggregator: Empty data, basic aggregation, acceptance rates, GitHub metrics
- ParquetExporter: Empty store, session export, filtering, roundtrip verification

**test_storage_aggregation.py** (25 test cases):
- Checkpoint management: Empty state, set/get, multiple jobs
- Daily session metrics: Insert, update, filtering
- Daily GitHub metrics: Insert, update, filtering
- Correlation cache: Insert, update, multiple lags
- Integration: Complete workflow

**test_trace_normalizer.py** (existing):
- Metadata extraction, token coercion, datetime normalization
- Session/developer ID extraction with fallbacks

**test_github_etl.py** (existing):
- ETag caching, pagination, reopen detection

**test_metrics.py** (existing):
- Velocity, acceptance rate, token efficiency
- PR throughput, merge times, rework rate
- Correlation calculations with effect sizes

## Performance Considerations

### Database Optimization

1. **Indexes**: Automatically created on `(event_date)` for fast date-based queries
2. **Partitioning**: Daily aggregates reduce query scope
3. **VACUUM**: Periodic maintenance recommended for SQLite
   ```python
   store.conn.execute("VACUUM")
   ```

### Parquet Optimization

1. **Compression**: Arrow's default Snappy compression
2. **Partition Pruning**: Query engines skip unrelated date ranges
3. **Column Selection**: Read only needed columns

**Example with DuckDB**:
```python
# Efficient: Only reads Oct 2024 parquets
result = duckdb.sql("""
    SELECT developer_id, SUM(total_tokens) as total
    FROM read_parquet('.prod-lens/parquet/org-repo/2024-10-*.parquet')
    GROUP BY developer_id
""")
```

## Troubleshooting

### Issue: Duplicate Trace Records

**Symptom**: Same trace appearing multiple times in aggregates

**Solution**: Check `trace_hash` uniqueness
```python
store = ProdLensStore(".prod-lens/cache.db")
dupes = store.conn.execute("""
    SELECT trace_hash, COUNT(*) as cnt
    FROM sessions
    GROUP BY trace_hash
    HAVING cnt > 1
""").fetchall()

if dupes:
    print(f"Found {len(dupes)} duplicate hashes")
```

### Issue: Stale ETag Cache

**Symptom**: GitHub sync not fetching new data

**Solution**: Clear ETag cache for a specific endpoint
```python
store = ProdLensStore(".prod-lens/cache.db")
store.set_etag("/repos/org/repo/pulls", None)  # Force refresh
```

### Issue: Missing Session Metrics

**Symptom**: Daily aggregates show zero sessions

**Solution**: Verify trace ingestion before aggregation
```python
sessions = store.sessions_dataframe()
print(f"Total sessions: {len(sessions)}")
print(f"Date range: {sessions['timestamp'].min()} to {sessions['timestamp'].max()}")
```

## Next Steps (Phase 2)

Phase 2 will extend Phase 1 with:

1. **Experience Sampling**: Embedded NPS/CSAT surveys during sessions
2. **A/B Testing Framework**: Experimental design support with statistical analysis
3. **Advanced Filtering**: Model-specific, time-range, developer cohort filtering
4. **Dashboard API**: FastAPI endpoints for real-time dashboard updates
5. **Export Formats**: JSON, CSV, Excel, PDF report generation
6. **Alerting**: Threshold-based notifications for significant changes

## References

- [ProdLens MVP v1.2 Design](prodlens-mvp-v1_2-design-eval.md)
- [Dev-Agent-Lens README](../README.md)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/)
- [Apache Parquet Format](https://parquet.apache.org/)
