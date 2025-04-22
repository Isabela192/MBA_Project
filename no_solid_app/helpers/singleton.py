from typing import Dict

from sqlmodel import Session


from database.models import Account, AccountType, User, UserType

# Singleton Pattern


class UserCreator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserCreator, cls).__new__(cls)
        return cls._instance

    def create_user(self, user_data: Dict, db: Session) -> User:
        try:
            # Criando novo usuário
            user = User(
                document_id=user_data["document_id"],
                username=user_data["username"],
                email=user_data["email"],
                user_type=UserType.CLIENT,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            account = Account(account_type=AccountType.CHECKING, user_id=user.id)

            db.add(account)
            db.commit()
            db.refresh(account)

            return user
        except Exception as exception:
            db.rollback()
            raise exception


user_creator = UserCreator()
