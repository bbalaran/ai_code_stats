# ProdLens Data Model Documentation

## Database Schema Overview

ProdLens uses SQLite with 5 tables optimized for analytics on AI development observability data.

**Database File**: `.prod-lens/cache.db` (default location)
**Schema Version**: v1.2
**ACID Compliance**: Full transactional support via SQLite

## Table Schemas

### 1. sessions

The core table storing AI interaction traces.

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    developer_id TEXT,
    timestamp TEXT NOT NULL,
    model TEXT,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    status_code INTEGER,
    accepted_flag INTEGER NOT NULL,
    repo_slug TEXT,
    event_date TEXT,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0,
    diff_ratio REAL,
    accepted_lines INTEGER,
    trace_hash TEXT UNIQUE
);

CREATE INDEX idx_sessions_repo_date ON sessions(repo_slug, event_date);
CREATE UNIQUE INDEX idx_sessions_trace_hash ON sessions(trace_hash);
```

#### Field Definitions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | INTEGER | ✅ | Auto-incrementing primary key | `1` |
| `session_id` | TEXT | ⚠️ | Normalized session identifier | `abc123` |
| `developer_id` | TEXT | ⚠️ | Developer/user identifier | `dev@example.com` |
| `timestamp` | TEXT | ✅ | ISO 8601 UTC timestamp | `2025-10-12T19:00:00+00:00` |
| `model` | TEXT | ⚠️ | Model identifier with provider | `anthropic/claude-3-5-sonnet-20241022` |
| `tokens_in` | INTEGER | ✅ | Input tokens (prompt) | `250` |
| `tokens_out` | INTEGER | ✅ | Output tokens (completion) | `150` |
| `latency_ms` | REAL | ✅ | Request latency in milliseconds | `1234.5` |
| `status_code` | INTEGER | ⚠️ | HTTP status code | `200` |
| `accepted_flag` | INTEGER | ✅ | 1=accepted, 0=not tracked | `0` |
| `repo_slug` | TEXT | ⚠️ | Repository identifier | `owner/repo` |
| `event_date` | TEXT | ✅ | Date partition (YYYY-MM-DD) | `2025-10-12` |
| `total_tokens` | INTEGER | ✅ | tokens_in + tokens_out | `400` |
| `cost_usd` | REAL | ✅ | Estimated cost in USD | `0.004` |
| `diff_ratio` | REAL | ❌ | Code diff ratio (0.0-1.0) | `0.75` or NULL |
| `accepted_lines` | INTEGER | ❌ | Lines of code accepted | `42` or NULL |
| `trace_hash` | TEXT | ✅ | SHA-1 deduplication hash | `5bbd8ec6...` |

**Legend**:
- ✅ Always populated
- ⚠️ Populated when available
- ❌ Optional (NULL for basic traces)

#### Field Population Rules

**Always Populated** (NOT NULL or defaulted):
- `timestamp`: Defaults to current UTC time if missing
- `tokens_in`, `tokens_out`, `total_tokens`: Default to 0
- `latency_ms`: Default to 0.0
- `accepted_flag`: Default to 0 (not tracked)
- `cost_usd`: Default to 0.0
- `event_date`: Derived from timestamp
- `trace_hash`: Computed from session metadata

**Conditionally Populated**:
- `session_id`: Extracted from metadata, NULL if unavailable
- `developer_id`: Extracted from metadata, NULL if unavailable
- `model`: Extracted from attributes, NULL if unavailable
- `status_code`: HTTP status if available, NULL otherwise
- `repo_slug`: From metadata or CLI argument, NULL otherwise

**Optional Analytics Fields**:
- `diff_ratio`: Only for code suggestion traces with diff analysis
- `accepted_lines`: Only when tracking code acceptance metrics

### 2. pull_requests

GitHub pull request metadata for correlation analysis.

```sql
CREATE TABLE pull_requests (
    id INTEGER PRIMARY KEY,
    number INTEGER NOT NULL,
    title TEXT,
    author TEXT,
    state TEXT,
    created_at TEXT,
    merged_at TEXT,
    updated_at TEXT,
    reopened INTEGER DEFAULT 0
);
```

#### Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | INTEGER | GitHub PR ID | `123456789` |
| `number` | INTEGER | PR number in repo | `42` |
| `title` | TEXT | PR title | `feat: Add user authentication` |
| `author` | TEXT | PR author username | `octocat` |
| `state` | TEXT | PR state | `open`, `closed`, `merged` |
| `created_at` | TEXT | Creation timestamp | `2025-10-12T10:00:00Z` |
| `merged_at` | TEXT | Merge timestamp or NULL | `2025-10-12T15:30:00Z` |
| `updated_at` | TEXT | Last update timestamp | `2025-10-12T15:30:00Z` |
| `reopened` | INTEGER | 1 if reopened, 0 otherwise | `0` |

**Population**: Via `prod-lens ingest-github --repo owner/name`

### 3. commits

GitHub commit metadata for developer activity tracking.

```sql
CREATE TABLE commits (
    sha TEXT PRIMARY KEY,
    author TEXT,
    timestamp TEXT NOT NULL
);
```

#### Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `sha` | TEXT | Git commit SHA | `1fc3613...` |
| `author` | TEXT | Commit author | `developer@example.com` |
| `timestamp` | TEXT | Commit timestamp | `2025-10-12T12:34:56Z` |

**Population**: Via `prod-lens ingest-github --repo owner/name`

### 4. etag_state

GitHub API ETag caching for efficient incremental sync.

```sql
CREATE TABLE etag_state (
    endpoint TEXT PRIMARY KEY,
    etag TEXT,
    last_modified TEXT,
    last_synced TEXT
);
```

#### Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `endpoint` | TEXT | GitHub API endpoint | `/repos/owner/repo/pulls` |
| `etag` | TEXT | HTTP ETag header | `W/"abc123def456"` |
| `last_modified` | TEXT | Last-Modified header | `2025-10-12T15:00:00Z` |
| `last_synced` | TEXT | Last sync timestamp | `2025-10-12T15:30:00Z` |

**Purpose**: Reduces API calls by 90%+ via conditional requests

### 5. etl_runs

ETL job execution tracking for monitoring and debugging.

```sql
CREATE TABLE etl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    row_count INTEGER DEFAULT 0,
    details TEXT
);
```

#### Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | INTEGER | Run identifier | `1` |
| `job` | TEXT | Job name | `ingest-traces` |
| `started_at` | TEXT | Start timestamp | `2025-10-12T12:00:00Z` |
| `finished_at` | TEXT | End timestamp | `2025-10-12T12:05:00Z` |
| `row_count` | INTEGER | Rows processed | `3` |
| `details` | TEXT | JSON metadata | `{"source": "traces.jsonl"}` |

## Data Flow

### Trace Ingestion Pipeline

```
LiteLLM JSONL File
    ↓
Trace Normalizer (17 fields extracted)
    ↓
Validation (required fields check)
    ↓
Deduplication (trace_hash lookup)
    ↓
SQLite Insert (sessions table)
    ↓
Parquet Cache (partitioned by repo/date)
```

### GitHub Sync Pipeline

```
GitHub API (with ETag caching)
    ↓
Pull Requests → pull_requests table
    ↓
Commits → commits table
    ↓
ETag State → etag_state table
```

## Indexing Strategy

### Primary Indexes
- `sessions.trace_hash` - UNIQUE index for deduplication
- `pull_requests.id` - PRIMARY KEY
- `commits.sha` - PRIMARY KEY
- `etag_state.endpoint` - PRIMARY KEY

### Query Optimization Indexes
- `sessions(repo_slug, event_date)` - For date-range queries per repository

### Future Indexes (Phase 2)
- `sessions(timestamp)` - For time-series queries
- `sessions(developer_id)` - For per-developer analytics
- `pull_requests(number)` - For PR lookup by number

## Cost Calculation

**Model Pricing** (per million tokens):

| Model | Input | Output |
|-------|-------|--------|
| `anthropic/claude-3-sonnet` | $15.00 | $75.00 |
| `anthropic/claude-3-opus` | $15.00 | $75.00 |
| `anthropic/claude-3-haiku` | $1.00 | $5.00 |
| `openai/gpt-4o` | $5.00 | $15.00 |
| `openai/gpt-4o-mini` | $0.15 | $0.60 |
| **Default (unknown)** | $10.00 | $10.00 |

**Formula**:
```python
cost_usd = (tokens_in / 1_000_000 * input_price) +
           (tokens_out / 1_000_000 * output_price)
```

**Implementation**: `trace_ingestion.py:30-37`

## Deduplication Strategy

**Trace Hash Computation**:
```python
payload = {
    "session_id": record["session_id"],
    "developer_id": record["developer_id"],
    "timestamp": record["timestamp"],
    "model": record["model"],
    "tokens_in": int(record["tokens_in"]),
    "tokens_out": int(record["tokens_out"]),
    "latency_ms": float(record["latency_ms"]),
    "status_code": record["status_code"],
    "accepted_flag": 1 if record["accepted_flag"] else 0,
    "repo_slug": record["repo_slug"],
    "event_date": record["event_date"]
}
trace_hash = hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()
```

**Conflict Resolution**: `ON CONFLICT(trace_hash) DO UPDATE` - Last write wins

## Migration Strategy

The schema supports forward migrations via `ALTER TABLE`:

```python
# Check for missing columns
columns = {row[1] for row in cursor.execute("PRAGMA table_info(sessions)")}

# Add new columns if missing
if "new_field" not in columns:
    cursor.execute("ALTER TABLE sessions ADD COLUMN new_field TEXT")
```

**Implementation**: `storage.py:94-113`

## Usage Examples

### Query Sessions by Date Range
```sql
SELECT
    developer_id,
    COUNT(*) as session_count,
    SUM(total_tokens) as total_tokens,
    SUM(cost_usd) as total_cost
FROM sessions
WHERE event_date BETWEEN '2025-10-01' AND '2025-10-31'
  AND repo_slug = 'myorg/myrepo'
GROUP BY developer_id
ORDER BY total_cost DESC;
```

### Correlate AI Usage with PRs
```sql
SELECT
    pr.number,
    pr.title,
    pr.author,
    COUNT(DISTINCT s.session_id) as ai_sessions,
    SUM(s.total_tokens) as tokens_used,
    SUM(s.cost_usd) as cost
FROM pull_requests pr
LEFT JOIN sessions s
    ON s.developer_id = pr.author
    AND DATE(s.timestamp) BETWEEN DATE(pr.created_at) AND DATE(pr.merged_at)
WHERE pr.state = 'merged'
GROUP BY pr.number
ORDER BY cost DESC
LIMIT 10;
```

### Find High-Cost Sessions
```sql
SELECT
    session_id,
    developer_id,
    model,
    total_tokens,
    cost_usd,
    timestamp
FROM sessions
WHERE cost_usd > 0.01
ORDER BY cost_usd DESC
LIMIT 20;
```

## Data Retention

**Current**: No automatic cleanup (all data retained)
**Future**: Implement configurable retention policies

Recommendations:
- Keep raw sessions indefinitely (small storage footprint)
- Archive parquet files older than 90 days
- Retain aggregated metrics permanently

## Related Documentation

- [Session ID Normalization](SESSION_ID_NORMALIZATION.md)
- [Testing Evidence](README.md)
- [ProdLens Technical Spec](../../dev-agent-lens/docs/PRODLENS_TECHNICAL_SPEC.md)

---

**Last Updated**: October 12, 2025
**Schema Version**: v1.2
**Database**: SQLite 3.x
