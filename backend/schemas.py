"""
Pydantic schemas for request/response validation.

This module defines all API request and response schemas including
RFC 7807 Problem Details for error responses.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
    """
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)


class TaskUpdate(BaseModel):
    """
    Schema for updating an existing task.

    At least one field must be provided for the update to be valid.

    Attributes:
        title: Optional new task title (1-200 characters)
        description: Optional new task description (max 2000 characters)
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator('title', 'description')
    @classmethod
    def check_at_least_one_field(cls, v, info):
        """Validate that at least one field is provided."""
        return v

    def model_post_init(self, __context):
        """Ensure at least one field is provided after model initialization."""
        if self.title is None and self.description is None:
            raise ValueError("At least one field (title or description) must be provided")


class TaskResponse(BaseModel):
    """
    Schema for task response data.

    Attributes:
        id: Unique task identifier
        user_id: ID of the user who owns the task
        title: Task title
        description: Optional task description
        status: Current task status (pending or completed)
        created_at: Timestamp when task was created (UTC)
        updated_at: Timestamp when task was last updated (UTC)
    """
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
