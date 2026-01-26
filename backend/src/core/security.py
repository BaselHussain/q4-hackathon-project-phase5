"""
Security utilities for authentication and authorization.

This module provides core security functions for the authentication system:
- JWT token generation and validation
- Password hashing and verification
- Token payload management

Dependencies:
- python-jose[cryptography] for JWT handling
- passlib[bcrypt] for password hashing
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

# Password hashing context using bcrypt
# bcrypt automatically generates unique salts for each password
# and handles salt storage within the hash string
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")
if not SECRET_KEY:
    raise ValueError("BETTER_AUTH_SECRET environment variable must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user_id: The user's unique identifier
        expires_delta: Optional custom expiration time. Defaults to 24 hours.

    Returns:
        str: Encoded JWT token

    Raises:
        ValueError: If SECRET_KEY is not configured

    Example:
        >>> token = create_access_token(user_id=UUID("550e8400-e29b-41d4-a716-446655440000"))
        >>> # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # JWT payload with standard claims
    to_encode = {
        "sub": str(user_id),  # Subject (user_id)
        "exp": expire,  # Expiration time
        "iat": datetime.now(timezone.utc),  # Issued at
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> tuple[Optional[dict], Optional[str]]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT token string to decode

    Returns:
        tuple: (payload, error_type) where:
            - payload: Token payload containing 'sub' (user_id), 'exp', 'iat' if successful, None otherwise
            - error_type: Error type string if failed, None if successful
                Possible error types:
                - "malformed-token": Token has invalid format or structure
                - "expired-token": Token has expired
                - "invalid-signature": Token signature verification failed
                - "invalid-token": Other JWT validation errors

    Example:
        >>> payload, error = decode_access_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        >>> if payload:
        ...     user_id = UUID(payload["sub"])
        >>> else:
        ...     print(f"Token validation failed: {error}")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return (payload, None)
    except ExpiredSignatureError:
        # Token has expired
        return (None, "expired-token")
    except JWTError as e:
        # Analyze the error to determine specific type
        error_msg = str(e).lower()

        # Check for signature verification errors
        if "signature" in error_msg or "verification" in error_msg:
            return (None, "invalid-signature")

        # Check for malformed token errors (invalid structure, bad encoding)
        if any(keyword in error_msg for keyword in [
            "not enough segments",
            "invalid header",
            "invalid payload",
            "invalid crypto padding",
            "incorrect padding",
            "invalid base64",
            "invalid token"
        ]):
            return (None, "malformed-token")

        # Generic invalid token error for other cases
        return (None, "invalid-token")

