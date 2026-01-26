"""
Integration tests for JWT token validation edge cases.

Tests various token validation scenarios including malformed tokens,
expired tokens, wrong signatures, and missing Bearer prefix.
"""
import os
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from jose import jwt

from src.core.security import ALGORITHM, create_access_token


class TestTokenValidationEdgeCases:
    """Integration tests for token validation edge cases (T056)."""

    @pytest.mark.asyncio
    async def test_malformed_token(self, client: AsyncClient):
        """
        Test request with malformed JWT token (invalid format).

        Expected: 401 Unauthorized with "malformed-token" error type.
        """
        # Arrange - Create various malformed tokens that pass header validation
        # but fail during JWT decoding
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        malformed_tokens = [
            "not.a.jwt.token",  # Has 3 segments but invalid base64
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid-payload.signature",  # Invalid base64 in payload
            "header.payload.signature",  # Valid structure but invalid base64
        ]

        for malformed_token in malformed_tokens:
            # Act - Make request with malformed token
            response = await client.get(
                f"/api/{user_id}/tasks",
                headers={"Authorization": f"Bearer {malformed_token}"}
            )

            # Assert
            assert response.status_code == 401, f"Failed for token: {malformed_token}"
            assert response.headers["content-type"] == "application/problem+json"

            error = response.json()
            assert error["type"] == "malformed-token", f"Wrong error type for token: {malformed_token}, got: {error['type']}"
            assert error["title"] == "Malformed Token"
            assert error["status"] == 401
            assert "malformed" in error["detail"].lower() or "invalid format" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_wrong_signature(self, client: AsyncClient):
        """
        Test request with token signed with different secret.

        Expected: 401 Unauthorized with "invalid-signature" error type.
        """
        # Arrange - Create a token with wrong secret
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        wrong_secret = "wrong-secret-key-that-doesnt-match"

        # Create token with wrong secret
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        wrong_token = jwt.encode(payload, wrong_secret, algorithm=ALGORITHM)

        # Act - Make request with wrong signature token
        response = await client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": f"Bearer {wrong_token}"}
        )

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-signature"
        assert error["title"] == "Invalid Signature"
        assert error["status"] == 401
        assert "signature" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient):
        """
        Test request with expired JWT token.

        Expected: 401 Unauthorized with "expired-token" error type.
        """
        # Arrange - Create an expired token
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        secret = os.getenv("BETTER_AUTH_SECRET")

        # Create token that expired 1 hour ago
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(payload, secret, algorithm=ALGORITHM)

        # Act - Make request with expired token
        response = await client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "expired-token"
        assert error["title"] == "Expired Token"
        assert error["status"] == 401
        assert "expired" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client: AsyncClient):
        """
        Test request with Authorization header missing 'Bearer ' prefix.

        Expected: 401 Unauthorized with "invalid-authorization-header" error type.
        """
        # Arrange - Create a valid token but send without Bearer prefix
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        from uuid import UUID
        token = create_access_token(UUID(user_id))

        # Act - Make request without Bearer prefix
        response = await client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": token}  # Missing "Bearer " prefix
        )

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-authorization-header"
        assert error["title"] == "Invalid Authorization Header"
        assert error["status"] == 401
        assert "bearer" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_with_invalid_user_id_format(self, client: AsyncClient):
        """
        Test request with token containing invalid UUID format in 'sub' claim.

        Expected: 401 Unauthorized with "invalid-token" error type.
        """
        # Arrange - Create token with invalid user_id format
        secret = os.getenv("BETTER_AUTH_SECRET")
        payload = {
            "sub": "not-a-valid-uuid",  # Invalid UUID format
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        invalid_token = jwt.encode(payload, secret, algorithm=ALGORITHM)

        # Act - Make request with invalid user_id token
        response = await client.get(
            "/api/550e8400-e29b-41d4-a716-446655440000/tasks",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-token"
        assert error["title"] == "Invalid Token"
        assert error["status"] == 401
        assert "invalid user identifier" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_missing_sub_claim(self, client: AsyncClient):
        """
        Test request with token missing 'sub' claim.

        Expected: 401 Unauthorized with "invalid-token" error type.
        """
        # Arrange - Create token without 'sub' claim
        secret = os.getenv("BETTER_AUTH_SECRET")
        payload = {
            # Missing "sub" claim
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        invalid_token = jwt.encode(payload, secret, algorithm=ALGORITHM)

        # Act - Make request with token missing sub claim
        response = await client.get(
            "/api/550e8400-e29b-41d4-a716-446655440000/tasks",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-token"
        assert error["title"] == "Invalid Token"
        assert error["status"] == 401
        assert "missing user identifier" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_valid_token_succeeds(self, client: AsyncClient, db):
        """
        Test that a valid token still works correctly after enhancements.

        Expected: 200 OK with successful response.
        """
        # Arrange - Register and login to get valid token
        register_payload = {
            "email": "validtoken@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        user_id = register_response.json()["user_id"]

        login_payload = {
            "email": "validtoken@example.com",
            "password": "SecurePass123!"
        }
        login_response = await client.post("/api/auth/login", json=login_payload)
        token = login_response.json()["access_token"]

        # Act - Make request with valid token
        response = await client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert - Should succeed
        assert response.status_code == 200
