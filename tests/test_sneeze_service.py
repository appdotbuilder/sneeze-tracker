import pytest
from datetime import datetime
from app.sneeze_service import SneezeService
from app.auth_service import AuthService
from app.models import UserCreate, SneezeCreate, SneezeUpdate, SeverityLevel
from app.database import reset_db


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


@pytest.fixture()
def test_user(new_db):
    """Create a test user"""
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    user = AuthService.register_user(user_data)
    assert user is not None
    return user


def test_create_sneeze(test_user):
    """Test creating a sneeze"""
    sneeze_data = SneezeCreate(severity=SeverityLevel.MODERATE, notes="Test sneeze")

    sneeze = SneezeService.create_sneeze(test_user.id, sneeze_data)

    assert sneeze is not None
    assert sneeze.user_id == test_user.id
    assert sneeze.severity == SeverityLevel.MODERATE
    assert sneeze.notes == "Test sneeze"
    assert sneeze.id is not None
    assert sneeze.timestamp is not None
    assert sneeze.created_at is not None


def test_create_sneeze_empty_notes(test_user):
    """Test creating a sneeze with empty notes"""
    sneeze_data = SneezeCreate(severity=SeverityLevel.LIGHT, notes="")

    sneeze = SneezeService.create_sneeze(test_user.id, sneeze_data)

    assert sneeze is not None
    assert sneeze.notes == ""


def test_get_user_sneezes_empty(test_user):
    """Test getting sneezes when user has none"""
    sneezes = SneezeService.get_user_sneezes(test_user.id)
    assert sneezes == []


def test_get_user_sneezes_with_data(test_user):
    """Test getting sneezes when user has some"""
    # Create multiple sneezes
    sneeze_data1 = SneezeCreate(severity=SeverityLevel.LIGHT, notes="First sneeze")
    sneeze_data2 = SneezeCreate(severity=SeverityLevel.HEAVY, notes="Second sneeze")

    sneeze1 = SneezeService.create_sneeze(test_user.id, sneeze_data1)
    sneeze2 = SneezeService.create_sneeze(test_user.id, sneeze_data2)

    assert sneeze1 is not None and sneeze1.id is not None
    assert sneeze2 is not None and sneeze2.id is not None

    sneezes = SneezeService.get_user_sneezes(test_user.id)

    assert len(sneezes) == 2
    # Should be ordered by timestamp descending (newest first)
    assert sneezes[0].id == sneeze2.id
    assert sneezes[1].id == sneeze1.id


def test_get_user_sneezes_with_limit(test_user):
    """Test getting sneezes with limit"""
    # Create 3 sneezes
    for i in range(3):
        sneeze_data = SneezeCreate(severity=SeverityLevel.MODERATE, notes=f"Sneeze {i}")
        SneezeService.create_sneeze(test_user.id, sneeze_data)

    # Get only 2
    sneezes = SneezeService.get_user_sneezes(test_user.id, limit=2)
    assert len(sneezes) == 2


def test_get_user_sneezes_different_users(new_db):
    """Test that users only see their own sneezes"""
    # Create two users
    user1_data = UserCreate(username="user1", email="user1@example.com", password="password123")
    user2_data = UserCreate(username="user2", email="user2@example.com", password="password123")

    user1 = AuthService.register_user(user1_data)
    user2 = AuthService.register_user(user2_data)

    assert user1 is not None and user1.id is not None
    assert user2 is not None and user2.id is not None

    # Create sneezes for each user
    sneeze1_data = SneezeCreate(severity=SeverityLevel.LIGHT, notes="User 1 sneeze")
    sneeze2_data = SneezeCreate(severity=SeverityLevel.HEAVY, notes="User 2 sneeze")

    SneezeService.create_sneeze(user1.id, sneeze1_data)
    SneezeService.create_sneeze(user2.id, sneeze2_data)

    # Each user should only see their own sneezes
    user1_sneezes = SneezeService.get_user_sneezes(user1.id)
    user2_sneezes = SneezeService.get_user_sneezes(user2.id)

    assert len(user1_sneezes) == 1
    assert len(user2_sneezes) == 1
    assert user1_sneezes[0].notes == "User 1 sneeze"
    assert user2_sneezes[0].notes == "User 2 sneeze"


def test_get_sneezes_by_month(test_user):
    """Test getting sneezes filtered by month"""
    # Create sneezes with specific timestamps (we'll manually set them)
    sneeze_data1 = SneezeCreate(severity=SeverityLevel.LIGHT, notes="January sneeze")
    sneeze_data2 = SneezeCreate(severity=SeverityLevel.MODERATE, notes="February sneeze")

    sneeze1 = SneezeService.create_sneeze(test_user.id, sneeze_data1)
    sneeze2 = SneezeService.create_sneeze(test_user.id, sneeze_data2)

    assert sneeze1 is not None and sneeze2 is not None

    # Manually update timestamps to specific months
    from app.database import get_session

    with get_session() as session:
        sneeze1.timestamp = datetime(2024, 1, 15, 10, 0, 0)
        sneeze2.timestamp = datetime(2024, 2, 20, 14, 30, 0)
        session.add(sneeze1)
        session.add(sneeze2)
        session.commit()

    # Test filtering
    jan_sneezes = SneezeService.get_sneezes_by_month(test_user.id, 2024, 1)
    feb_sneezes = SneezeService.get_sneezes_by_month(test_user.id, 2024, 2)
    mar_sneezes = SneezeService.get_sneezes_by_month(test_user.id, 2024, 3)

    assert len(jan_sneezes) == 1
    assert len(feb_sneezes) == 1
    assert len(mar_sneezes) == 0

    assert jan_sneezes[0].notes == "January sneeze"
    assert feb_sneezes[0].notes == "February sneeze"


def test_get_sneezes_by_month_december(test_user):
    """Test getting sneezes for December (edge case for year boundary)"""
    sneeze_data = SneezeCreate(severity=SeverityLevel.EXPLOSIVE, notes="December sneeze")
    sneeze = SneezeService.create_sneeze(test_user.id, sneeze_data)

    assert sneeze is not None

    # Set timestamp to December
    from app.database import get_session

    with get_session() as session:
        sneeze.timestamp = datetime(2024, 12, 25, 12, 0, 0)
        session.add(sneeze)
        session.commit()

    dec_sneezes = SneezeService.get_sneezes_by_month(test_user.id, 2024, 12)
    jan_sneezes = SneezeService.get_sneezes_by_month(test_user.id, 2025, 1)

    assert len(dec_sneezes) == 1
    assert len(jan_sneezes) == 0


def test_get_sneeze_by_id(test_user):
    """Test getting a specific sneeze by ID"""
    sneeze_data = SneezeCreate(severity=SeverityLevel.HEAVY, notes="Test sneeze")
    created_sneeze = SneezeService.create_sneeze(test_user.id, sneeze_data)

    assert created_sneeze is not None and created_sneeze.id is not None

    retrieved_sneeze = SneezeService.get_sneeze_by_id(created_sneeze.id, test_user.id)

    assert retrieved_sneeze is not None
    assert retrieved_sneeze.id == created_sneeze.id
    assert retrieved_sneeze.notes == "Test sneeze"


def test_get_sneeze_by_id_wrong_user(new_db):
    """Test getting sneeze with wrong user ID"""
    # Create two users
    user1_data = UserCreate(username="user1", email="user1@example.com", password="password123")
    user2_data = UserCreate(username="user2", email="user2@example.com", password="password123")

    user1 = AuthService.register_user(user1_data)
    user2 = AuthService.register_user(user2_data)

    assert user1 is not None and user1.id is not None
    assert user2 is not None and user2.id is not None

    # Create sneeze for user1
    sneeze_data = SneezeCreate(severity=SeverityLevel.MODERATE, notes="User 1 sneeze")
    sneeze = SneezeService.create_sneeze(user1.id, sneeze_data)

    assert sneeze is not None and sneeze.id is not None

    # Try to get it as user2
    retrieved_sneeze = SneezeService.get_sneeze_by_id(sneeze.id, user2.id)
    assert retrieved_sneeze is None


def test_update_sneeze(test_user):
    """Test updating a sneeze"""
    # Create initial sneeze
    sneeze_data = SneezeCreate(severity=SeverityLevel.LIGHT, notes="Original note")
    sneeze = SneezeService.create_sneeze(test_user.id, sneeze_data)

    assert sneeze is not None and sneeze.id is not None

    # Update it
    update_data = SneezeUpdate(severity=SeverityLevel.EXPLOSIVE, notes="Updated note")
    updated_sneeze = SneezeService.update_sneeze(sneeze.id, test_user.id, update_data)

    assert updated_sneeze is not None
    assert updated_sneeze.severity == SeverityLevel.EXPLOSIVE
    assert updated_sneeze.notes == "Updated note"
    assert updated_sneeze.id == sneeze.id


def test_update_sneeze_partial(test_user):
    """Test partial update of sneeze"""
    # Create initial sneeze
    sneeze_data = SneezeCreate(severity=SeverityLevel.MODERATE, notes="Original note")
    sneeze = SneezeService.create_sneeze(test_user.id, sneeze_data)

    assert sneeze is not None and sneeze.id is not None

    # Update only severity
    update_data = SneezeUpdate(severity=SeverityLevel.HEAVY)
    updated_sneeze = SneezeService.update_sneeze(sneeze.id, test_user.id, update_data)

    assert updated_sneeze is not None
    assert updated_sneeze.severity == SeverityLevel.HEAVY
    assert updated_sneeze.notes == "Original note"  # Should remain unchanged


def test_update_sneeze_nonexistent(test_user):
    """Test updating nonexistent sneeze"""
    update_data = SneezeUpdate(severity=SeverityLevel.HEAVY)
    updated_sneeze = SneezeService.update_sneeze(999, test_user.id, update_data)
    assert updated_sneeze is None


def test_delete_sneeze(test_user):
    """Test deleting a sneeze"""
    # Create sneeze
    sneeze_data = SneezeCreate(severity=SeverityLevel.MODERATE, notes="To be deleted")
    sneeze = SneezeService.create_sneeze(test_user.id, sneeze_data)

    assert sneeze is not None and sneeze.id is not None

    # Verify it exists
    assert SneezeService.get_sneeze_by_id(sneeze.id, test_user.id) is not None

    # Delete it
    result = SneezeService.delete_sneeze(sneeze.id, test_user.id)
    assert result is True

    # Verify it's gone
    assert SneezeService.get_sneeze_by_id(sneeze.id, test_user.id) is None


def test_delete_sneeze_nonexistent(test_user):
    """Test deleting nonexistent sneeze"""
    result = SneezeService.delete_sneeze(999, test_user.id)
    assert result is False


def test_get_sneeze_stats_empty(test_user):
    """Test getting stats when user has no sneezes"""
    stats = SneezeService.get_sneeze_stats(test_user.id)

    assert stats["total_count"] == 0
    assert stats["today_count"] == 0
    assert stats["this_month_count"] == 0
    assert all(count == 0 for count in stats["severity_counts"].values())


def test_get_sneeze_stats_with_data(test_user):
    """Test getting stats with actual data"""
    # Create sneezes with different severities

    sneeze_data1 = SneezeCreate(severity=SeverityLevel.LIGHT, notes="Light sneeze")
    sneeze_data2 = SneezeCreate(severity=SeverityLevel.LIGHT, notes="Another light")
    sneeze_data3 = SneezeCreate(severity=SeverityLevel.HEAVY, notes="Heavy sneeze")

    SneezeService.create_sneeze(test_user.id, sneeze_data1)
    SneezeService.create_sneeze(test_user.id, sneeze_data2)
    SneezeService.create_sneeze(test_user.id, sneeze_data3)

    stats = SneezeService.get_sneeze_stats(test_user.id)

    assert stats["total_count"] == 3
    assert stats["severity_counts"][SeverityLevel.LIGHT] == 2
    assert stats["severity_counts"][SeverityLevel.HEAVY] == 1
    assert stats["severity_counts"][SeverityLevel.MODERATE] == 0
    assert stats["severity_counts"][SeverityLevel.EXPLOSIVE] == 0

    # Since we just created them, they should count for today and this month
    assert stats["today_count"] == 3
    assert stats["this_month_count"] == 3
