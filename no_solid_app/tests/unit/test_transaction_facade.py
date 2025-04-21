from helpers.transaction_facade import TransactionFacade


def test_singleton_instance():
    """Test that TransactionFacade class is a singleton"""
    facade1 = TransactionFacade()
    facade2 = TransactionFacade()

    # Both instances should be the same object
    assert facade1 is facade2

    # Both instances should have the same memory address
    assert id(facade1) == id(facade2)


# Mock tests - in a real application, you'd use proper mocking of the database session
def test_facade_structure():
    """Test the structure of transaction facade methods (without actually performing operations)"""
    facade = TransactionFacade()

    # Verify methods exist and have the expected signatures
    assert hasattr(facade, "process_deposit")
    assert callable(facade.process_deposit)

    assert hasattr(facade, "process_withdraw")
    assert callable(facade.process_withdraw)

    assert hasattr(facade, "process_transfer")
    assert callable(facade.process_transfer)

    assert hasattr(facade, "get_transaction_history")
    assert callable(facade.get_transaction_history)
