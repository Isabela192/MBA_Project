from fastapi import HTTPException
from sqlmodel import Session, select
from typing import Dict, Any, List

from database.models import Account, Transaction
from helpers.singleton import Singleton

# Facade Pattern Implementation


class AccountValidator:
    """Subsystem component for account validation"""

    @staticmethod
    def validate_account_exists(account_id: str, db: Session) -> Account:
        """
        Validates that an account exists and returns it.
        Raises HTTPException if account doesn't exist.
        """
        statement = select(Account).where(Account.account_id == account_id)
        account = db.exec(statement).first()
        if not account:
            raise HTTPException(
                status_code=404, detail=f"Account {account_id} not found"
            )
        return account

    @staticmethod
    def validate_sufficient_funds(account: Account, amount: float) -> None:
        """
        Validates that an account has sufficient funds for a transaction.
        Raises HTTPException if funds are insufficient.
        """
        if account.balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds in account {account.account_id}",
            )


class TransactionCreator:
    """Subsystem component for creating transactions"""

    @staticmethod
    def create_deposit_transaction(
        account: Account, amount: float, db: Session
    ) -> Transaction:
        """Creates a deposit transaction"""
        transaction = Transaction(
            account_id=account.id, transaction_type="DEPOSIT", amount=amount
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def create_withdrawal_transaction(
        account: Account, amount: float, db: Session
    ) -> Transaction:
        """Creates a withdrawal transaction"""
        transaction = Transaction(
            account_id=account.id, transaction_type="WITHDRAW", amount=amount
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def create_transfer_transaction(
        source_account: Account, dest_account_id: str, amount: float, db: Session
    ) -> Transaction:
        """Creates a transfer transaction"""
        transaction = Transaction(
            account_id=source_account.id,
            destination_account_id=dest_account_id,
            transaction_type="TRANSFER",
            amount=amount,
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction


class AccountUpdater:
    """Subsystem component for updating account balances"""

    @staticmethod
    def add_funds(account: Account, amount: float, db: Session) -> Account:
        """Adds funds to an account"""
        account.balance += amount
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def subtract_funds(account: Account, amount: float, db: Session) -> Account:
        """Subtracts funds from an account"""
        account.balance -= amount
        db.add(account)
        db.commit()
        db.refresh(account)
        return account


class TransactionFacade(Singleton):
    """
    Facade that provides a unified interface to the subsystems for transaction operations
    """

    def process_deposit(
        self, account_id: str, amount: float, db: Session
    ) -> Dict[str, Any]:
        """Processes a deposit into an account"""
        # Validate account - will raise HTTPException if not found
        account = AccountValidator.validate_account_exists(account_id, db)

        # Update account balance
        account = AccountUpdater.add_funds(account, amount, db)

        # Create transaction record
        transaction = TransactionCreator.create_deposit_transaction(account, amount, db)

        # Return result
        return {
            "transaction_id": transaction.transaction_id,
            "type": "DEPOSIT",
            "account_id": account.account_id,
            "amount": amount,
            "timestamp": transaction.timestamp,
        }

    def process_withdrawal(
        self, account_id: str, amount: float, db: Session
    ) -> Dict[str, Any]:
        """Processes a withdrawal from an account"""
        # Validate account - will raise HTTPException if not found
        account = AccountValidator.validate_account_exists(account_id, db)

        # Validate sufficient funds - will raise HTTPException if insufficient
        AccountValidator.validate_sufficient_funds(account, amount)

        # Update account balance
        account = AccountUpdater.subtract_funds(account, amount, db)

        # Create transaction record
        transaction = TransactionCreator.create_withdrawal_transaction(
            account, amount, db
        )

        # Return result
        return {
            "transaction_id": transaction.transaction_id,
            "type": "WITHDRAW",
            "account_id": account.account_id,
            "amount": amount,
            "timestamp": transaction.timestamp,
        }

    def process_transfer(
        self, source_account_id: str, dest_account_id: str, amount: float, db: Session
    ) -> Dict[str, Any]:
        """Processes a transfer between accounts"""
        # Validate source account - will raise HTTPException if not found
        source_account = AccountValidator.validate_account_exists(source_account_id, db)

        # Validate sufficient funds - will raise HTTPException if insufficient
        AccountValidator.validate_sufficient_funds(source_account, amount)

        # Validate destination account - will raise HTTPException if not found
        dest_account = AccountValidator.validate_account_exists(dest_account_id, db)

        # Update account balances
        source_account = AccountUpdater.subtract_funds(source_account, amount, db)
        dest_account = AccountUpdater.add_funds(dest_account, amount, db)

        # Create transaction record
        transaction = TransactionCreator.create_transfer_transaction(
            source_account, dest_account_id, amount, db
        )

        # Return result
        return {
            "transaction_id": transaction.transaction_id,
            "type": "TRANSFER",
            "account_id": source_account.account_id,
            "destination_account_id": dest_account_id,
            "amount": amount,
            "timestamp": transaction.timestamp,
        }

    def get_account_transactions(
        self, account_id: str, db: Session
    ) -> List[Dict[str, Any]]:
        """Gets all transactions for an account"""
        # Validate account - will raise HTTPException if not found
        account = AccountValidator.validate_account_exists(account_id, db)

        # Get transactions
        statement = select(Transaction).where(Transaction.account_id == account.id)
        transactions = db.exec(statement).all()

        # Format and return transactions
        return [
            {
                "transaction_id": tx.transaction_id,
                "type": tx.transaction_type,
                "account_id": account.account_id,
                "destination_account_id": tx.destination_account_id,
                "amount": tx.amount,
                "timestamp": tx.timestamp,
            }
            for tx in transactions
        ]

    def get_account_balance(self, account_id: str, db: Session) -> Dict[str, Any]:
        """Gets the current balance of an account"""
        # Validate account - will raise HTTPException if not found
        account = AccountValidator.validate_account_exists(account_id, db)

        # Return balance
        return {"account_id": account.account_id, "balance": account.balance}


# Instância única do Facade
transaction_facade = TransactionFacade()
