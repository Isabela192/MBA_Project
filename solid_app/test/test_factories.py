import pytest


from src.main import UserCreate
from src.factories import UserFactory


@pytest.fixture
def sample_user_data():
    return UserCreate(
        document_id="12345678901",
        username="Mei Lin Lee",
        email="mei_lin_fofinha@gmail.com",
    )


class TestUserFactory:
    def test_create_user(self, sample_user_data):
        factory = UserFactory()

        result = factory.create_user(sample_user_data)

        assert isinstance(result, dict)
        assert result["document_id"] == sample_user_data.document_id
        assert result["username"] == sample_user_data.username
        assert result["email"] == sample_user_data.email
        assert result["user_type"] == "client"
