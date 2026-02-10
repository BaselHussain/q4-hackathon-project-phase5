"""
Logging Middleware for Request Context.

This middleware captures request-scoped information (request_id, user_id, trace_id)
and sets it in the logging context for structured logging.
"""

import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utils.structured_logger import set_request_context, clear_request_context


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture request context for structured logging.

    Extracts or generates:
    - request_id: Unique identifier for each request
    - user_id: Authenticated user ID (from JWT token if available)
    - trace_id: Distributed tracing ID (from headers if available)
    - span_id: Span ID for tracing (from headers if available)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and set logging context.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Extract trace context from headers (OpenTelemetry format)
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get("traceparent")
        span_id = request.headers.get("X-Span-ID")

        # Extract user ID from request state (set by auth middleware)
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = str(request.state.user_id)

        # Set logging context
        set_request_context(
            request_id=request_id,
            user_id=user_id,
            trace_id=trace_id,
            span_id=span_id
        )

        try:
            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        finally:
            # Clear context after request
            clear_request_context()
