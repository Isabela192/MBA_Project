from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import uuid4, UUID
from datetime import datetime
from sqlmodel import Session, select
from .db_sqlite.models import Account, Transaction, TransactionType, TransactionStatus
from typing import Dict, Any

# Command Pattern


class Command(ABC):
    @abstractmethod
    def execute(self, session: Session) -> Dict[str, Any]:
        pass


class DepositComand(Command):
    def __init__(self, account_id: str, amount: Decimal):
        # Convert string to UUID if it's not already a UUID
        try:
            self.account_id = (
                UUID(account_id) if isinstance(account_id, str) else account_id
            )
        except ValueError:
            # For tests with non-UUID strings, just use the string as-is
            self.account_id = account_id
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
        # Use model_dump instead of dict (deprecated)
        return account.model_dump()


class TransferCommand(Command):
    def __init__(self, from_account_id: str, to_account_id: str, amount: Decimal):
        # Convert string to UUID if it's not already a UUID
        try:
            self.from_account_id = (
                UUID(from_account_id)
                if isinstance(from_account_id, str)
                else from_account_id
            )
        except ValueError:
            # For tests with non-UUID strings, just use the string as-is
            self.from_account_id = from_account_id

        try:
            self.to_account_id = (
                UUID(to_account_id) if isinstance(to_account_id, str) else to_account_id
            )
        except ValueError:
            # For tests with non-UUID strings, just use the string as-is
            self.to_account_id = to_account_id

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
        # Convert string to UUID if it's not already a UUID
        try:
            self.account_id = (
                UUID(account_id) if isinstance(account_id, str) else account_id
            )
        except ValueError:
            # For tests with non-UUID strings, just use the string as-is
            self.account_id = account_id
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
        # Use model_dump instead of dict (deprecated)
        return account.model_dump()
