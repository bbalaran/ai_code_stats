# ProdLens MVP v1.2 – AI Development Observability Platform

## Overview

ProdLens is a pilot-ready analytics toolkit that helps engineering leaders understand how AI-assisted development correlates with downstream delivery outcomes. The MVP ingests LiteLLM proxy traces, synchronises GitHub pull requests and commits, stores everything in SQLite/Parquet, and computes statistically rigorous metrics (including lagged correlations) that can be exported to JSON or CSV.

- **Total Changes (MVP)**: 16 files, ~2k LOC
- **Production Code**: ~1.5k LOC
- **Tests**: 11 cases, 513 LOC, 100 % passing

### System Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  LiteLLM Proxy  │ ───▶ │  Trace Ingestion │ ───▶ │ SQLite Storage  │
│  (localhost:    │      │  Dead-Letter Q   │      │ + Parquet Cache │
│   4000)         │      │  Cost Estimation │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                                              │
┌─────────────────┐      ┌──────────────────┐               │
│  GitHub API     │ ───▶ │  GitHub ETL      │ ──────────────┤
│  (PRs/Commits)  │      │  ETag Caching    │               │
└─────────────────┘      └──────────────────┘               │
                                                              ▼
                         ┌──────────────────┐      ┌─────────────────┐
                         │  Report CLI      │ ◀─── │ Metrics Engine  │
                         │  JSON + CSV      │      │ Correlations    │
                         └──────────────────┘      │ BH Correction   │
                                                    └─────────────────┘
```

## Core Components

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `cli.py` | User-facing CLI (`prod-lens`) | Commands: `ingest-traces`, `ingest-github`, `report`; runtime profile detection; JSON & CSV export |
| `trace_normalizer.py` | Converts LiteLLM JSONL into canonical records | Session/developer extraction, UTC timestamps, token calculations, acceptance flags, diff ratios |
| `trace_ingestion.py` | Orchestrates ingestion pipeline | Validation & dead-letter queue, cost estimation, Parquet partitioning, SQLite inserts |
| `storage.py` | SQLite-backed persistence layer | Automatic migrations, trace hash dedupe, indexes, ETL run tracking, pandas DataFrame helpers |
| `github_etl.py` | Syncs pull requests & commits | ETag caching, pagination, reopened detection via issue events, error handling |
| `metrics.py` | Computes analytics report | 10+ metrics, lagged AI→outcome correlations, Benjamini–Hochberg correction, SciPy fallback support |
| `schemas.py` | Dataclasses | `CanonicalTrace` with slots + type conversions |
| Tests (`tests/*`) | Validation & regression | Coverage for ETL, metrics, normaliser and ingestion pipelines |

### CLI Commands

```bash
# Ingest LiteLLM traces
prod-lens ingest-traces /path/to/traces.jsonl \
  --repo openai/dev-agent-lens \
  --db .prod-lens/cache.db

# Sync GitHub data
export GITHUB_TOKEN="ghp_xxx"
prod-lens ingest-github --repo openai/dev-agent-lens \
  --db .prod-lens/cache.db

# Generate metrics (JSON + optional CSV)
prod-lens report \
  --repo openai/dev-agent-lens \
  --since 2025-10-01 \
  --lag-days 1 \
  --policy-model "claude-3-*" \
  --output pilot-results.csv
```

Outputs include runtime profile detection (Litellm proxy, Phoenix, Arize) plus structured JSON metrics.

## Data Model & Storage

### `sessions` table
```
id INTEGER PRIMARY KEY AUTOINCREMENT
session_id TEXT
developer_id TEXT
timestamp TEXT NOT NULL
model TEXT
tokens_in INTEGER NOT NULL
tokens_out INTEGER NOT NULL
latency_ms REAL NOT NULL
status_code INTEGER
accepted_flag INTEGER NOT NULL
repo_slug TEXT
event_date TEXT
total_tokens INTEGER NOT NULL DEFAULT 0
cost_usd REAL NOT NULL DEFAULT 0
diff_ratio REAL
accepted_lines INTEGER
trace_hash TEXT UNIQUE
```

- Indexes: `idx_sessions_repo_date`, `idx_sessions_trace_hash`
- Automatic migrations add missing columns and backfill derived fields.

### `pull_requests`, `commits`, `etag_state`, `etl_runs`

- Pull requests include reopened flag set via issue event scan.
- Commits stored by SHA with UTC timestamps.
- `etag_state` keeps per-endpoint ETags and last sync time.
- `etl_runs` records job metadata (start/finish timestamps, row counts, details).

### Parquet Cache

- Partitioned by `(repo_slug, event_date)` under `.prod-lens/parquet/`.
- Deduplicated on `(session_id, timestamp, model)`.
- Enables fast analytics and incremental appends.

## Trace Ingestion Pipeline

1. **Parsing & Validation** – JSONL parsing, required fields enforced (`timestamp`, `usage`).
2. **Normalization** – `normalize_records` converts payloads into `CanonicalTrace` objects.
3. **Cost Estimation** – Model-specific pricing (per million tokens). Defaults provided for unsupported models.
4. **Parquet Output** – Partitioned writes, dedupe merges with existing files.
5. **SQLite Insert** – Batch UPSERT using `trace_hash` for deduplication.
6. **Dead-Letter Queue** – Malformed lines appended to `<filename>.deadletter.jsonl`.

Pricing Table (USD / 1M tokens):

| Model | Input | Output |
|-------|-------|--------|
| `anthropic/claude-3-sonnet` | 15.0 | 75.0 |
| `anthropic/claude-3-opus` | 15.0 | 75.0 |
| `anthropic/claude-3-haiku` | 1.0 | 5.0 |
| `openai/gpt-4o` | 5.0 | 15.0 |
| `openai/gpt-4o-mini` | 0.15 | 0.6 |

## GitHub ETL Pipeline

- **Endpoints**: `GET /repos/{owner}/{repo}/pulls?state=closed`, `GET /repos/{owner}/{repo}/commits`
- **Pagination**: Follows `Link` headers; fetches all pages.
- **ETag caching**: Only first page uses cache key; 304 short-circuits.
- **Reopened detection**: After syncing PRs, `_was_reopened` walks `issues/{number}/events` to flag reopened events.
- **Idempotency**: Database UPSERTS by PR `id` and commit `sha`.
- **ETL run tracking**: `record_etl_run` persists metadata for observability.

## Metrics Engine

`ReportGenerator.generate_report()` constructs a data dictionary with:

1. **AI Interaction Velocity** – median latency, sessions per hour, total session count.
2. **Acceptance Rate** – share of accepted sessions.
3. **Model Selection Accuracy** – policy compliance when policy models provided.
4. **Error Rate** – HTTP status ≥ 400 ratio.
5. **Token Efficiency** – tokens per accepted session & per accepted line.
6. **Acceptance Quality** – diff ratio average, share above 0.7 threshold, sample size.
7. **PR Throughput** – merged PR counts.
8. **Commit Frequency** – commits per active day.
9. **PR Merge Time** – sorted list (hours) from creation to merge.
10. **Rework Rate** – share of closed PRs marked reopened.
11. **Cost Metrics** – total session cost, merged PR count, cost per merged PR.
12. **AI Outcome Association** – lagged Pearson/Spearman correlations with sample counts, optional p-values.
13. **Multiple Comparison Adjustment** – Benjamini–Hochberg correction over available p-values (including acceptance threshold proxy).

### Statistical Handling

- Requires ≥ 2 samples to emit correlation values; fallback returns `None`.
- Optional SciPy dependency for p-values; fallback computes correlations via pandas and leaves `p_value=None`.
- BH correction ignores missing p-values and gracefully handles fallback cases.

## Test Suite

| File | Focus |
|------|-------|
| `tests/test_github_etl.py` | ETag usage, pagination, reopened detection, Data persistence |
| `tests/test_metrics.py` | Comprehensive metric calculations, timezone handling, BH adjustment |
| `tests/test_trace_ingestion.py` | Dead-letter queue, Parquet dedupe, cost estimation, SQLite persistence |
| `tests/test_trace_normalizer.py` | Multi-format normalization, timestamp conversion, session/developer extraction |
| `tests/conftest.py` | Adds `src/` to PYTHONPATH for tests |

Run all tests:

```bash
cd dev-agent-lens/scripts
pytest tests -q
```

## Usage Example – Pilot Playbook

**Day 0 – Setup**
```bash
cd dev-agent-lens/scripts
pip install -e .
export GITHUB_TOKEN="ghp_xxx"
docker compose --profile phoenix up -d    # start LiteLLM proxy + observability stack
```

**Daily Routine (Days 1‑14)**
```bash
prod-lens ingest-traces /var/log/litellm/$(date +%F).jsonl \
  --repo openai/dev-agent-lens
prod-lens ingest-github --repo openai/dev-agent-lens
prod-lens report --repo openai/dev-agent-lens \
  --since 2025-10-01 \
  --output daily-metrics.csv
```

Share CSV with leadership:
```bash
cat daily-metrics.csv | mail -s "ProdLens Daily Report" leadership@company.com
```

**Day 15 – Final Analysis**
```bash
prod-lens report \
  --repo openai/dev-agent-lens \
  --since 2025-10-01 \
  --lag-days 1 \
  --policy-model "claude-3-*" \
  --output pilot-results.csv
```

Example output snippet:

```
ai_interaction_velocity.median_latency_ms,1420.5
ai_interaction_velocity.sessions_per_hour,4.2
acceptance_rate,0.37
token_efficiency.tokens_per_accept,756.3
token_efficiency.tokens_per_accepted_line,21.8
cost_metrics.cost_per_merged_pr_usd,0.42
ai_outcome_association.pearson.r,0.68
ai_outcome_association.pearson.p_value,0.018
ai_outcome_association.pearson.adjusted_p,0.036
```

Interpretation: velocity, acceptance, and cost exceed pilot thresholds; correlations statistically significant (adjusted p < 0.05).

## Pilot Success Criteria

| Category | Target |
|----------|--------|
| Statistically significant AI→outcome association | ≥ 1 correlation with p < 0.05 |
| Participant NPS | ≥ 4 from ≥ 80 % of developers |
| Cost per merged PR | < $0.50 |

Technical milestones delivered:

- Trace ingestion with dead-letter queue and cost estimation
- GitHub ETL with ETag caching & reopened detection
- 10+ metrics with lagged correlations & BH adjustment
- CSV export for stakeholders
- Optional telemetry detection (LiteLLM proxy, Phoenix, Arize)
- Comprehensive automated tests

## Defensive Programming & Performance

- Graceful degradation when SciPy missing; correlations still available.
- Auto migrations add missing columns and backfill derived values.
- Deduplication via `trace_hash` and Parquet drop duplicates.
- UTC-normalised timestamps across pipelines.
- Transactions for inserts ensure ACID guarantees.
- Composite indexes on SQLite for analytics queries.
- Batch Parquet writes for analytics speedup (columnar).
- ETag caching minimizes GitHub API usage.

## Future Enhancements (v1.3 Roadmap Ideas)

- A/B testing scaffolding for experimentation
- Expanded rework detection using git blame diffing
- SPACE framework surveys for qualitative signal
- Postgres or cloud warehouse migration path
- Slack webhooks & automated reporting
- Optional Firebase Admin SDK authentication

## Configuration

- **LiteLLM**: `dev-agent-lens/litellm_config.yaml` (model routing, telemetry callbacks).
- **Python Package**: `pyproject.toml` adds `prod-lens` console entry and dependencies (`scipy` optional, `pytest` for tests).

## Getting Help

- Run `prod-lens report --help` for command usage.
- Check dead-letter queue (`.prod-lens/dead-letter/`) for malformed traces.
- Review `etl_runs` table for job execution metadata.
- Consult `docs/prodlens-mvp-v1_2-design-eval.md` for design rationale.

ProdLens MVP v1.2 is ready for 5‑10 developer pilots, delivering actionable insights into AI-assisted development workflows while maintaining statistical rigor and operational resilience.
