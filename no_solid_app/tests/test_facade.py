import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from database.models import Account, Transaction, TransactionStatus, TransactionType
from helpers.facade import TransactionFacade
from sqlmodel import Session


class TestTransactionFacade:
    @pytest.fixture
    def transaction_facade(self):
        return TransactionFacade()

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_account(self):
        return Account(
            id=1,
            account_id=uuid.uuid4(),
            account_number="123456",
            balance=Decimal("1000.00"),
            user_id=1,
        )

    def test_deposit_success(self, transaction_facade, mock_session, mock_account):
        # Setup
        mock_session.exec.return_value.first.return_value = mock_account
        amount = Decimal("500.00")
        initial_balance = mock_account.balance

        # Execute
        result = transaction_facade.deposit(
            mock_account.account_id, amount, mock_session
        )

        # Verify
        assert result["status"] == "success"
        assert result["message"] == "Deposit successful"
        assert "transaction_id" in result
        assert result["new_balance"] == str(initial_balance + amount)
        assert mock_account.balance == initial_balance + amount
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_deposit_account_not_found(self, transaction_facade, mock_session):
        # Setup
        mock_session.exec.return_value.first.return_value = None
        account_id = uuid.uuid4()

        # Execute
        result = transaction_facade.deposit(account_id, Decimal("100.00"), mock_session)

        # Verify
        assert result["status"] == "failed"
        assert result["message"] == f"Account {account_id} not found"
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_withdraw_success(self, transaction_facade, mock_session, mock_account):
        # Setup
        mock_session.exec.return_value.first.return_value = mock_account
        amount = Decimal("300.00")
        initial_balance = mock_account.balance

        # Execute
        result = transaction_facade.withdraw(
            mock_account.account_id, amount, mock_session
        )

        # Verify
        assert result["status"] == "success"
        assert result["message"] == "Withdraw successful"
        assert "transaction_id" in result
        assert result["new_balance"] == str(initial_balance - amount)
        assert mock_account.balance == initial_balance - amount
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_withdraw_insufficient_funds(
        self, transaction_facade, mock_session, mock_account
    ):
        # Setup
        mock_session.exec.return_value.first.return_value = mock_account
        amount = Decimal("2000.00")  # Greater than balance

        # Execute
        result = transaction_facade.withdraw(
            mock_account.account_id, amount, mock_session
        )

        # Verify
        assert result["status"] == "failed"
        assert (
            result["message"]
            == f"Insufficient funds in account {mock_account.account_id}"
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_transfer_success(self, transaction_facade, mock_session):
        # Setup - create real Account objects
        from_account = Account(
            id=1,
            account_id=uuid.uuid4(),
            account_number="123456",
            balance=Decimal("1000.00"),
            user_id=1,
        )

        to_account = Account(
            id=2,
            account_id=uuid.uuid4(),
            account_number="654321",
            balance=Decimal("500.00"),
            user_id=2,
        )

        # Create mock response for the first and second query
        mock_from_query_result = MagicMock()
        mock_from_query_result.first.return_value = from_account

        mock_to_query_result = MagicMock()
        mock_to_query_result.first.return_value = to_account

        # Configure mock_session.exec to return different results based on call order
        mock_session.exec.side_effect = [mock_from_query_result, mock_to_query_result]

        amount = Decimal("300.00")
        from_initial_balance = from_account.balance
        to_initial_balance = to_account.balance

        # Execute
        result = transaction_facade.transfer(
            from_account.account_id, to_account.account_id, amount, mock_session
        )

        # Verify
        assert result["status"] == "success"
        assert result["message"] == "Transfer successful"
        assert "transaction_id" in result
        assert result["from_account_balance"] == str(from_initial_balance - amount)
        assert from_account.balance == from_initial_balance - amount
        assert to_account.balance == to_initial_balance + amount
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_balance_success(self, transaction_facade, mock_session, mock_account):
        # Setup
        mock_session.exec.return_value.first.return_value = mock_account

        # Execute
        result = transaction_facade.get_balance(mock_account.account_id, mock_session)

        # Verify
        assert result["status"] == "success"
        assert result["account_id"] == str(mock_account.account_id)
        assert result["balance"] == str(mock_account.balance)

    def test_get_transactions_success(self, transaction_facade, mock_session):
        # Create test account
        account = Account(
            id=1,
            account_id=uuid.uuid4(),
            account_number="123456",
            balance=Decimal("1000.00"),
            user_id=1,
        )

        # Create test transactions
        transactions = [
            Transaction(
                id=1,
                transaction_id=uuid.uuid4(),
                type=TransactionType.DEPOSIT,
                amount=Decimal("100.00"),
                status=TransactionStatus.COMPLETED,
                to_account_id=account.id,
            ),
            Transaction(
                id=2,
                transaction_id=uuid.uuid4(),
                type=TransactionType.WITHDRAW,
                amount=Decimal("50.00"),
                status=TransactionStatus.COMPLETED,
                from_account_id=account.id,
            ),
        ]

        # Create mocks for the session
        mock_account_query = MagicMock()
        mock_account_query.first.return_value = account

        mock_tx_query = MagicMock()
        mock_tx_query.all.return_value = transactions

        # Configure the session.exec to return different values based on call order
        mock_session.exec.side_effect = [mock_account_query, mock_tx_query]

        # Execute
        result = transaction_facade.get_transactions(account.account_id, mock_session)

        # Verify
        assert result["status"] == "success"
        assert result["account_id"] == str(account.account_id)
        assert len(result["transactions"]) == 2
        assert result["transactions"][0]["type"] == TransactionType.DEPOSIT
        assert result["transactions"][0]["direction"] == "INCOMING"
        assert result["transactions"][1]["type"] == TransactionType.WITHDRAW
        assert result["transactions"][1]["direction"] == "OUTGOING"
