from no_solid_app.helpers.account_operations import AccountOperations


def test_singleton_instance():
    """Test that AccountOperations class is a singleton"""
    operations1 = AccountOperations()
    operations2 = AccountOperations()

    # Both instances should be the same object
    assert operations1 is operations2

    # Both instances should have the same memory address
    assert id(operations1) == id(operations2)


# Mock tests - in a real application, you'd use proper mocking of the database session
def test_operations_structure():
    """Test the structure of account operations methods (without actually performing operations)"""
    operations = AccountOperations()

    # Verify methods exist and have the expected signatures
    assert hasattr(operations, "deposit")
    assert callable(operations.deposit)

    assert hasattr(operations, "withdraw")
    assert callable(operations.withdraw)

    assert hasattr(operations, "transfer")
    assert callable(operations.transfer)

    assert hasattr(operations, "get_account_by_uuid")
    assert callable(operations.get_account_by_uuid)
