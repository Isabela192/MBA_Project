from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID, uuid4

from database.models import Account, Transaction, TransactionStatus, TransactionType
from sqlmodel import Session, select

# Command Pattern


class Command(ABC):
    @abstractmethod
    def execute(self, session: Session) -> Dict[str, Any]:
        pass


class DepositCommand(Command):
    def __init__(self, account_id: str, amount: Decimal):
        try:
            self.account_id = (
                UUID(account_id) if isinstance(account_id, str) else account_id
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid account_id format. Expected UUID, got: {account_id}"
            ) from error

        self.amount = amount

    def execute(self, session: Session) -> Dict[str, Any]:
        statement = select(Account).where(Account.account_id == self.account_id)
        account = session.exec(statement).first()

        if not account:
            raise ValueError(f"FAILED! Account {self.account_id} not found")

        transaction = Transaction(
            transaction_id=uuid4(),
            type=TransactionType.DEPOSIT,
            amount=self.amount,
            status=TransactionStatus.COMPLETED,
            to_account_id=account.id,
        )

        account.balance += self.amount
        account.updated_at = datetime.now()

        session.add(transaction)
        session.commit()
        session.refresh(account)
        return account.model_dump()


class TransferCommand(Command):
    def __init__(self, from_account_id: str, to_account_id: str, amount: Decimal):
        try:
            self.from_account_id = (
                UUID(from_account_id)
                if isinstance(from_account_id, str)
                else from_account_id
            )
        except ValueError as e:
            raise ValueError(
                f"Invalid from_account_id format. Expected UUID, got: {from_account_id}"
            ) from e

        try:
            self.to_account_id = (
                UUID(to_account_id) if isinstance(to_account_id, str) else to_account_id
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid to_account_id format. Expected UUID, got: {to_account_id}"
            ) from error

        self.amount = amount

    def execute(self, session: Session) -> Dict[str, Any]:
        from_statement = select(Account).where(
            Account.account_id == self.from_account_id
        )
        from_account = session.exec(from_statement).first()

        if not from_account:
            raise ValueError(f"FAILED! From Account {self.from_account_id} not found")

        if from_account.balance < self.amount:
            raise ValueError(
                f"FAILED! Insufficient funds in account {self.from_account_id}"
            )

        to_statement = select(Account).where(Account.account_id == self.to_account_id)
        to_account = session.exec(to_statement).first()

        if not to_account:
            raise ValueError(f"FAILED! To Account {self.to_account_id} not found")

        transaction = Transaction(
            transaction_id=uuid4(),
            type=TransactionType.TRANSFER,
            amount=self.amount,
            status=TransactionStatus.COMPLETED,
            from_account_id=from_account.id,
            to_account_id=to_account.id,
        )

        from_account.balance -= self.amount
        to_account.balance += self.amount
        from_account.updated_at = datetime.now()
        to_account.updated_at = datetime.now()

        session.add(transaction)
        session.add(from_account)
        session.add(to_account)
        session.commit()
        session.refresh(transaction)

        return transaction.model_dump()


class WithdrawCommand(Command):
    def __init__(self, account_id: str, amount: Decimal):
        try:
            self.account_id = (
                UUID(account_id) if isinstance(account_id, str) else account_id
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid account_id format. Expected UUID, got: {account_id}"
            ) from error

        self.amount = amount

    def execute(self, session: Session) -> Dict[str, Any]:
        statement = select(Account).where(Account.account_id == self.account_id)
        account = session.exec(statement).first()

        if not account:
            raise ValueError(f"FAILED! Account {self.account_id} not found")

        if account.balance < self.amount:
            raise ValueError(f"FAILED! Insufficient funds in account {self.account_id}")

        transaction = Transaction(
            transaction_id=uuid4(),
            type=TransactionType.WITHDRAW,
            amount=self.amount,
            status=TransactionStatus.COMPLETED,
            from_account_id=account.id,
        )

        account.balance -= self.amount
        account.updated_at = datetime.now()

        session.add(transaction)
        session.commit()
        session.refresh(account)
        return account.model_dump()


class GetTransactionsCommand(Command):
    def __init__(self, account_id: str):
        try:
            self.account_id = (
                UUID(account_id) if isinstance(account_id, str) else account_id
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid account_id format. Expected UUID, got: {account_id}"
            ) from error

    def execute(self, session: Session) -> Dict[str, Any]:
        # Find the account
        account_statement = select(Account).where(Account.account_id == self.account_id)
        account = session.exec(account_statement).first()

        if not account:
            return {
                "status": "failed",
                "message": f"Account {self.account_id} not found",
            }

        # Get transactions where this account is either sender or receiver
        statement = (
            select(Transaction)
            .where(
                (Transaction.from_account_id == account.id)
                | (Transaction.to_account_id == account.id)
            )
            .order_by(Transaction.timestamp)
        )

        transactions = session.exec(statement).all()

        # Format transactions for response
        formatted_transactions = [
            {
                "transaction_id": str(transaction.transaction_id),
                "type": transaction.type,
                "amount": str(transaction.amount),
                "status": transaction.status,
                "timestamp": transaction.timestamp,
                "direction": "OUTGOING"
                if transaction.from_account_id == account.id
                else "INCOMING",
            }
            for transaction in transactions
        ]

        return {
            "status": "success",
            "account_id": str(self.account_id),
            "transactions": formatted_transactions,
        }
