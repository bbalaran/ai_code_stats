"""User profile endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_optional_user
from database import get_prodlens_store
from models import DimensionValue, ProfileResponse

router = APIRouter(prefix="/api", tags=["profile"])


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get User Profile",
    description="Get profile and statistics for the current user or all users",
    responses={
        200: {"description": "Profile retrieved successfully"},
        500: {"description": "Error retrieving profile"},
    },
)
async def get_profile(
    developer_id: str = None,
    user: dict = Depends(get_optional_user),
) -> ProfileResponse:
    """Get user profile with statistics and dimensions.

    Args:
        developer_id: Optional specific developer to get profile for
        user: Optional authenticated user

    Returns:
        ProfileResponse with profile data
    """
    try:
        store = get_prodlens_store()

        # Get sessions dataframe
        df = store.sessions_dataframe()

        if df.empty:
            return ProfileResponse(
                developer_id=developer_id,
                total_sessions=0,
                total_tokens_used=0,
                total_cost_usd=0.0,
                avg_latency_ms=0.0,
                acceptance_rate=0.0,
                most_used_models=[],
                active_repos=[],
                sessions_by_date={},
            )

        # Filter by developer if specified
        if developer_id:
            df = df[df["developer_id"] == developer_id]

        if df.empty and developer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Developer {developer_id} not found",
            )

        # Calculate aggregate statistics
        total_sessions = len(df)
        total_tokens = int(
            (df.get("tokens_in", 0).fillna(0).astype(int) +
             df.get("tokens_out", 0).fillna(0).astype(int)).sum()
        )
        total_cost = float(df.get("cost_usd", 0).fillna(0).sum())
        avg_latency = float(df.get("latency_ms", 0).fillna(0).mean())

        # Calculate acceptance rate
        accepted_sessions = (df.get("accepted_flag", False) == True).sum()  # noqa: E712
        acceptance_rate = (accepted_sessions / total_sessions * 100) if total_sessions > 0 else 0.0

        # Get most used models
        model_counts = df.get("model", "unknown").value_counts()
        most_used_models = [
            DimensionValue(value=str(model), count=int(count))
            for model, count in model_counts.head(5).items()
        ]

        # Get active repos
        repo_counts = df.get("repo_slug", "unknown").value_counts()
        active_repos = [
            DimensionValue(value=str(repo), count=int(count))
            for repo, count in repo_counts.head(5).items()
        ]

        # Get sessions by date
        df["date"] = pd.to_datetime(df.get("timestamp", ""), errors="coerce").dt.date
        sessions_by_date_dict = df.groupby("date").size().to_dict()
        sessions_by_date = {str(d): int(c) for d, c in sessions_by_date_dict.items()}

        return ProfileResponse(
            developer_id=developer_id,
            total_sessions=total_sessions,
            total_tokens_used=total_tokens,
            total_cost_usd=total_cost,
            avg_latency_ms=avg_latency,
            acceptance_rate=float(acceptance_rate),
            most_used_models=most_used_models,
            active_repos=active_repos,
            sessions_by_date=sessions_by_date,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving profile: {str(e)}",
        )
    finally:
        try:
            store.close()
        except Exception:
            pass


import pandas as pd
