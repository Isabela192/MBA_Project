from uuid import UUID
from solid_app.src.factories import ClientFactory, ManagerFactory, SavingsAccountFactory, CheckingAccountFactory
from solid_app.src.db_sqlite.models import User, UserType
from decimal import Decimal


# User Factory Tests

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

def test_manager_factory_create_user(manager_user, mock_session):
    """Test that ManagerFactory creates a user with MANAGER type and is_staff=True."""
    factory = ManagerFactory()
    
    def side_effect(user):
        return user
    
    mock_session.refresh.side_effect = side_effect
    
    user = factory.create_user(manager_user, mock_session)
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    
    assert user.user_type == UserType.MANAGER
    assert user.is_staff is True
    assert user.document_id == "2137982347"
    assert user.username == "Nala Lee"
    assert user.email == "nala_mail@example.com"

def test_client_factory_integration(client_user, db_session):
    """Integration test that ClientFactory actually saves a user to the database."""
    factory = ClientFactory()
    
    user = factory.create_user(client_user, db_session)
    
    assert user.id is not None  
    assert isinstance(user.account_id, UUID)
    assert user.user_type == UserType.CLIENT
    assert user.is_staff is False
    
    db_user = db_session.get(User, user.id)
    assert db_user is not None
    assert db_user.document_id == "12345678901"
    assert db_user.username == "Lucky Luke"

def test_manager_factory_integration(manager_user, db_session):
    """Integration test that ClientFactory actually saves a user to the database."""
    factory = ClientFactory()
    
    user = factory.create_user(manager_user, db_session)
    
    assert user.id is not None  
    assert isinstance(user.account_id, UUID)
    assert user.user_type == UserType.CLIENT
    assert user.is_staff is False
    
    db_user = db_session.get(User, user.id)
    assert db_user is not None
    assert db_user.document_id == "2137982347"
    assert db_user.username == "Nala Lee"

# Account Factory Tests

def test_savings_account_factory_create_account(account_data, mock_session):
    """Test that SavingsAccountFactory creates a savings account."""
    factory = SavingsAccountFactory()
    
    def side_effect(account):
        return account
    
    mock_session.refresh.side_effect = side_effect
    
    account = factory.create_account(account_data, mock_session)
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    
    assert account.account_type == "savings"
    assert account.balance == Decimal("0")
    assert account.document_id == "12345678901"

def test_checking_account_factory_create_account(mock_session):
    """Test that SavingsAccountFactory creates a savings account."""
    factory = CheckingAccountFactory()
    account_data = {
        "document_id": "12345678901",
        "balance": Decimal("0"),
        "account_type": "checking"
    }
    
    def side_effect(account):
        return account
    
    mock_session.refresh.side_effect = side_effect
    
    account = factory.create_account(account_data, mock_session)
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    
    assert account.account_type == "checking"
    assert account.balance == Decimal("0")
    assert account.document_id == "12345678901"
