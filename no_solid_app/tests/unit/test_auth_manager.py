from helpers.auth_manager import AuthenticationManager


def test_singleton_instance():
    """Test that AuthenticationManager class is a singleton"""
    auth_manager1 = AuthenticationManager()
    auth_manager2 = AuthenticationManager()

    # Both instances should be the same object
    assert auth_manager1 is auth_manager2

    # Both instances should have the same memory address
    assert id(auth_manager1) == id(auth_manager2)


# Mock tests - in a real application, you'd use proper mocking of the database session
def test_auth_manager_structure():
    """Test the structure of auth manager methods (without actually performing operations)"""
    auth_manager = AuthenticationManager()

    # Verify methods exist and have the expected signatures
    assert hasattr(auth_manager, "register_user")
    assert callable(auth_manager.register_user)

    assert hasattr(auth_manager, "authenticate_user")
    assert callable(auth_manager.authenticate_user)

    assert hasattr(auth_manager, "is_authenticated")
    assert callable(auth_manager.is_authenticated)

    assert hasattr(auth_manager, "logout")
    assert callable(auth_manager.logout)
