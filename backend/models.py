"""
Database models for the Task Management API.

This module re-exports models from src.models for backward compatibility.
"""
# Import models from new location to avoid duplicate table definitions
from src.models.user import User
from src.models.task import Task, TaskStatus

# Re-export for backward compatibility
__all__ = ["User", "Task", "TaskStatus"]

