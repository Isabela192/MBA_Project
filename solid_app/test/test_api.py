from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Bank API with SQLModel using SOLID Principles"
    }


def test_user_get():
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
