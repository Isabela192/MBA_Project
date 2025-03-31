import sys
import os
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient

from src.main import app
from src.db_sqlite.database import get_session

pyproject_root = Path(__file__).parent
sys.path.insert(0, str(pyproject_root))

src_path = os.path.join(pyproject_root, "src")
sys.path.insert(0, src_path)

# Test database settings
TEST_DB_PATH = "testing.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

# Create test engine once
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

# Initialize database once for test session
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

SQLModel.metadata.create_all(engine)


@pytest.fixture
def db_session():
    with Session(engine) as session:
        yield session
        # Rollback changes made by test
        session.rollback()


@pytest.fixture
def client(db_session):
    def override_get_session():
        return db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
