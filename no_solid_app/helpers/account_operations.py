from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from uuid import UUID, uuid4
from sqlmodel import Session, select
from fastapi import HTTPException

from database.models import Account, Transaction, TransactionType, TransactionStatus
from database.database import engine
from helpers.singleton import Singleton


class AccountOperations(metaclass=Singleton):
    """
    Singleton class for account operations (deposits, withdrawals, transfers).
    Integrates with the database.
    """

    def get_account_by_uuid(self, account_uuid: UUID) -> Account:
        """
        Get an account by its UUID.

        Args:
            account_uuid: The UUID of the account

        Returns:
            The Account object

        Raises:
            HTTPException: If the account is not found
        """
        with Session(engine) as session:
            account = session.exec(
                select(Account).where(Account.account_id == account_uuid)
            ).first()

            if not account:
                raise HTTPException(
                    status_code=404, detail=f"Account with ID {account_uuid} not found"
                )

            return account

    def deposit(self, account_uuid: UUID, amount: Decimal) -> Dict[str, Any]:
        """
        Deposit money into an account.

        Args:
            account_uuid: The UUID of the account
            amount: The amount to deposit

        Returns:
            Dictionary with transaction details

        Raises:
            HTTPException: If the account is not found or amount is invalid
        """
        if amount <= Decimal("0"):
            raise HTTPException(
                status_code=400, detail="Deposit amount must be positive"
            )

        with Session(engine) as session:
            # Get the account
            account = session.exec(
                select(Account).where(Account.account_id == account_uuid)
            ).first()

            if not account:
                raise HTTPException(
                    status_code=404, detail=f"Account with ID {account_uuid} not found"
                )

            # Update the balance
            account.balance += amount
            account.updated_at = datetime.now()

            # Create a transaction record
            transaction = Transaction(
                transaction_id=uuid4(),
                type=TransactionType.DEPOSIT,
                amount=amount,
                status=TransactionStatus.COMPLETED,
                to_account_id=account.id,
            )

            session.add(transaction)
            session.commit()
            session.refresh(account)
            session.refresh(transaction)

            return {
                "transaction_id": transaction.transaction_id,
                "type": transaction.type.value,
                "amount": float(transaction.amount),
                "status": transaction.status.value,
                "timestamp": transaction.timestamp,
                "to_account_id": transaction.to_account_id,
                "new_balance": float(account.balance),
            }

    def withdraw(self, account_uuid: UUID, amount: Decimal) -> Dict[str, Any]:
        """
        Withdraw money from an account.

        Args:
            account_uuid: The UUID of the account
            amount: The amount to withdraw

        Returns:
            Dictionary with transaction details

        Raises:
            HTTPException: If the account is not found, amount is invalid, or insufficient funds
        """
        if amount <= Decimal("0"):
            raise HTTPException(
                status_code=400, detail="Withdrawal amount must be positive"
            )

        with Session(engine) as session:
            # Get the account
            account = session.exec(
                select(Account).where(Account.account_id == account_uuid)
            ).first()

            if not account:
                raise HTTPException(
                    status_code=404, detail=f"Account with ID {account_uuid} not found"
                )

            # Check if sufficient funds
            if account.balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")

            # Update the balance
            account.balance -= amount
            account.updated_at = datetime.now()

            # Create a transaction record
            transaction = Transaction(
                transaction_id=uuid4(),
                type=TransactionType.WITHDRAW,
                amount=amount,
                status=TransactionStatus.COMPLETED,
                from_account_id=account.id,
            )

            session.add(transaction)
            session.commit()
            session.refresh(account)
            session.refresh(transaction)

            return {
                "transaction_id": transaction.transaction_id,
                "type": transaction.type.value,
                "amount": float(transaction.amount),
                "status": transaction.status.value,
                "timestamp": transaction.timestamp,
                "from_account_id": transaction.from_account_id,
                "new_balance": float(account.balance),
            }

    def transfer(
        self, from_account_uuid: UUID, to_account_uuid: UUID, amount: Decimal
    ) -> Dict[str, Any]:
        """
        Transfer money between accounts.

        Args:
            from_account_uuid: The UUID of the source account
            to_account_uuid: The UUID of the destination account
            amount: The amount to transfer

        Returns:
            Dictionary with transaction details

        Raises:
            HTTPException: If either account is not found, amount is invalid, or insufficient funds
        """
        if amount <= Decimal("0"):
            raise HTTPException(
                status_code=400, detail="Transfer amount must be positive"
            )

        with Session(engine) as session:
            # Get the source account
            from_account = session.exec(
                select(Account).where(Account.account_id == from_account_uuid)
            ).first()

            if not from_account:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source account with ID {from_account_uuid} not found",
                )

            # Get the destination account
            to_account = session.exec(
                select(Account).where(Account.account_id == to_account_uuid)
            ).first()

            if not to_account:
                raise HTTPException(
                    status_code=404,
                    detail=f"Destination account with ID {to_account_uuid} not found",
                )

            # Check if sufficient funds
            if from_account.balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")

            # Update balances
            from_account.balance -= amount
            to_account.balance += amount
            from_account.updated_at = datetime.now()
            to_account.updated_at = datetime.now()

            # Create a transaction record
            transaction = Transaction(
                transaction_id=uuid4(),
                type=TransactionType.TRANSFER,
                amount=amount,
                status=TransactionStatus.COMPLETED,
                from_account_id=from_account.id,
                to_account_id=to_account.id,
            )

            session.add(transaction)
            session.commit()
            session.refresh(from_account)
            session.refresh(to_account)
            session.refresh(transaction)

            return {
                "transaction_id": transaction.transaction_id,
                "type": transaction.type.value,
                "amount": float(transaction.amount),
                "status": transaction.status.value,
                "timestamp": transaction.timestamp,
                "from_account_id": transaction.from_account_id,
                "to_account_id": transaction.to_account_id,
                "source_balance": float(from_account.balance),
                "destination_balance": float(to_account.balance),
            }
