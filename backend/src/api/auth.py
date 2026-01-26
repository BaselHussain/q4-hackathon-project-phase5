"""
Authentication API endpoints.

This module implements user registration and login endpoints with
JWT token-based authentication.
"""
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db
from src.api.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from src.core.security import create_access_token
from src.middleware.logging import log_security_event
from src.models.user import User
from src.services.email_validator import validate_and_normalize_email
from src.services.password import hash_password, validate_password_strength, verify_password


# Create router with prefix and tags
router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)

# T038: Initialize rate limiter for login endpoint
limiter = Limiter(key_func=get_remote_address)


def create_rfc7807_error(
    request: Request,
    error_type: str,
    title: str,
    status: int,
    detail: str
) -> JSONResponse:
    """
    Create RFC 7807 Problem Details error response.

    Args:
        request: FastAPI request object for instance URL
        error_type: Error type identifier (e.g., "invalid-email-format")
        title: Short, human-readable error title
        status: HTTP status code
        detail: Detailed error message

    Returns:
        JSONResponse with RFC 7807 format and application/problem+json content type
    """
    return JSONResponse(
        status_code=status,
        content={
            "type": error_type,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": str(request.url.path)
        },
        headers={"Content-Type": "application/problem+json"}
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    request: Request,
    registration_data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> RegisterResponse:
    """
    Register a new user account.

    Creates a new user with email and password. Email must be unique and follow
    RFC 5322 format. Password must meet complexity requirements.

    Args:
        request: FastAPI request object
        registration_data: User registration data (email and password)
        db: Database session

    Returns:
        RegisterResponse: User ID, email, and success message with 201 Created

    Raises:
        JSONResponse (400): Invalid email format or weak password
        JSONResponse (409): Email already registered
    """
    # Step 1: Validate and normalize email
    try:
        normalized_email = validate_and_normalize_email(registration_data.email)
    except ValueError as e:
        return create_rfc7807_error(
            request=request,
            error_type="invalid-email-format",
            title="Invalid Email Format",
            status=400,
            detail=str(e)
        )

    # Step 2: Validate password strength
    is_valid, error_message = validate_password_strength(registration_data.password)
    if not is_valid:
        return create_rfc7807_error(
            request=request,
            error_type="invalid-password",
            title="Invalid Password",
            status=400,
            detail=error_message
        )

    # Step 3: Check if email already exists
    result = await db.execute(
        select(User).where(User.email == normalized_email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return create_rfc7807_error(
            request=request,
            error_type="email-already-registered",
            title="Email Already Registered",
            status=409,
            detail="An account with this email address already exists"
        )

    # Step 4: Hash password
    password_hash = hash_password(registration_data.password)

    # Step 5: Create user in database
    new_user = User(
        id=uuid4(),
        email=normalized_email,
        password_hash=password_hash
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        # Handle race condition where user was created between check and insert
        await db.rollback()
        return create_rfc7807_error(
            request=request,
            error_type="email-already-registered",
            title="Email Already Registered",
            status=409,
            detail="An account with this email address already exists"
        )

    # Step 6: Return success response
    return RegisterResponse(
        user_id=new_user.id,
        email=new_user.email,
        message="User registered successfully"
    )


@router.post("/login", response_model=LoginResponse, status_code=200)
@limiter.limit("5/minute")  # T038: Apply rate limit (5 requests per minute per IP)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> LoginResponse:
    """
    Authenticate user and return JWT access token.

    Validates user credentials and returns a JWT token for API authentication.
    Returns generic error for both wrong password and non-existent email to
    prevent user enumeration attacks.

    Args:
        request: FastAPI request object
        login_data: User login credentials (email and password)
        db: Database session

    Returns:
        LoginResponse: JWT access token, token type, user_id, and email with 200 OK

    Raises:
        JSONResponse (401): Invalid email or password (generic error for security)
    """
    # Step 1: Normalize email to lowercase for case-insensitive lookup
    normalized_email = login_data.email.lower().strip()

    # Step 2: Query database for user by email
    result = await db.execute(
        select(User).where(User.email == normalized_email)
    )
    user = result.scalar_one_or_none()

    # Step 3: If user doesn't exist, return generic error (prevent user enumeration)
    if not user:
        # T063: Log failed login attempt (user not found)
        log_security_event(
            event_type="failed_login",
            user_id=None,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={
                "email": normalized_email,
                "reason": "user_not_found"
            }
        )
        return create_rfc7807_error(
            request=request,
            error_type="invalid-credentials",
            title="Invalid Credentials",
            status=401,
            detail="Invalid email or password"
        )

    # Step 4: Verify password
    is_password_valid = verify_password(login_data.password, user.password_hash)

    # Step 5: If password is wrong, return same generic error
    if not is_password_valid:
        # T063: Log failed login attempt (invalid password)
        log_security_event(
            event_type="failed_login",
            user_id=user.id,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={
                "email": normalized_email,
                "reason": "invalid_password"
            }
        )
        return create_rfc7807_error(
            request=request,
            error_type="invalid-credentials",
            title="Invalid Credentials",
            status=401,
            detail="Invalid email or password"
        )

    # Step 6: Update last_login_at timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    # Step 7: Generate JWT access token
    access_token = create_access_token(user_id=user.id)

    # Step 8: Return success response with token
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email
    )
