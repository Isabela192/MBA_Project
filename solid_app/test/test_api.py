from decimal import Decimal

import pytest
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


@pytest.mark.skip(reason="Integration test requires database setup")
def test_update_balance(client, db_session):
    """Test the update_balance endpoint with a test database session."""
    from uuid import uuid4

    from database.models import Account, User

    # Create test user and account directly in the database
    test_user = User(
        document_id="12345678901",
        name="John Doe",
        email="john@test.com",
        username="johndoe_test",
        user_type="client",
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    test_account = Account(
        account_id=uuid4(),
        account_type="checking",
        user_id=test_user.id,
        balance=Decimal("0.0"),
    )
    db_session.add(test_account)
    db_session.commit()
    db_session.refresh(test_account)

    # Update the balance
    amount = 100.50
    response = client.put(
        f"/accounts/{test_account.account_id}/balance", json={"amount": amount}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Balance updated successfully"
    assert float(response.json()["balance"]) == amount
