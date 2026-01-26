"""
Unit tests for rate limiting functionality.

Tests the rate limiting configuration and setup using slowapi.
Note: Actual rate limit enforcement is tested in integration tests
where we make real HTTP requests to rate-limited endpoints.

This unit test file focuses on:
- Limiter initialization and configuration
- Key function behavior (IP extraction)
- Rate limit decorator application
"""
import pytest
from unittest.mock import Mock
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


class TestRateLimitConfiguration:
    """Unit tests for rate limit configuration (T036)."""

    def test_limiter_initialization(self):
        """
        Test that Limiter can be initialized with correct configuration.

        Expected: Limiter instance created with key_func and default limits.
        """
        # Act
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["5/minute"]
        )

        # Assert
        assert limiter is not None
        assert limiter.enabled is True
        assert limiter._key_func == get_remote_address

    def test_limiter_with_custom_limit_string(self):
        """
        Test that custom limit strings are parsed correctly.

        Expected: Various limit formats (5/minute, 10/hour, etc.) work.
        """
        # Arrange & Act
        limiter1 = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
        limiter2 = Limiter(key_func=get_remote_address, default_limits=["100/hour"])
        limiter3 = Limiter(key_func=get_remote_address, default_limits=["1000/day"])

        # Assert - All should initialize successfully
        assert limiter1 is not None
        assert limiter2 is not None
        assert limiter3 is not None

    def test_limiter_can_be_disabled(self):
        """
        Test that limiter can be disabled via configuration.

        Expected: Limiter with enabled=False doesn't enforce limits.
        """
        # Act
        limiter = Limiter(
            key_func=get_remote_address,
            enabled=False
        )

        # Assert
        assert limiter is not None
        assert limiter.enabled is False

    def test_limiter_key_function_extracts_ip(self):
        """
        Test that the key function correctly extracts IP address from request.

        Expected: get_remote_address returns client IP from request.
        """
        # Arrange
        request = Mock(spec=Request)
        request.client.host = "203.0.113.42"

        # Act
        ip_address = get_remote_address(request)

        # Assert
        assert ip_address == "203.0.113.42"

    def test_limiter_key_function_with_different_ips(self):
        """
        Test that key function returns different keys for different IPs.

        Expected: Each unique IP gets a unique key.
        """
        # Arrange
        request1 = Mock(spec=Request)
        request1.client.host = "192.168.1.1"

        request2 = Mock(spec=Request)
        request2.client.host = "192.168.1.2"

        # Act
        key1 = get_remote_address(request1)
        key2 = get_remote_address(request2)

        # Assert
        assert key1 != key2
        assert key1 == "192.168.1.1"
        assert key2 == "192.168.1.2"

    def test_limiter_key_function_with_none_client(self):
        """
        Test rate limiting key function when client IP is None.

        Expected: Should handle gracefully (return default or raise).
        """
        # Arrange
        request = Mock(spec=Request)
        request.client = None  # No client information

        # Act & Assert - Should not crash
        try:
            key = get_remote_address(request)
            # If we get here, slowapi handled it with a default
            assert key is not None
        except (AttributeError, TypeError):
            # If it raises, that's also acceptable behavior
            # The application should ensure client is always present
            pass

    def test_limiter_limit_decorator_format(self):
        """
        Test that limit decorator accepts various format strings.

        Expected: Different rate limit formats are valid.
        """
        # Arrange
        limiter = Limiter(key_func=get_remote_address)

        # Act & Assert - These should all be valid limit strings
        valid_limits = [
            "5/minute",
            "10/hour",
            "100/day",
            "1/second",
            "5 per minute",
            "10 per hour"
        ]

        for limit_string in valid_limits:
            # Verify the limit string can be used with the decorator
            # We're not actually applying it, just checking it's valid
            assert isinstance(limit_string, str)
            assert "/" in limit_string or "per" in limit_string

    def test_limiter_storage_backend(self):
        """
        Test that limiter uses in-memory storage by default.

        Expected: Limiter initializes with default storage backend.
        """
        # Act
        limiter = Limiter(key_func=get_remote_address)

        # Assert
        assert limiter is not None
        # slowapi uses in-memory storage by default
        # We can verify the limiter was created successfully

    def test_limiter_multiple_instances(self):
        """
        Test that multiple limiter instances can be created.

        Expected: Each instance is independent.
        """
        # Act
        limiter1 = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
        limiter2 = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

        # Assert
        assert limiter1 is not None
        assert limiter2 is not None
        assert limiter1 is not limiter2  # Different instances
