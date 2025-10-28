# Phase 1 Quick Start Guide

## Installation

```bash
# Navigate to scripts directory
cd dev-agent-lens/scripts

# Install with test dependencies (recommended for development)
pip install -e ".[test]"

# Or install production-only
pip install -e .
```

## Basic Setup

### 1. Create .env file
```bash
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
chmod 600 .env
```

### 2. Prepare LiteLLM traces (JSONL format)
```bash
# Expected format: one JSON object per line
cat > /tmp/traces.jsonl << 'EOF'
{"timestamp": "2024-10-28T12:00:00Z", "usage": {"input_tokens": 1000, "output_tokens": 500}, "attributes": {"llm.model_name": "claude-3-sonnet"}, "metadata": {"session_id": "session_abc123", "developer_id": "alice"}}
EOF
```

## Core Commands

### Ingest Traces
```bash
python3 -m prodlens.cli ingest-traces /tmp/traces.jsonl \
    --repo "org/repo" \
    --db ".prod-lens/cache.db"
```

### Ingest GitHub Data
```bash
python3 -m prodlens.cli ingest-github \
    --repo "org/repo" \
    --token "$GITHUB_TOKEN" \
    --db ".prod-lens/cache.db"
```

### Generate Report
```bash
python3 -m prodlens.cli report \
    --repo "org/repo" \
    --db ".prod-lens/cache.db" \
    --since "2024-10-01" \
    --output "report.csv"
```

## Python API Quick Reference

### Initialize Storage
```python
from prodlens.storage import ProdLensStore

store = ProdLensStore(".prod-lens/cache.db")
```

### Ingest Traces
```python
from prodlens.trace_ingestion import TraceIngestor

ingestor = TraceIngestor(store)
inserted = ingestor.ingest_file("/tmp/traces.jsonl", repo_slug="org/repo")
print(f"Inserted {inserted} trace records")
```

### Aggregate Metrics
```python
from prodlens.aggregation import DailyAggregator

aggregator = DailyAggregator(store)
session_count, github_count = aggregator.write_aggregates()
print(f"Aggregated {session_count} session metrics")
```

### Generate Report
```python
from prodlens.metrics import ReportGenerator
from datetime import date

generator = ReportGenerator(store)
report = generator.generate_report(
    repo="org/repo",
    since=date(2024, 10, 1),
    lag_days=1
)

# Access specific metrics
print(f"Acceptance rate: {report['acceptance_rate']:.1%}")
print(f"Error rate: {report['error_rate']:.1%}")
print(f"Token efficiency: {report['token_efficiency']}")
print(f"Correlations: {report['ai_outcome_association']}")
```

### Export to Parquet
```python
from prodlens.aggregation import ParquetExporter
from datetime import date

exporter = ParquetExporter(".prod-lens/parquet")
count = exporter.export_sessions_by_date(
    store,
    since=date(2024, 10, 1)
)
print(f"Exported {count} session records to Parquet")
```

### Checkpoint Management
```python
from datetime import datetime, timezone

# Get last checkpoint
last_checkpoint = store.get_last_checkpoint("trace_ingestion")
if last_checkpoint:
    print(f"Resume from: {last_checkpoint}")

# Set a new checkpoint after successful processing
store.set_checkpoint("trace_ingestion", datetime.now(timezone.utc))
```

## Common Workflows

### Daily Ingestion Script
```python
#!/usr/bin/env python3
"""Daily ProdLens ingestion and aggregation."""

import os
from datetime import datetime, date, timezone
from pathlib import Path
from dotenv import load_dotenv

from prodlens.storage import ProdLensStore
from prodlens.trace_ingestion import TraceIngestor
from prodlens.github_etl import GithubETL
from prodlens.aggregation import DailyAggregator, ParquetExporter

load_dotenv()

DB_PATH = ".prod-lens/cache.db"
TRACE_FILE = Path("/var/log/litellm/traces.jsonl")
REPO = "org/repo"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def main():
    store = ProdLensStore(DB_PATH)

    # 1. Ingest traces
    if TRACE_FILE.exists():
        ingestor = TraceIngestor(store)
        trace_count = ingestor.ingest_file(TRACE_FILE, repo_slug=REPO)
        print(f"✓ Ingested {trace_count} trace records")

    # 2. Sync GitHub data
    github = GithubETL(store)
    owner, repo = REPO.split("/")
    pr_count = github.sync_pull_requests(owner, repo, token=GITHUB_TOKEN)
    commit_count = github.sync_commits(owner, repo, token=GITHUB_TOKEN)
    print(f"✓ Synced {pr_count} PRs and {commit_count} commits")

    # 3. Aggregate daily metrics
    aggregator = DailyAggregator(store)
    session_count, github_count = aggregator.write_aggregates()
    print(f"✓ Aggregated {session_count} session metrics and {github_count} GitHub metrics")

    # 4. Export to Parquet (daily)
    exporter = ParquetExporter(".prod-lens/parquet")
    export_count = exporter.export_sessions_by_date(store, since=date.today())
    print(f"✓ Exported {export_count} session records to Parquet")

    # 5. Update checkpoint
    store.set_checkpoint("daily_ingestion", datetime.now(timezone.utc))

    store.close()
    print("✓ Daily ingestion complete")

if __name__ == "__main__":
    main()
```

### Weekly Report Script
```python
#!/usr/bin/env python3
"""Generate weekly ProdLens report."""

import csv
from datetime import date, timedelta
from prodlens.storage import ProdLensStore
from prodlens.metrics import ReportGenerator

DB_PATH = ".prod-lens/cache.db"
REPO = "org/repo"
OUTPUT_FILE = "weekly_report.csv"

def main():
    store = ProdLensStore(DB_PATH)
    generator = ReportGenerator(store)

    # Last 7 days
    since = date.today() - timedelta(days=7)

    report = generator.generate_report(
        repo=REPO,
        since=since,
        lag_days=1,
        policy_models={"claude-3-sonnet", "claude-3-haiku"}
    )

    # Flatten and save to CSV
    rows = []
    for key, value in report.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                rows.append({"metric": f"{key}.{subkey}", "value": subvalue})
        else:
            rows.append({"metric": key, "value": value})

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ Report saved to {OUTPUT_FILE}")
    store.close()

if __name__ == "__main__":
    main()
```

## Data Structure Reference

### CanonicalTrace Schema
```python
{
    "session_id": "session_abc123",
    "developer_id": "alice",
    "timestamp": "2024-10-28T12:00:00+00:00",
    "model": "claude-3-sonnet",
    "tokens_in": 1000,
    "tokens_out": 500,
    "latency_ms": 1234.5,
    "status_code": 200,
    "accepted_flag": True,
    "repo_slug": "org/repo",
    "diff_ratio": 0.85,
    "accepted_lines": 42
}
```

### Report Schema
```python
{
    "ai_interaction_velocity": {
        "median_latency_ms": 1200.0,
        "sessions_per_hour": 4.2,
        "total_sessions": 101
    },
    "acceptance_rate": 0.72,
    "error_rate": 0.03,
    "token_efficiency": {
        "tokens_per_accept": 3214,
        "accepted_sessions": 72,
        "total_tokens": 231408,
        "tokens_per_accepted_line": 42.1
    },
    "pr_throughput": {
        "weekly_merged_prs": 12,
        "total_merged": 12
    },
    "ai_outcome_association": {
        "pearson": {"r": 0.45, "p_value": 0.05, "count": 7},
        "spearman": {"r": 0.48, "p_value": 0.04, "count": 7},
        "lag_days": 1
    },
    # ... more metrics
}
```

## Troubleshooting

### Check database status
```python
from prodlens.storage import ProdLensStore

store = ProdLensStore(".prod-lens/cache.db")

sessions = store.fetch_sessions()
prs = store.fetch_pull_requests()
commits = store.fetch_commits()

print(f"Sessions: {len(sessions)}")
print(f"PRs: {len(prs)}")
print(f"Commits: {len(commits)}")

store.close()
```

### View trace ingestion results
```python
import pandas as pd
from prodlens.storage import ProdLensStore

store = ProdLensStore(".prod-lens/cache.db")
df = store.sessions_dataframe()

print(f"Total sessions: {len(df)}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Acceptance rate: {df['accepted_flag'].mean():.1%}")
print(f"Error rate: {(df['status_code'] >= 400).mean():.1%}")
print(f"Average cost: ${df['cost_usd'].mean():.4f}")

store.close()
```

### Query Parquet data
```python
import duckdb

# Query all sessions from last 7 days
result = duckdb.sql("""
    SELECT
        event_date,
        COUNT(*) as session_count,
        AVG(latency_ms) as avg_latency_ms,
        SUM(total_tokens) as total_tokens,
        AVG(accepted_flag::int) as acceptance_rate,
        SUM(cost_usd) as daily_cost
    FROM read_parquet('.prod-lens/parquet/org-repo/*.parquet')
    WHERE event_date >= '2024-10-21'
    GROUP BY event_date
    ORDER BY event_date DESC
""")

print(result.pl())
```

## Next Steps

1. **Automate ingestion**: Set up cron job for daily/hourly runs
2. **Configure monitoring**: Add alerts for anomalies (error spikes, cost increases)
3. **Extend dashboard**: Integrate Parquet exports with BI tools (Tableau, Metabase)
4. **Plan Phase 2**: Experience sampling and A/B testing framework
