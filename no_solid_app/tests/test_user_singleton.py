from database.models import UserType
from fastapi.testclient import TestClient
from helpers.singleton import UserCreator, user_creator
from sqlmodel import Session


class TestUserCreatorSingleton:
    def test_singleton_instance(self):
        """Test that multiple instantiations return the same instance"""
        instance1 = UserCreator()
        instance2 = UserCreator()

        assert instance1 is instance2
        assert instance1 is user_creator
        assert user_creator is UserCreator()

    def test_create_user(self, db_session: Session):
        """Test that create_user method properly creates a user and account"""
        # Arrange
        user_data = {
            "document_id": "12345678901",
            "username": "testuser",
            "email": "test@example.com",
            "name": "Test User",
        }

        # Act
        user = user_creator.create_user(user_data, db_session)

        # Assert
        assert user is not None
        assert user.document_id == user_data["document_id"]
        assert user.username == user_data["username"]
        assert user.email == user_data["email"]
        assert user.user_type == UserType.CLIENT

        # Check that an account was created
        assert len(user.accounts) == 1
        assert user.accounts[0].user_id == user.id
        assert user.accounts[0].balance == 0


class TestUserEndpoint:
    def test_create_user_endpoint(self, client: TestClient):
        """Test the POST /users/ endpoint"""
        # Arrange
        user_data = {
            "document_id": "12345678903",
            "username": "testuser3",
            "email": "test3@example.com",
            "name": "Test User 3",
        }

        # Act
        response = client.post("/users/", json=user_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == user_data["document_id"]
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["user_type"] == UserType.CLIENT.value
        assert "account_id" in data
        assert data["account_id"] is not None

    def test_create_user_unique_constraint(self, client: TestClient):
        """Test that creating a user with duplicate data returns an error"""
        # Arrange
        user_data = {
            "document_id": "12345678904",
            "username": "testuser4",
            "email": "test4@example.com",
            "name": "Test User 4",
        }

        # First creation should succeed
        response1 = client.post("/users/", json=user_data)
        assert response1.status_code == 201
