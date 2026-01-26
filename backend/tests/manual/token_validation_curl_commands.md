# Manual Testing: Token Validation Edge Cases

This document provides curl commands for manually testing JWT token validation edge cases.

## Prerequisites

1. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

2. Set environment variables:
```bash
# Get the BETTER_AUTH_SECRET from your .env file
export BETTER_AUTH_SECRET="your-secret-here"
```

## Test Setup: Create a Test User

First, register a test user and get a valid token:

```bash
# Register a test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Login to get a valid token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Save the returned access_token and user_id for the tests below
```

## Test 1: Malformed Token

Test with tokens that have invalid JWT format:

```bash
# Token with invalid base64 encoding
curl -X GET http://localhost:8000/api/{USER_ID}/tasks \
  -H "Authorization: Bearer not.a.jwt.token" \
  -v

# Expected Response:
# HTTP/1.1 401 Unauthorized
# Content-Type: application/problem+json
# {
#   "type": "malformed-token",
#   "title": "Malformed Token",
#   "status": 401,
#   "detail": "Token has invalid format or structure"
# }
```

```bash
# Token with invalid payload
curl -X GET http://localhost:8000/api/{USER_ID}/tasks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid-payload.signature" \
  -v

# Expected: Same 401 malformed-token error
```

## Test 2: Invalid Signature

Test with a token signed with a different secret:

```bash
# Create a token with wrong secret (use Python):
python3 << 'EOF'
from jose import jwt
from datetime import datetime, timedelta, timezone

payload = {
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    "iat": datetime.now(timezone.utc)
}
wrong_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
print(f"Wrong signature token: {wrong_token}")
EOF

# Use the generated token:
curl -X GET http://localhost:8000/api/550e8400-e29b-41d4-a716-446655440000/tasks \
  -H "Authorization: Bearer {WRONG_SIGNATURE_TOKEN}" \
  -v

# Expected Response:
# HTTP/1.1 401 Unauthorized
# Content-Type: application/problem+json
# {
#   "type": "invalid-signature",
#   "title": "Invalid Signature",
#   "status": 401,
#   "detail": "Token signature verification failed"
# }
```

## Test 3: Expired Token

Test with an expired token:

```bash
# Create an expired token (use Python):
python3 << 'EOF'
import os
from jose import jwt
from datetime import datetime, timedelta, timezone

secret = os.getenv("BETTER_AUTH_SECRET")
payload = {
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
    "iat": datetime.now(timezone.utc) - timedelta(hours=2)
}
expired_token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Expired token: {expired_token}")
EOF

# Use the generated token:
curl -X GET http://localhost:8000/api/550e8400-e29b-41d4-a716-446655440000/tasks \
  -H "Authorization: Bearer {EXPIRED_TOKEN}" \
  -v

# Expected Response:
# HTTP/1.1 401 Unauthorized
# Content-Type: application/problem+json
# {
#   "type": "expired-token",
#   "title": "Expired Token",
#   "status": 401,
#   "detail": "Token has expired"
# }
```

## Test 4: Missing Bearer Prefix

Test with Authorization header missing "Bearer " prefix:

```bash
# Use a valid token but without "Bearer " prefix
curl -X GET http://localhost:8000/api/{USER_ID}/tasks \
  -H "Authorization: {VALID_TOKEN}" \
  -v

# Expected Response:
# HTTP/1.1 401 Unauthorized
# Content-Type: application/problem+json
# {
#   "type": "invalid-authorization-header",
#   "title": "Invalid Authorization Header",
#   "status": 401,
#   "detail": "Authorization header must be in format: Bearer <token>"
# }
```

## Test 5: Token with Invalid User ID Format

Test with a token containing an invalid UUID in the 'sub' claim:

```bash
# Create a token with invalid user_id (use Python):
python3 << 'EOF'
import os
from jose import jwt
from datetime import datetime, timedelta, timezone

secret = os.getenv("BETTER_AUTH_SECRET")
payload = {
    "sub": "not-a-valid-uuid",  # Invalid UUID format
    "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    "iat": datetime.now(timezone.utc)
}
invalid_token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Invalid user_id token: {invalid_token}")
EOF

# Use the generated token:
curl -X GET http://localhost:8000/api/550e8400-e29b-41d4-a716-446655440000/tasks \
  -H "Authorization: Bearer {INVALID_USER_ID_TOKEN}" \
  -v

# Expected Response:
# HTTP/1.1 401 Unauthorized
# Content-Type: application/problem+json
# {
#   "type": "invalid-token",
#   "title": "Invalid Token",
#   "status": 401,
#   "detail": "Token contains invalid user identifier"
# }
```

## Test 6: Token Missing 'sub' Claim

Test with a token missing the required 'sub' claim:

```bash
# Create a token without 'sub' claim (use Python):
python3 << 'EOF'
import os
from jose import jwt
from datetime import datetime, timedelta, timezone

secret = os.getenv("BETTER_AUTH_SECRET")
payload = {
    # Missing "sub" claim
    "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    "iat": datetime.now(timezone.utc)
}
no_sub_token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Token without sub: {no_sub_token}")
EOF

# Use the generated token:
curl -X GET http://localhost:8000/api/550e8400-e29b-41d4-a716-446655440000/tasks \
  -H "Authorization: Bearer {NO_SUB_TOKEN}" \
  -v

# Expected Response:
# HTTP/1.1 401 Unauthorized
# Content-Type: application/problem+json
# {
#   "type": "invalid-token",
#   "title": "Invalid Token",
#   "status": 401,
#   "detail": "Token missing user identifier"
# }
```

## Test 7: Valid Token (Success Case)

Test that valid tokens still work correctly:

```bash
# Use the valid token from login
curl -X GET http://localhost:8000/api/{USER_ID}/tasks \
  -H "Authorization: Bearer {VALID_TOKEN}" \
  -v

# Expected Response:
# HTTP/1.1 200 OK
# Content-Type: application/json
# []  (empty array if no tasks exist)
```

## Test 8: Missing Authorization Header

Test with no Authorization header at all:

```bash
curl -X GET http://localhost:8000/api/{USER_ID}/tasks \
  -v

# Expected Response:
# HTTP/1.1 401 Unauthorized
# Content-Type: application/problem+json
# {
#   "type": "invalid-authorization-header",
#   "title": "Invalid Authorization Header",
#   "status": 401,
#   "detail": "Authorization header must use Bearer scheme"
# }
```

## Verification Checklist

For each test, verify:
- [ ] HTTP status code is 401 Unauthorized (except success case: 200 OK)
- [ ] Content-Type header is `application/problem+json`
- [ ] Response body contains correct `type` field
- [ ] Response body contains correct `title` field
- [ ] Response body contains `status` field matching HTTP status code
- [ ] Response body contains descriptive `detail` field
- [ ] Error messages don't leak sensitive information (e.g., secret keys, internal paths)

## Security Considerations

All error messages follow these security principles:
1. **No information leakage**: Error messages don't reveal whether a user exists or internal system details
2. **Consistent timing**: All authentication failures return similar response times
3. **RFC 7807 compliance**: All errors follow Problem Details standard
4. **Clear but secure**: Messages are helpful for debugging but don't expose security vulnerabilities
