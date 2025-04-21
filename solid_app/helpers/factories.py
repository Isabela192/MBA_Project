from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlmodel import Session
from database.database import get_session
from database.models import User, UserType, Account, AccountStatus
from fastapi import Depends
from decimal import Decimal


# Factory Method Pattern


class UserFactory(ABC):
    @abstractmethod
    def create_user(
        self, user_data: Dict[str, Any], session: Session = Depends(get_session)
    ) -> User:
        pass

    @abstractmethod
    def create_user_account(
        self,
        user: User,
        account_data: Dict[str, Any],
        session: Session = Depends(get_session),
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

    def create_user_account(
        self,
        user: User,
        account_data: Dict[str, Any],
        session: Session = Depends(get_session),
    ) -> Account:
        account = Account(
            **account_data,
            owner=user,
            balance=Decimal("0"),
            status=AccountStatus.ACTIVE,
        )

        session.add(account)
        session.commit()
        session.refresh(account)
        return account


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

    def create_user_account(
        self,
        user: User,
        account_data: Dict[str, Any],
        session: Session = Depends(get_session),
    ) -> Account:
        account = Account(
            **account_data,
            owner=user,
            balance=Decimal("0"),
            status=AccountStatus.ACTIVE,
        )

        session.add(account)
        session.commit()
        session.refresh(account)
        return account
