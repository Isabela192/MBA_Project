from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from uuid import UUID, uuid4
from sqlmodel import Session, select
from fastapi import HTTPException

from database.models import Account, Transaction, TransactionType, TransactionStatus
from database.database import engine
from helpers.singleton import Singleton


class TransactionFacade(metaclass=Singleton):
    """
    Facade pattern implementation for transaction processing.
    Provides a simplified interface to the complex transaction subsystem.
    Uses Singleton pattern to ensure only one instance exists.
    """

    def process_deposit(self, account_id: UUID, amount: Decimal) -> Dict[str, Any]:
        """
        Process a deposit transaction.

        Args:
            account_id: The UUID of the account
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
                select(Account).where(Account.account_id == account_id)
            ).first()

            if not account:
                raise HTTPException(
                    status_code=404, detail=f"Account with ID {account_id} not found"
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
                "account_id": account.account_id,
                "timestamp": transaction.timestamp,
                "new_balance": float(account.balance),
            }

    def process_withdraw(self, account_id: UUID, amount: Decimal) -> Dict[str, Any]:
        """
        Process a withdrawal transaction.

        Args:
            account_id: The UUID of the account
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
                select(Account).where(Account.account_id == account_id)
            ).first()

            if not account:
                raise HTTPException(
                    status_code=404, detail=f"Account with ID {account_id} not found"
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
                "account_id": account.account_id,
                "timestamp": transaction.timestamp,
                "new_balance": float(account.balance),
            }

    def process_transfer(
        self, source_account: UUID, dest_account: UUID, amount: Decimal
    ) -> Dict[str, Any]:
        """
        Process a transfer transaction between accounts.

        Args:
            source_account: The UUID of the source account
            dest_account: The UUID of the destination account
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
            source = session.exec(
                select(Account).where(Account.account_id == source_account)
            ).first()

            if not source:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source account with ID {source_account} not found",
                )

            # Get the destination account
            destination = session.exec(
                select(Account).where(Account.account_id == dest_account)
            ).first()

            if not destination:
                raise HTTPException(
                    status_code=404,
                    detail=f"Destination account with ID {dest_account} not found",
                )

            # Check if sufficient funds
            if source.balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")

            # Update balances
            source.balance -= amount
            destination.balance += amount
            source.updated_at = datetime.now()
            destination.updated_at = datetime.now()

            # Create a transaction record
            transaction = Transaction(
                transaction_id=uuid4(),
                type=TransactionType.TRANSFER,
                amount=amount,
                status=TransactionStatus.COMPLETED,
                from_account_id=source.id,
                to_account_id=destination.id,
            )

            session.add(transaction)
            session.commit()
            session.refresh(source)
            session.refresh(destination)
            session.refresh(transaction)

            return {
                "transaction_id": transaction.transaction_id,
                "type": transaction.type.value,
                "amount": float(transaction.amount),
                "status": transaction.status.value,
                "source_account": source.account_id,
                "destination_account": destination.account_id,
                "timestamp": transaction.timestamp,
                "source_balance": float(source.balance),
                "destination_balance": float(destination.balance),
            }

    def get_transaction_history(self, account_id: UUID, limit: int = 10) -> list:
        """
        Get transaction history for an account.

        Args:
            account_id: The UUID of the account
            limit: Maximum number of transactions to return (default 10)

        Returns:
            List of transaction dictionaries

        Raises:
            HTTPException: If the account is not found
        """
        with Session(engine) as session:
            # Get the account
            account = session.exec(
                select(Account).where(Account.account_id == account_id)
            ).first()

            if not account:
                raise HTTPException(
                    status_code=404, detail=f"Account with ID {account_id} not found"
                )

            # Get incoming transactions
            incoming = session.exec(
                select(Transaction)
                .where(Transaction.to_account_id == account.id)
                .order_by(Transaction.timestamp.desc())
                .limit(limit)
            ).all()

            # Get outgoing transactions
            outgoing = session.exec(
                select(Transaction)
                .where(Transaction.from_account_id == account.id)
                .order_by(Transaction.timestamp.desc())
                .limit(limit)
            ).all()

            # Combine and sort by timestamp
            all_transactions = incoming + outgoing
            all_transactions.sort(key=lambda x: x.timestamp, reverse=True)

            # Convert to dictionaries
            result = []
            for tx in all_transactions[:limit]:
                tx_dict = {
                    "transaction_id": tx.transaction_id,
                    "type": tx.type.value,
                    "amount": float(tx.amount),
                    "status": tx.status.value,
                    "timestamp": tx.timestamp,
                }

                if tx.from_account_id:
                    tx_dict["from_account_id"] = tx.from_account_id

                if tx.to_account_id:
                    tx_dict["to_account_id"] = tx.to_account_id

                result.append(tx_dict)

            return result
