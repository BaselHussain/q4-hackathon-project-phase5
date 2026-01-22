"""
Database models for the Task Management API.

This module defines SQLModel ORM models for users and tasks.
"""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, func
from sqlmodel import Field, SQLModel


class TaskStatus(str, enum.Enum):
    """Enumeration for task status values."""
    PENDING = "pending"
    COMPLETED = "completed"


class User(SQLModel, table=True):
    """
    User model representing a user in the system.

    Users are automatically created on first task operation with placeholder emails.
    """
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False
    )
    email: str = Field(
        sa_column=Column(String(255), unique=True, index=True, nullable=False)
    )


class Task(SQLModel, table=True):
    """
    Task model representing a user's task.

    Each task belongs to a user and tracks title, description, status, and timestamps.
    """
    __tablename__ = "tasks"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )
    title: str = Field(
        sa_column=Column(String(200), nullable=False),
        min_length=1,
        max_length=200
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(String(2000), nullable=True),
        max_length=2000
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        nullable=False
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now()
        )
    )
