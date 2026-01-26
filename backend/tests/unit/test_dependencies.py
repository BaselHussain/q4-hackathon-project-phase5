"""
Unit tests for FastAPI dependencies.

Tests the authentication dependencies used to protect endpoints:
- get_current_user: Extracts and validates JWT token from Authorization header
- verify_user_access: Ensures token user_id matches path user_id
"""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import UUID, uuid4
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from src.api.dependencies import get_current_user, verify_user_access
from src.core.security import create_access_token


class TestGetCurrentUserDependency:
    """Unit tests for get_current_user dependency (T042)."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self):
        """
        Test extracting user from valid JWT token.

        Expected: Returns user_id from token payload.
        """
        # Arrange
        user_id = uuid4()
        token = create_access_token(user_id)

        # Create mock request with Authorization header
        request = Mock(spec=Request)
        request.headers = {"authorization": f"Bearer {token}"}

        # Act
        result = await get_current_user(request)

        # Assert
        assert result is not None
        assert isinstance(result, UUID)
        assert result == user_id

    @pytest.mark.asyncio
    async def test_get_current_user_with_missing_token(self):
        """
        Test behavior when Authorization header is missing.

        Expected: Raises HTTPException with 401 status.
        """
        # Arrange
        request = Mock(spec=Request)
        request.headers = {}  # No Authorization header

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "authorization" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token_format(self):
        """
        Test behavior when token format is invalid (not Bearer scheme).

        Expected: Raises HTTPException with 401 status.
        """
        # Arrange
        request = Mock(spec=Request)
        request.headers = {"authorization": "InvalidFormat token123"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_expired_token(self):
        """
        Test behavior when token has expired.

        Expected: Raises HTTPException with 401 status.
        """
        # Arrange
        from datetime import timedelta
        user_id = uuid4()
        # Create token that expires immediately
        token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))

        request = Mock(spec=Request)
        request.headers = {"authorization": f"Bearer {token}"}
        request.client = Mock()
        request.client.host = "127.0.0.1"  # Mock client IP for security logging
        request.url = Mock()
        request.url.path = "/test"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_signature(self):
        """
        Test behavior when token has invalid signature.

        Expected: Raises HTTPException with 401 status.
        """
        # Arrange
        # Create a token with wrong signature
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        request = Mock(spec=Request)
        request.headers = {"authorization": f"Bearer {invalid_token}"}
        request.client = Mock()
        request.client.host = "127.0.0.1"  # Mock client IP for security logging
        request.url = Mock()
        request.url.path = "/test"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_malformed_token(self):
        """
        Test behavior when token is malformed.

        Expected: Raises HTTPException with 401 status.
        """
        # Arrange
        request = Mock(spec=Request)
        request.headers = {"authorization": "Bearer not.a.valid.token"}
        request.client = Mock()
        request.client.host = "127.0.0.1"  # Mock client IP for security logging
        request.url = Mock()
        request.url.path = "/test"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_empty_token(self):
        """
        Test behavior when token is empty string.

        Expected: Raises HTTPException with 401 status.
        """
        # Arrange
        request = Mock(spec=Request)
        request.headers = {"authorization": "Bearer "}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_case_insensitive_bearer(self):
        """
        Test that Bearer scheme is case-insensitive.

        Expected: Works with 'bearer', 'Bearer', 'BEARER'.
        """
        # Arrange
        user_id = uuid4()
        token = create_access_token(user_id)

        # Test different cases
        for bearer_prefix in ["bearer", "Bearer", "BEARER"]:
            request = Mock(spec=Request)
            request.headers = {"authorization": f"{bearer_prefix} {token}"}

            # Act
            result = await get_current_user(request)

            # Assert
            assert result == user_id


class TestVerifyUserAccessDependency:
    """Unit tests for verify_user_access dependency (T042)."""

    @pytest.mark.asyncio
    async def test_verify_user_access_matching_ids(self):
        """
        Test access verification when token user_id matches path user_id.

        Expected: Returns user_id (access granted).
        """
        # Arrange
        user_id = uuid4()
        current_user_id = user_id  # Same ID

        # Act
        result = await verify_user_access(
            user_id=user_id,
            current_user_id=current_user_id
        )

        # Assert
        assert result == user_id

    @pytest.mark.asyncio
    async def test_verify_user_access_different_ids(self):
        """
        Test access verification when token user_id doesn't match path user_id.

        Expected: Raises HTTPException with 403 status.
        """
        # Arrange
        token_user_id = uuid4()
        path_user_id = uuid4()  # Different ID

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_user_access(
                user_id=path_user_id,
                current_user_id=token_user_id
            )

        assert exc_info.value.status_code == 403
        assert "access" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_verify_user_access_with_string_ids(self):
        """
        Test access verification when IDs are provided as UUIDs.

        Expected: Compares UUIDs correctly.
        """
        # Arrange
        user_id = uuid4()

        # Act
        result = await verify_user_access(
            user_id=user_id,
            current_user_id=user_id
        )

        # Assert
        assert result == user_id

    @pytest.mark.asyncio
    async def test_verify_user_access_error_message(self):
        """
        Test that error message is clear and doesn't leak sensitive info in detail.

        Expected: Generic access denied message in detail field.
        Note: The instance field can contain the path (which includes user_id) per RFC 7807.
        """
        # Arrange
        token_user_id = uuid4()
        path_user_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_user_access(
                user_id=path_user_id,
                current_user_id=token_user_id
            )

        # Verify error detail message doesn't contain actual UUIDs
        # (instance field can contain the path per RFC 7807)
        error_detail_dict = exc_info.value.detail
        detail_message = error_detail_dict.get("detail", "")

        assert str(token_user_id) not in detail_message
        assert str(path_user_id) not in detail_message
        assert "permission" in detail_message.lower()
