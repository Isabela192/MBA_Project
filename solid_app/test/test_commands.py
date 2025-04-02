import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from solid_app.src.commands import DepositComand, WithdrawCommand, TransferCommand
from solid_app.src.db_sqlite.models import (
    Account,
    Transaction,
    AccountType,
    AccountStatus,
)
from solid_app.src.db_sqlite.models import TransactionType, TransactionStatus


@pytest.fixture
def mock_account():
    """Create a mock account for testing."""
    account = MagicMock(spec=Account)
    account.id = 1
    account.account_id = UUID("12345678-1234-5678-1234-567812345678")
    account.balance = Decimal("1000.0")
    # Since we're updating to model_dump, we need to mock it
    account.model_dump.return_value = {
        "id": 1,
        "account_id": UUID("12345678-1234-5678-1234-567812345678"),
        "balance": Decimal("1000.0"),
        "document_id": "12345678901",
        "account_type": "checking",
        "status": "active",
    }
    return account


@pytest.fixture
def mock_transaction():
    """Create a mock transaction for testing."""
    transaction = MagicMock(spec=Transaction)
    transaction.id = 1
    transaction.transaction_id = UUID("12345678-1234-5678-1234-567812345678")
    transaction.type = TransactionType.TRANSFER
    transaction.amount = Decimal("500.0")
    transaction.status = TransactionStatus.COMPLETED
    transaction.from_account_id = 1
    transaction.to_account_id = 2
    # Since we're updating to model_dump, we need to mock it
    transaction.model_dump.return_value = {
        "id": 1,
        "transaction_id": UUID("12345678-1234-5678-1234-567812345678"),
        "type": TransactionType.TRANSFER,
        "amount": Decimal("500.0"),
        "status": TransactionStatus.COMPLETED,
        "from_account_id": 1,
        "to_account_id": 2,
    }
    return transaction


class TestDepositCommand:
    def test_deposit_command_success(self, mock_session, mock_account):
        """Test successful deposit to an account."""
        # Arrange
        amount = Decimal("500.0")
        mock_session.exec.return_value.first.return_value = mock_account
        command = DepositComand(str(mock_account.account_id), amount)

        # Act
        result = command.execute(mock_session)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_account)
        assert mock_account.balance == Decimal("1500.0")
        assert isinstance(result, dict)
        assert "account_id" in result
        assert result["balance"] == Decimal(
            "1000.0"
        )  # Dict method returns a mock result

    def test_deposit_command_account_not_found(self, mock_session):
        """Test deposit to non-existent account."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        command = DepositComand("non-existent-id", Decimal("500.0"))

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            command.execute(mock_session)

        assert "Account non-existent-id not found" in str(excinfo.value)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestWithdrawCommand:
    def test_withdraw_command_success(self, mock_session, mock_account):
        """Test successful withdrawal from an account."""
        # Arrange
        amount = Decimal("500.0")
        mock_session.exec.return_value.first.return_value = mock_account
        command = WithdrawCommand(str(mock_account.account_id), amount)

        # Act
        result = command.execute(mock_session)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_account)
        assert mock_account.balance == Decimal("500.0")
        assert isinstance(result, dict)
        assert "account_id" in result
        assert result["balance"] == Decimal(
            "1000.0"
        )  # Dict method returns a mock result

    def test_withdraw_command_account_not_found(self, mock_session):
        """Test withdrawal from non-existent account."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        command = WithdrawCommand("non-existent-id", Decimal("500.0"))

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            command.execute(mock_session)

        assert "Account non-existent-id not found" in str(excinfo.value)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_withdraw_command_insufficient_funds(self, mock_session, mock_account):
        """Test withdrawal with insufficient funds."""
        # Arrange
        mock_account.balance = Decimal("400.0")
        mock_session.exec.return_value.first.return_value = mock_account
        command = WithdrawCommand(str(mock_account.account_id), Decimal("500.0"))

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            command.execute(mock_session)

        assert "Insufficient funds" in str(excinfo.value)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestTransferCommand:
    def test_transfer_command_success(
        self, mock_session, mock_account, mock_transaction
    ):
        """Test successful transfer between accounts."""
        # Arrange
        from_account = mock_account
        to_account = MagicMock(spec=Account)
        to_account.id = 2
        to_account.account_id = UUID("87654321-8765-4321-8765-432187654321")
        to_account.balance = Decimal("500.0")

        mock_session.exec.return_value.first.side_effect = [from_account, to_account]
        mock_session.refresh.return_value = mock_transaction

        command = TransferCommand(
            str(from_account.account_id), str(to_account.account_id), Decimal("300.0")
        )

        # Act
        result = command.execute(mock_session)

        # Assert
        assert mock_session.add.call_count >= 3  # Transaction and both accounts
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert from_account.balance == Decimal("700.0")
        assert to_account.balance == Decimal("800.0")
        assert isinstance(result, dict)
        assert "transaction_id" in result
        assert result["type"] == TransactionType.TRANSFER

    def test_transfer_command_from_account_not_found(self, mock_session):
        """Test transfer from non-existent account."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        command = TransferCommand("non-existent-id", "valid-id", Decimal("500.0"))

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            command.execute(mock_session)

        assert "From Account non-existent-id not found" in str(excinfo.value)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_transfer_command_to_account_not_found(self, mock_session, mock_account):
        """Test transfer to non-existent account."""
        # Arrange
        mock_session.exec.return_value.first.side_effect = [mock_account, None]
        command = TransferCommand(
            str(mock_account.account_id), "non-existent-id", Decimal("500.0")
        )

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            command.execute(mock_session)

        assert "To Account non-existent-id not found" in str(excinfo.value)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_transfer_command_insufficient_funds(self, mock_session, mock_account):
        """Test transfer with insufficient funds."""
        # Arrange
        from_account = mock_account
        from_account.balance = Decimal("200.0")
        to_account = MagicMock(spec=Account)
        to_account.id = 2
        to_account.account_id = UUID("87654321-8765-4321-8765-432187654321")

        mock_session.exec.return_value.first.side_effect = [from_account, to_account]

        command = TransferCommand(
            str(from_account.account_id), str(to_account.account_id), Decimal("500.0")
        )

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            command.execute(mock_session)

        assert "Insufficient funds" in str(excinfo.value)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


class TestCommandsIntegration:
    """Integration tests for commands using a real database session."""

    @pytest.fixture
    def test_accounts(self, db_session):
        """Create test accounts for integration tests."""
        # Create first account
        account1 = Account(
            account_id=uuid4(),
            document_id="12345678901",
            balance=Decimal("1000.0"),
            account_type=AccountType.CHECKING,
            status=AccountStatus.ACTIVE,
        )

        # Create second account
        account2 = Account(
            account_id=uuid4(),
            document_id="98765432109",
            balance=Decimal("500.0"),
            account_type=AccountType.SAVINGS,
            status=AccountStatus.ACTIVE,
        )

        db_session.add(account1)
        db_session.add(account2)
        db_session.commit()
        db_session.refresh(account1)
        db_session.refresh(account2)

        yield (account1, account2)

        # Clean up
        db_session.delete(account1)
        db_session.delete(account2)
        db_session.commit()

    def test_deposit_integration(self, db_session, test_accounts):
        """Integration test for deposit command."""
        # Arrange
        account = test_accounts[0]
        initial_balance = account.balance
        amount = Decimal("500.0")

        # Act
        command = DepositComand(str(account.account_id), amount)
        result = command.execute(db_session)

        # Assert
        # Reload account to get fresh data
        db_session.refresh(account)
        assert account.balance == initial_balance + amount
        assert result["balance"] == initial_balance + amount

        # Verify transaction was created
        from sqlmodel import select

        transactions = db_session.exec(
            select(Transaction).where(Transaction.to_account_id == account.id)
        ).all()
        assert len(transactions) > 0
        latest_transaction = transactions[-1]
        assert latest_transaction.amount == amount
        assert latest_transaction.type == TransactionType.DEPOSIT
        assert latest_transaction.status == TransactionStatus.COMPLETED

    def test_withdraw_integration(self, db_session, test_accounts):
        """Integration test for withdraw command."""
        # Arrange
        account = test_accounts[0]
        initial_balance = account.balance
        amount = Decimal("300.0")

        # Act
        command = WithdrawCommand(str(account.account_id), amount)
        result = command.execute(db_session)

        # Assert
        # Reload account to get fresh data
        db_session.refresh(account)
        assert account.balance == initial_balance - amount
        assert result["balance"] == initial_balance - amount

        # Verify transaction was created
        from sqlmodel import select

        transactions = db_session.exec(
            select(Transaction).where(Transaction.from_account_id == account.id)
        ).all()
        assert len(transactions) > 0
        latest_transaction = transactions[-1]
        assert latest_transaction.amount == amount
        assert latest_transaction.type == TransactionType.WITHDRAW
        assert latest_transaction.status == TransactionStatus.COMPLETED

    def test_transfer_integration(self, db_session, test_accounts):
        """Integration test for transfer command."""
        # Arrange
        from_account, to_account = test_accounts
        from_initial_balance = from_account.balance
        to_initial_balance = to_account.balance
        amount = Decimal("200.0")

        # Act
        command = TransferCommand(
            str(from_account.account_id), str(to_account.account_id), amount
        )
        result = command.execute(db_session)

        # Assert
        # Reload accounts to get fresh data
        db_session.refresh(from_account)
        db_session.refresh(to_account)

        assert from_account.balance == from_initial_balance - amount
        assert to_account.balance == to_initial_balance + amount

        # Verify transaction was created
        assert result["type"] == TransactionType.TRANSFER
        assert result["amount"] == amount
        assert result["status"] == TransactionStatus.COMPLETED
        assert result["from_account_id"] == from_account.id
        assert result["to_account_id"] == to_account.id
