"""
Unit tests for password security functionality.

Tests password hashing, verification, and validation following TDD approach.
These tests should FAIL initially until the password service is implemented.

Test Coverage:
- Password hashing with bcrypt
- Password verification
- Unique salt generation
- Password length validation (min 8, max 128)
- Password complexity validation (uppercase, lowercase, number, special char)
"""

import pytest
from src.services.password import (
    hash_password,
    verify_password,
    validate_password_strength,
)


class TestPasswordHashing:
    """Test password hashing and verification functionality."""

    def test_hash_password(self):
        """Test that password hashing works correctly."""
        plain_password = "SecurePass123!"
        hashed = hash_password(plain_password)

        # Verify hash is not empty
        assert hashed is not None
        assert len(hashed) > 0

        # Verify hash is different from plain password
        assert hashed != plain_password

        # Verify hash starts with bcrypt identifier
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_password(self):
        """Test that password verification works correctly."""
        plain_password = "SecurePass123!"
        hashed = hash_password(plain_password)

        # Correct password should verify successfully
        assert verify_password(plain_password, hashed) is True

        # Incorrect password should fail verification
        assert verify_password("WrongPassword123!", hashed) is False
        assert verify_password("securepass123!", hashed) is False  # Case sensitive
        assert verify_password("", hashed) is False  # Empty password

    def test_unique_salts(self):
        """Test that same password produces different hashes (unique salts)."""
        plain_password = "SecurePass123!"

        # Hash the same password multiple times
        hash1 = hash_password(plain_password)
        hash2 = hash_password(plain_password)
        hash3 = hash_password(plain_password)

        # All hashes should be different due to unique salts
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3

        # But all should verify with the original password
        assert verify_password(plain_password, hash1) is True
        assert verify_password(plain_password, hash2) is True
        assert verify_password(plain_password, hash3) is True


class TestPasswordValidation:
    """Test password strength validation functionality."""

    def test_password_length_minimum(self):
        """Test that passwords must be at least 8 characters."""
        # Valid: exactly 8 characters with all requirements
        is_valid, message = validate_password_strength("Abcd123!")
        assert is_valid is True
        assert message == ""

        # Invalid: 7 characters
        is_valid, message = validate_password_strength("Abc12!")
        assert is_valid is False
        assert "at least 8 characters" in message.lower()

        # Invalid: empty password
        is_valid, message = validate_password_strength("")
        assert is_valid is False
        assert "at least 8 characters" in message.lower()

    def test_password_max_length(self):
        """Test that passwords must not exceed 128 characters."""
        # Valid: exactly 128 characters
        valid_password = "A1!" + "a" * 125  # 128 chars total
        is_valid, message = validate_password_strength(valid_password)
        assert is_valid is True
        assert message == ""

        # Invalid: 129 characters
        invalid_password = "A1!" + "a" * 126  # 129 chars total
        is_valid, message = validate_password_strength(invalid_password)
        assert is_valid is False
        assert "128 characters" in message

    def test_password_complexity_uppercase(self):
        """Test that password must contain at least one uppercase letter."""
        # Valid: has uppercase
        is_valid, message = validate_password_strength("Abcdef123!")
        assert is_valid is True

        # Invalid: no uppercase
        is_valid, message = validate_password_strength("abcdef123!")
        assert is_valid is False
        assert "uppercase" in message.lower()

    def test_password_complexity_lowercase(self):
        """Test that password must contain at least one lowercase letter."""
        # Valid: has lowercase
        is_valid, message = validate_password_strength("ABCdef123!")
        assert is_valid is True

        # Invalid: no lowercase
        is_valid, message = validate_password_strength("ABCDEF123!")
        assert is_valid is False
        assert "lowercase" in message.lower()

    def test_password_complexity_number(self):
        """Test that password must contain at least one number."""
        # Valid: has number
        is_valid, message = validate_password_strength("Abcdefgh1!")
        assert is_valid is True

        # Invalid: no number
        is_valid, message = validate_password_strength("Abcdefgh!")
        assert is_valid is False
        assert "number" in message.lower() or "digit" in message.lower()

    def test_password_complexity_special_char(self):
        """Test that password must contain at least one special character."""
        # Valid: has special character
        is_valid, message = validate_password_strength("Abcdefgh1!")
        assert is_valid is True

        # Invalid: no special character
        is_valid, message = validate_password_strength("Abcdefgh123")
        assert is_valid is False
        assert "special" in message.lower()

    def test_password_complexity_all_requirements(self):
        """Test various passwords against all complexity requirements."""
        # Valid passwords
        valid_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd",
            "Test1234!@#$",
            "Abcd123!",  # Minimum valid
            "A1!" + "a" * 125,  # Maximum valid (128 chars)
        ]

        for password in valid_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid but got: {message}"
            assert message == ""

        # Invalid passwords with specific failures
        invalid_passwords = [
            ("abc123!", "no uppercase"),  # Missing uppercase
            ("ABC123!", "no lowercase"),  # Missing lowercase
            ("Abcdefg!", "no number"),  # Missing number
            ("Abcdefg123", "no special"),  # Missing special char
            ("Abc12!", "too short"),  # Too short (7 chars)
            ("A1!" + "a" * 126, "too long"),  # Too long (129 chars)
        ]

        for password, reason in invalid_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is False, f"Password '{password}' should be invalid ({reason})"
            assert len(message) > 0, f"Should have error message for '{password}'"
