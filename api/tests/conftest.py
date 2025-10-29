"""Test configuration and fixtures."""

import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add api directory to path
api_dir = Path(__file__).parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from database import get_db
from main import app


# Use in-memory SQLite for tests
@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield engine
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db) -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Get authentication token for tests."""
    response = client.post(
        "/auth/token",
        json={"username": "demo", "password": "demo123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}
