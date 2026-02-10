"""
Structured JSON Logger for Kubernetes + Loki Integration.

This module provides a structured logging configuration that outputs JSON logs
compatible with Loki's log aggregation. All logs include:
- timestamp (RFC3339Nano format)
- level (INFO, WARNING, ERROR, etc.)
- logger (module name)
- message (log message)
- trace_id (distributed tracing ID, if available)
- span_id (span ID for tracing, if available)
- user_id (authenticated user ID, if available)
- request_id (unique request identifier, if available)

Usage:
    from utils.structured_logger import get_logger

    logger = get_logger(__name__)
    logger.info("User logged in", extra={"user_id": "123", "request_id": "abc"})
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variables for request-scoped data
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format with all required fields for Loki ingestion.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables if available
        if request_id_var.get():
            log_data["request_id"] = request_id_var.get()

        if user_id_var.get():
            log_data["user_id"] = user_id_var.get()

        if trace_id_var.get():
            log_data["trace_id"] = trace_id_var.get()

        if span_id_var.get():
            log_data["span_id"] = span_id_var.get()

        # Add extra fields from log record
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id

        if hasattr(record, "span_id"):
            log_data["span_id"] = record.span_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add stack trace if present
        if record.stack_info:
            log_data["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_data)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a structured JSON logger.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)

        # Create console handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(JSONFormatter())

        logger.addHandler(handler)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None
) -> None:
    """
    Set request-scoped context variables for logging.

    This should be called at the beginning of each request to set
    context that will be included in all logs for that request.

    Args:
        request_id: Unique request identifier
        user_id: Authenticated user ID
        trace_id: Distributed tracing ID
        span_id: Span ID for tracing
    """
    if request_id:
        request_id_var.set(request_id)

    if user_id:
        user_id_var.set(user_id)

    if trace_id:
        trace_id_var.set(trace_id)

    if span_id:
        span_id_var.set(span_id)


def clear_request_context() -> None:
    """
    Clear request-scoped context variables.

    This should be called at the end of each request to clean up context.
    """
    request_id_var.set(None)
    user_id_var.set(None)
    trace_id_var.set(None)
    span_id_var.set(None)


# Example usage
if __name__ == "__main__":
    # Create logger
    logger = get_logger(__name__)

    # Set request context
    set_request_context(
        request_id="req-123",
        user_id="user-456",
        trace_id="trace-789",
        span_id="span-abc"
    )

    # Log messages
    logger.info("User logged in successfully")
    logger.warning("Rate limit approaching", extra={"remaining": 10})
    logger.error("Database connection failed", extra={"db": "postgres"})

    # Clear context
    clear_request_context()
