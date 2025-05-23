from unittest.mock import MagicMock

import pytest
from database.database import get_session
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    return MagicMock(spec=Session)


engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)


SQLModel.metadata.create_all(engine)


@pytest.fixture
def db_session():
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def client(db_session):
    def override_get_session():
        return db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def client_user():
    return {
        "user_id": 1,
        "document_id": "12345678901",
        "username": "Lucky Luke",
        "email": "lucky_mail@example.com",
    }


@pytest.fixture
def manager_user():
    return {
        "document_id": "2137982347",
        "username": "Nala Lee",
        "email": "nala_mail@example.com",
    }
