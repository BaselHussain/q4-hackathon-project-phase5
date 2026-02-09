"""
Pydantic schemas for request/response validation.

This module defines all API request and response schemas including
RFC 7807 Problem Details for error responses.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


VALID_PRIORITIES = ["high", "medium", "low"]
VALID_RECURRENCES = ["none", "daily", "weekly", "monthly", "yearly"]


class ProblemDetail(BaseModel):
    """
    RFC 7807 Problem Details schema for standardized error responses.

    Attributes:
        type: URI reference identifying the problem type
        title: Short, human-readable summary of the problem
        detail: Human-readable explanation specific to this occurrence
        status: HTTP status code
    """
    type: str
    title: str
    detail: str
    status: int


class TaskCreate(BaseModel):
    """
    Schema for creating a new task.

    Attributes:
        title: Task title (1-200 characters)
        description: Optional task description (max 2000 characters)
        due_date: Optional due date (timezone-aware datetime)
        priority: Task priority level (high/medium/low, default: medium)
        tags: Optional list of tags (max 10 tags, max 50 chars each)
        recurrence: Task recurrence pattern (default: none)
    """
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[datetime] = Field(None)
    priority: Optional[str] = Field("medium")
    tags: Optional[list[str]] = Field(None)
    recurrence: Optional[str] = Field("none")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v.lower() not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")
        return v.lower() if v else "medium"

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(cls, v):
        if v is not None and v.lower() not in VALID_RECURRENCES:
            raise ValueError(f"Recurrence must be one of: {', '.join(VALID_RECURRENCES)}")
        return v.lower() if v else "none"

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Maximum 10 tags per task")
        normalized = []
        for tag in v:
            tag = tag.strip().lower()
            if len(tag) < 1 or len(tag) > 50:
                raise ValueError("Each tag must be between 1 and 50 characters")
            normalized.append(tag)
        return list(dict.fromkeys(normalized))  # deduplicate preserving order


class TaskUpdate(BaseModel):
    """
    Schema for updating an existing task.

    At least one field must be provided for the update to be valid.

    Attributes:
        title: Optional new task title (1-200 characters)
        description: Optional new task description (max 2000 characters)
        due_date: Optional due date (timezone-aware datetime)
        priority: Optional task priority level (high/medium/low)
        tags: Optional list of tags
        recurrence: Optional task recurrence pattern
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[datetime] = Field(None)
    priority: Optional[str] = Field(None)
    tags: Optional[list[str]] = Field(None)
    recurrence: Optional[str] = Field(None)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v.lower() not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")
        return v.lower() if v else v

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(cls, v):
        if v is not None and v.lower() not in VALID_RECURRENCES:
            raise ValueError(f"Recurrence must be one of: {', '.join(VALID_RECURRENCES)}")
        return v.lower() if v else v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Maximum 10 tags per task")
        normalized = []
        for tag in v:
            tag = tag.strip().lower()
            if len(tag) < 1 or len(tag) > 50:
                raise ValueError("Each tag must be between 1 and 50 characters")
            normalized.append(tag)
        return list(dict.fromkeys(normalized))

    def model_post_init(self, __context):
        """Ensure at least one field is provided after model initialization."""
        if all(
            v is None
            for v in [self.title, self.description, self.due_date, self.priority, self.tags, self.recurrence]
        ):
            raise ValueError("At least one field must be provided")


class TaskResponse(BaseModel):
    """
    Schema for task response data.

    Attributes:
        id: Unique task identifier
        user_id: ID of the user who owns the task
        title: Task title
        description: Optional task description
        status: Current task status (pending or completed)
        priority: Task priority level
        due_date: Optional due date
        tags: Optional list of tags
        recurrence: Task recurrence pattern
        created_at: Timestamp when task was created (UTC)
        updated_at: Timestamp when task was last updated (UTC)
    """
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    recurrence: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
