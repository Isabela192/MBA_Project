from no_solid_app.helpers.user_creator import UserCreator


def test_singleton_instance():
    """Test that UserCreator class is a singleton"""
    user_creator1 = UserCreator()
    user_creator2 = UserCreator()

    # Both instances should be the same object
    assert user_creator1 is user_creator2

    # Both instances should have the same memory address
    assert id(user_creator1) == id(user_creator2)


# Mock tests - in a real application, you'd use proper mocking of the database session
def test_create_user_structure():
    """Test the structure of create_user method (without actually creating users)"""
    user_creator = UserCreator()

    # Verify the method exists and has the expected signature
    assert hasattr(user_creator, "create_user")
    assert callable(user_creator.create_user)

    # Verify other methods exist
    assert hasattr(user_creator, "get_user_by_id")
    assert hasattr(user_creator, "get_user_by_document_id")
    assert hasattr(user_creator, "get_user_by_username")
