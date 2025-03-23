from abc import ABC, abstractmethod
from models import User, UserType
from sqlmodel import Session
from typing import Dict, Any


class UserFactory(ABC):
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any], session: Session) -> User:
        pass


class ClientFactory(UserFactory):
    def create_user(self, user_data: Dict[str, Any], session: Session) -> User:
        user = User(**user_data, user_type=UserType.CLIENT, is_staff=False)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user


class ManagerFactory(UserFactory):
    def create_user(self, user_data: Dict[str, Any], session: Session) -> User:
        user = User(**user_data, user_type=UserType.MANAGER, is_staff=True)

        session.add(user)
        session.commit()
        session.refresh(user)
        return user
