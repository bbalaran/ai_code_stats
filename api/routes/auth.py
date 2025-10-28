"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status

from auth import create_access_token
from models import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


# For demo/pilot purposes, accept any username/password
# In production, validate against a proper user database
VALID_USERS = {
    "demo": "demo123",
    "pilot": "pilot123",
    "admin": "admin123",
}


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Get Access Token",
    description="Obtain a JWT access token for authenticated requests",
)
async def login(request: TokenRequest) -> TokenResponse:
    """Authenticate user and return JWT token.

    Args:
        request: Login credentials

    Returns:
        TokenResponse with JWT token

    Raises:
        HTTPException: If credentials are invalid
    """
    if request.username not in VALID_USERS or VALID_USERS[request.username] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": request.username, "user_id": request.username})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes in seconds
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Token",
    description="Refresh an existing JWT token",
)
async def refresh_token(request: TokenRequest) -> TokenResponse:
    """Refresh token endpoint.

    Args:
        request: Login credentials for re-authentication

    Returns:
        TokenResponse with new JWT token
    """
    # For simplicity, re-authenticate
    return await login(request)
