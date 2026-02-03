"""
MCP Tools package for Todo Task Management.

This package contains stateless MCP tools that interact with the database
to manage user tasks. All tools are designed for AI agent consumption.
"""

from .tasks import register_tools

__all__ = ["register_tools"]
