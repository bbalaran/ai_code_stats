"""Insights and analytics endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_optional_user
from database import get_prodlens_store
from models import CorrelationMetric, InsightsResponse

router = APIRouter(prefix="/api", tags=["insights"])


@router.get(
    "/insights",
    response_model=InsightsResponse,
    summary="Get AI Analytics Insights",
    description="Get generated insights, correlations, and recommendations",
    responses={
        200: {"description": "Insights retrieved successfully"},
        500: {"description": "Error computing insights"},
    },
)
async def get_insights(
    since: str = Query("7", description="Number of days to look back"),
    lag_days: int = Query(1, ge=0, le=7, description="Lag days for correlations"),
    user: dict = Depends(get_optional_user),
) -> InsightsResponse:
    """Get AI analytics insights including correlations and recommendations.

    Args:
        since: Number of days to include in analysis
        lag_days: Number of days to lag when computing correlations
        user: Optional authenticated user

    Returns:
        InsightsResponse with insights and recommendations
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

        # Generate base report
        report = generator.generate_report(
            repo="",
            since=since_date,
            lag_days=lag_days,
        )

        # Extract and format correlations if available
        correlations = []
        if "correlations" in report and isinstance(report["correlations"], dict):
            for corr_key, corr_data in report["correlations"].items():
                if isinstance(corr_data, dict):
                    sig = corr_data.get("p_value", 1.0) is not None and corr_data.get("p_value", 1.0) < 0.05
                    correlations.append(
                        CorrelationMetric(
                            variable1=corr_key.split("_vs_")[0] if "_vs_" in corr_key else "var1",
                            variable2=corr_key.split("_vs_")[1] if "_vs_" in corr_key else "var2",
                            r=corr_data.get("r"),
                            p_value=corr_data.get("p_value"),
                            count=corr_data.get("count", 0),
                            lag_days=lag_days,
                            significant=sig,
                        )
                    )

        # Generate key findings
        key_findings = generate_findings(report)

        # Generate recommendations
        recommendations = generate_recommendations(report)

        # Detect anomalies
        anomalies = detect_anomalies(report)

        return InsightsResponse(
            key_findings=key_findings,
            correlations=correlations,
            recommendations=recommendations,
            anomalies=anomalies,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing insights: {str(e)}",
        )
    finally:
        try:
            store.close()
        except Exception:
            pass


def generate_findings(report: dict) -> list[str]:
    """Generate key findings from metrics report.

    Args:
        report: Metrics report dictionary

    Returns:
        List of key finding strings
    """
    findings = []

    # AI Interaction Velocity
    velocity = report.get("ai_interaction_velocity", {})
    if isinstance(velocity, dict) and velocity.get("value", 0) > 4:
        findings.append("✓ High AI interaction velocity - team is actively using AI tools")

    # Acceptance Rate
    acceptance = report.get("acceptance_rate", {})
    if isinstance(acceptance, dict):
        val = float(acceptance.get("value", 0))
        if val > 50:
            findings.append("✓ High acceptance rate - suggestions are well-received")
        elif val > 25:
            findings.append("• Good acceptance rate - positive team engagement")
        elif val > 0:
            findings.append("⚠ Low acceptance rate - may need suggestion improvements")

    # Error Rate
    error_rate = report.get("error_rate", {})
    if isinstance(error_rate, dict) and error_rate.get("value", 0) < 5:
        findings.append("✓ Low error rate - system is stable")

    # Token Efficiency
    token_eff = report.get("token_efficiency", {})
    if isinstance(token_eff, dict) and token_eff.get("value", 0) < 50:
        findings.append("✓ Good token efficiency - cost-effective interactions")

    # PR Throughput
    pr_throughput = report.get("pr_throughput", {})
    if isinstance(pr_throughput, dict) and pr_throughput.get("value", 0) > 5:
        findings.append("✓ Strong PR throughput - good development velocity")

    return findings if findings else ["Collecting data for insights..."]


def generate_recommendations(report: dict) -> list[str]:
    """Generate recommendations based on metrics.

    Args:
        report: Metrics report dictionary

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Acceptance Rate recommendations
    acceptance = report.get("acceptance_rate", {})
    if isinstance(acceptance, dict) and acceptance.get("value", 0) < 25:
        recommendations.append("Review AI suggestion quality and consider model fine-tuning")

    # Error Rate recommendations
    error_rate = report.get("error_rate", {})
    if isinstance(error_rate, dict) and error_rate.get("value", 100) > 5:
        recommendations.append("Investigate error sources and improve system reliability")

    # Token Efficiency recommendations
    token_eff = report.get("token_efficiency", {})
    if isinstance(token_eff, dict) and token_eff.get("value", 0) > 50:
        recommendations.append("Optimize prompts to reduce token usage and costs")

    # PR Merge Time recommendations
    merge_time = report.get("pr_merge_time_hours", {})
    if isinstance(merge_time, dict) and merge_time.get("value", 0) > 24:
        recommendations.append("Streamline code review process to reduce PR merge time")

    # Rework Rate recommendations
    rework = report.get("rework_rate", {})
    if isinstance(rework, dict) and rework.get("value", 0) > 22:
        recommendations.append("Improve code quality checks and review processes")

    if not recommendations:
        recommendations.append("Continue current practices - metrics are healthy")

    return recommendations


def detect_anomalies(report: dict) -> list[str]:
    """Detect anomalies in the metrics.

    Args:
        report: Metrics report dictionary

    Returns:
        List of anomaly descriptions
    """
    anomalies = []

    # Check for zero values indicating missing data
    metrics_to_check = [
        "ai_interaction_velocity",
        "acceptance_rate",
        "pr_throughput",
        "commit_frequency",
    ]

    for metric in metrics_to_check:
        value = report.get(metric, {})
        if isinstance(value, dict) and value.get("value", 0) == 0:
            anomalies.append(f"No data for {metric} - may indicate data collection issues")

    # Check for abnormal error rates
    error_rate = report.get("error_rate", {})
    if isinstance(error_rate, dict) and error_rate.get("value", 0) > 20:
        anomalies.append("Unusually high error rate detected - immediate investigation recommended")

    # Check for unusually high rework
    rework = report.get("rework_rate", {})
    if isinstance(rework, dict) and rework.get("value", 0) > 40:
        anomalies.append("High rework rate detected - review process quality may be degraded")

    return anomalies
