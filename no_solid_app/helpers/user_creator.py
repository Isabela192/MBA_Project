from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from sqlmodel import Session, select

from database.models import User, UserType
from database.database import engine
from helpers.singleton import Singleton


class UserCreator(metaclass=Singleton):
    """
    Singleton class for user creation that integrates with the database.
    """

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Create a new user in the database.

        Args:
            user_data: Dictionary containing user information
                - document_id: User's document ID
                - username: User's username
                - email: User's email
                - user_type: User type (client or manager)

        Returns:
            The created User object

        Raises:
            HTTPException: If username or email already exists
        """
        with Session(engine) as session:
            # Check if user with the same document_id, email or username already exists
            existing_user = session.exec(
                select(User).where(
                    (User.document_id == user_data["document_id"])
                    | (User.email == user_data["email"])
                    | (User.username == user_data["username"])
                )
            ).first()

            if existing_user:
                if existing_user.document_id == user_data["document_id"]:
                    raise HTTPException(
                        status_code=400, detail="Document ID already registered"
                    )
                elif existing_user.email == user_data["email"]:
                    raise HTTPException(
                        status_code=400, detail="Email already registered"
                    )
                else:
                    raise HTTPException(
                        status_code=400, detail="Username already exists"
                    )

            # Create new user
            user = User(
                account_id=user_data.get("account_id", uuid4()),
                document_id=user_data["document_id"],
                username=user_data["username"],
                email=user_data["email"],
                user_type=UserType(user_data["user_type"]),
                created_at=datetime.now(),
                is_staff=user_data.get("is_staff", False),
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by their ID"""
        with Session(engine) as session:
            return session.get(User, user_id)

    def get_user_by_document_id(self, document_id: str) -> Optional[User]:
        """Get a user by their document ID"""
        with Session(engine) as session:
            return session.exec(
                select(User).where(User.document_id == document_id)
            ).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username"""
        with Session(engine) as session:
            return session.exec(select(User).where(User.username == username)).first()
