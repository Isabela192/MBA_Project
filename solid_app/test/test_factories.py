from uuid import UUID

from database.models import AccountType, User, UserType
from helpers.factories import ClientFactory, ManagerFactory


def test_client_factory_create_user(client_user, mock_session):
    """Test that ClientFactory creates a user with CLIENT type and is_staff=False."""
    factory = ClientFactory()

    def side_effect(user):
        return user

    mock_session.refresh.side_effect = side_effect

    user = factory.create_user(client_user, mock_session)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

    assert user.user_type == UserType.CLIENT
    assert user.is_staff is False
    assert user.document_id == "12345678901"
    assert user.username == "Lucky Luke"
    assert user.email == "lucky_mail@example.com"


def test_manager_factory_create_user(mock_session):
    """Test that ManagerFactory creates a user with MANAGER type and is_staff=True."""
    factory = ManagerFactory()
    user_data = {
        "document_id": "12345678901",
        "username": "testmanager",
        "email": "manager@example.com",
        "name": "Test Manager",
    }

    def side_effect(user):
        return user

    mock_session.refresh.side_effect = side_effect

    user = factory.create_user(user_data, mock_session)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

    assert user.user_type == UserType.MANAGER
    assert user.is_staff is True
    assert user.document_id == "12345678901"
    assert user.username == "testmanager"
    assert user.email == "manager@example.com"


def test_client_factory_integration(db_session):
    """Integration test that ClientFactory actually saves a user to the database."""
    # Arrange
    factory = ClientFactory()
    user_data = {
        "document_id": "12345678901",
        "username": "testclient",
        "email": "test@example.com",
        "name": "Test Client",
    }

    # Act
    user = factory.create_user(user_data, db_session)

    # Assert
    assert user.id is not None  # ID should be assigned by the database
    assert user.user_type == UserType.CLIENT
    assert user.is_staff is False

    # Create an account for the user and verify it has an account_id
    account_data = {"account_type": AccountType.CHECKING}
    account = factory.create_user_account(user, account_data, db_session)
    assert isinstance(account.account_id, UUID)

    # Verify user is in the database
    db_user = db_session.get(User, user.id)
    assert db_user is not None
    assert db_user.document_id == "12345678901"
    assert db_user.username == "testclient"
