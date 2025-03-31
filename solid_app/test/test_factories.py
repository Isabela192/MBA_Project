from src.main import app
from src.db_sqlite import get_session
from sqlmodel import Session, SQLModel, create_engine


def test_create_user():
    engine = create_engine(
        "sqlite:///testing.db", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:

        def get_session_override():
            return session

        app.dependency_overrides[get_session] = get_session_override
