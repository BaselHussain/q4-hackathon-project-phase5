# Quickstart Guide: Authentication & User Management

**Feature**: 002-auth-user-management
**Date**: 2026-01-22
**Purpose**: Quick setup and testing guide for authentication implementation

## Prerequisites

- Python 3.11+ installed
- PostgreSQL database (Neon Serverless) configured
- Git repository cloned
- Virtual environment tool (venv or virtualenv)

## Setup Steps

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**New Dependencies Added**:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `email-validator` - Email validation
- `slowapi` - Rate limiting
- `python-multipart` - Form data parsing

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and set required variables
```

**Required Environment Variables**:

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:password@host/database
BETTER_AUTH_SECRET=your-32-character-secret-key-here-change-this
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
```

**Generate Secure Secret**:
```bash
# Generate a secure 32-character secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

⚠️ **Security Warning**: Never commit `.env` file to version control!

### 3. Run Database Migrations

```bash
# Apply migrations to create users table
alembic upgrade head

# Verify migration
alembic current
# Should show: 002 (head)
```

**What This Does**:
- Creates `users` table with email, password_hash, timestamps
- Adds `user_id` foreign key to `tasks` table
- Creates indexes for performance

### 4. Start Development Server

```bash
# Start FastAPI server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# http://localhost:8000
```

**Verify Server is Running**:
```bash
curl http://localhost:8000/docs
# Should return Swagger UI HTML
```

## Quick Test Workflow

### Step 1: Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response** (201 Created):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "alice@example.com",
  "message": "User registered successfully"
}
```

**Save the `user_id` for next steps!**

### Step 2: Login to Get JWT Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Save the `access_token` for next steps!**

### Step 3: Create a Task (Authenticated)

```bash
# Set variables from previous steps
TOKEN="<your_access_token_here>"
USER_ID="<your_user_id_here>"

curl -X POST http://localhost:8000/api/${USER_ID}/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "My First Task",
    "description": "Testing authentication"
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "title": "My First Task",
  "description": "Testing authentication",
  "status": "pending",
  "created_at": "2026-01-22T10:00:00Z",
  "updated_at": "2026-01-22T10:00:00Z"
}
```

### Step 4: Get All Tasks (Authenticated)

```bash
curl -X GET http://localhost:8000/api/${USER_ID}/tasks \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected Response** (200 OK):
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "My First Task",
    "description": "Testing authentication",
    "status": "pending",
    "created_at": "2026-01-22T10:00:00Z",
    "updated_at": "2026-01-22T10:00:00Z"
  }
]
```

### Step 5: Test Authorization (Should Fail)

```bash
# Try to access another user's tasks
OTHER_USER_ID="550e8400-e29b-41d4-a716-446655440099"

curl -X GET http://localhost:8000/api/${OTHER_USER_ID}/tasks \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected Response** (403 Forbidden):
```json
{
  "type": "access-denied",
  "title": "Access Denied",
  "status": 403,
  "detail": "You do not have permission to access this resource",
  "instance": "/api/550e8400-e29b-41d4-a716-446655440099/tasks"
}
```

### Step 6: Test Without Token (Should Fail)

```bash
curl -X GET http://localhost:8000/api/${USER_ID}/tasks
```

**Expected Response** (401 Unauthorized):
```json
{
  "type": "invalid-authorization-header",
  "title": "Invalid Authorization Header",
  "status": 401,
  "detail": "Authorization header must use Bearer scheme",
  "instance": "/api/550e8400-e29b-41d4-a716-446655440000/tasks"
}
```

## Testing with Postman

### Import OpenAPI Spec

1. Open Postman
2. Click **Import** → **Link**
3. Enter: `http://localhost:8000/openapi.json`
4. Click **Import**

### Configure Environment

1. Create new environment: "Todo App Local"
2. Add variables:
   - `base_url`: `http://localhost:8000`
   - `token`: (leave empty, will be set after login)
   - `user_id`: (leave empty, will be set after registration)

### Test Workflow

1. **Register User**:
   - Request: POST `{{base_url}}/api/auth/register`
   - Body: `{"email": "test@example.com", "password": "Test123!"}`
   - Save `user_id` from response to environment

2. **Login**:
   - Request: POST `{{base_url}}/api/auth/login`
   - Body: `{"email": "test@example.com", "password": "Test123!"}`
   - Save `access_token` from response to `token` environment variable

3. **Create Task**:
   - Request: POST `{{base_url}}/api/{{user_id}}/tasks`
   - Headers: `Authorization: Bearer {{token}}`
   - Body: `{"title": "Test Task", "description": "Testing"}`

4. **Get Tasks**:
   - Request: GET `{{base_url}}/api/{{user_id}}/tasks`
   - Headers: `Authorization: Bearer {{token}}`

## Common Issues & Solutions

### Issue: "BETTER_AUTH_SECRET not configured"

**Solution**: Set `BETTER_AUTH_SECRET` in `.env` file
```bash
# Generate new secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
echo "BETTER_AUTH_SECRET=<generated_secret>" >> .env
```

### Issue: "Database connection failed"

**Solution**: Verify `DATABASE_URL` in `.env` file
```bash
# Test database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('your_database_url'); print('Connected!')"
```

### Issue: "Email already registered"

**Solution**: Use different email or delete existing user
```sql
-- Delete user from database
DELETE FROM users WHERE email = 'test@example.com';
```

### Issue: "Token expired"

**Solution**: Login again to get new token
```bash
# Tokens expire after 24 hours
# Simply login again to get fresh token
curl -X POST http://localhost:8000/api/auth/login ...
```

### Issue: "Rate limit exceeded"

**Solution**: Wait 60 seconds before retrying
```bash
# Rate limit: 5 login attempts per minute
# Wait for rate limit window to reset
sleep 60
```

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_password.py -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run auth endpoint tests
pytest tests/integration/test_auth_endpoints.py -v

# Run protected endpoint tests
pytest tests/integration/test_protected_endpoints.py -v
```

### All Tests

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

## Development Workflow

### 1. Make Code Changes

```bash
# Edit files in src/
# Example: src/services/auth.py
```

### 2. Run Tests

```bash
# Run relevant tests
pytest tests/unit/test_auth_service.py -v
```

### 3. Test Manually

```bash
# Server auto-reloads with --reload flag
# Test with curl or Postman
```

### 4. Check Logs

```bash
# View security events
tail -f logs/security.log

# View application logs
tail -f logs/app.log
```

## API Documentation

### Interactive Docs (Swagger UI)

```
http://localhost:8000/docs
```

**Features**:
- Try out API endpoints
- View request/response schemas
- Test authentication flow
- See error responses

### Alternative Docs (ReDoc)

```
http://localhost:8000/redoc
```

**Features**:
- Clean, readable documentation
- Better for reference
- Printable format

### OpenAPI Spec (JSON)

```
http://localhost:8000/openapi.json
```

**Use Cases**:
- Import into Postman
- Generate client SDKs
- API contract validation

## Security Checklist

Before deploying to production:

- [ ] Change `BETTER_AUTH_SECRET` to strong random value
- [ ] Enable HTTPS (required for production)
- [ ] Set `LOG_LEVEL=WARNING` or `ERROR` in production
- [ ] Review security event logs regularly
- [ ] Rotate `BETTER_AUTH_SECRET` periodically
- [ ] Backup database regularly
- [ ] Monitor rate limit triggers
- [ ] Test token expiration behavior
- [ ] Verify user isolation enforcement
- [ ] Scan dependencies for vulnerabilities

## Next Steps

1. **Implement Frontend**: Integrate authentication with Next.js frontend
2. **Add Features**: Password reset, email verification, MFA
3. **Enhance Security**: Token revocation, session management
4. **Scale**: Redis rate limiting, read replicas
5. **Monitor**: Set up logging aggregation and alerting

## Useful Commands

```bash
# Check Python version
python --version

# List installed packages
pip list

# Check database migrations
alembic history

# Rollback migration
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "description"

# Format code
black src/

# Lint code
flake8 src/

# Type check
mypy src/
```

## Support & Resources

- **API Documentation**: http://localhost:8000/docs
- **Specification**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Research**: [research.md](./research.md)

## Summary

✅ **Setup Complete** when:
- Dependencies installed
- Environment configured
- Database migrated
- Server running
- Registration works
- Login returns token
- Protected endpoints require auth
- User isolation enforced

**Estimated Setup Time**: 10-15 minutes

**Ready for Development**: Yes, proceed with `/sp.tasks` to generate implementation tasks!
