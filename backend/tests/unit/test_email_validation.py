"""
Unit tests for email validation service.

Tests email validation and normalization following RFC 5322 format,
with 254 character max length and case-insensitive normalization.
"""

import pytest
from src.services.email_validator import validate_and_normalize_email


class TestEmailValidation:
    """Test suite for email validation and normalization."""

    def test_valid_email_simple(self):
        """Test validation of simple valid email format."""
        email = "user@example.com"
        result = validate_and_normalize_email(email)
        assert result == "user@example.com"

    def test_valid_email_with_subdomain(self):
        """Test validation of email with subdomain."""
        email = "user@mail.example.com"
        result = validate_and_normalize_email(email)
        assert result == "user@mail.example.com"

    def test_valid_email_with_dots(self):
        """Test validation of email with dots in local part."""
        email = "user.name@example.com"
        result = validate_and_normalize_email(email)
        assert result == "user.name@example.com"

    def test_valid_email_with_plus(self):
        """Test validation of email with plus sign in local part."""
        email = "user+tag@example.com"
        result = validate_and_normalize_email(email)
        assert result == "user+tag@example.com"

    def test_valid_email_with_hyphen(self):
        """Test validation of email with hyphen in domain."""
        email = "user@my-domain.com"
        result = validate_and_normalize_email(email)
        assert result == "user@my-domain.com"

    def test_valid_email_with_numbers(self):
        """Test validation of email with numbers."""
        email = "user123@example456.com"
        result = validate_and_normalize_email(email)
        assert result == "user123@example456.com"

    def test_valid_email_country_tld(self):
        """Test validation of email with country TLD."""
        email = "user.name@example.co.uk"
        result = validate_and_normalize_email(email)
        assert result == "user.name@example.co.uk"

    def test_invalid_format_no_at_sign(self):
        """Test rejection of email without @ sign."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("userexample.com")
        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_format_multiple_at_signs(self):
        """Test rejection of email with multiple @ signs."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("user@@example.com")
        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_format_no_domain(self):
        """Test rejection of email without domain."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("user@")
        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_format_no_local_part(self):
        """Test rejection of email without local part."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("@example.com")
        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_format_no_tld(self):
        """Test rejection of email without TLD."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("user@example")
        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_format_spaces(self):
        """Test rejection of email with spaces."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("user name@example.com")
        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_format_special_chars(self):
        """Test rejection of email with invalid special characters."""
        # Test with angle brackets which are invalid in email addresses
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("user<>@example.com")
        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_format_empty_string(self):
        """Test rejection of empty string."""
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email("")
        assert "Invalid email format" in str(exc_info.value)

    def test_email_too_long_255_chars(self):
        """Test rejection of email exceeding 254 character limit (255 chars)."""
        # Create email with 255 characters total
        # Formula: local + @ + domain = 255
        # 64 + 1 + 190 = 255
        local_part = "a" * 64
        domain_part = "b" * 186 + ".com"  # 186 + 4 (.com) = 190 chars
        long_email = f"{local_part}@{domain_part}"

        assert len(long_email) == 255
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email(long_email)
        assert "must not exceed 254 characters" in str(exc_info.value)

    def test_email_too_long_300_chars(self):
        """Test rejection of email with 300 characters."""
        # Create email with 300 characters total
        # Formula: local + @ + domain = 300
        # 64 + 1 + 235 = 300
        local_part = "a" * 64
        domain_part = "b" * 231 + ".com"  # 231 + 4 (.com) = 235 chars
        long_email = f"{local_part}@{domain_part}"

        assert len(long_email) == 300
        with pytest.raises(ValueError) as exc_info:
            validate_and_normalize_email(long_email)
        assert "must not exceed 254 characters" in str(exc_info.value)

    def test_email_exactly_254_chars(self):
        """Test acceptance of email with exactly 254 characters (boundary)."""
        # Create email with exactly 254 characters
        # Formula: local + @ + domain = 254
        # 64 + 1 + 189 = 254
        # Domain must respect DNS label length limit (63 chars per label)
        # Domain structure: 61 + . + 61 + . + 61 + . + com = 189 chars
        local_part = "a" * 64
        domain_part = "b" * 61 + "." + "c" * 61 + "." + "d" * 61 + ".com"
        email_254 = f"{local_part}@{domain_part}"

        assert len(email_254) == 254
        result = validate_and_normalize_email(email_254)
        assert result == email_254.lower()

    def test_case_insensitive_uppercase(self):
        """Test normalization of uppercase email to lowercase."""
        email = "USER@EXAMPLE.COM"
        result = validate_and_normalize_email(email)
        assert result == "user@example.com"

    def test_case_insensitive_mixed_case(self):
        """Test normalization of mixed case email to lowercase."""
        email = "User.Name@Example.Com"
        result = validate_and_normalize_email(email)
        assert result == "user.name@example.com"

    def test_case_insensitive_already_lowercase(self):
        """Test that already lowercase email remains unchanged."""
        email = "user@example.com"
        result = validate_and_normalize_email(email)
        assert result == "user@example.com"

    def test_case_insensitive_with_numbers(self):
        """Test normalization preserves numbers while lowercasing letters."""
        email = "User123@Example456.COM"
        result = validate_and_normalize_email(email)
        assert result == "user123@example456.com"
