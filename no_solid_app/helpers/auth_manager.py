from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta
from sqlmodel import Session, select
from fastapi import HTTPException

from database.models import User
from database.database import engine
from helpers.singleton import Singleton


class AuthenticationManager(metaclass=Singleton):
    """
    Authentication manager for user authentication and session management.
    Implements Singleton pattern through metaclass.
    """

    def __init__(self):
        self.active_sessions = {}  # Using in-memory sessions for simplicity

    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register user data in the authentication system.
        This is used in conjunction with the database user creation.

        Args:
            user_data: Dictionary with user information

        Returns:
            Dictionary with user information
        """
        with Session(engine) as session:
            # Check if user exists in database
            user = session.exec(
                select(User).where(User.username == user_data["username"])
            ).first()

            if not user:
                raise HTTPException(
                    status_code=404, detail="User not found in database"
                )

            return {
                "id": user.id,
                "account_id": user.account_id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
            }

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.

        Args:
            username: User's username
            password: User's password (in a real app, this would be hashed)

        Returns:
            User data dictionary if authenticated, None otherwise
        """
        # In a real application, this would verify the password hash
        # For this example, we'll skip password verification and just check if user exists

        with Session(engine) as session:
            user = session.exec(select(User).where(User.username == username)).first()

            if not user:
                return None

            # Generate session ID
            session_id = str(uuid4())
            self.active_sessions[username] = {
                "session_id": session_id,
                "expires": datetime.now() + timedelta(hours=24),
            }

            return {
                "id": user.id,
                "account_id": user.account_id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
                "session_id": session_id,
            }

    def is_authenticated(self, username: str, session_id: str) -> bool:
        """
        Check if a user is authenticated with a valid session.

        Args:
            username: User's username
            session_id: Session ID to verify

        Returns:
            Boolean indicating if the user is authenticated
        """
        session_data = self.active_sessions.get(username)
        if not session_data:
            return False

        if session_data["session_id"] != session_id:
            return False

        if session_data["expires"] < datetime.now():
            # Session expired
            del self.active_sessions[username]
            return False

        return True

    def logout(self, username: str) -> bool:
        """
        Log out a user by invalidating their session.

        Args:
            username: User's username

        Returns:
            Boolean indicating success
        """
        if username in self.active_sessions:
            del self.active_sessions[username]
            return True
        return False
