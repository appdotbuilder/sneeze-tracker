from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels for sneezes"""

    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    EXPLOSIVE = "explosive"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password_hash: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to sneezes
    sneezes: List["Sneeze"] = Relationship(back_populates="user")


class Sneeze(SQLModel, table=True):
    __tablename__ = "sneezes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    severity: SeverityLevel = Field(index=True)
    notes: str = Field(default="", max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to user
    user: User = Relationship(back_populates="sneezes")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    username: str = Field(max_length=50)
    email: str = Field(max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(min_length=8, max_length=100)


class UserLogin(SQLModel, table=False):
    username: str = Field(max_length=50)
    password: str = Field(max_length=100)


class UserResponse(SQLModel, table=False):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


class SneezeCreate(SQLModel, table=False):
    severity: SeverityLevel
    notes: str = Field(default="", max_length=1000)


class SneezeUpdate(SQLModel, table=False):
    severity: Optional[SeverityLevel] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=1000)


class SneezeResponse(SQLModel, table=False):
    id: int
    timestamp: datetime
    severity: SeverityLevel
    notes: str
    created_at: datetime


class SneezeWithUser(SQLModel, table=False):
    id: int
    timestamp: datetime
    severity: SeverityLevel
    notes: str
    user: UserResponse
