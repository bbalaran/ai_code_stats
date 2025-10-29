"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    """Single metric value with optional metadata."""

    value: float
    unit: Optional[str] = None
    threshold: Optional[float] = None
    status: Optional[str] = None  # "good", "warning", "critical"


class MetricsResponse(BaseModel):
    """Aggregated metrics response."""

    ai_interaction_velocity: MetricValue = Field(
        description="Sessions per hour and median latency in seconds"
    )
    acceptance_rate: MetricValue = Field(
        description="Percentage of accepted suggestions (0-100)"
    )
    model_selection_accuracy: MetricValue = Field(
        description="Model selection alignment with policy (0-100)"
    )
    error_rate: MetricValue = Field(description="Error rate percentage (0-100)")
    token_efficiency: MetricValue = Field(description="Tokens per accepted line")
    pr_throughput: MetricValue = Field(description="Merged PRs per week")
    commit_frequency: MetricValue = Field(description="Commits per active day")
    pr_merge_time_hours: MetricValue = Field(description="Average PR merge time in hours")
    rework_rate: MetricValue = Field(description="Rework rate percentage (0-100)")
    timestamp: datetime = Field(description="Report generation timestamp")


class SessionMetadata(BaseModel):
    """Metadata for a single session."""

    session_id: str
    developer_id: Optional[str] = None
    timestamp: datetime
    model: Optional[str] = None
    tokens_in: int
    tokens_out: int
    total_tokens: int
    latency_ms: float
    status_code: Optional[int] = None
    accepted_flag: bool
    cost_usd: float
    diff_ratio: Optional[float] = None
    accepted_lines: Optional[int] = None


class SessionsListResponse(BaseModel):
    """Paginated list of sessions."""

    sessions: list[SessionMetadata]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class SessionDetailsResponse(BaseModel):
    """Detailed information about a single session."""

    session_id: str
    developer_id: Optional[str] = None
    timestamp: datetime
    model: Optional[str] = None
    tokens_in: int
    tokens_out: int
    total_tokens: int
    latency_ms: float
    status_code: Optional[int] = None
    accepted_flag: bool
    cost_usd: float
    diff_ratio: Optional[float] = None
    accepted_lines: Optional[int] = None
    repo_slug: Optional[str] = None
    # Additional context from related data
    related_pr_number: Optional[int] = None
    related_commits: list[str] = Field(default_factory=list)


class DimensionValue(BaseModel):
    """A dimension value with count."""

    value: str
    count: int


class ProfileResponse(BaseModel):
    """User/engineer profile and dimension data."""

    developer_id: Optional[str] = None
    total_sessions: int
    total_tokens_used: int
    total_cost_usd: float
    avg_latency_ms: float
    acceptance_rate: float
    most_used_models: list[DimensionValue]
    active_repos: list[DimensionValue]
    sessions_by_date: dict[str, int]  # ISO date -> count


class CorrelationMetric(BaseModel):
    """Correlation result between two variables."""

    variable1: str
    variable2: str
    r: Optional[float] = None
    p_value: Optional[float] = None
    count: int
    lag_days: int = 0
    significant: bool = False
    effect_size: Optional[str] = None  # Human-readable effect size


class InsightsResponse(BaseModel):
    """Generated insights and recommendations."""

    key_findings: list[str]
    correlations: list[CorrelationMetric]
    recommendations: list[str]
    anomalies: list[str]
    generated_at: datetime


class TokenRequest(BaseModel):
    """Request for token generation."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    database_connected: bool
    prodlens_cache_exists: bool
