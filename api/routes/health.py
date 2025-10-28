"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

from database import check_database_health, get_prodlens_cache_exists
from models import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the API and database are healthy",
)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database_connected=check_database_health(),
        prodlens_cache_exists=get_prodlens_cache_exists(),
    )
