import sys
import os
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient
from sqlmodel.pool import StaticPool

from solid_app.src.main import app
from solid_app.src.db_sqlite.database import get_session


pyproject_root = Path(__file__).parent
sys.path.insert(0, str(pyproject_root))

src_path = os.path.join(pyproject_root, "src")
sys.path.insert(0, src_path)


engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)


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
