import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4
from datetime import datetime

from helpers.proxies import RealAccount, AccountProxy
from database.models import Account, AccountType, AccountStatus


@pytest.fixture
def mock_account():
    """Create a mock account for testing."""
    account = MagicMock(spec=Account)
    account.id = 1
    account.account_id = UUID("12345678-1234-5678-1234-567812345678")
    account.balance = Decimal("1000.0")
    account.model_dump.return_value = {
        "id": 1,
        "account_id": UUID("12345678-1234-5678-1234-567812345678"),
        "balance": Decimal("1000.0"),
        "document_id": "12345678901",
        "account_type": "checking",
        "status": "active",
    }
    return account


class TestRealAccount:
    def test_get_balance(self, mock_session, mock_account):
        """Test getting the balance from an account."""
        # Arrange
        mock_session.exec.return_value.first.return_value = mock_account
        real_account = RealAccount()
        account_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        balance = real_account.get_balance(account_id, mock_session)

        # Assert
        mock_session.exec.assert_called_once()
        assert balance == Decimal("1000.0")

    def test_get_balance_account_not_found(self, mock_session):
        """Test getting the balance from a non-existent account."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        real_account = RealAccount()
        account_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        balance = real_account.get_balance(account_id, mock_session)

        # Assert
        mock_session.exec.assert_called_once()
        assert balance is None

    def test_update_balance(self, mock_session, mock_account):
        """Test updating the balance of an account."""
        # Arrange
        mock_session.exec.return_value.first.return_value = mock_account
        real_account = RealAccount()
        account_id = UUID("12345678-1234-5678-1234-567812345678")
        amount = Decimal("500.0")

        # Act
        result = real_account.update_balance(account_id, amount, mock_session)

        # Assert
        mock_session.exec.assert_called_once()
        mock_session.add.assert_called_once_with(mock_account)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_account)
        assert mock_account.balance == Decimal("1500.0")
        assert result is True

    def test_update_balance_account_not_found(self, mock_session):
        """Test updating the balance of a non-existent account."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        real_account = RealAccount()
        account_id = UUID("12345678-1234-5678-1234-567812345678")
        amount = Decimal("500.0")

        # Act
        result = real_account.update_balance(account_id, amount, mock_session)

        # Assert
        mock_session.exec.assert_called_once()
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()
        assert result is False


class TestAccountProxy:
    def test_get_balance(self, mock_session, mock_account):
        """Test getting the balance through a proxy."""
        # Arrange
        mock_session.exec.return_value.first.return_value = mock_account
        real_account = RealAccount()
        account_proxy = AccountProxy(real_account)
        account_id = UUID("12345678-1234-5678-1234-567812345678")

        # Act
        balance = account_proxy.get_balance(account_id, mock_session)

        # Assert
        mock_session.exec.assert_called_once()
        assert balance == Decimal("1000.0")
        assert len(account_proxy.access_log) == 1
        assert account_proxy.access_log[0]["account_id"] == account_id
        assert account_proxy.access_log[0]["action"] == "get_balance"
        assert isinstance(account_proxy.access_log[0]["timestamp"], datetime)

    def test_update_balance(self, mock_session, mock_account):
        """Test updating the balance through a proxy."""
        # Arrange
        mock_session.exec.return_value.first.return_value = mock_account
        real_account = RealAccount()
        account_proxy = AccountProxy(real_account)
        account_id = UUID("12345678-1234-5678-1234-567812345678")
        amount = Decimal("500.0")

        # Act
        result = account_proxy.update_balance(account_id, amount, mock_session)

        # Assert
        mock_session.exec.assert_called_once()
        mock_session.add.assert_called_once_with(mock_account)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_account)
        assert mock_account.balance == Decimal("1500.0")
        assert result is True
        assert len(account_proxy.access_log) == 1
        assert account_proxy.access_log[0]["account_id"] == account_id
        assert account_proxy.access_log[0]["action"] == "update_balance"
        assert isinstance(account_proxy.access_log[0]["timestamp"], datetime)

    def test_multiple_actions_logged(self, mock_session, mock_account):
        """Test that multiple actions are logged in the proxy."""
        # Arrange
        mock_session.exec.return_value.first.return_value = mock_account
        real_account = RealAccount()
        account_proxy = AccountProxy(real_account)
        account_id = UUID("12345678-1234-5678-1234-567812345678")
        amount = Decimal("500.0")

        # Act
        account_proxy.get_balance(account_id, mock_session)
        account_proxy.update_balance(account_id, amount, mock_session)
        account_proxy.get_balance(account_id, mock_session)

        # Assert
        assert len(account_proxy.access_log) == 3
        assert account_proxy.access_log[0]["action"] == "get_balance"
        assert account_proxy.access_log[1]["action"] == "update_balance"
        assert account_proxy.access_log[2]["action"] == "get_balance"


class TestIntegrationTests:
    @pytest.fixture
    def test_account(self, db_session):
        """Create a test account for integration tests."""
        # Create account
        account = Account(
            account_id=uuid4(),
            document_id="12345678901",
            balance=Decimal("1000.0"),
            account_type=AccountType.CHECKING,
            status=AccountStatus.ACTIVE,
        )

        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)

        yield account

        # Clean up
        db_session.delete(account)
        db_session.commit()

    def test_real_account_integration(self, db_session, test_account):
        """Integration test for RealAccount."""
        # Arrange
        real_account = RealAccount()

        # Act - Get Balance
        balance = real_account.get_balance(test_account.account_id, db_session)

        # Assert
        assert balance == Decimal("1000.0")

        # Act - Update Balance
        result = real_account.update_balance(
            test_account.account_id, Decimal("500.0"), db_session
        )

        # Assert
        db_session.refresh(test_account)
        assert result is True
        assert test_account.balance == Decimal("1500.0")

    def test_proxy_integration(self, db_session, test_account):
        """Integration test for AccountProxy."""
        # Arrange
        real_account = RealAccount()
        account_proxy = AccountProxy(real_account)

        # Act - Get Balance
        balance = account_proxy.get_balance(test_account.account_id, db_session)

        # Assert
        assert balance == Decimal("1000.0")
        assert len(account_proxy.access_log) == 1
        assert account_proxy.access_log[0]["account_id"] == test_account.account_id

        # Act - Update Balance
        result = account_proxy.update_balance(
            test_account.account_id, Decimal("500.0"), db_session
        )

        # Assert
        db_session.refresh(test_account)
        assert result is True
        assert test_account.balance == Decimal("1500.0")
        assert len(account_proxy.access_log) == 2
