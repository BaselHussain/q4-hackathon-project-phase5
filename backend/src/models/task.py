"""
Task model for user task management.

This module defines the Task SQLModel for storing user tasks.
"""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, Column, DateTime, String, func
from sqlmodel import Field, SQLModel


class TaskStatus(str, enum.Enum):
    """Enumeration for task status values."""
    PENDING = "pending"
    COMPLETED = "completed"


class TaskPriority(str, enum.Enum):
    """Enumeration for task priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskRecurrence(str, enum.Enum):
    """Enumeration for task recurrence patterns."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Task(SQLModel, table=True):
    """
    Task model representing a user's task.

    Attributes:
        id: Unique task identifier (UUID, primary key)
        user_id: Owner of this task (foreign key to users.id)
        title: Task title (max 200 chars)
        description: Task description (optional, max 2000 chars)
        status: Task status (pending or completed)
        created_at: Task creation timestamp (auto-generated)
        updated_at: Last update timestamp (auto-updated)

    Business Rules:
        - Every task must have an owner (user_id NOT NULL)
        - Tasks are isolated by user - users can only access their own tasks
        - When user is deleted, all their tasks are deleted (CASCADE)
        - updated_at refreshed on any field change
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
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        sa_column=Column(String(10), nullable=False, default="medium")
    )
    due_date: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    tags: Optional[list[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String(50)), nullable=True)
    )
    recurrence: TaskRecurrence = Field(
        default=TaskRecurrence.NONE,
        sa_column=Column(String(10), nullable=False, default="none")
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
