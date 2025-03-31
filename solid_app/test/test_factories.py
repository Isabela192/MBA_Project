from uuid import UUID
from src.factories import ClientFactory
from src.db_sqlite.models import User, UserType


class TestClientFactory:
    def test_create_client_user(self, db_session):
        """Test that ClientFactory creates a client user in the database."""
        # Arrange
        factory = ClientFactory()
        user_data = {
            "document_id": "12345678901",
            "username": "testclient",
            "email": "testclient@example.com",
        }

        # Act
        user = factory.create_user(user_data, db_session)

        # Assert
        assert isinstance(user, User)
        assert isinstance(user.account_id, UUID)
        assert user.user_type == UserType.CLIENT
        assert user.is_staff is False
        assert user.document_id == "12345678901"
        assert user.username == "testclient"
        assert user.email == "testclient@example.com"
