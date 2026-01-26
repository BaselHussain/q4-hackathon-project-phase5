"""
Configuration settings for authentication and security.

This module manages authentication-related configuration from environment variables:
- JWT token settings (secret key, algorithm, expiration)
- Rate limiting configuration
- Security parameters

All settings are loaded from environment variables with sensible defaults.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Authentication and security configuration settings."""

    # JWT Configuration
    BETTER_AUTH_SECRET: str = os.getenv(
        "BETTER_AUTH_SECRET",
        "default_secret_key_change_in_production_minimum_32_chars"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    TOKEN_EXPIRE_HOURS: int = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_LOGIN_ATTEMPTS: int = int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True

    def validate_secret_key(self) -> None:
        """
        Validate that the secret key meets minimum security requirements.

        Raises:
            ValueError: If secret key is too short or uses default value in production.
        """
        if len(self.BETTER_AUTH_SECRET) < 32:
            raise ValueError(
                "BETTER_AUTH_SECRET must be at least 32 characters long. "
                "Generate a secure key with: openssl rand -hex 32"
            )

        if (
            self.BETTER_AUTH_SECRET == "default_secret_key_change_in_production_minimum_32_chars"
            and os.getenv("ENVIRONMENT", "development") == "production"
        ):
            raise ValueError(
                "BETTER_AUTH_SECRET must be changed from default value in production. "
                "Generate a secure key with: openssl rand -hex 32"
            )


# Global settings instance
auth_settings = AuthSettings()
