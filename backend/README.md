# Task Management API - Backend

RESTful API for managing user tasks with authentication, built with FastAPI and Neon PostgreSQL.

## Features

- **User Authentication**: JWT token-based authentication with Better Auth integration
- **User Registration**: Secure account creation with email validation and password hashing
- **User Login**: Credential verification with rate limiting
- **Task Management**: CRUD operations for user tasks with isolation
- **Security**: Bcrypt password hashing, JWT tokens, rate limiting, security logging
- **Database**: Neon Serverless PostgreSQL with async support

## Technology Stack

- **Framework**: FastAPI 0.109+
- **ORM**: SQLModel 0.0.14+
- **Database**: Neon Serverless PostgreSQL (asyncpg 0.29+)
- **Authentication**: JWT tokens (python-jose), Bcrypt (passlib)
- **Validation**: Pydantic 2.5+, email-validator
- **Rate Limiting**: slowapi
- **Server**: uvicorn 0.27+

## Prerequisites

- Python 3.11+
- Neon PostgreSQL database (or compatible PostgreSQL)
- pip or uv package manager

## Setup Instructions

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host/database

# Authentication Configuration (REQUIRED)
BETTER_AUTH_SECRET=your-secret-key-here-min-32-chars

# Optional Configuration
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
```

#### Generating a Secure BETTER_AUTH_SECRET

The `BETTER_AUTH_SECRET` is used to sign JWT tokens and **must be at least 32 characters long**.

**Option 1: Using Python**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option 2: Using OpenSSL**
```bash
openssl rand -base64 32
```

**Option 3: Using /dev/urandom (Linux/Mac)**
```bash
head -c 32 /dev/urandom | base64
```

Copy the generated secret and set it in your `.env` file:
```bash
BETTER_AUTH_SECRET=your-generated-secret-here
```

**IMPORTANT**:
- Never commit your `.env` file to version control
- Use different secrets for development, staging, and production
- Rotate secrets periodically for security

### 3. Set Up Database

#### Run Migrations

The application uses Alembic for database migrations. Run the following command to create the required tables (users, tasks):

```bash
# Navigate to backend directory
cd backend

# Run all migrations
alembic upgrade head
```

This will create:
- `users` table (id, email, password_hash, created_at, last_login_at)
- `tasks` table (id, user_id, title, description, status, created_at, updated_at)

#### Verify Database Setup

```bash
# Check current migration version
alembic current

# View migration history
alembic history
```

### 4. Start the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: `http://localhost:8000`

### 5. Access API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing Authentication Endpoints

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response (201 Created):**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "message": "User registered successfully"
}
```

**Password Requirements:**
- Minimum 8 characters
- Maximum 128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### 2. Login with Credentials

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com"
}
```

**Note**: Save the `access_token` for authenticated requests.

### 3. Access Protected Endpoints

Use the JWT token in the `Authorization` header:

```bash
# Get user's tasks
curl -X GET http://localhost:8000/api/123e4567-e89b-12d3-a456-426614174000/tasks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Create a new task
curl -X POST http://localhost:8000/api/123e4567-e89b-12d3-a456-426614174000/tasks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project",
    "description": "Finish authentication implementation",
    "status": "pending"
  }'
```

### 4. Test Rate Limiting

The login endpoint is rate-limited to 5 requests per minute per IP address:

```bash
# Make 6 rapid login attempts
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "wrong"}' \
    -w "\nStatus: %{http_code}\n\n"
done
```

The 6th request should return `429 Too Many Requests` with a `Retry-After: 60` header.

## Error Handling

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "invalid-credentials",
  "title": "Invalid Credentials",
  "status": 401,
  "detail": "Invalid email or password",
  "instance": "/api/auth/login"
}
```

### Common Error Types

| Status | Type | Description |
|--------|------|-------------|
| 400 | `invalid-email-format` | Email doesn't match RFC 5322 format |
| 400 | `invalid-password` | Password doesn't meet complexity requirements |
| 401 | `invalid-credentials` | Wrong email or password (generic for security) |
| 401 | `expired-token` | JWT token has expired |
| 401 | `invalid-token` | JWT token is malformed or invalid |
| 403 | `access-denied` | User trying to access another user's resources |
| 409 | `email-already-registered` | Email already exists in database |
| 429 | `rate-limit-exceeded` | Too many requests, retry after 60 seconds |

## Security Features

### Password Security
- **Hashing**: Bcrypt with automatic salt generation
- **Validation**: Enforces complexity requirements (uppercase, lowercase, digit, special char)
- **Storage**: Only password hashes stored, never plain text

### JWT Tokens
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 24 hours (configurable)
- **Claims**: Standard JWT claims (sub, exp, iat)
- **Validation**: Signature verification on every request

### Rate Limiting
- **Login Endpoint**: 5 requests per minute per IP
- **Protection**: Prevents brute force attacks
- **Response**: RFC 7807 error with `Retry-After` header

### Security Logging
All security events are logged in structured JSON format:
- Failed login attempts (with email and reason)
- Token rejection events (with error type)
- Rate limit violations (with endpoint and IP)

**Note**: Logs never contain sensitive data (passwords, full tokens, etc.)

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest backend/tests/unit/ -v

# Run specific test file
pytest backend/tests/unit/test_password.py -v

# Run with coverage
pytest backend/tests/unit/ -v --cov=backend/src
```

### Integration Tests

```bash
# Run all integration tests
pytest backend/tests/integration/ -v

# Run authentication tests only
pytest backend/tests/integration/test_auth_endpoints.py -v

# Run protected endpoint tests
pytest backend/tests/integration/test_protected_endpoints.py -v
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=backend/src --cov-report=html --cov-report=term

# View report
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

## Troubleshooting

### Database Connection Issues

**Error**: `asyncpg.exceptions.InvalidCatalogNameError: database "..." does not exist`

**Solution**: Create the database first:
```bash
# Using psql
psql -h your-host -U your-user -c "CREATE DATABASE your_database;"
```

### Migration Issues

**Error**: `alembic.util.exc.CommandError: Can't locate revision identified by '...'`

**Solution**: Reset migrations (development only):
```bash
# Drop all tables
alembic downgrade base

# Re-run migrations
alembic upgrade head
```

### Authentication Issues

**Error**: `401 Unauthorized` on protected endpoints

**Solution**:
1. Verify token is included in `Authorization: Bearer <token>` header
2. Check token hasn't expired (24 hour lifetime)
3. Ensure `BETTER_AUTH_SECRET` matches between token creation and validation

**Error**: `ValueError: Secret key must be at least 32 characters`

**Solution**: Generate a new secret key (see "Generating a Secure BETTER_AUTH_SECRET" above)

### Rate Limiting Issues

**Error**: `429 Too Many Requests` on login

**Solution**: Wait 60 seconds or disable rate limiting in development:
```bash
# In .env file
RATE_LIMIT_ENABLED=false
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   └── versions/         # Migration files
├── src/
│   ├── api/              # API endpoints
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── dependencies.py  # Auth dependencies
│   │   └── schemas/      # Pydantic models
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration
│   │   └── security.py   # JWT and security utilities
│   ├── middleware/       # Middleware
│   │   └── logging.py    # Security logging
│   ├── models/           # Database models
│   │   ├── user.py       # User model
│   │   └── task.py       # Task model
│   └── services/         # Business logic
│       ├── password.py   # Password hashing/validation
│       └── email_validator.py  # Email validation
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── main.py               # FastAPI application
├── database.py           # Database connection
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in git)
└── README.md             # This file
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login and get JWT token | No |

### Tasks

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/{user_id}/tasks` | Get all user tasks | Yes |
| POST | `/api/{user_id}/tasks` | Create new task | Yes |
| GET | `/api/{user_id}/tasks/{task_id}` | Get specific task | Yes |
| PUT | `/api/{user_id}/tasks/{task_id}` | Update task | Yes |
| DELETE | `/api/{user_id}/tasks/{task_id}` | Delete task | Yes |

### Health Check

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | API health status | No |

## Contributing

1. Follow the existing code style and structure
2. Write tests for new features
3. Update documentation for API changes
4. Ensure all tests pass before submitting PR

## License

[Your License Here]

## Support

For issues and questions, please open an issue on the project repository.
