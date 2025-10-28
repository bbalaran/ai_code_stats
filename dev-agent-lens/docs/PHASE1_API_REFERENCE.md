# Phase 1 API Reference

## Module: prodlens.storage

### Class: ProdLensStore

SQLite-backed storage for ProdLens data with session, PR, commit, and aggregation tables.

#### Constructor
```python
ProdLensStore(path: Path | str) -> ProdLensStore
```

Creates or opens an SQLite database at the given path. Automatically initializes schema on first use.

**Example**:
```python
store = ProdLensStore(".prod-lens/cache.db")
```

#### Session Management

##### insert_sessions
```python
def insert_sessions(
    self,
    sessions: Iterable[CanonicalTrace | Mapping[str, object]]
) -> int
```

Insert normalized trace records into the sessions table. Uses upsert-on-conflict semantics based on trace_hash.

**Parameters**:
- `sessions`: Iterable of CanonicalTrace objects or dictionaries

**Returns**: Number of rows inserted/updated

**Example**:
```python
from prodlens.schemas import CanonicalTrace

traces = [
    CanonicalTrace(
        session_id="sess_1",
        developer_id="alice",
        timestamp=datetime.now(timezone.utc),
        model="claude-3-sonnet",
        tokens_in=1000,
        tokens_out=500,
        latency_ms=1200,
        status_code=200,
        accepted_flag=True
    )
]
count = store.insert_sessions(traces)
```

##### fetch_sessions
```python
def fetch_sessions() -> List[sqlite3.Row]
```

Fetch all session records from the database.

**Returns**: List of Row objects (dict-like)

##### sessions_dataframe
```python
def sessions_dataframe() -> pd.DataFrame
```

Fetch all sessions as a Pandas DataFrame with proper type inference.

**Returns**: DataFrame with columns:
- session_id (object)
- developer_id (object)
- timestamp (datetime64[ns, UTC])
- model (object)
- tokens_in (int64)
- tokens_out (int64)
- latency_ms (float64)
- status_code (int64)
- accepted_flag (int64)
- repo_slug (object)
- total_tokens (int64)
- cost_usd (float64)
- diff_ratio (float64)
- accepted_lines (int64)

#### Pull Request Management

##### insert_pull_requests
```python
def insert_pull_requests(
    self,
    pull_requests: Iterable[Mapping[str, object]]
) -> int
```

Insert GitHub pull request metadata. Uses upsert-on-conflict by PR ID.

**Required fields**:
- id: Unique PR ID
- number: PR number
- title: PR title
- author: Author login
- state: "open" or "closed"
- created_at: ISO8601 timestamp
- merged_at: ISO8601 timestamp (or None)
- updated_at: ISO8601 timestamp
- reopened: Boolean

**Example**:
```python
prs = [
    {
        "id": 12345,
        "number": 42,
        "title": "Add feature X",
        "author": "alice",
        "state": "closed",
        "created_at": "2024-10-20T10:00:00Z",
        "merged_at": "2024-10-21T14:00:00Z",
        "updated_at": "2024-10-21T14:00:00Z",
        "reopened": False
    }
]
count = store.insert_pull_requests(prs)
```

##### pull_requests_dataframe
```python
def pull_requests_dataframe() -> pd.DataFrame
```

Fetch all PRs as a Pandas DataFrame.

#### Commit Management

##### insert_commits
```python
def insert_commits(
    self,
    commits: Iterable[Mapping[str, object]]
) -> int
```

Insert commit metadata.

**Required fields**:
- sha: Commit SHA
- author: Author name or login
- timestamp: ISO8601 timestamp

##### commits_dataframe
```python
def commits_dataframe() -> pd.DataFrame
```

Fetch all commits as a Pandas DataFrame.

#### Checkpoint Management

##### get_last_checkpoint
```python
def get_last_checkpoint(job_name: str) -> Optional[datetime]
```

Get the timestamp of the last successful checkpoint for a job.

**Parameters**:
- `job_name`: Logical job identifier (e.g., "trace_ingestion", "github_sync")

**Returns**: datetime in UTC or None if no checkpoint exists

**Example**:
```python
checkpoint = store.get_last_checkpoint("trace_ingestion")
if checkpoint:
    print(f"Resume from {checkpoint}")
else:
    print("Starting fresh")
```

##### set_checkpoint
```python
def set_checkpoint(
    job_name: str,
    checkpoint_timestamp: datetime
) -> None
```

Record a successful checkpoint for incremental processing.

**Parameters**:
- `job_name`: Logical job identifier
- `checkpoint_timestamp`: datetime in UTC

#### Daily Metrics Management

##### insert_daily_session_metrics
```python
def insert_daily_session_metrics(
    self,
    metrics: Iterable[Mapping[str, object]]
) -> int
```

Insert or update daily session aggregates.

**Fields**:
- event_date: ISO8601 date string (YYYY-MM-DD)
- developer_id: Optional developer identifier
- session_count: Integer
- total_tokens: Integer
- accepted_count: Integer
- error_count: Integer
- median_latency_ms: Float
- cost_usd: Float

##### insert_daily_github_metrics
```python
def insert_daily_github_metrics(
    self,
    metrics: Iterable[Mapping[str, object]]
) -> int
```

Insert or update daily GitHub metrics.

**Fields**:
- event_date: ISO8601 date string
- merged_pr_count: Integer
- commit_count: Integer
- reopened_pr_count: Integer
- avg_merge_hours: Float or None

##### fetch_daily_session_metrics
```python
def fetch_daily_session_metrics(
    self,
    since: Optional[date] = None
) -> List[dict]
```

Fetch daily session metrics, optionally filtered by date.

**Parameters**:
- `since`: Optional starting date (inclusive)

**Returns**: List of metric dictionaries

##### fetch_daily_github_metrics
```python
def fetch_daily_github_metrics(
    self,
    since: Optional[date] = None
) -> List[dict]
```

Fetch daily GitHub metrics, optionally filtered by date.

#### ETag Management (for GitHub API caching)

##### get_etag
```python
def get_etag(endpoint: str) -> Optional[str]
```

Get cached ETag for efficient GitHub API polling.

##### set_etag
```python
def set_etag(endpoint: str, etag: Optional[str]) -> None
```

Cache an ETag for conditional requests.

---

## Module: prodlens.trace_normalizer

### Function: normalize_records

```python
def normalize_records(
    records: Iterable[Mapping[str, object]]
) -> List[CanonicalTrace]
```

Normalize raw LiteLLM trace payloads into canonical CanonicalTrace objects.

**Input Format**: JSONL records with:
- timestamp: ISO8601 string or Unix timestamp
- usage: Object with input_tokens, output_tokens, total_tokens
- attributes: Object with model name, latency, status code
- metadata: Object with session_id, developer_id

**Output**: List of CanonicalTrace objects with:
- All fields validated and coerced to correct types
- Missing fields filled with sensible defaults (0, None, False)
- Timestamps normalized to UTC
- Token counts derived from available fields

**Robustness Features**:
- Flexible metadata extraction (supports nested dicts, JSON strings)
- Session ID extraction with regex fallback
- Token count derivation (if input missing, derive from total-output)
- Datetime parsing (ISO8601, Unix timestamps, with/without timezone)

---

## Module: prodlens.trace_ingestion

### Class: TraceIngestor

Ingest LiteLLM proxy JSONL traces with dead-letter queue and Parquet export.

#### Constructor
```python
TraceIngestor(
    store: ProdLensStore,
    *,
    dead_letter_dir: Path | str = Path(".prod-lens/dead-letter"),
    parquet_dir: Path | str = Path(".prod-lens/parquet")
)
```

#### ingest_file
```python
def ingest_file(
    self,
    path: Path | str,
    *,
    repo_slug: Optional[str] = None
) -> int
```

Ingest a JSONL file of traces.

**Parameters**:
- `path`: Path to JSONL file
- `repo_slug`: Optional repository slug (applied to all records if not in metadata)

**Returns**: Number of successfully inserted records

**Process**:
1. Read JSONL line-by-line
2. Normalize each record with fallback for invalid JSON
3. Write valid records to database and Parquet
4. Write invalid records to dead-letter directory

**Example**:
```python
ingestor = TraceIngestor(store)
count = ingestor.ingest_file("/tmp/traces.jsonl", repo_slug="org/repo")
print(f"Ingested {count} records")
```

---

## Module: prodlens.aggregation

### Class: DailyAggregator

Compute daily metrics aggregates from session and GitHub data.

#### Constructor
```python
DailyAggregator(store: ProdLensStore)
```

#### aggregate_sessions
```python
def aggregate_sessions(
    self,
    event_date: Optional[date] = None
) -> Dict[str, object]
```

Compute daily session metrics.

**Returns**: Dictionary mapping ISO date strings to metric dictionaries:
```python
{
    "2024-10-28": {
        "event_date": "2024-10-28",
        "session_count": 42,
        "total_tokens": 21000,
        "accepted_count": 30,
        "error_count": 2,
        "median_latency_ms": 1200.5,
        "cost_usd": 0.15
    }
}
```

#### aggregate_github
```python
def aggregate_github(
    self,
    event_date: Optional[date] = None
) -> Dict[str, object]
```

Compute daily GitHub metrics.

**Returns**: Dictionary mapping ISO date strings to metric dictionaries:
```python
{
    "2024-10-28": {
        "event_date": "2024-10-28",
        "merged_pr_count": 3,
        "commit_count": 15,
        "reopened_pr_count": 1,
        "avg_merge_hours": 4.5
    }
}
```

#### write_aggregates
```python
def write_aggregates() -> Tuple[int, int]
```

Compute all daily aggregates and write to database.

**Returns**: Tuple of (session_metrics_written, github_metrics_written)

### Class: ParquetExporter

Export trace data to Apache Parquet with date and repository partitioning.

#### Constructor
```python
ParquetExporter(
    parquet_dir: Path | str = Path(".prod-lens/parquet")
)
```

#### export_sessions_by_date
```python
def export_sessions_by_date(
    self,
    store: ProdLensStore,
    since: Optional[date] = None,
    repo_filter: Optional[str] = None
) -> int
```

Export session records to Parquet files partitioned by date and repository.

**Parameters**:
- `store`: ProdLensStore instance
- `since`: Optional starting date (inclusive)
- `repo_filter`: Optional repository filter

**Directory Structure**:
```
.prod-lens/parquet/
├── org-repo-1/
│   ├── 2024-10-28.parquet
│   └── 2024-10-29.parquet
└── org-repo-2/
    └── 2024-10-28.parquet
```

**Returns**: Number of records exported

#### export_aggregates_by_date
```python
def export_aggregates_by_date(
    self,
    store: ProdLensStore,
    since: Optional[date] = None
) -> int
```

Export pre-computed daily aggregates to Parquet.

**Output Files**:
- `.prod-lens/parquet/_aggregates/daily_sessions.parquet`
- `.prod-lens/parquet/_aggregates/daily_github.parquet`

#### list_partitions
```python
def list_partitions() -> List[Path]
```

List all exported Parquet partition files.

**Returns**: Sorted list of .parquet file paths

---

## Module: prodlens.metrics

### Class: ReportGenerator

Compute comprehensive ProdLens metrics and correlations.

#### Constructor
```python
ReportGenerator(store: ProdLensStore)
```

#### generate_report
```python
def generate_report(
    self,
    *,
    repo: str,
    since: date | datetime,
    lag_days: int = 1,
    policy_models: Optional[Set[str]] = None
) -> Dict[str, object]
```

Generate comprehensive report with all Phase 1 metrics.

**Parameters**:
- `repo`: Repository slug (for metadata)
- `since`: Start date for data filter
- `lag_days`: Lag for correlation analysis (default: 1)
- `policy_models`: Optional set of approved models for accuracy metric

**Returns**: Dictionary with keys:
- `ai_interaction_velocity`: Median latency and sessions per hour
- `acceptance_rate`: Fraction of accepted suggestions
- `model_selection_accuracy`: Adherence to model policy
- `error_rate`: Fraction of error responses
- `token_efficiency`: Tokens per accepted suggestion
- `acceptance_quality`: Diff ratio statistics
- `pr_throughput`: Merged PRs per week
- `commit_frequency`: Commits per active day
- `pr_merge_time_hours`: List of merge times
- `rework_rate`: Fraction of reopened PRs
- `cost_metrics`: Total cost and cost per PR
- `ai_outcome_association`: Pearson/Spearman correlations with lags
- `multiple_comparison_adjustment`: Benjamini-Hochberg adjusted p-values
- `metadata`: repo, since, lag_days

#### compute_effect_sizes
```python
def compute_effect_sizes(
    self,
    sessions: pd.DataFrame,
    pull_requests: pd.DataFrame
) -> Dict[str, object]
```

Compute effect sizes for accepted vs rejected code.

**Returns** Dictionary with:
- `latency_cohens_d`: Cohen's d for latency difference
- `token_efficiency_ratio`: Tokens per accepted vs average
- `model_acceptance_rates`: Acceptance rate per model

**Interpretation**:
- Cohen's d < 0.2: Negligible effect
- Cohen's d 0.2-0.5: Small effect
- Cohen's d 0.5-0.8: Medium effect
- Cohen's d > 0.8: Large effect

#### get_correlations_with_effect_sizes
```python
def get_correlations_with_effect_sizes(
    self,
    sessions: pd.DataFrame,
    commits: pd.DataFrame,
    lag_days: int = 1
) -> Dict[str, object]
```

Compute correlations with contextual effect sizes.

**Returns**: Dictionary with:
- `pearson`: Correlation result (r, p_value, count)
- `spearman`: Correlation result (r, p_value, count)
- `lag_days`: Lag days used
- `effect_sizes`: Effect size metrics
- `session_growth_percent`: Daily growth percentage

---

## Module: prodlens.github_etl

### Class: GithubETL

Synchronize GitHub repository metadata into ProdLens store.

#### Constructor
```python
GithubETL(
    store: ProdLensStore,
    session: Optional[requests.Session] = None
)
```

#### sync_pull_requests
```python
def sync_pull_requests(
    self,
    owner: str,
    repo: str,
    *,
    token: Optional[str] = None,
    since: Optional[datetime] = None
) -> int
```

Fetch closed pull requests from GitHub API.

**Features**:
- ETag-based conditional caching
- Automatic pagination handling
- Reopened PR detection via events API
- Rate limit awareness

**Parameters**:
- `owner`: Repository owner
- `repo`: Repository name
- `token`: GitHub API token (optional)
- `since`: ISO8601 datetime for delta sync

**Returns**: Number of PRs inserted/updated

#### sync_commits
```python
def sync_commits(
    self,
    owner: str,
    repo: str,
    *,
    token: Optional[str] = None,
    since: Optional[datetime] = None
) -> int
```

Fetch commits from GitHub API.

**Parameters**: Same as sync_pull_requests

**Returns**: Number of commits inserted

---

## CLI Commands

### prod-lens ingest-traces

```bash
python3 -m prodlens.cli ingest-traces <input> \
    [--db <path>] \
    [--repo <slug>] \
    [--dead-letter-dir <dir>] \
    [--parquet-dir <dir>]
```

### prod-lens ingest-github

```bash
python3 -m prodlens.cli ingest-github \
    --repo <slug> \
    [--token <token>] \
    [--db <path>] \
    [--since <date>]
```

### prod-lens report

```bash
python3 -m prodlens.cli report \
    --repo <slug> \
    --since <date> \
    [--db <path>] \
    [--lag-days <days>] \
    [--policy-model <model>]... \
    [--output <file>]
```

---

## Data Type Reference

### CanonicalTrace

```python
@dataclass
class CanonicalTrace:
    session_id: Optional[str]
    developer_id: Optional[str]
    timestamp: datetime
    model: Optional[str]
    tokens_in: int
    tokens_out: int
    latency_ms: float
    status_code: Optional[int]
    accepted_flag: bool
    repo_slug: Optional[str] = None
    diff_ratio: Optional[float] = None
    accepted_lines: Optional[int] = None

    def to_record(self) -> dict:
        """Convert to SQLite-friendly dictionary."""
```

### Report Structure

See PHASE1_QUICK_START.md for detailed schema examples.

---

## Error Handling

### Dead Letter Queue

Invalid trace records are written to `.prod-lens/dead-letter/` for manual inspection:

```bash
cat .prod-lens/dead-letter/traces.deadletter.jsonl | jq . | head -20
```

### Validation

Trace normalization includes:
- Required field checking (timestamp, usage)
- Token count coercion (derives missing fields)
- Datetime parsing with multiple format support
- Repository slug sanitization (prevents path traversal)

### Checkpoints

Checkpoints enable safe retries without data loss:

```python
# Get last successful point
checkpoint = store.get_last_checkpoint("job_name")

# Resume from checkpoint
if checkpoint:
    fetch_since = checkpoint
```

---

## Performance Tips

1. **Batch operations**: Insert 1000+ records at once
2. **Use Parquet**: Query with DuckDB/Pandas for faster analysis
3. **Index properly**: Automatic indexes on date columns
4. **Vacuum periodically**: SQLite maintenance
   ```python
   store.conn.execute("VACUUM")
   ```
5. **Partition data**: Export by date to enable query pruning
