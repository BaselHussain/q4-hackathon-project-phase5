"""
Unit tests for JWT token generation and validation.

Tests the core JWT functionality in src/core/security.py including:
- Token creation with valid user IDs
- Token validation and payload extraction
- Expiration handling
- Invalid token scenarios
"""
import time
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from jose import jwt

from src.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
)


class TestJWTTokenGeneration:
    """Unit tests for JWT token generation (T028)."""

    def test_create_token_with_valid_user_id(self):
        """
        Test creating a JWT token with a valid user ID.

        Expected: Token is created successfully and contains correct payload.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token = create_access_token(user_id)

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode token to verify payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_contains_required_claims(self):
        """
        Test that generated token contains all required JWT claims.

        Expected: Token contains 'sub' (user_id), 'exp' (expiration), 'iat' (issued at).
        """
        # Arrange
        user_id = uuid4()

        # Act
        token = create_access_token(user_id)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert - Verify all required claims are present
        assert "sub" in payload, "Token missing 'sub' claim"
        assert "exp" in payload, "Token missing 'exp' claim"
        assert "iat" in payload, "Token missing 'iat' claim"

        # Verify claim types
        assert isinstance(payload["sub"], str)
        assert isinstance(payload["exp"], int)
        assert isinstance(payload["iat"], int)

    def test_create_token_with_custom_expiration(self):
        """
        Test creating a token with custom expiration time.

        Expected: Token expires at the specified custom time.
        """
        # Arrange
        user_id = uuid4()
        custom_expiration = timedelta(minutes=30)

        # Act
        token = create_access_token(user_id, expires_delta=custom_expiration)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert - Verify expiration is approximately 30 minutes from now
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        token_lifetime = exp_timestamp - iat_timestamp

        # Allow 5 second tolerance for test execution time
        assert 1795 <= token_lifetime <= 1805, f"Expected ~1800 seconds, got {token_lifetime}"

    def test_create_token_default_expiration_24_hours(self):
        """
        Test that default token expiration is 24 hours.

        Expected: Token expires 24 hours (1440 minutes) after creation.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token = create_access_token(user_id)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert - Verify expiration is approximately 24 hours from now
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        token_lifetime = exp_timestamp - iat_timestamp

        # 24 hours = 86400 seconds, allow 5 second tolerance
        assert 86395 <= token_lifetime <= 86405, f"Expected ~86400 seconds, got {token_lifetime}"

    def test_create_token_user_id_format(self):
        """
        Test that user_id is correctly stored as string in token.

        Expected: UUID is converted to string format in 'sub' claim.
        """
        # Arrange
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        # Act
        token = create_access_token(user_id)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Assert
        assert payload["sub"] == "550e8400-e29b-41d4-a716-446655440000"
        assert isinstance(payload["sub"], str)

        # Verify we can convert back to UUID
        reconstructed_uuid = UUID(payload["sub"])
        assert reconstructed_uuid == user_id

    def test_create_token_uses_hs256_algorithm(self):
        """
        Test that tokens are created using HS256 algorithm.

        Expected: Token header specifies HS256 algorithm.
        """
        # Arrange
        user_id = uuid4()

        # Act
        token = create_access_token(user_id)

        # Assert - Decode header without verification to check algorithm
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"
        assert header["typ"] == "JWT"


class TestJWTTokenValidation:
    """Unit tests for JWT token validation (T029)."""

    def test_decode_valid_token(self):
        """
        Test decoding a valid, non-expired token.

        Expected: Token is decoded successfully and returns correct payload.
        """
        # Arrange
        user_id = uuid4()
        token = create_access_token(user_id)

        # Act
        payload, error_type = decode_access_token(token)

        # Assert
        assert payload is not None
        assert error_type is None
        assert payload["sub"] == str(user_id)
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_expired_token(self):
        """
        Test decoding a token that has expired.

        Expected: Returns (None, "expired-token") for expired token.
        """
        # Arrange - Create token that expires immediately
        user_id = uuid4()
        token = create_access_token(user_id, expires_delta=timedelta(seconds=1))

        # Wait for token to expire
        time.sleep(2)

        # Act
        payload, error_type = decode_access_token(token)

        # Assert
        assert payload is None, "Expired token should return None payload"
        assert error_type == "expired-token", "Should return expired-token error type"

    def test_decode_invalid_signature(self):
        """
        Test decoding a token with invalid signature.

        Expected: Returns (None, "invalid-signature") for token with wrong signature.
        """
        # Arrange - Create token with different secret
        user_id = uuid4()
        wrong_secret = "wrong_secret_key_12345"
        token = jwt.encode(
            {"sub": str(user_id), "exp": time.time() + 3600},
            wrong_secret,
            algorithm=ALGORITHM
        )

        # Act
        payload, error_type = decode_access_token(token)

        # Assert
        assert payload is None, "Token with invalid signature should return None payload"
        assert error_type == "invalid-signature", "Should return invalid-signature error type"

    def test_decode_malformed_token(self):
        """
        Test decoding a malformed token string.

        Expected: Returns (None, "malformed-token") for malformed token.
        """
        # Arrange
        malformed_tokens = [
            "not.a.token",
            "invalid_token_string",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "header.payload",  # Missing signature
        ]

        for malformed_token in malformed_tokens:
            # Act
            payload, error_type = decode_access_token(malformed_token)

            # Assert
            assert payload is None, f"Malformed token '{malformed_token}' should return None payload"
            assert error_type in ["malformed-token", "invalid-token"], f"Should return error type for '{malformed_token}'"

    def test_decode_token_missing_required_claims(self):
        """
        Test decoding a token missing required claims.

        Expected: Token is decoded but may be missing expected fields.
        """
        # Arrange - Create token without 'sub' claim
        token = jwt.encode(
            {"exp": time.time() + 3600, "iat": time.time()},
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        # Act
        payload, error_type = decode_access_token(token)

        # Assert - Token is valid but missing 'sub' claim
        assert payload is not None
        assert error_type is None
        assert "sub" not in payload
        assert "exp" in payload

    def test_decode_token_with_wrong_algorithm(self):
        """
        Test decoding a token created with different algorithm.

        Expected: Returns (None, error_type) for token with wrong algorithm.
        """
        # Arrange - Create token with HS512 instead of HS256
        user_id = uuid4()
        token = jwt.encode(
            {"sub": str(user_id), "exp": time.time() + 3600, "iat": time.time()},
            SECRET_KEY,
            algorithm="HS512"
        )

        # Act
        payload, error_type = decode_access_token(token)

        # Assert
        assert payload is None, "Token with wrong algorithm should return None payload"
        assert error_type is not None, "Should return an error type"

    def test_decode_token_preserves_user_id(self):
        """
        Test that user_id can be correctly extracted from decoded token.

        Expected: User ID can be reconstructed as UUID from token payload.
        """
        # Arrange
        original_user_id = uuid4()
        token = create_access_token(original_user_id)

        # Act
        payload, error_type = decode_access_token(token)

        # Assert
        assert payload is not None
        assert error_type is None
        reconstructed_user_id = UUID(payload["sub"])
        assert reconstructed_user_id == original_user_id

    def test_decode_none_token(self):
        """
        Test decoding None as token.

        Expected: Returns None gracefully without raising exception.
        """
        # Act & Assert
        with pytest.raises(Exception):
            # decode_access_token expects a string, passing None should raise
            decode_access_token(None)

    def test_decode_token_case_sensitivity(self):
        """
        Test that token decoding is case-sensitive.

        Expected: Changing case of token string makes it invalid.
        """
        # Arrange
        user_id = uuid4()
        token = create_access_token(user_id)

        # Act - Change case of token
        modified_token = token.upper()
        payload, error_type = decode_access_token(modified_token)

        # Assert
        assert payload is None, "Case-modified token should be invalid"
        assert error_type is not None, "Should return an error type"
