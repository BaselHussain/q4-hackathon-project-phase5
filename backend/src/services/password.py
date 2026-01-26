"""
Password security service for user authentication.

This module provides secure password hashing, verification, and validation
following security best practices:
- bcrypt hashing with automatic salt generation
- Password complexity validation
- Length constraints (8-128 characters)

Security Requirements:
- Passwords are never stored in plain text
- Each password gets a unique salt (automatic with bcrypt)
- Complexity rules enforce strong passwords
"""

import re
from typing import Tuple
from src.core.security import pwd_context


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    bcrypt automatically generates a unique salt for each password and
    embeds it in the hash string. This ensures that the same password
    will produce different hashes each time.

    Args:
        plain_password: The plain text password to hash

    Returns:
        str: The bcrypt hash string (includes salt and hash)

    Example:
        >>> hashed = hash_password("SecurePass123!")
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hash to verify against

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("SecurePass123!")
        >>> verify_password("SecurePass123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength against complexity requirements.

    Password Requirements:
    - Minimum 8 characters
    - Maximum 128 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one number (0-9)
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

    Args:
        password: The password to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if password meets all requirements, False otherwise
            - error_message: Empty string if valid, descriptive error if invalid

    Example:
        >>> validate_password_strength("SecurePass123!")
        (True, "")
        >>> validate_password_strength("weak")
        (False, "Password must be at least 8 characters long")
    """
    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    # Check maximum length
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    # Check for at least one number
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"

    # Check for at least one special character
    # Common special characters: !@#$%^&*()_+-=[]{}|;:,.<>?
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False, "Password must contain at least one special character"

    # All requirements met
    return True, ""
