import uuid
from datetime import datetime
from decimal import Decimal

from helpers.abstract_factory import HandlerAccountFactory, AccountInterface
from database.models import Account, Transaction


def test_account_factory_creates_account_handler():
    factory = HandlerAccountFactory()
    handler = factory.create_account_handler()

    assert isinstance(handler, AccountInterface)


def test_get_balance_with_existing_account(mock_session):
    # Setup
    account_id = uuid.uuid4()
    account = Account(
        account_id=account_id,
        balance=Decimal("1000.00"),
        account_type="standard",
        status="active",
    )

    mock_session.exec.return_value.first.return_value = account

    # Execute
    factory = HandlerAccountFactory()
    handler = factory.create_account_handler()
    result = handler.get_balance(account_id, mock_session)

    # Verify
    assert result == {
        "account_id": str(account_id),
        "balance": "1000.00",
        "account_type": "standard",
        "status": "active",
    }


def test_get_balance_with_nonexistent_account(mock_session):
    # Setup
    account_id = uuid.uuid4()
    mock_session.exec.return_value.first.return_value = None

    # Execute
    factory = HandlerAccountFactory()
    handler = factory.create_account_handler()
    result = handler.get_balance(account_id, mock_session)

    # Verify
    assert result is None


def test_update_balance_successfully(mock_session):
    # Setup
    account_id = uuid.uuid4()
    account = Account(
        id=1,
        account_id=account_id,
        balance=Decimal("1000.00"),
        account_type="standard",
        status="active",
    )

    mock_session.exec.return_value.first.return_value = account

    # Execute
    factory = HandlerAccountFactory()
    handler = factory.create_account_handler()
    result = handler.update_balance(account_id, Decimal("500.00"), mock_session)

    # Verify
    assert result == {
        "status": "success",
        "account_id": str(account_id),
        "new_balance": "1500.00",
        "account_type": "standard",
    }
    assert account.balance == Decimal("1500.00")
    mock_session.add.assert_called_once_with(account)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(account)


def test_update_balance_insufficient_funds(mock_session):
    # Setup
    account_id = uuid.uuid4()
    account = Account(
        id=1,
        account_id=account_id,
        balance=Decimal("100.00"),
        account_type="standard",
        status="active",
    )

    mock_session.exec.return_value.first.return_value = account

    # Execute
    factory = HandlerAccountFactory()
    handler = factory.create_account_handler()
    result = handler.update_balance(account_id, Decimal("-200.00"), mock_session)

    # Verify
    assert result == {
        "status": "failed",
        "message": "Operation would result in negative balance",
        "current_balance": "100.00",
    }
    assert account.balance == Decimal("100.00")
    mock_session.add.assert_not_called()


def test_get_transactions(mock_session):
    # Setup
    account_id = uuid.uuid4()
    account = Account(id=1, account_id=account_id)

    transaction1 = Transaction(
        id=1,
        transaction_id=uuid.uuid4(),
        type="deposit",
        amount=Decimal("100.00"),
        status="completed",
        timestamp=datetime.now(),
    )

    transaction2 = Transaction(
        id=2,
        transaction_id=uuid.uuid4(),
        type="withdrawal",
        amount=Decimal("50.00"),
        status="completed",
        timestamp=datetime.now(),
    )

    mock_session.exec.return_value.first.return_value = account
    mock_session.exec.return_value.all.return_value = [transaction1, transaction2]

    # Execute
    factory = HandlerAccountFactory()
    handler = factory.create_account_handler()
    result = handler.get_transactions(account_id, mock_session)

    # Verify
    assert result["account_id"] == str(account_id)
    assert result["count"] == 2
    assert len(result["transactions"]) == 2
    assert result["transactions"][0]["transaction_id"] == str(
        transaction1.transaction_id
    )
    assert result["transactions"][1]["transaction_id"] == str(
        transaction2.transaction_id
    )


def test_get_account_details(mock_session):
    # Setup
    account_id = uuid.uuid4()
    created_at = datetime.now()
    updated_at = datetime.now()

    account = Account(
        account_id=account_id,
        balance=Decimal("1000.00"),
        account_type="standard",
        status="active",
        created_at=created_at,
        updated_at=updated_at,
    )

    mock_session.exec.return_value.first.return_value = account

    # Execute
    factory = HandlerAccountFactory()
    handler = factory.create_account_handler()
    result = handler.get_account_details(account_id, mock_session)

    # Verify
    assert result == {
        "account_id": str(account_id),
        "balance": "1000.00",
        "account_type": "standard",
        "status": "active",
        "created_at": created_at,
        "updated_at": updated_at,
    }
