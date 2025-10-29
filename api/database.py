"""Database connection and session management."""

import logging
import sys
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

# Add prodlens to Python path for imports
PRODLENS_PATH = Path(__file__).parent.parent / "dev-agent-lens" / "scripts" / "src"
if str(PRODLENS_PATH) not in sys.path:
    sys.path.insert(0, str(PRODLENS_PATH))

# Import ProdLens storage module
from prodlens.storage import ProdLensStore

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency.

    Yields:
        SQLAlchemy Session for database operations
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"Failed to close database session: {e}", exc_info=True)


def get_prodlens_store() -> ProdLensStore:
    """Get ProdLens data store.

    Returns:
        ProdLensStore instance connected to cache database
    """
    db_path = Path(settings.prodlens_cache_db)
    return ProdLensStore(db_path)


def check_database_health() -> bool:
    """Check if database is accessible.

    Returns:
        True if database is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_prodlens_cache_exists() -> bool:
    """Check if ProdLens cache database exists.

    Returns:
        True if cache database file exists, False otherwise
    """
    db_path = Path(settings.prodlens_cache_db)
    return db_path.exists()
