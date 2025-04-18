from decimal import Decimal
from fastapi import status
from sqlmodel import select
from database.models import User, Account, UserType, AccountType


class TestUserEndpoints:
    def test_create_client_user_success(self, client, db_session):
        """Test creating a client user successfully."""
        # Arrange
        # FastAPI expects user_data and account_data as separate objects
        user_data = {
            "document_id": "12345678999",  # Use unique document_id
            "name": "Test User",
            "email": "test_client@example.com",  # Use unique email
            "username": "testuser",
        }

        account_data = {"account_type": "checking", "password": "secure_password123"}

        # Act
        response = client.post(
            "/users/",
            params={"user_type": "client"},
            json={"user_data": user_data, "account_data": account_data},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "account" in data
        assert "account_id" in data["account"]
        assert "account_type" in data["account"]
        assert "balance" in data["account"]
        assert data["username"] == "testuser"
        assert data["account"]["account_type"] == "checking"
        assert float(data["account"]["balance"]) == 0

        # Verify user was created in the database
        db_user = db_session.exec(
            select(User).where(User.email == "test_client@example.com")
        ).first()
        assert db_user is not None
        assert db_user.user_type == UserType.CLIENT

        # Verify account was created in the database
        db_account = db_session.exec(
            select(Account).where(Account.user_id == db_user.id)
        ).first()
        assert db_account is not None
        assert db_account.account_type == AccountType.CHECKING
        assert db_account.balance == Decimal("0")
        assert db_account.status == "active"

    def test_create_manager_user_success(self, client, db_session):
        """Test creating a manager user successfully."""
        # Arrange
        user_data = {
            "document_id": "98765432199",  # Use unique document_id
            "name": "Manager User",
            "email": "manager_test@example.com",  # Use unique email
            "username": "manageruser",
        }

        account_data = {"account_type": "checking", "password": "manager_password456"}

        # Act
        response = client.post(
            "/users/",
            params={"user_type": "manager"},
            json={"user_data": user_data, "account_data": account_data},
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "account" in data
        assert "account_id" in data["account"]
        assert data["username"] == "manageruser"
        assert data["account"]["account_type"] == "checking"

        # Verify user was created in the database
        db_user = db_session.exec(
            select(User).where(User.email == "manager_test@example.com")
        ).first()
        assert db_user is not None
        assert db_user.user_type == UserType.MANAGER

    def test_create_user_invalid_user_type(self, client):
        """Test creating a user with invalid user type."""
        # Arrange
        user_data = {
            "document_id": "12345678000",  # Use unique document_id
            "name": "Test User",
            "email": "test_invalid@example.com",  # Use unique email
            "username": "testuser",
        }

        account_data = {"account_type": "checking", "password": "secure_password123"}

        # Act
        response = client.post(
            "/users/",
            params={"user_type": "invalid_type"},
            json={"user_data": user_data, "account_data": account_data},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid user type"
