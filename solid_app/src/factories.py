from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlmodel import Session
from db_sqlite.models import User, UserType

# Factory Method Pattern


class UserFactory(ABC):
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any], session: Session) -> User:
        pass


class ClientFactory(UserFactory):
    """
    Factory Method applied to create users on the Database.
    """

    def create_user(self, user_data: Dict[str, Any], session: Session) -> User:
        user = User(**user_data, user_type=UserType.CLIENT, is_staff=False)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user


class ManagerFactory(UserFactory):
    """
    Factory Method applied to create manager users on the Database.
    """

    def create_user(self, user_data: Dict[str, Any], session: Session) -> User:
        user = User(**user_data, user_type=UserType.MANAGER, is_staff=True)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user
