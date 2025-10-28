"""Metrics endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_optional_user
from database import get_prodlens_store
from models import MetricValue, MetricsResponse

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Get Aggregated Metrics",
    description="Get aggregated ProdLens metrics for the configured repository",
    responses={
        200: {"description": "Metrics retrieved successfully"},
        500: {"description": "Error computing metrics"},
    },
)
async def get_metrics(
    since: str = Query("7", description="Number of days to look back (default: 7)"),
    user: dict = Depends(get_optional_user),
) -> MetricsResponse:
    """Get aggregated metrics from ProdLens.

    Args:
        since: Number of days to include in metrics (as string, converted to days)
        user: Optional authenticated user

    Returns:
        MetricsResponse with computed metrics

    Raises:
        HTTPException: If metrics cannot be computed
    """
    try:
        days_back = int(since)
    except (ValueError, TypeError):
        days_back = 7

    try:
        store = get_prodlens_store()
        from prodlens.metrics import ReportGenerator

        generator = ReportGenerator(store)
        since_date = datetime.utcnow().date() - timedelta(days=days_back)

        report = generator.generate_report(
            repo="",  # Use configured repo if needed
            since=since_date,
        )

        # Convert report dict to MetricsResponse
        def get_metric(key: str, unit: str = "", threshold: float = None) -> MetricValue:
            """Helper to extract metric and determine status."""
            value = report.get(key, {})
            if isinstance(value, dict):
                val = float(value.get("value", 0))
            else:
                val = float(value) if value is not None else 0

            # Determine status based on thresholds
            status_val = None
            if threshold is not None and val >= threshold:
                status_val = "good"
            elif threshold is not None and val >= (threshold * 0.5):
                status_val = "warning"
            elif threshold is not None:
                status_val = "critical"

            return MetricValue(value=val, unit=unit, threshold=threshold, status=status_val)

        return MetricsResponse(
            ai_interaction_velocity=get_metric(
                "ai_interaction_velocity", "sessions/hour", 4.0
            ),
            acceptance_rate=get_metric("acceptance_rate", "%", 25.0),
            model_selection_accuracy=get_metric("model_selection_accuracy", "%", 80.0),
            error_rate=get_metric("error_rate", "%", 5.0),
            token_efficiency=get_metric("token_efficiency", "tokens/line", 50.0),
            pr_throughput=get_metric("pr_throughput", "PRs/week", 5.0),
            commit_frequency=get_metric("commit_frequency", "commits/day", 10.0),
            pr_merge_time_hours=get_metric("pr_merge_time_hours", "hours", 24.0),
            rework_rate=get_metric("rework_rate", "%", 22.0),
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing metrics: {str(e)}",
        )
    finally:
        try:
            store.close()
        except Exception:
            pass


@router.get(
    "/metrics/raw",
    summary="Get Raw Metrics Data",
    description="Get raw metrics data as JSON for custom analysis",
)
async def get_raw_metrics(
    since: str = Query("7", description="Number of days to look back"),
    user: dict = Depends(get_optional_user),
) -> dict:
    """Get raw metrics data from ProdLens.

    Args:
        since: Number of days to include
        user: Optional authenticated user

    Returns:
        Dictionary with raw metrics data
    """
    try:
        days_back = int(since)
    except (ValueError, TypeError):
        days_back = 7

    try:
        store = get_prodlens_store()
        from prodlens.metrics import ReportGenerator

        generator = ReportGenerator(store)
        since_date = datetime.utcnow().date() - timedelta(days=days_back)

        report = generator.generate_report(
            repo="",
            since=since_date,
        )

        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving raw metrics: {str(e)}",
        )
    finally:
        try:
            store.close()
        except Exception:
            pass
