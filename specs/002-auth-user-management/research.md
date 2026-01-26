# Research: Authentication & User Management

**Feature**: 002-auth-user-management
**Date**: 2026-01-22
**Purpose**: Document technology research and decisions for authentication implementation

## Overview

This document captures research findings and technology decisions for implementing secure user authentication and isolation using Better Auth with JWT tokens in a FastAPI backend.

## Research Areas

### 1. Better Auth Python Integration

**Research Question**: How to integrate Better Auth library with FastAPI for JWT token generation and validation?

**Findings**:

After researching Better Auth, it appears Better Auth is primarily a JavaScript/TypeScript library designed for Next.js and Node.js environments. There is no official Python adapter for Better Auth.

**Decision**: Use python-jose for JWT handling instead of Better Auth Python adapter

**Rationale**:
- Better Auth is a JavaScript library without Python support
- python-jose is the industry-standard JWT library for Python
- python-jose integrates seamlessly with FastAPI
- Provides all required JWT functionality (signing, verification, claims)
- Well-documented and actively maintained

**Implementation Approach**:
- Use python-jose[cryptography] for JWT token operations
- Implement custom JWT token generation in auth service
- Create FastAPI dependency for token validation
- Share BETTER_AUTH_SECRET between frontend (Better Auth) and backend (python-jose)
- Both systems use same secret for signing/verification

**Alternative Considered**: PyJWT
- Also a valid option, but python-jose is more commonly used with FastAPI
- python-jose has better integration examples in FastAPI documentation

### 2. JWT Token Strategy

**Research Question**: What JWT token structure and claims should be used for user authentication?

**Findings**:

**Standard JWT Claims** (RFC 7519):
- `iss` (issuer): Identifies who issued the token
- `sub` (subject): User identifier (user_id)
- `exp` (expiration): Token expiration timestamp
- `iat` (issued at): Token creation timestamp
- `nbf` (not before): Token validity start time (optional)

**Custom Claims for This Application**:
- `user_id`: UUID of authenticated user
- `email`: User's email address (for display/logging)

**Decision**: Use HS256 algorithm with standard + custom claims

**Token Structure**:
```json
{
  "iss": "todo-app-backend",
  "sub": "<user_id>",
  "exp": <timestamp>,
  "iat": <timestamp>,
  "user_id": "<user_id>",
  "email": "user@example.com"
}
```

**Rationale**:
- HS256 (HMAC with SHA-256) is symmetric and suitable for shared secret
- Standard claims provide interoperability and best practices
- Custom claims provide convenient access to user data
- 24-hour expiration balances security and UX

**Token Signing Algorithm Comparison**:

| Algorithm | Type | Key Management | Performance | Use Case |
|-----------|------|----------------|-------------|----------|
| HS256 | Symmetric | Single shared secret | Fast | Single backend, shared secret model |
| RS256 | Asymmetric | Public/private key pair | Slower | Multiple services, public verification |

**Chosen**: HS256 - Simpler key management, sufficient for single backend architecture

### 3. Password Security

**Research Question**: What password hashing algorithm and validation rules should be used?

**Findings**:

**Password Hashing Algorithms**:

| Algorithm | Strength | Speed | Memory | Recommendation |
|-----------|----------|-------|--------|----------------|
| bcrypt | High | Slow (good) | Low | Industry standard, proven |
| argon2 | Very High | Configurable | High | Modern, winner of PHC |
| scrypt | High | Slow | High | Good but less common |
| PBKDF2 | Medium | Fast (bad) | Low | Older, less secure |

**Decision**: Use bcrypt via passlib[bcrypt]

**Rationale**:
- Constitution explicitly requires bcrypt
- Industry-proven security track record
- Automatic salt generation and storage
- Configurable work factor (cost)
- Wide library support and documentation

**Password Validation Rules** (from spec):
- Minimum length: 8 characters
- Maximum length: 128 characters
- Must contain: uppercase, lowercase, number, special character
- Email max: 254 characters (RFC 5321)

**Implementation**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed)
```

**Bcrypt Work Factor**: Use default (12 rounds)
- Provides good balance between security and performance
- Takes ~0.3 seconds to hash (acceptable for login/registration)
- Automatically increases over time as hardware improves

### 4. Rate Limiting Implementation

**Research Question**: How to implement IP-based rate limiting for login attempts?

**Findings**:

**Rate Limiting Libraries for FastAPI**:

| Library | Storage | Complexity | Features |
|---------|---------|------------|----------|
| slowapi | In-memory | Low | Simple, FastAPI-specific |
| fastapi-limiter | Redis | Medium | Distributed, scalable |
| Custom middleware | Configurable | High | Full control |

**Decision**: Use slowapi with in-memory storage

**Rationale**:
- Simplest implementation for MVP
- No additional infrastructure (Redis) required
- Sufficient for 100 concurrent users
- Easy to upgrade to Redis later if needed
- FastAPI-native integration

**Rate Limit Configuration**:
- Limit: 5 requests per minute per IP address
- Scope: Login endpoint only
- Response: 429 Too Many Requests with Retry-After header
- Storage: In-memory dictionary (acceptable for single instance)

**Implementation**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

**Limitations**:
- In-memory storage doesn't work across multiple server instances
- Rate limit resets on server restart
- No persistent tracking of repeat offenders

**Future Enhancement**: Migrate to Redis-based rate limiting for production scale

### 5. Security Event Logging

**Research Question**: What security events should be logged and in what format?

**Findings**:

**Security Events to Log** (from clarifications):
- Failed login attempts (with email, IP, timestamp)
- Token rejections (invalid, expired, malformed)
- Rate limit triggers (IP, endpoint, timestamp)
- Successful registrations (email, timestamp)

**Logging Best Practices**:
- Use structured logging (JSON format)
- Include correlation IDs for request tracking
- Sanitize sensitive data (no passwords, full tokens)
- Log at appropriate levels (INFO, WARNING, ERROR)
- Include context (IP, user agent, endpoint)

**Decision**: Use Python's built-in logging with structured format

**Log Format**:
```json
{
  "timestamp": "2026-01-22T10:30:00Z",
  "level": "WARNING",
  "event": "failed_login",
  "email": "user@example.com",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "reason": "invalid_password"
}
```

**Implementation**:
```python
import logging
import json

logger = logging.getLogger("security")

def log_security_event(event_type, **kwargs):
    logger.warning(json.dumps({
        "event": event_type,
        **kwargs
    }))
```

**What NOT to Log**:
- Plain text passwords
- Full JWT tokens (log only first 10 chars)
- Password hashes
- Full credit card numbers (if added later)

**Log Levels**:
- INFO: Successful registrations, successful logins
- WARNING: Failed login attempts, rate limit triggers
- ERROR: Token validation errors, system errors

### 6. Email Validation

**Research Question**: How to implement RFC 5322 email validation?

**Findings**:

**Email Validation Approaches**:

| Approach | Accuracy | Complexity | Recommendation |
|----------|----------|------------|----------------|
| Regex | Low | High | Not recommended |
| email-validator | High | Low | Recommended |
| DNS MX check | Very High | Medium | Overkill for MVP |

**Decision**: Use email-validator library

**Rationale**:
- RFC 5322 compliant (per clarifications)
- Handles edge cases correctly
- Simple API
- Well-maintained library
- No external dependencies

**Implementation**:
```python
from email_validator import validate_email, EmailNotValidError

def validate_email_address(email: str) -> str:
    try:
        # Validate and normalize
        valid = validate_email(email, check_deliverability=False)
        return valid.email.lower()  # Store lowercase
    except EmailNotValidError as e:
        raise ValueError(str(e))
```

**Validation Rules**:
- Format: local@domain
- Max length: 254 characters (RFC 5321)
- Case-insensitive (store lowercase)
- No DNS verification (check_deliverability=False)

### 7. Error Response Format

**Research Question**: How to implement RFC 7807 Problem Details format?

**Findings**:

**RFC 7807 Structure**:
```json
{
  "type": "https://example.com/errors/invalid-credentials",
  "title": "Invalid Credentials",
  "status": 401,
  "detail": "The email or password provided is incorrect",
  "instance": "/api/auth/login"
}
```

**Decision**: Create custom exception classes with RFC 7807 handler

**Implementation Approach**:
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class AuthException(HTTPException):
    def __init__(self, status_code, error_type, title, detail):
        self.status_code = status_code
        self.error_type = error_type
        self.title = title
        self.detail = detail

@app.exception_handler(AuthException)
async def auth_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": exc.error_type,
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path)
        }
    )
```

**Error Types** (from spec):
- `email-already-registered` (400)
- `invalid-email-format` (400)
- `invalid-password` (400)
- `invalid-credentials` (401)
- `token-expired` (401)
- `invalid-token` (401)
- `invalid-authorization-header` (401)
- `rate-limit-exceeded` (429)
- `access-denied` (403)

## Technology Stack Summary

### Core Dependencies

```txt
# requirements.txt additions
fastapi==0.109.0
sqlmodel==0.0.14
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
email-validator==2.1.0
slowapi==0.1.9
python-multipart==0.0.6
```

### Development Dependencies

```txt
# requirements-dev.txt additions
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
pytest-cov==4.1.0
```

## Integration Architecture

### Authentication Flow

```
1. User Registration:
   Client → POST /api/auth/register → Validate email → Hash password →
   Store user → Return user_id

2. User Login:
   Client → POST /api/auth/login → Validate credentials →
   Generate JWT (python-jose) → Return token

3. Protected Request:
   Client → GET /api/{user_id}/tasks + Authorization header →
   Middleware extracts token → Validate JWT (python-jose) →
   Extract user_id → Compare with path user_id → Allow/Deny
```

### Database Schema Changes

```sql
-- New users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Update tasks table
ALTER TABLE tasks
ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
```

### Middleware Stack

```
Request → Rate Limiter → JWT Validator → User Extractor →
Authorization Check → Endpoint Handler → Response
```

## Security Considerations

### Threat Model

**Threats Addressed**:
1. ✅ Brute force attacks → Rate limiting (5/min)
2. ✅ Password compromise → bcrypt hashing
3. ✅ Token theft → Short expiration (24h), HTTPS required
4. ✅ User isolation breach → JWT user_id validation
5. ✅ Replay attacks → Token expiration

**Threats NOT Addressed** (out of scope):
1. ❌ Token revocation → No blacklist mechanism
2. ❌ Account takeover → No MFA
3. ❌ Password reset → Out of scope
4. ❌ Session hijacking → No device tracking

### Security Best Practices Applied

1. **Password Storage**: bcrypt with automatic salting
2. **Token Signing**: HS256 with 32+ character secret
3. **Input Validation**: Email (RFC 5322), password complexity
4. **Error Messages**: Generic messages (don't reveal if email exists)
5. **Rate Limiting**: Prevent brute force attacks
6. **Logging**: Security events for monitoring
7. **HTTPS**: Required for production (documented)

## Performance Considerations

### Expected Latencies

| Operation | Target | Expected |
|-----------|--------|----------|
| Registration | <3s | ~0.5s (bcrypt hashing) |
| Login | <2s | ~0.5s (bcrypt verify + JWT gen) |
| Token validation | <50ms | ~5-10ms (JWT verify) |
| Rate limit check | <5ms | ~1ms (in-memory lookup) |

### Optimization Opportunities

1. **Token Validation Caching**: Cache decoded tokens for request duration
2. **Password Hashing**: Use async workers for bcrypt operations
3. **Rate Limiting**: Upgrade to Redis for distributed systems
4. **Database Queries**: Add indexes on email and user_id

## Testing Strategy

### Unit Test Coverage

- Password hashing and verification
- Email validation (valid/invalid formats)
- JWT token generation and parsing
- Rate limiting logic
- User model validation

### Integration Test Scenarios

1. Registration with valid/invalid inputs
2. Login with correct/incorrect credentials
3. Token validation (valid/expired/malformed)
4. User isolation (own tasks vs others)
5. Rate limiting (exceed limit, retry after)
6. Error responses (RFC 7807 format)

### Manual Testing Checklist

- [ ] Register new user successfully
- [ ] Register with duplicate email (400)
- [ ] Register with invalid email format (400)
- [ ] Register with weak password (400)
- [ ] Login with correct credentials (200 + token)
- [ ] Login with wrong password (401)
- [ ] Login with non-existent email (401)
- [ ] Access own tasks with valid token (200)
- [ ] Access other user's tasks (403)
- [ ] Access without token (401)
- [ ] Access with expired token (401)
- [ ] Trigger rate limit (429)

## Open Questions & Future Work

### Resolved Questions

1. ✅ JWT library choice → python-jose
2. ✅ Password hashing → bcrypt via passlib
3. ✅ Rate limiting → slowapi (in-memory)
4. ✅ Email validation → email-validator library
5. ✅ Error format → RFC 7807 custom handler

### Future Enhancements

1. **Token Refresh**: Implement refresh token mechanism
2. **Redis Rate Limiting**: Upgrade for multi-instance deployment
3. **Token Revocation**: Add blacklist/whitelist mechanism
4. **Password Reset**: Email-based password recovery
5. **MFA**: Two-factor authentication support
6. **OAuth**: Social login integration
7. **Session Management**: Track active sessions per user
8. **Audit Trail**: Comprehensive login history

## References

- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices (RFC 8725)](https://tools.ietf.org/html/rfc8725)
- [RFC 7807 Problem Details](https://tools.ietf.org/html/rfc7807)
- [RFC 5322 Email Format](https://tools.ietf.org/html/rfc5322)
- [passlib Documentation](https://passlib.readthedocs.io/)
- [slowapi Documentation](https://slowapi.readthedocs.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetsecurity.org/cheatsheets/authentication-cheat-sheet/)

## Conclusion

All research tasks completed. Technology decisions documented and justified. Ready to proceed with Phase 1 (Design & Contracts) to create data-model.md, contracts/openapi.yaml, and quickstart.md.

**Key Takeaway**: Better Auth is JavaScript-only, so we'll use python-jose for JWT handling in the backend while maintaining compatibility with Better Auth frontend through shared secret.
