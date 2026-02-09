"""
Database models for the Task Management API.

This module re-exports models from src.models for backward compatibility.
"""
# Import models from new location to avoid duplicate table definitions
from src.models.user import User
from src.models.task import Task, TaskStatus, TaskPriority, TaskRecurrence
from src.models.conversation import Conversation
from src.models.message import Message, MessageRole

# Re-export for backward compatibility
__all__ = ["User", "Task", "TaskStatus", "TaskPriority", "TaskRecurrence", "Conversation", "Message", "MessageRole"]

