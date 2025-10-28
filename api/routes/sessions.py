"""Session endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from auth import get_optional_user
from database import get_prodlens_store
from models import SessionDetailsResponse, SessionMetadata, SessionsListResponse

router = APIRouter(prefix="/api", tags=["sessions"])


@router.get(
    "/sessions",
    response_model=SessionsListResponse,
    summary="List Sessions",
    description="Get paginated list of AI interaction sessions",
    responses={
        200: {"description": "Sessions retrieved successfully"},
        500: {"description": "Error retrieving sessions"},
    },
)
async def list_sessions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    developer_id: str = Query(None, description="Filter by developer ID"),
    model: str = Query(None, description="Filter by model name"),
    sort_by: str = Query("timestamp", description="Sort field (timestamp, cost_usd, tokens)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    user: dict = Depends(get_optional_user),
) -> SessionsListResponse:
    """List AI interaction sessions with filtering and pagination.

    Args:
        page: Page number for pagination
        page_size: Number of items per page
        developer_id: Optional filter by developer
        model: Optional filter by model
        sort_by: Field to sort by
        sort_order: Sort direction
        user: Optional authenticated user

    Returns:
        SessionsListResponse with paginated sessions
    """
    try:
        store = get_prodlens_store()

        # Get sessions dataframe
        df = store.sessions_dataframe()

        if df.empty:
            return SessionsListResponse(
                sessions=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False,
            )

        # Apply filters
        if developer_id:
            df = df[df["developer_id"] == developer_id]

        if model:
            df = df[df["model"] == model]

        # Sort
        if sort_by in df.columns:
            ascending = sort_order.lower() == "asc"
            df = df.sort_values(by=sort_by, ascending=ascending)

        total_count = len(df)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        df_page = df.iloc[start_idx:end_idx]

        # Convert to SessionMetadata models
        sessions = []
        for _, row in df_page.iterrows():
            sessions.append(
                SessionMetadata(
                    session_id=str(row.get("session_id", "")),
                    developer_id=row.get("developer_id"),
                    timestamp=datetime.fromisoformat(str(row.get("timestamp", ""))),
                    model=row.get("model"),
                    tokens_in=int(row.get("tokens_in", 0)),
                    tokens_out=int(row.get("tokens_out", 0)),
                    total_tokens=int(
                        row.get("total_tokens", row.get("tokens_in", 0) + row.get("tokens_out", 0))
                    ),
                    latency_ms=float(row.get("latency_ms", 0)),
                    status_code=row.get("status_code"),
                    accepted_flag=bool(row.get("accepted_flag", False)),
                    cost_usd=float(row.get("cost_usd", 0)),
                    diff_ratio=row.get("diff_ratio"),
                    accepted_lines=row.get("accepted_lines"),
                )
            )

        return SessionsListResponse(
            sessions=sessions,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=end_idx < total_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sessions: {str(e)}",
        )
    finally:
        try:
            store.close()
        except Exception:
            pass


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailsResponse,
    summary="Get Session Details",
    description="Get detailed information about a specific session",
    responses={
        200: {"description": "Session details retrieved successfully"},
        404: {"description": "Session not found"},
        500: {"description": "Error retrieving session"},
    },
)
async def get_session_details(
    session_id: str,
    user: dict = Depends(get_optional_user),
) -> SessionDetailsResponse:
    """Get detailed information about a session.

    Args:
        session_id: Session ID to retrieve
        user: Optional authenticated user

    Returns:
        SessionDetailsResponse with session details

    Raises:
        HTTPException: If session not found or error occurs
    """
    try:
        store = get_prodlens_store()

        # Get sessions dataframe
        df = store.sessions_dataframe()

        # Find the session
        session_rows = df[df["session_id"] == session_id]

        if session_rows.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        row = session_rows.iloc[0]

        # Try to find related PR and commits
        related_pr = None
        related_commits = []

        try:
            prs_df = store.pull_requests_dataframe()
            if not prs_df.empty:
                # Get most recent PR after session timestamp
                session_ts = datetime.fromisoformat(str(row.get("timestamp", "")))
                future_prs = prs_df[
                    pd.to_datetime(prs_df["created_at"]) >= session_ts
                ]
                if not future_prs.empty:
                    related_pr = int(future_prs.iloc[0]["number"])

            commits_df = store.commits_dataframe()
            if not commits_df.empty:
                session_ts = datetime.fromisoformat(str(row.get("timestamp", "")))
                future_commits = commits_df[
                    pd.to_datetime(commits_df["timestamp"]) >= session_ts
                ]
                if not future_commits.empty:
                    related_commits = future_commits["sha"].head(5).tolist()
        except Exception:
            pass  # Continue even if we can't find related data

        return SessionDetailsResponse(
            session_id=str(row.get("session_id", "")),
            developer_id=row.get("developer_id"),
            timestamp=datetime.fromisoformat(str(row.get("timestamp", ""))),
            model=row.get("model"),
            tokens_in=int(row.get("tokens_in", 0)),
            tokens_out=int(row.get("tokens_out", 0)),
            total_tokens=int(
                row.get("total_tokens", row.get("tokens_in", 0) + row.get("tokens_out", 0))
            ),
            latency_ms=float(row.get("latency_ms", 0)),
            status_code=row.get("status_code"),
            accepted_flag=bool(row.get("accepted_flag", False)),
            cost_usd=float(row.get("cost_usd", 0)),
            diff_ratio=row.get("diff_ratio"),
            accepted_lines=row.get("accepted_lines"),
            repo_slug=row.get("repo_slug"),
            related_pr_number=related_pr,
            related_commits=related_commits,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session details: {str(e)}",
        )
    finally:
        try:
            store.close()
        except Exception:
            pass


# Fix imports for pandas
import pandas as pd
