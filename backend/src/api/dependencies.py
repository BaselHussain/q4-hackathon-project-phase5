"""
FastAPI dependencies for authentication and authorization.

This module provides dependency functions for:
- Extracting and validating JWT tokens from Authorization headers
- Verifying user access to resources
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.core.security import decode_access_token
from src.middleware.logging import log_security_event


async def get_current_user(request: Request) -> UUID:
    """
    Dependency to extract and validate JWT token from Authorization header.

    Extracts the Bearer token from the Authorization header, validates it,
    and returns the user_id from the token payload.

    Args:
        request: FastAPI request object containing headers

    Returns:
        UUID: User ID extracted from valid JWT token

    Raises:
        HTTPException: 401 if token is missing, invalid, expired, or malformed
    """
    # Extract Authorization header
    auth_header = request.headers.get("authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "invalid-authorization-header",
                "title": "Invalid Authorization Header",
                "detail": "Authorization header must use Bearer scheme",
                "status": 401
            },
            headers={"Content-Type": "application/problem+json"}
        )

    # Parse Bearer token
    parts = auth_header.split()

    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "invalid-authorization-header",
                "title": "Invalid Authorization Header",
                "detail": "Authorization header must be in format: Bearer <token>",
                "status": 401
            },
            headers={"Content-Type": "application/problem+json"}
        )

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "invalid-authorization-header",
                "title": "Invalid Authorization Header",
                "detail": "Authorization header must use Bearer scheme",
                "status": 401
            },
            headers={"Content-Type": "application/problem+json"}
        )

    if not token or token.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "invalid-authorization-header",
                "title": "Invalid Authorization Header",
                "detail": "Token cannot be empty",
                "status": 401
            },
            headers={"Content-Type": "application/problem+json"}
        )

    # Decode and validate token
    payload, error_type = decode_access_token(token)

    if payload is None:
        # T064: Log token rejection events
        log_security_event(
            event_type="token_rejected",
            user_id=None,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={
                "error_type": error_type,
                "endpoint": str(request.url.path)
            }
        )

        # Provide specific error messages based on error type
        if error_type == "malformed-token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "malformed-token",
                    "title": "Malformed Token",
                    "detail": "Token has invalid format or structure",
                    "status": 401
                },
                headers={"Content-Type": "application/problem+json"}
            )
        elif error_type == "expired-token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "expired-token",
                    "title": "Expired Token",
                    "detail": "Token has expired",
                    "status": 401
                },
                headers={"Content-Type": "application/problem+json"}
            )
        elif error_type == "invalid-signature":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "invalid-signature",
                    "title": "Invalid Signature",
                    "detail": "Token signature verification failed",
                    "status": 401
                },
                headers={"Content-Type": "application/problem+json"}
            )
        else:
            # Generic invalid token error
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "invalid-token",
                    "title": "Invalid Token",
                    "detail": "Token is invalid",
                    "status": 401
                },
                headers={"Content-Type": "application/problem+json"}
            )

    # Extract user_id from token payload
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "invalid-token",
                "title": "Invalid Token",
                "detail": "Token missing user identifier",
                "status": 401
            },
            headers={"Content-Type": "application/problem+json"}
        )

    try:
        user_id = UUID(user_id_str)
        return user_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "type": "invalid-token",
                "title": "Invalid Token",
                "detail": "Token contains invalid user identifier",
                "status": 401
            },
            headers={"Content-Type": "application/problem+json"}
        )


async def verify_user_access(
    user_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user)]
) -> UUID:
    """
    Dependency to verify that the authenticated user can access the requested resource.

    Ensures that the user_id from the JWT token matches the user_id in the URL path.
    This enforces user isolation - users can only access their own resources.

    Args:
        user_id: User ID from the URL path parameter
        current_user_id: User ID extracted from JWT token

    Returns:
        UUID: The user_id if access is granted

    Raises:
        HTTPException: 403 if user_id from token doesn't match path user_id
    """
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "access-denied",
                "title": "Access Denied",
                "detail": "You do not have permission to access this resource",
                "status": 403
            },
            headers={"Content-Type": "application/problem+json"}
        )

    return user_id
