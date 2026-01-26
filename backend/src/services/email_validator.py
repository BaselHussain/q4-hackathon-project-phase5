"""
Email validation and normalization service.

Provides RFC 5322 compliant email validation with case-insensitive
normalization and length enforcement.
"""

from email_validator import validate_email, EmailNotValidError


def validate_and_normalize_email(email: str) -> str:
    """
    Validate and normalize an email address.

    Validates email format according to RFC 5322 standards and normalizes
    to lowercase for case-insensitive storage and comparison.

    Args:
        email: Email address to validate and normalize

    Returns:
        Normalized email address (lowercase)

    Raises:
        ValueError: If email format is invalid or exceeds length limit

    Examples:
        >>> validate_and_normalize_email("User@Example.COM")
        'user@example.com'

        >>> validate_and_normalize_email("invalid-email")
        ValueError: Invalid email format: ...

        >>> validate_and_normalize_email("a" * 255 + "@example.com")
        ValueError: Email must not exceed 254 characters
    """
    # Check length first (RFC 5321 standard)
    if len(email) > 254:
        raise ValueError("Email must not exceed 254 characters")

    try:
        # Validate email format (RFC 5322)
        # check_deliverability=False: Skip DNS verification as per requirements
        valid = validate_email(email, check_deliverability=False)

        # Normalize to lowercase for case-insensitive storage
        # Use .normalized instead of deprecated .email attribute
        return valid.normalized.lower()

    except EmailNotValidError as e:
        # Wrap library exception with clear error message
        raise ValueError(f"Invalid email format: {str(e)}")
