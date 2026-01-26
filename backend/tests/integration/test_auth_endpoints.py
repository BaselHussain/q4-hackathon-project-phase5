"""
Integration tests for authentication endpoints.

Tests the registration and login endpoints with various scenarios including
success cases, validation errors, and edge cases.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class TestRegistrationEndpoint:
    """Integration tests for POST /api/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, db: AsyncSession):
        """
        Test successful user registration with valid email and password.

        Expected: 201 Created with user_id, email, and success message.
        """
        # Arrange
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        }

        # Act
        response = await client.post("/api/auth/register", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "user_id" in data
        assert "email" in data
        assert "message" in data

        # Verify response values
        assert data["email"] == "newuser@example.com"
        assert data["message"] == "User registered successfully"

        # Verify user was created in database
        result = await db.execute(
            select(User).where(User.email == "newuser@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.password_hash is not None
        assert user.password_hash != "SecurePass123!"  # Password should be hashed

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, db: AsyncSession):
        """
        Test registration with email that already exists.

        Expected: 409 Conflict with RFC 7807 error response.
        """
        # Arrange - Create first user
        first_payload = {
            "email": "duplicate@example.com",
            "password": "FirstPass123!"
        }
        await client.post("/api/auth/register", json=first_payload)

        # Act - Try to register with same email
        second_payload = {
            "email": "duplicate@example.com",
            "password": "SecondPass456!"
        }
        response = await client.post("/api/auth/register", json=second_payload)

        # Assert
        assert response.status_code == 409
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "email-already-registered"
        assert error["title"] == "Email Already Registered"
        assert error["status"] == 409
        assert "already exists" in error["detail"].lower()
        assert error["instance"] == "/api/auth/register"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """
        Test registration with invalid email format.

        Expected: 400 Bad Request with RFC 7807 error response.
        """
        # Arrange
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "spaces in@email.com",
            "double@@domain.com"
        ]

        for invalid_email in invalid_emails:
            # Act
            payload = {
                "email": invalid_email,
                "password": "ValidPass123!"
            }
            response = await client.post("/api/auth/register", json=payload)

            # Assert
            assert response.status_code == 400, f"Failed for email: {invalid_email}"
            assert response.headers["content-type"] == "application/problem+json"

            error = response.json()
            assert error["type"] == "invalid-email-format"
            assert error["title"] == "Invalid Email Format"
            assert error["status"] == 400
            assert error["instance"] == "/api/auth/register"

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """
        Test registration with passwords that fail complexity requirements.

        Expected: 400 Bad Request with RFC 7807 error response.
        """
        # Arrange - Test various weak passwords
        weak_passwords = [
            ("short", "too short"),
            ("nouppercase123!", "no uppercase"),
            ("NOLOWERCASE123!", "no lowercase"),
            ("NoNumbers!", "no numbers"),
            ("NoSpecialChar123", "no special character"),
            ("a" * 129, "too long")
        ]

        for password, reason in weak_passwords:
            # Act
            payload = {
                "email": f"test_{reason.replace(' ', '_')}@example.com",
                "password": password
            }
            response = await client.post("/api/auth/register", json=payload)

            # Assert
            assert response.status_code == 400, f"Failed for password ({reason}): {password}"
            assert response.headers["content-type"] == "application/problem+json"

            error = response.json()
            assert error["type"] == "invalid-password"
            assert error["title"] == "Invalid Password"
            assert error["status"] == 400
            assert error["instance"] == "/api/auth/register"

    @pytest.mark.asyncio
    async def test_register_email_case_insensitive(self, client: AsyncClient, db: AsyncSession):
        """
        Test that email registration is case-insensitive.

        Expected: Email stored in lowercase, duplicate detection works regardless of case.
        """
        # Arrange & Act - Register with mixed case email
        payload = {
            "email": "MixedCase@Example.COM",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/auth/register", json=payload)

        # Assert - Email stored in lowercase
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "mixedcase@example.com"

        # Verify in database
        result = await db.execute(
            select(User).where(User.email == "mixedcase@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "mixedcase@example.com"

        # Act - Try to register with different case
        payload2 = {
            "email": "mixedcase@EXAMPLE.com",
            "password": "AnotherPass456!"
        }
        response2 = await client.post("/api/auth/register", json=payload2)

        # Assert - Should be rejected as duplicate
        assert response2.status_code == 409

    @pytest.mark.asyncio
    async def test_register_email_too_long(self, client: AsyncClient):
        """
        Test registration with email exceeding 254 character limit.

        Expected: 400 Bad Request with validation error.
        """
        # Arrange - Create email longer than 254 characters
        long_email = "a" * 250 + "@example.com"  # 263 characters

        payload = {
            "email": long_email,
            "password": "ValidPass123!"
        }

        # Act
        response = await client.post("/api/auth/register", json=payload)

        # Assert
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["status"] == 400
        assert "254" in error["detail"]  # Should mention the limit


class TestLoginEndpoint:
    """Integration tests for POST /api/auth/login endpoint (T032)."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db: AsyncSession):
        """
        Test successful login with valid credentials.

        Expected: 200 OK with access_token, token_type, user_id, and email.
        """
        # Arrange - Register a user first
        register_payload = {
            "email": "loginuser@example.com",
            "password": "SecurePass123!"
        }
        await client.post("/api/auth/register", json=register_payload)

        # Act - Login with correct credentials
        login_payload = {
            "email": "loginuser@example.com",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert "email" in data

        # Verify response values
        assert data["token_type"] == "bearer"
        assert data["email"] == "loginuser@example.com"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

        # Verify last_login_at was updated in database
        result = await db.execute(
            select(User).where(User.email == "loginuser@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """
        Test login with incorrect password.

        Expected: 401 Unauthorized with generic "Invalid credentials" error.
        """
        # Arrange - Register a user first
        register_payload = {
            "email": "wrongpass@example.com",
            "password": "CorrectPass123!"
        }
        await client.post("/api/auth/register", json=register_payload)

        # Act - Login with wrong password
        login_payload = {
            "email": "wrongpass@example.com",
            "password": "WrongPassword456!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-credentials"
        assert error["title"] == "Invalid Credentials"
        assert error["status"] == 401
        assert error["detail"] == "Invalid email or password"
        assert error["instance"] == "/api/auth/login"

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        """
        Test login with email that doesn't exist.

        Expected: 401 Unauthorized with same generic error as wrong password.
        """
        # Act - Login with non-existent email
        login_payload = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert - Same error as wrong password (security best practice)
        assert response.status_code == 401
        assert response.headers["content-type"] == "application/problem+json"

        error = response.json()
        assert error["type"] == "invalid-credentials"
        assert error["title"] == "Invalid Credentials"
        assert error["status"] == 401
        assert error["detail"] == "Invalid email or password"
        assert error["instance"] == "/api/auth/login"

    @pytest.mark.asyncio
    async def test_login_case_insensitive_email(self, client: AsyncClient):
        """
        Test that login is case-insensitive for email.

        Expected: Login succeeds with different case variations of email.
        """
        # Arrange - Register with lowercase email
        register_payload = {
            "email": "casetest@example.com",
            "password": "SecurePass123!"
        }
        await client.post("/api/auth/register", json=register_payload)

        # Act - Login with uppercase email
        login_payload = {
            "email": "CASETEST@EXAMPLE.COM",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "casetest@example.com"  # Normalized to lowercase

    @pytest.mark.asyncio
    async def test_login_updates_last_login_timestamp(self, client: AsyncClient, db: AsyncSession):
        """
        Test that last_login_at timestamp is updated on successful login.

        Expected: last_login_at is set to current time after login.
        """
        # Arrange - Register a user
        register_payload = {
            "email": "timestamp@example.com",
            "password": "SecurePass123!"
        }
        await client.post("/api/auth/register", json=register_payload)

        # Get initial last_login_at (should be None)
        result = await db.execute(
            select(User).where(User.email == "timestamp@example.com")
        )
        user_before = result.scalar_one_or_none()
        assert user_before.last_login_at is None

        # Act - Login
        login_payload = {
            "email": "timestamp@example.com",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 200

        # Verify last_login_at was updated
        await db.refresh(user_before)
        assert user_before.last_login_at is not None

    @pytest.mark.asyncio
    async def test_login_returns_valid_jwt_token(self, client: AsyncClient):
        """
        Test that login returns a valid JWT token that can be decoded.

        Expected: Token can be decoded and contains correct user_id.
        """
        # Arrange - Register a user
        register_payload = {
            "email": "jwttest@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_payload)
        registered_user_id = register_response.json()["user_id"]

        # Act - Login
        login_payload = {
            "email": "jwttest@example.com",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify token can be decoded
        from src.core.security import decode_access_token
        token = data["access_token"]
        payload, error_type = decode_access_token(token)

        assert payload is not None
        assert error_type is None
        assert payload["sub"] == registered_user_id
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_login_missing_email(self, client: AsyncClient):
        """
        Test login with missing email field.

        Expected: 422 Unprocessable Entity (Pydantic validation error).
        """
        # Act - Login without email
        login_payload = {
            "password": "SecurePass123!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client: AsyncClient):
        """
        Test login with missing password field.

        Expected: 422 Unprocessable Entity (Pydantic validation error).
        """
        # Act - Login without password
        login_payload = {
            "email": "test@example.com"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_empty_email(self, client: AsyncClient):
        """
        Test login with empty email string.

        Expected: 401 Unauthorized with invalid credentials error.
        """
        # Act - Login with empty email
        login_payload = {
            "email": "",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_empty_password(self, client: AsyncClient):
        """
        Test login with empty password string.

        Expected: 401 Unauthorized with invalid credentials error.
        """
        # Arrange - Register a user
        register_payload = {
            "email": "emptypass@example.com",
            "password": "SecurePass123!"
        }
        await client.post("/api/auth/register", json=register_payload)

        # Act - Login with empty password
        login_payload = {
            "email": "emptypass@example.com",
            "password": ""
        }
        response = await client.post("/api/auth/login", json=login_payload)

        # Assert
        assert response.status_code == 401
