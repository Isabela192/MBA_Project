from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import uuid4
from sqlmodel import Session, select

from database.models import Account, AccountType, AccountStatus, User
from database.database import engine
from helpers.singleton import Singleton


class AccountFactory(ABC, metaclass=Singleton):
    """
    Abstract factory for creating different types of accounts.
    Implements Singleton pattern through metaclass.
    """

    @abstractmethod
    def create_account(
        self, user_id: int, document_id: str, initial_balance: Decimal = Decimal("0")
    ) -> Account:
        """Create a new account for a user"""
        pass

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """Get an account by its ID"""
        with Session(engine) as session:
            return session.get(Account, account_id)

    def get_account_by_document_id(self, document_id: str) -> Optional[Account]:
        """Get an account by its document ID"""
        with Session(engine) as session:
            return session.exec(
                select(Account).where(Account.document_id == document_id)
            ).first()


class CheckingAccountFactory(AccountFactory):
    """Factory for creating checking accounts"""

    def create_account(
        self, user_id: int, document_id: str, initial_balance: Decimal = Decimal("0")
    ) -> Account:
        """
        Create a new checking account.

        Args:
            user_id: The ID of the account owner
            document_id: The document ID for the account
            initial_balance: Initial account balance (default 0)

        Returns:
            The created Account object
        """
        with Session(engine) as session:
            # Check if user exists
            user = session.get(User, user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Check if account with the same document_id already exists
            existing_account = session.exec(
                select(Account).where(Account.document_id == document_id)
            ).first()

            if existing_account:
                raise ValueError("An account with this document ID already exists")

            # Create new checking account
            account = Account(
                account_id=uuid4(),
                document_id=document_id,
                balance=initial_balance,
                account_type=AccountType.CHECKING,
                status=AccountStatus.ACTIVE,
                user_id=user_id,
                created_at=datetime.now(),
            )

            session.add(account)
            session.commit()
            session.refresh(account)

            return account

    def get_features(self) -> Dict[str, Any]:
        """Get the features of a checking account"""
        return {
            "overdraft_allowed": True,
            "minimum_balance": Decimal("0"),
            "maintenance_fee": Decimal("10"),
        }


class SavingsAccountFactory(AccountFactory):
    """Factory for creating savings accounts"""

    def create_account(
        self, user_id: int, document_id: str, initial_balance: Decimal = Decimal("0")
    ) -> Account:
        """
        Create a new savings account.

        Args:
            user_id: The ID of the account owner
            document_id: The document ID for the account
            initial_balance: Initial account balance (default 0)

        Returns:
            The created Account object
        """
        if initial_balance < Decimal("100"):
            raise ValueError(
                "Savings accounts require a minimum initial balance of 100"
            )

        with Session(engine) as session:
            # Check if user exists
            user = session.get(User, user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Check if account with the same document_id already exists
            existing_account = session.exec(
                select(Account).where(Account.document_id == document_id)
            ).first()

            if existing_account:
                raise ValueError("An account with this document ID already exists")

            # Create new savings account
            account = Account(
                account_id=uuid4(),
                document_id=document_id,
                balance=initial_balance,
                account_type=AccountType.SAVINGS,
                status=AccountStatus.ACTIVE,
                user_id=user_id,
                created_at=datetime.now(),
            )

            session.add(account)
            session.commit()
            session.refresh(account)

            return account

    def get_features(self) -> Dict[str, Any]:
        """Get the features of a savings account"""
        return {
            "interest_rate": Decimal("0.025"),
            "minimum_balance": Decimal("100"),
            "withdrawal_limit": 6,
        }


def get_account_factory(account_type: str) -> AccountFactory:
    """
    Factory method to get the appropriate account factory.

    Args:
        account_type: The type of account ("CHECKING" or "SAVINGS")

    Returns:
        An instance of the appropriate account factory

    Raises:
        ValueError: If an invalid account type is provided
    """
    if account_type.upper() == "CHECKING":
        return CheckingAccountFactory()
    elif account_type.upper() == "SAVINGS":
        return SavingsAccountFactory()
    else:
        raise ValueError(
            f"Invalid account type: {account_type}. Must be 'CHECKING' or 'SAVINGS'"
        )
