"""FastAPI application configuration."""

from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./cache.db"
    sqlalchemy_echo: bool = False

    # Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["Content-Type", "Authorization"]

    # External Services
    litellm_proxy_url: str = "http://localhost:4000"
    github_token: Optional[str] = None

    # ProdLens Configuration
    prodlens_cache_db: str = ".prod-lens/cache.db"
    prodlens_repo: str = "owner/repo"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False


# Load settings
settings = Settings()
