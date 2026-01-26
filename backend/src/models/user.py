"""
User model for authentication and user management.

This module defines the User SQLModel for storing user authentication credentials.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, func
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    User model representing a registered user with authentication credentials.

    Attributes:
        id: Unique user identifier (UUID, primary key)
        email: User's email address (unique, indexed, max 254 chars per RFC 5321)
        password_hash: Bcrypt hashed password with salt (60 chars)
        created_at: Account creation timestamp (auto-generated)
        last_login_at: Last successful login timestamp (nullable)

    Business Rules:
        - Email must be unique across all users
        - Email is case-insensitive (stored lowercase)
        - Password hash never exposed in API responses
        - User deletion cascades to all owned tasks
    """
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False
    )
    email: str = Field(
        sa_column=Column(String(254), unique=True, index=True, nullable=False),
        max_length=254
    )
    password_hash: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
