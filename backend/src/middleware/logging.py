"""
Security event logging middleware.

This module provides structured logging for security-related events such as
failed login attempts, token rejections, and rate limit violations.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID


# Configure logger for security events
logger = logging.getLogger("security")
logger.setLevel(logging.WARNING)


def log_security_event(
    event_type: str,
    user_id: Optional[UUID],
    ip_address: str,
    user_agent: str,
    details: Dict[str, Any]
) -> None:
    """
    Log a security event with structured JSON format.

    Creates a structured log entry for security-related events. All logs are
    output as JSON for easy parsing and analysis by security monitoring tools.

    IMPORTANT: This function must NEVER log sensitive data such as:
    - Passwords (plain text or hashed)
    - JWT tokens (full token values)
    - API keys or secrets
    - Credit card numbers or PII

    Args:
        event_type: Type of security event (e.g., "failed_login", "token_rejected")
        user_id: User ID if available, None otherwise
        ip_address: Client IP address
        user_agent: Client User-Agent header
        details: Additional event-specific details (must not contain sensitive data)

    Example:
        log_security_event(
            event_type="failed_login",
            user_id=None,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            details={"email": "user@example.com", "reason": "invalid_password"}
        )
    """
    # Create structured log entry
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": str(user_id) if user_id else None,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "details": details
    }

    # Convert to JSON string for structured logging
    log_message = json.dumps(log_entry)

    # Log at WARNING level for security events (so they're always captured)
    logger.warning(log_message)
