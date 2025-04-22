from typing import Dict, Optional
from uuid import uuid4

import bcrypt
from fastapi import HTTPException
from sqlmodel import Session, select

from database.models import Account, SessionModel, User

# Singleton Pattern Implementation


class Singleton:
    """
    Base Singleton pattern implementation
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize()
            self._initialized = True

    def _initialize(self):
        pass


class AuthenticationManager(Singleton):
    """
    Singleton implementation for authentication management
    """

    def _initialize(self):
        self.active_sessions = {}
        self.user_creator = None  # Will be set after UserCreator is instantiated

    def set_user_creator(self, user_creator_instance):
        """Set the user creator reference"""
        self.user_creator = user_creator_instance

    def register_user(self, user_data: dict, db: Session) -> User:
        """Register a new user in the system using UserCreator"""
        # Always use UserCreator for user creation to avoid code duplication
        if self.user_creator:
            return self.user_creator.create_user(user_data, db)
        else:
            # This should never happen if singletons are properly connected
            raise RuntimeError("UserCreator not set in AuthenticationManager")

    def authenticate_user(
        self, username: str, password: str, db: Session
    ) -> Optional[Dict]:
        """Autentica um usuário e cria uma sessão"""

        statement = select(User).where(User.username == username)
        user = db.exec(statement).first()
        if not user:
            return None

        if not bcrypt.checkpw(
            password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            return None

        session_id = str(uuid4())
        self.active_sessions[username] = session_id

        new_session = SessionModel(username=username, session_id=session_id)
        db.add(new_session)
        db.commit()

        return {
            "user": {
                "account_id": user.account_id,
                "document_id": user.document_id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
            },
            "session_id": session_id,
        }

    def is_authenticated(
        self, username: str, session_id: str, db: Session = None
    ) -> bool:
        """Verifica se o usuário está autenticado"""

        if self.active_sessions.get(username) == session_id:
            return True

        if db:
            statement = select(SessionModel).where(
                SessionModel.username == username, SessionModel.session_id == session_id
            )
            session = db.exec(statement).first()
            if session:
                self.active_sessions[username] = session_id
                return True

        return False


class UserCreator(Singleton):
    """
    Singleton implementation for user creation operations
    """

    def create_user(self, user_data: dict, db: Session) -> User:
        """Create a new user in the system with password hashing"""
        # Check if user already exists
        statement = select(User).where(User.username == user_data["username"])
        existing_user = db.exec(statement).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Hash the password if provided
        password_hash = ""
        if "password" in user_data and user_data["password"]:
            password_bytes = user_data["password"].encode("utf-8")
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
        elif "password_hash" in user_data:
            password_hash = user_data["password_hash"]

        # Create the new user
        new_user = User(
            document_id=user_data["document_id"],
            username=user_data["username"],
            password_hash=password_hash,
            email=user_data["email"],
            user_type=user_data["user_type"],
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user


class AccountCreator(Singleton):
    """
    Singleton implementation for account creation operations
    """

    def create_account(self, user: User, account_data: dict, db: Session) -> Account:
        """Create a new account for a user"""
        # Create new account
        account = Account(
            document_id=user.document_id,
            account_type=account_data["account_type"],
            balance=0.0,
            status="ACTIVE",
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        # Link account to user
        account.users.append(user)
        db.commit()
        db.refresh(account)

        return account

    def get_user_accounts(self, user_id: int, db: Session) -> list:
        """Get all accounts for a user"""
        statement = select(User).where(User.id == user_id)
        user = db.exec(statement).first()

        if not user:
            return []

        return user.accounts


# Create singleton instances
auth_manager = AuthenticationManager()
user_creator = UserCreator()
account_creator = AccountCreator()

# Connect singletons where they need to collaborate
auth_manager.set_user_creator(user_creator)
