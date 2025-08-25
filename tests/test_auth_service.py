import pytest
from app.auth_service import AuthService
from app.models import UserCreate, UserLogin
from app.database import reset_db


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


def test_hash_password():
    """Test password hashing"""
    password = "test_password_123"
    hash1 = AuthService.hash_password(password)
    hash2 = AuthService.hash_password(password)

    # Same password should produce same hash
    assert hash1 == hash2
    # Hash should not be the original password
    assert hash1 != password
    # Hash should be consistent length
    assert len(hash1) == 64  # SHA-256 hex digest length


def test_verify_password():
    """Test password verification"""
    password = "correct_password"
    wrong_password = "wrong_password"
    password_hash = AuthService.hash_password(password)

    # Correct password should verify
    assert AuthService.verify_password(password, password_hash)
    # Wrong password should not verify
    assert not AuthService.verify_password(wrong_password, password_hash)


def test_register_user_success(new_db):
    """Test successful user registration"""
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")

    user = AuthService.register_user(user_data)

    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.password_hash != "password123"  # Password should be hashed
    assert user.id is not None


def test_register_user_duplicate_username(new_db):
    """Test registration with duplicate username"""
    user_data1 = UserCreate(username="testuser", email="test1@example.com", password="password123")

    user_data2 = UserCreate(
        username="testuser",  # Same username
        email="test2@example.com",
        password="password456",
    )

    # First registration should succeed
    user1 = AuthService.register_user(user_data1)
    assert user1 is not None

    # Second registration should fail
    user2 = AuthService.register_user(user_data2)
    assert user2 is None


def test_register_user_duplicate_email(new_db):
    """Test registration with duplicate email"""
    user_data1 = UserCreate(username="testuser1", email="test@example.com", password="password123")

    user_data2 = UserCreate(
        username="testuser2",
        email="test@example.com",  # Same email
        password="password456",
    )

    # First registration should succeed
    user1 = AuthService.register_user(user_data1)
    assert user1 is not None

    # Second registration should fail
    user2 = AuthService.register_user(user_data2)
    assert user2 is None


def test_authenticate_user_success(new_db):
    """Test successful user authentication"""
    # First register a user
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    registered_user = AuthService.register_user(user_data)
    assert registered_user is not None

    # Now authenticate
    login_data = UserLogin(username="testuser", password="password123")

    authenticated_user = AuthService.authenticate_user(login_data)
    assert authenticated_user is not None
    assert authenticated_user.username == "testuser"
    assert authenticated_user.id == registered_user.id


def test_authenticate_user_wrong_password(new_db):
    """Test authentication with wrong password"""
    # First register a user
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    AuthService.register_user(user_data)

    # Try to authenticate with wrong password
    login_data = UserLogin(username="testuser", password="wrong_password")

    authenticated_user = AuthService.authenticate_user(login_data)
    assert authenticated_user is None


def test_authenticate_user_nonexistent(new_db):
    """Test authentication with nonexistent username"""
    login_data = UserLogin(username="nonexistent", password="password123")

    authenticated_user = AuthService.authenticate_user(login_data)
    assert authenticated_user is None


def test_authenticate_user_inactive(new_db):
    """Test authentication with inactive user"""
    # Register a user
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    user = AuthService.register_user(user_data)
    assert user is not None

    # Manually deactivate user (in real app this would be done through admin interface)
    from app.database import get_session

    with get_session() as session:
        user.is_active = False
        session.add(user)
        session.commit()

    # Try to authenticate
    login_data = UserLogin(username="testuser", password="password123")

    authenticated_user = AuthService.authenticate_user(login_data)
    assert authenticated_user is None


def test_get_user_by_id(new_db):
    """Test getting user by ID"""
    # Register a user
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    registered_user = AuthService.register_user(user_data)
    assert registered_user is not None
    assert registered_user.id is not None

    # Get user by ID
    retrieved_user = AuthService.get_user_by_id(registered_user.id)
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.id == registered_user.id


def test_get_user_by_id_nonexistent(new_db):
    """Test getting nonexistent user by ID"""
    retrieved_user = AuthService.get_user_by_id(999)
    assert retrieved_user is None


def test_get_user_by_username(new_db):
    """Test getting user by username"""
    # Register a user
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    registered_user = AuthService.register_user(user_data)
    assert registered_user is not None

    # Get user by username
    retrieved_user = AuthService.get_user_by_username("testuser")
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.id == registered_user.id


def test_get_user_by_username_nonexistent(new_db):
    """Test getting nonexistent user by username"""
    retrieved_user = AuthService.get_user_by_username("nonexistent")
    assert retrieved_user is None
