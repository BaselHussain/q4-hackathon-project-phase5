"""
Authentication API schemas for request and response validation.

This module defines Pydantic models for authentication endpoints including
user registration and login.
"""
from uuid import UUID
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """
    Request schema for user registration.

    Attributes:
        email: User email address (RFC 5322 format, max 254 chars)
        password: User password (8-128 chars with complexity requirements)
    """
    email: str = Field(
        ...,
        description="User email address in RFC 5322 format",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="Password with complexity requirements: 8-128 chars, uppercase, lowercase, number, special char",
        examples=["SecurePass123!"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePass123!"
                }
            ]
        }
    }


class RegisterResponse(BaseModel):
    """
    Response schema for successful user registration.

    Attributes:
        user_id: Unique identifier for the newly created user
        email: Registered email address (normalized to lowercase)
        message: Success message confirming registration
    """
    user_id: UUID = Field(
        ...,
        description="Unique user identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    email: str = Field(
        ...,
        description="Registered email address (lowercase)",
        examples=["user@example.com"]
    )
    message: str = Field(
        ...,
        description="Success message",
        examples=["User registered successfully"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "message": "User registered successfully"
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """
    Request schema for user login.

    Attributes:
        email: User email address
        password: User password
    """
    email: str = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["SecurePass123!"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePass123!"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    """
    Response schema for successful user login.

    Attributes:
        access_token: JWT access token for authentication
        token_type: Token type (always "bearer")
        user_id: Unique identifier for the authenticated user
        email: User's email address
    """
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Token type for Authorization header",
        examples=["bearer"]
    )
    user_id: UUID = Field(
        ...,
        description="Unique user identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    email: str = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com"
                }
            ]
        }
    }
