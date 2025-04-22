import os
import sys
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import get_session
from main import app


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
