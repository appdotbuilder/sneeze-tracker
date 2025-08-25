from typing import Optional
import hashlib
from sqlmodel import select
from app.database import get_session
from app.models import User, UserCreate, UserLogin


class AuthService:
    """Service for user authentication operations"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

    @staticmethod
    def register_user(user_data: UserCreate) -> Optional[User]:
        """Register a new user"""
        with get_session() as session:
            # Check if username or email already exists
            existing_user = session.exec(
                select(User).where((User.username == user_data.username) | (User.email == user_data.email))
            ).first()

            if existing_user:
                return None  # User already exists

            # Create new user
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=AuthService.hash_password(user_data.password),
            )

            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user

    @staticmethod
    def authenticate_user(login_data: UserLogin) -> Optional[User]:
        """Authenticate user with username and password"""
        with get_session() as session:
            user = session.exec(select(User).where(User.username == login_data.username)).first()

            if user is None:
                return None

            if not user.is_active:
                return None

            if not AuthService.verify_password(login_data.password, user.password_hash):
                return None

            return user

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        with get_session() as session:
            return session.get(User, user_id)

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        with get_session() as session:
            return session.exec(select(User).where(User.username == username)).first()
