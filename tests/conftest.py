"""
Pytest configuration and fixtures for Photo Proof API tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.db.base import Base
from app.db.session import get_db
from app.services.auth_service import AuthService


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def app():
    """Create test application."""
    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture(scope="function")
def db():
    """Create database tables and provide session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(app, db):
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Generate authentication headers with a test token."""
    token_data = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "role": "studio_owner",
        "studio_id": "test-studio-id",
    }
    token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client_auth_headers():
    """Generate authentication headers for a client user."""
    token_data = {
        "sub": "test-client-id",
        "email": "client@example.com",
        "role": "client",
        "client_id": "test-client-id",
    }
    token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}
