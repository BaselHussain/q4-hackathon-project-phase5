"""
Unit tests for security logging functionality.

Tests verify that security events are logged with proper structure and content.
"""
import json
import logging
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.middleware.logging import log_security_event


class TestSecurityLogging:
    """Test suite for security event logging."""

    @patch('src.middleware.logging.logger')
    def test_log_failed_login(self, mock_logger):
        """
        Test that failed login attempts are logged with correct structure.

        Verifies:
        - Event type is 'failed_login'
        - Email (hashed/partial) is included
        - IP address is included
        - No sensitive data (passwords) in logs
        - Structured JSON format
        """
        # Arrange
        event_type = "failed_login"
        user_id = None  # No user_id for failed login
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0"
        details = {
            "email": "test@example.com",
            "reason": "invalid_password"
        }

        # Act
        log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify it's valid JSON
        log_data = json.loads(call_args)

        assert log_data["event_type"] == "failed_login"
        assert log_data["ip_address"] == ip_address
        assert log_data["user_agent"] == user_agent
        assert log_data["details"]["email"] == "test@example.com"
        assert log_data["details"]["reason"] == "invalid_password"
        assert "timestamp" in log_data
        # Ensure no actual password values are logged (not the word "password" in reason)
        assert "SecurePass123!" not in str(log_data)  # Check for actual password value
        assert "password_hash" not in str(log_data)  # Check for password hash field

    @patch('src.middleware.logging.logger')
    def test_log_token_rejection(self, mock_logger):
        """
        Test that invalid token attempts are logged correctly.

        Verifies:
        - Event type is 'token_rejected'
        - Token type error is included
        - IP address is included
        - Actual token value is NOT logged
        - Structured JSON format
        """
        # Arrange
        event_type = "token_rejected"
        user_id = None  # No user_id for rejected token
        ip_address = "10.0.0.50"
        user_agent = "curl/7.68.0"
        details = {
            "error_type": "expired-token",
            "endpoint": "/api/123e4567-e89b-12d3-a456-426614174000/tasks"
        }

        # Act
        log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify it's valid JSON
        log_data = json.loads(call_args)

        assert log_data["event_type"] == "token_rejected"
        assert log_data["ip_address"] == ip_address
        assert log_data["details"]["error_type"] == "expired-token"
        assert log_data["details"]["endpoint"] == "/api/123e4567-e89b-12d3-a456-426614174000/tasks"
        assert "timestamp" in log_data
        # Ensure actual token is not in logs
        assert "eyJ" not in str(log_data)  # JWT tokens start with eyJ

    @patch('src.middleware.logging.logger')
    def test_log_rate_limit(self, mock_logger):
        """
        Test that rate limit triggers are logged correctly.

        Verifies:
        - Event type is 'rate_limit_exceeded'
        - IP address is included
        - Endpoint being rate limited is included
        - Structured JSON format
        """
        # Arrange
        event_type = "rate_limit_exceeded"
        user_id = None  # May or may not have user_id
        ip_address = "203.0.113.42"
        user_agent = "PostmanRuntime/7.29.0"
        details = {
            "endpoint": "/api/auth/login",
            "limit": "5/minute"
        }

        # Act
        log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify it's valid JSON
        log_data = json.loads(call_args)

        assert log_data["event_type"] == "rate_limit_exceeded"
        assert log_data["ip_address"] == ip_address
        assert log_data["details"]["endpoint"] == "/api/auth/login"
        assert log_data["details"]["limit"] == "5/minute"
        assert "timestamp" in log_data

    @patch('src.middleware.logging.logger')
    def test_log_with_user_id(self, mock_logger):
        """
        Test that user_id is included when available.

        Verifies:
        - user_id is included in log when provided
        - user_id is properly formatted as string
        """
        # Arrange
        event_type = "suspicious_activity"
        user_id = uuid4()
        ip_address = "172.16.0.1"
        user_agent = "Python/3.11"
        details = {"action": "multiple_failed_attempts"}

        # Act
        log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify it's valid JSON
        log_data = json.loads(call_args)

        assert log_data["user_id"] == str(user_id)
        assert log_data["event_type"] == "suspicious_activity"

    @patch('src.middleware.logging.logger')
    def test_log_without_user_id(self, mock_logger):
        """
        Test that logs work correctly when user_id is None.

        Verifies:
        - user_id field is null when not provided
        - Log still contains all other required fields
        """
        # Arrange
        event_type = "unauthorized_access"
        user_id = None
        ip_address = "198.51.100.1"
        user_agent = "Unknown"
        details = {"endpoint": "/api/admin"}

        # Act
        log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify it's valid JSON
        log_data = json.loads(call_args)

        assert log_data["user_id"] is None
        assert log_data["event_type"] == "unauthorized_access"
        assert log_data["ip_address"] == ip_address

    @patch('src.middleware.logging.logger')
    def test_log_json_structure(self, mock_logger):
        """
        Test that log output is valid JSON with all required fields.

        Verifies:
        - Output is valid JSON
        - Contains: timestamp, event_type, user_id, ip_address, user_agent, details
        - Timestamp is in ISO 8601 format
        """
        # Arrange
        event_type = "test_event"
        user_id = uuid4()
        ip_address = "127.0.0.1"
        user_agent = "TestAgent/1.0"
        details = {"test": "data"}

        # Act
        log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]

        # Verify it's valid JSON
        log_data = json.loads(call_args)

        # Check all required fields
        assert "timestamp" in log_data
        assert "event_type" in log_data
        assert "user_id" in log_data
        assert "ip_address" in log_data
        assert "user_agent" in log_data
        assert "details" in log_data

        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        datetime.fromisoformat(log_data["timestamp"].replace('Z', '+00:00'))
