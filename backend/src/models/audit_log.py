"""
Audit log model for event tracking and compliance.

This module defines the AuditLog SQLModel for recording all task-related events
for audit trail, compliance, and debugging purposes.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    """
    Audit log model for tracking all task-related events.

    Stores immutable event records for compliance, debugging, and audit trail.
    Each event is identified by a unique event_id to ensure idempotency.

    Attributes:
        id: Unique audit log entry identifier (UUID, primary key)
        event_id: Unique event identifier for idempotency (UUID, unique)
        timestamp: Event occurrence timestamp (timezone-aware, indexed)
        user_id: User who triggered the event (foreign key to users)
        event_type: Type of event (e.g., 'task.created', 'task.updated')
        task_id: Related task identifier (nullable, foreign key to tasks)
        payload: Event-specific data stored as JSONB
        created_at: Audit log creation timestamp (auto-generated)

    Business Rules:
        - event_id must be unique (enforces idempotency)
        - timestamp reflects when the event occurred (not when logged)
        - task_id can be null if task is deleted (ON DELETE SET NULL)
        - payload contains event-specific context as JSON
        - All records are immutable once created (append-only log)
    """
    __tablename__ = "audit_logs"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False
    )
    event_id: UUID = Field(
        nullable=False,
        unique=True,
        index=True
    )
    timestamp: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            index=True
        )
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )
    event_type: str = Field(
        sa_column=Column(String(50), nullable=False),
        max_length=50,
        index=True
    )
    task_id: Optional[UUID] = Field(
        default=None,
        foreign_key="tasks.id",
        index=True
    )
    payload: dict = Field(
        sa_column=Column(JSONB, nullable=False),
        default_factory=dict
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now()
        )
    )
