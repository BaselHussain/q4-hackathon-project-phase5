# Manual End-to-End Testing Guide

**Feature**: Authentication & User Management (002-auth-user-management)
**Date**: 2026-01-26
**Purpose**: Verify complete authentication flow works correctly in production-like environment

## Prerequisites

1. **Database Setup**
   ```bash
   # Ensure DATABASE_URL is set in .env
   # Run migrations
   cd backend
   alembic upgrade head
   ```

2. **Start Server**
   ```bash
   # From backend directory
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verify Health Check**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status": "healthy", "timestamp": "..."}
   ```

## Test Scenario 1: User Registration

### 1.1 Register Valid User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response (201 Created):**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "testuser@example.com",
  "message": "User registered successfully"
}
```

**Verification:**
- ✅ Status code is 201
- ✅ Response contains user_id (valid UUID)
- ✅ Email matches input (normalized to lowercase)
- ✅ Success message present

### 1.2 Register Duplicate Email

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "AnotherPass456!"
  }'
```

**Expected Response (409 Conflict):**
```json
{
  "type": "email-already-registered",
  "title": "Email Already Registered",
  "status": 409,
  "detail": "An account with this email address already exists",
  "instance": "/api/auth/register"
}
```

**Verification:**
- ✅ Status code is 409
- ✅ RFC 7807 format (type, title, status, detail, instance)
- ✅ Clear error message

### 1.3 Register with Invalid Email

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email",
    "password": "SecurePass123!"
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "type": "invalid-email-format",
  "title": "Invalid Email Format",
  "status": 400,
  "detail": "Invalid email format...",
  "instance": "/api/auth/register"
}
```

**Verification:**
- ✅ Status code is 400
- ✅ Specific error type for email validation

### 1.4 Register with Weak Password

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "weak"
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "type": "invalid-password",
  "title": "Invalid Password",
  "status": 400,
  "detail": "Password must be at least 8 characters long...",
  "instance": "/api/auth/register"
}
```

**Verification:**
- ✅ Status code is 400
- ✅ Detailed password requirements in error message

## Test Scenario 2: User Login

### 2.1 Login with Valid Credentials

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "testuser@example.com"
}
```

**Verification:**
- ✅ Status code is 200
- ✅ access_token is present (JWT format: xxx.yyy.zzz)
- ✅ token_type is "bearer"
- ✅ user_id matches registration
- ✅ Email matches

**Save the access_token for subsequent tests!**

### 2.2 Login with Wrong Password

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "WrongPassword123!"
  }'
```

**Expected Response (401 Unauthorized):**
```json
{
  "type": "invalid-credentials",
  "title": "Invalid Credentials",
  "status": 401,
  "detail": "Invalid email or password",
  "instance": "/api/auth/login"
}
```

**Verification:**
- ✅ Status code is 401
- ✅ Generic error message (doesn't reveal if email exists)
- ✅ Security log entry created (check logs)

### 2.3 Login with Non-existent Email

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nonexistent@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response (401 Unauthorized):**
```json
{
  "type": "invalid-credentials",
  "title": "Invalid Credentials",
  "status": 401,
  "detail": "Invalid email or password",
  "instance": "/api/auth/login"
}
```

**Verification:**
- ✅ Status code is 401
- ✅ Same error message as wrong password (prevents user enumeration)

## Test Scenario 3: Rate Limiting

### 3.1 Trigger Rate Limit

```bash
# Make 6 rapid login attempts (limit is 5/minute)
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "wrong"}' \
    -w "\nStatus: %{http_code}\n\n"
  sleep 1
done
```

**Expected:**
- First 5 attempts: 401 Unauthorized
- 6th attempt: 429 Too Many Requests

**Expected Response (429):**
```json
{
  "type": "rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please try again later.",
  "instance": "/api/auth/login"
}
```

**Verification:**
- ✅ 6th request returns 429
- ✅ Response includes `Retry-After: 60` header
- ✅ Security log entry created

## Test Scenario 4: Authenticated Task Access

### 4.1 Access Tasks with Valid Token

```bash
# Replace {user_id} with actual user_id from login
# Replace {token} with actual access_token from login
curl -X GET http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer {token}"
```

**Expected Response (200 OK):**
```json
{
  "tasks": [],
  "total": 0
}
```

**Verification:**
- ✅ Status code is 200
- ✅ Returns user's tasks (empty for new user)

### 4.2 Create Task with Valid Token

```bash
curl -X POST http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Testing authentication",
    "status": "pending"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "task-uuid",
  "user_id": "user-uuid",
  "title": "Test Task",
  "description": "Testing authentication",
  "status": "pending",
  "created_at": "2026-01-26T...",
  "updated_at": "2026-01-26T..."
}
```

**Verification:**
- ✅ Status code is 201
- ✅ Task created with correct user_id
- ✅ All fields present

### 4.3 Access Tasks Without Token

```bash
curl -X GET http://localhost:8000/api/{user_id}/tasks
```

**Expected Response (401 Unauthorized):**
```json
{
  "type": "invalid-authorization-header",
  "title": "Invalid Authorization Header",
  "status": 401,
  "detail": "Authorization header must use Bearer scheme",
  "instance": "/api/{user_id}/tasks"
}
```

**Verification:**
- ✅ Status code is 401
- ✅ Clear error message about missing token

### 4.4 Access Another User's Tasks (User Isolation)

```bash
# Register second user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user2@example.com",
    "password": "SecurePass456!"
  }'

# Login as second user
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user2@example.com",
    "password": "SecurePass456!"
  }'

# Try to access first user's tasks with second user's token
curl -X GET http://localhost:8000/api/{user1_id}/tasks \
  -H "Authorization: Bearer {user2_token}"
```

**Expected Response (403 Forbidden):**
```json
{
  "type": "access-denied",
  "title": "Access Denied",
  "status": 403,
  "detail": "You do not have permission to access this resource",
  "instance": "/api/{user1_id}/tasks"
}
```

**Verification:**
- ✅ Status code is 403
- ✅ User isolation enforced
- ✅ Cannot access other user's resources

## Test Scenario 5: Token Validation

### 5.1 Access with Expired Token

```bash
# Wait 24+ hours or create token with short expiration for testing
curl -X GET http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer {expired_token}"
```

**Expected Response (401 Unauthorized):**
```json
{
  "type": "expired-token",
  "title": "Expired Token",
  "status": 401,
  "detail": "Token has expired",
  "instance": "/api/{user_id}/tasks"
}
```

**Verification:**
- ✅ Status code is 401
- ✅ Specific error for expired token
- ✅ Security log entry created

### 5.2 Access with Malformed Token

```bash
curl -X GET http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer invalid.token.here"
```

**Expected Response (401 Unauthorized):**
```json
{
  "type": "malformed-token",
  "title": "Malformed Token",
  "status": 401,
  "detail": "Token has invalid format or structure",
  "instance": "/api/{user_id}/tasks"
}
```

**Verification:**
- ✅ Status code is 401
- ✅ Specific error for malformed token

### 5.3 Access with Invalid Signature

```bash
# Use a token signed with different secret
curl -X GET http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
```

**Expected Response (401 Unauthorized):**
```json
{
  "type": "invalid-signature",
  "title": "Invalid Signature",
  "status": 401,
  "detail": "Token signature verification failed",
  "instance": "/api/{user_id}/tasks"
}
```

**Verification:**
- ✅ Status code is 401
- ✅ Signature validation working

## Test Scenario 6: Security Logging

### 6.1 Verify Security Logs

Check application logs for security events:

```bash
# View recent logs (adjust path to your log file)
tail -f /path/to/logs/app.log | grep -i "security"
```

**Expected Log Entries (JSON format):**

1. **Failed Login:**
```json
{
  "timestamp": "2026-01-26T...",
  "event_type": "failed_login",
  "user_id": null,
  "ip_address": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "details": {
    "email": "testuser@example.com",
    "reason": "invalid_password"
  }
}
```

2. **Token Rejected:**
```json
{
  "timestamp": "2026-01-26T...",
  "event_type": "token_rejected",
  "user_id": null,
  "ip_address": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "details": {
    "error_type": "expired-token",
    "endpoint": "/api/{user_id}/tasks"
  }
}
```

3. **Rate Limit Exceeded:**
```json
{
  "timestamp": "2026-01-26T...",
  "event_type": "rate_limit_exceeded",
  "user_id": null,
  "ip_address": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "details": {
    "endpoint": "/api/auth/login",
    "limit": "5/minute"
  }
}
```

**Verification:**
- ✅ All security events logged
- ✅ Structured JSON format
- ✅ No sensitive data (passwords, full tokens) in logs
- ✅ Timestamps in ISO 8601 format

## Test Scenario 7: OpenAPI Documentation

### 7.1 Access Swagger UI

1. Open browser: http://localhost:8000/docs
2. Verify authentication section is present
3. Click "Authorize" button
4. Enter JWT token from login
5. Try executing protected endpoints

**Verification:**
- ✅ Swagger UI loads correctly
- ✅ Authentication endpoints documented
- ✅ Bearer token authentication scheme visible
- ✅ Can test endpoints interactively

### 7.2 Access ReDoc

1. Open browser: http://localhost:8000/redoc
2. Verify comprehensive documentation
3. Check authentication flow examples

**Verification:**
- ✅ ReDoc loads correctly
- ✅ Authentication flow documented
- ✅ Example requests/responses present

## Test Results Summary

| Test Scenario | Status | Notes |
|--------------|--------|-------|
| 1.1 Register Valid User | ⬜ | |
| 1.2 Register Duplicate Email | ⬜ | |
| 1.3 Register Invalid Email | ⬜ | |
| 1.4 Register Weak Password | ⬜ | |
| 2.1 Login Valid Credentials | ⬜ | |
| 2.2 Login Wrong Password | ⬜ | |
| 2.3 Login Non-existent Email | ⬜ | |
| 3.1 Rate Limiting | ⬜ | |
| 4.1 Access Tasks with Token | ⬜ | |
| 4.2 Create Task with Token | ⬜ | |
| 4.3 Access Without Token | ⬜ | |
| 4.4 User Isolation | ⬜ | |
| 5.1 Expired Token | ⬜ | |
| 5.2 Malformed Token | ⬜ | |
| 5.3 Invalid Signature | ⬜ | |
| 6.1 Security Logging | ⬜ | |
| 7.1 Swagger UI | ⬜ | |
| 7.2 ReDoc | ⬜ | |

**Legend:** ✅ Pass | ❌ Fail | ⬜ Not Tested

## Common Issues and Troubleshooting

### Issue: Database Connection Error

**Symptom:** `asyncpg.exceptions.InvalidCatalogNameError`

**Solution:**
1. Verify DATABASE_URL in .env
2. Ensure database exists
3. Run migrations: `alembic upgrade head`

### Issue: Token Validation Fails

**Symptom:** All tokens return 401

**Solution:**
1. Verify BETTER_AUTH_SECRET is set and matches
2. Check secret is at least 32 characters
3. Restart server after changing .env

### Issue: Rate Limiting Not Working

**Symptom:** Can make unlimited requests

**Solution:**
1. Check RATE_LIMIT_ENABLED=true in .env
2. Verify slowapi is installed
3. Check rate limiter is attached to app.state

## Conclusion

After completing all test scenarios:

1. **Mark all checkboxes** in Test Results Summary
2. **Document any failures** with details
3. **Verify all acceptance criteria** from spec.md
4. **Sign off** on manual testing completion

**Tester Signature:** ________________
**Date:** ________________
**Overall Result:** ⬜ PASS | ⬜ FAIL
