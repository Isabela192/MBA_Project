import pytest
from decimal import Decimal
from no_solid_app.helpers.account_factory import (
    CheckingAccountFactory,
    SavingsAccountFactory,
    get_account_factory,
)


def test_singleton_instances():
    """Test that AccountFactory subclasses are singletons"""
    # Get checking account factories
    checking_factory1 = CheckingAccountFactory()
    checking_factory2 = CheckingAccountFactory()

    # Get savings account factories
    savings_factory1 = SavingsAccountFactory()
    savings_factory2 = SavingsAccountFactory()

    # Both checking factories should be the same object
    assert checking_factory1 is checking_factory2
    assert id(checking_factory1) == id(checking_factory2)

    # Both savings factories should be the same object
    assert savings_factory1 is savings_factory2
    assert id(savings_factory1) == id(savings_factory2)

    # But checking and savings factories should be different objects
    assert checking_factory1 is not savings_factory1


def test_factory_method():
    """Test the factory method that returns the appropriate factory"""
    # Get factories using the factory method
    checking_factory = get_account_factory("CHECKING")
    savings_factory = get_account_factory("SAVINGS")

    # Factory method should return singleton instances
    assert checking_factory is CheckingAccountFactory()
    assert savings_factory is SavingsAccountFactory()

    # Test case insensitivity
    assert get_account_factory("checking") is CheckingAccountFactory()
    assert get_account_factory("savings") is SavingsAccountFactory()

    # Test invalid account type
    with pytest.raises(ValueError):
        get_account_factory("INVALID")


def test_account_features():
    """Test the features of different account types"""
    checking_factory = CheckingAccountFactory()
    savings_factory = SavingsAccountFactory()

    # Check checking account features
    checking_features = checking_factory.get_features()
    assert checking_features["overdraft_allowed"] is True
    assert checking_features["minimum_balance"] == Decimal("0")
    assert checking_features["maintenance_fee"] == Decimal("10")

    # Check savings account features
    savings_features = savings_factory.get_features()
    assert savings_features["interest_rate"] == Decimal("0.025")
    assert savings_features["minimum_balance"] == Decimal("100")
    assert savings_features["withdrawal_limit"] == 6


# Mock tests - in a real application, you'd use proper mocking of the database session
def test_account_creation_methods():
    """Test the structure of account creation methods (without actually creating accounts)"""
    checking_factory = CheckingAccountFactory()
    savings_factory = SavingsAccountFactory()

    # Verify methods exist and have the expected signatures
    assert hasattr(checking_factory, "create_account")
    assert callable(checking_factory.create_account)

    assert hasattr(savings_factory, "create_account")
    assert callable(savings_factory.create_account)

    # Verify other methods exist
    assert hasattr(checking_factory, "get_account_by_id")
    assert hasattr(checking_factory, "get_account_by_document_id")
