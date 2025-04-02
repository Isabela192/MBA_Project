import sys
import os
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient
from sqlmodel.pool import StaticPool

from solid_app.src.main import app
from solid_app.src.db_sqlite.database import get_session
from unittest.mock import MagicMock

pyproject_root = Path(__file__).parent
sys.path.insert(0, str(pyproject_root))

src_path = os.path.join(pyproject_root, "src")
sys.path.insert(0, src_path)


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
