from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import uuid4
from sqlmodel import Session
from .db_sqlite.database import get_session
<<<<<<< Updated upstream
from .db_sqlite.models import User, UserType
=======
from .db_sqlite.models import User, UserType, Account, AccountType, AccountStatus
>>>>>>> Stashed changes
from fastapi import Depends
from decimal import Decimal


# Factory Method Pattern


class UserFactory(ABC):
    @abstractmethod
    def create_user(
        self, user_data: Dict[str, Any], session: Session = Depends(get_session)
    ) -> User:
        pass

class AccountFactory(ABC):
    @abstractmethod
    def create_account(
        self, account_data: Dict[str, Any], session: Session = Depends(get_session)
    ) -> Account:
        pass

class ClientFactory(UserFactory):
    """
    Factory Method applied to create users on the Database.
    """

    def create_user(
        self, user_data: Dict[str, Any], session: Session = Depends(get_session)
    ) -> User:
        user = User(**user_data, user_type=UserType.CLIENT, is_staff=False)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user


class ManagerFactory(UserFactory):
    """
    Factory Method applied to create manager users on the Database.
    """

    def create_user(
        self, user_data: Dict[str, Any], session: Session = Depends(get_session)
    ) -> User:
        user = User(**user_data, user_type=UserType.MANAGER, is_staff=True)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user

class SavingsAccountFactory(AccountFactory):
    """
    Factory Method applied to create savings accounts on the Database.
    """
    def create_account(
        self, account_data: Dict[str, Any], session: Session = Depends(get_session)
    ) -> Account:
        
        account = Account(
            account_id=uuid4(),
            document_id=account_data["document_id"],
            account_type=AccountType.SAVINGS,
            balance=Decimal("0"),
            status=AccountStatus.ACTIVE
        )
        session.add(account)
        session.commit()
        session.refresh(account)
        return account
    
class CheckingAccountFactory(AccountFactory):
    """
    Factory Method applied to create checking accounts on the Database.
    """
    def create_account(
        self, account_data: Dict[str, Any], session: Session = Depends(get_session)
    ) -> Account:
       
        account = Account(
            account_id=uuid4(),
            document_id=account_data["document_id"],
            account_type=AccountType.CHECKING,
            balance=Decimal("0"),
            status=AccountStatus.ACTIVE
        )
        session.add(account)
        session.commit()
        session.refresh(account)
        return account