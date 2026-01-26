# Implementation Plan: Authentication & User Management

**Branch**: `002-auth-user-management` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-auth-user-management/spec.md`

## Summary

Add secure user authentication and isolation to the multi-user todo application using Better Auth with JWT tokens. This feature implements user registration, login, and token-based authentication to protect all task endpoints. The system will enforce strict user isolation, ensuring each user can only access their own tasks. Authentication uses industry-standard JWT tokens signed with a shared secret, with comprehensive validation and error handling following RFC 7807 format.

**Technical Approach**: Integrate Better Auth library for JWT token generation and validation. Implement FastAPI middleware to extract and verify tokens from Authorization headers. Add authentication dependency to all task endpoints with user_id matching validation. Extend database schema to include user accounts with secure password hashing. Implement rate limiting for login attempts and comprehensive security event logging.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/Next.js 16+ (frontend - future integration)
**Primary Dependencies**:
- FastAPI 0.109+ (web framework)
- Better Auth Python adapter (JWT token generation/validation)
- SQLModel 0.0.14+ (ORM for user data)
- passlib[bcrypt] (password hashing)
- python-jose[cryptography] (JWT handling)
- email-validator (RFC 5322 email validation)
- slowapi (rate limiting)

**Storage**: Neon Serverless PostgreSQL (existing from Spec 1, extend with users table)
**Testing**: pytest with pytest-asyncio for async tests, httpx for API testing
**Target Platform**: Linux server (FastAPI backend), HTTPS required for production
**Project Type**: Web application (backend API + frontend client)
**Performance Goals**:
- Registration: <3 seconds response time
- Login: <2 seconds response time
- Token validation: <50ms overhead per request
- Concurrent auth requests: 100 without degradation

**Constraints**:
- JWT tokens must be stateless (no server-side session storage)
- Token validation on every protected endpoint request
- Rate limiting: 5 login attempts per minute per IP
- Email max 254 chars, password 8-128 chars
- All errors must use RFC 7807 format

**Scale/Scope**:
- Support 100+ concurrent users
- Multiple concurrent sessions per user allowed
- 24-hour token expiration
- Security event logging for monitoring

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Spec-Driven Development
- **Status**: PASS
- **Evidence**: Complete specification with acceptance criteria, edge cases, and constraints defined in spec.md

### ✅ II. Full-Stack Modern Architecture
- **Status**: PASS
- **Evidence**: Using FastAPI backend with REST API contracts. Frontend integration planned but out of scope for this feature (focuses on backend auth only)

### ✅ III. Secure Authentication & Authorization
- **Status**: PASS
- **Evidence**:
  - Better Auth with JWT tokens (FR-008, FR-011)
  - JWT verification middleware on all endpoints (FR-020)
  - User isolation enforced (FR-018, FR-019)
  - Password hashing with bcrypt (FR-004)

### ✅ IV. Persistent Data Storage
- **Status**: PASS
- **Evidence**: User accounts stored in Neon PostgreSQL with proper schema design (users table with constraints)

### ✅ V. Test-First Development
- **Status**: PASS
- **Evidence**: Testing strategy defined with specific test scenarios for each user story. Tests will be written before implementation.

### ✅ VI. REST API Security
- **Status**: PASS
- **Evidence**:
  - All endpoints secured with JWT middleware (FR-020)
  - 401 for authentication failures, 403 for authorization failures (Constraints)
  - Rate limiting implemented (FR-024, FR-025)

### ✅ VII. Responsive & Accessible UI
- **Status**: DEFERRED
- **Evidence**: Frontend UI is out of scope for this backend-focused feature. Will be addressed in future frontend feature.

**Overall Gate Status**: ✅ PASS - All applicable principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/002-auth-user-management/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   └── openapi.yaml     # API contract for auth endpoints
└── tasks.md             # Phase 2 output (created by /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── user.py              # User model (NEW)
│   │   └── task.py              # Task model (existing, update foreign key)
│   ├── services/
│   │   ├── auth.py              # Authentication service (NEW)
│   │   ├── password.py          # Password hashing utilities (NEW)
│   │   └── rate_limit.py        # Rate limiting service (NEW)
│   ├── api/
│   │   ├── auth.py              # Auth endpoints: /register, /login (NEW)
│   │   ├── tasks.py             # Task endpoints (UPDATE with auth)
│   │   └── dependencies.py      # FastAPI dependencies (NEW)
│   ├── middleware/
│   │   ├── auth.py              # JWT verification middleware (NEW)
│   │   └── logging.py           # Security event logging (NEW)
│   └── core/
│       ├── config.py            # Configuration (UPDATE with auth settings)
│       └── security.py          # Security utilities (NEW)
├── tests/
│   ├── unit/
│   │   ├── test_auth_service.py      # Auth service tests (NEW)
│   │   ├── test_password.py          # Password hashing tests (NEW)
│   │   └── test_rate_limit.py        # Rate limiting tests (NEW)
│   ├── integration/
│   │   ├── test_auth_endpoints.py    # Auth API tests (NEW)
│   │   └── test_protected_endpoints.py # Task endpoint auth tests (NEW)
│   └── contract/
│       └── test_auth_contract.py     # OpenAPI contract tests (NEW)
├── requirements.txt     # UPDATE: add auth dependencies
├── .env.example         # UPDATE: add BETTER_AUTH_SECRET
└── alembic/
    └── versions/
        └── 002_add_users_table.py    # Database migration (NEW)

frontend/
└── (out of scope for this feature - auth integration in future feature)
```

**Structure Decision**: Web application structure with backend focus. This feature adds authentication layer to existing backend from Spec 1. Frontend integration will be handled in a separate feature. The backend follows FastAPI best practices with clear separation of concerns: models (data), services (business logic), api (endpoints), middleware (cross-cutting concerns), and core (configuration/utilities).

## Complexity Tracking

> No constitution violations requiring justification. All complexity is necessary for secure authentication implementation.

## Phase 0: Research & Technology Decisions

### Research Tasks

1. **Better Auth Python Integration**
   - Research: How to integrate Better Auth library with FastAPI
   - Research: Better Auth JWT token generation and validation APIs
   - Research: Better Auth configuration for shared secret management

2. **JWT Token Strategy**
   - Research: JWT token structure and standard claims (iss, sub, exp, iat)
   - Research: Token signing algorithms (HS256 vs RS256 for shared secret)
   - Research: Token payload design for user identification

3. **Password Security**
   - Research: bcrypt vs argon2 for password hashing
   - Research: Salt generation and storage best practices
   - Research: Password complexity validation patterns

4. **Rate Limiting Implementation**
   - Research: slowapi library for FastAPI rate limiting
   - Research: IP-based rate limiting strategies
   - Research: Rate limit storage (in-memory vs Redis)

5. **Security Event Logging**
   - Research: Python logging best practices for security events
   - Research: Structured logging formats for security monitoring
   - Research: Log sanitization to prevent sensitive data leakage

### Decision Table

| Decision Point | Options Considered | Chosen | Rationale |
|----------------|-------------------|--------|-----------|
| JWT Library | python-jose, PyJWT, Better Auth native | python-jose[cryptography] | Industry standard, well-maintained, supports all required algorithms, integrates with Better Auth |
| Password Hashing | bcrypt, argon2, scrypt | passlib[bcrypt] | Constitution requires bcrypt, widely supported, proven security track record |
| Token Signing Algorithm | HS256 (symmetric), RS256 (asymmetric) | HS256 | Shared secret model per spec, simpler key management, sufficient for single backend |
| Rate Limiting Storage | In-memory dict, Redis, Database | slowapi with in-memory | Simplest for MVP, no additional infrastructure, acceptable for 100 concurrent users |
| Email Validation | regex, email-validator library | email-validator | RFC 5322 compliant per clarifications, handles edge cases correctly |
| Session Management | Server-side sessions, Stateless JWT | Stateless JWT | Per spec requirements, scalable, no session storage needed |
| Token Expiration | 1 hour, 24 hours, 7 days | 24 hours | Per spec assumptions, balances security and user experience |

### Technology Integration Points

1. **Better Auth + FastAPI**
   - Better Auth handles token generation on login
   - FastAPI middleware validates tokens on each request
   - Shared BETTER_AUTH_SECRET environment variable

2. **SQLModel + User Authentication**
   - Extend existing database with users table
   - Foreign key relationship: tasks.user_id → users.id
   - Alembic migration for schema changes

3. **FastAPI Dependencies**
   - Create `get_current_user` dependency
   - Inject into all protected endpoints
   - Automatic 401 handling for invalid tokens

4. **Error Handling**
   - Custom exception handlers for auth errors
   - RFC 7807 Problem Details format
   - Consistent error responses across all endpoints

## Phase 1: Design & Contracts

### Data Model

**See**: [data-model.md](./data-model.md) (to be created)

**Summary**:
- **User Entity**: id (UUID), email (unique, lowercase), password_hash, created_at, last_login_at
- **Task Entity Update**: Add user_id foreign key, cascade delete on user deletion
- **Relationships**: User 1:N Tasks (one user owns many tasks)
- **Indexes**: email (unique), user_id on tasks table
- **Constraints**: Email max 254 chars, password_hash not null

### API Contracts

**See**: [contracts/openapi.yaml](./contracts/openapi.yaml) (to be created)

**New Endpoints**:

1. **POST /api/auth/register**
   - Request: `{ email: string, password: string }`
   - Response 201: `{ user_id: UUID, email: string, message: string }`
   - Errors: 400 (validation), 409 (email exists)

2. **POST /api/auth/login**
   - Request: `{ email: string, password: string }`
   - Response 200: `{ access_token: string, token_type: "bearer", expires_in: number }`
   - Errors: 401 (invalid credentials), 429 (rate limit)

**Updated Endpoints** (all task endpoints from Spec 1):
- Add required header: `Authorization: Bearer <token>`
- Add error responses: 401 (missing/invalid token), 403 (wrong user_id)
- Examples:
  - GET /api/{user_id}/tasks
  - POST /api/{user_id}/tasks
  - GET /api/{user_id}/tasks/{task_id}
  - PUT /api/{user_id}/tasks/{task_id}
  - DELETE /api/{user_id}/tasks/{task_id}

### Implementation Phases

**Phase 1: Database & Models** (Foundation)
1. Create User model with SQLModel
2. Update Task model with user_id foreign key
3. Create Alembic migration for users table
4. Test database schema changes

**Phase 2: Password Security** (Core Security)
1. Implement password hashing with passlib[bcrypt]
2. Implement password validation (length, complexity)
3. Test password hashing and verification
4. Test password validation rules

**Phase 3: JWT Token Management** (Authentication Core)
1. Configure Better Auth with shared secret
2. Implement JWT token generation on login
3. Implement JWT token validation middleware
4. Test token generation and validation

**Phase 4: Authentication Endpoints** (User-Facing)
1. Implement POST /api/auth/register endpoint
2. Implement POST /api/auth/login endpoint
3. Implement email validation (RFC 5322)
4. Test registration and login flows

**Phase 5: Authorization Middleware** (Protection)
1. Create get_current_user FastAPI dependency
2. Implement user_id matching validation
3. Add dependency to all task endpoints
4. Test authorization enforcement

**Phase 6: Rate Limiting** (Security Enhancement)
1. Implement rate limiting with slowapi
2. Configure 5 attempts per minute per IP
3. Add rate limit to login endpoint
4. Test rate limiting behavior

**Phase 7: Security Logging** (Observability)
1. Implement security event logging
2. Log failed logins, token rejections, rate limits
3. Configure structured logging format
4. Test logging output

**Phase 8: Error Handling** (User Experience)
1. Implement RFC 7807 error responses
2. Create custom exception handlers
3. Add error responses to all auth endpoints
4. Test error response formats

### Testing Strategy

**Unit Tests**:
- Password hashing and verification
- Email validation (RFC 5322)
- JWT token generation and parsing
- Rate limiting logic
- User model validation

**Integration Tests**:
- Registration flow: valid/invalid inputs
- Login flow: correct/incorrect credentials
- Token validation: valid/expired/malformed tokens
- User isolation: access own tasks, blocked from others
- Rate limiting: exceed limit, wait and retry
- Error responses: verify RFC 7807 format

**Contract Tests**:
- OpenAPI schema validation
- Request/response format compliance
- Error response structure

**Test Commands**:
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests
pytest tests/contract/ -v

# All tests with coverage
pytest --cov=src --cov-report=html

# Specific auth tests
pytest tests/integration/test_auth_endpoints.py -v
pytest tests/integration/test_protected_endpoints.py -v
```

**Manual Testing Scenarios** (Postman/curl):

1. **Registration Success**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
# Expected: 201 Created with user_id
```

2. **Registration Duplicate Email**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
# Expected: 400 Bad Request (email already registered)
```

3. **Login Success**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
# Expected: 200 OK with JWT token
```

4. **Access Own Tasks with Valid Token**:
```bash
TOKEN="<jwt_token_from_login>"
USER_ID="<user_id_from_registration>"
curl -X GET http://localhost:8000/api/${USER_ID}/tasks \
  -H "Authorization: Bearer ${TOKEN}"
# Expected: 200 OK with task list
```

5. **Access Other User's Tasks (Forbidden)**:
```bash
TOKEN="<jwt_token_from_login>"
OTHER_USER_ID="<different_user_id>"
curl -X GET http://localhost:8000/api/${OTHER_USER_ID}/tasks \
  -H "Authorization: Bearer ${TOKEN}"
# Expected: 403 Forbidden
```

6. **Access Without Token**:
```bash
curl -X GET http://localhost:8000/api/${USER_ID}/tasks
# Expected: 401 Unauthorized
```

7. **Access With Expired Token**:
```bash
EXPIRED_TOKEN="<expired_jwt_token>"
curl -X GET http://localhost:8000/api/${USER_ID}/tasks \
  -H "Authorization: Bearer ${EXPIRED_TOKEN}"
# Expected: 401 Unauthorized (token expired)
```

8. **Rate Limiting Test**:
```bash
# Make 6 rapid login attempts with wrong password
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "user@example.com", "password": "WrongPass"}'
done
# Expected: First 5 return 401, 6th returns 429 with Retry-After header
```

### Quickstart Guide

**See**: [quickstart.md](./quickstart.md) (to be created)

**Summary**:
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: Copy `.env.example` to `.env`, set `BETTER_AUTH_SECRET`
3. Run migrations: `alembic upgrade head`
4. Start server: `uvicorn src.main:app --reload`
5. Test registration: POST to `/api/auth/register`
6. Test login: POST to `/api/auth/login` to get JWT token
7. Test protected endpoint: GET `/api/{user_id}/tasks` with Authorization header

## Phase 2: Task Breakdown

**Note**: Detailed task breakdown will be generated by `/sp.tasks` command. This section provides high-level task categories.

### Task Categories

1. **Database Setup** (2-3 tasks)
   - Create User model
   - Create Alembic migration
   - Update Task model with foreign key

2. **Password Security** (2-3 tasks)
   - Implement password hashing
   - Implement password validation
   - Write password tests

3. **JWT Token Management** (3-4 tasks)
   - Configure Better Auth
   - Implement token generation
   - Implement token validation
   - Write token tests

4. **Authentication Endpoints** (3-4 tasks)
   - Implement registration endpoint
   - Implement login endpoint
   - Implement email validation
   - Write endpoint tests

5. **Authorization Middleware** (2-3 tasks)
   - Create get_current_user dependency
   - Update task endpoints
   - Write authorization tests

6. **Rate Limiting** (2 tasks)
   - Implement rate limiting
   - Write rate limit tests

7. **Security Logging** (2 tasks)
   - Implement security event logging
   - Write logging tests

8. **Error Handling** (2-3 tasks)
   - Implement RFC 7807 error responses
   - Create exception handlers
   - Write error handling tests

**Estimated Total**: 18-25 tasks

## Dependencies & Integration Points

### External Dependencies

1. **Better Auth Library**
   - Purpose: JWT token generation and validation
   - Integration: Configure with BETTER_AUTH_SECRET
   - Risk: Library compatibility with FastAPI
   - Mitigation: Pin specific version, test thoroughly

2. **Neon PostgreSQL**
   - Purpose: User account storage
   - Integration: Extend existing database schema
   - Risk: Migration conflicts with existing data
   - Mitigation: Test migrations on staging database first

3. **Environment Configuration**
   - Purpose: Secure secret management
   - Integration: BETTER_AUTH_SECRET in .env file
   - Risk: Secret exposure in version control
   - Mitigation: Use .env.example template, add .env to .gitignore

### Internal Dependencies

1. **Spec 1: Backend API & Data Layer**
   - Dependency: Existing task endpoints and database schema
   - Integration: Add authentication middleware to existing endpoints
   - Impact: All task endpoints require authentication after this feature
   - Migration: Existing API clients must include Authorization header

2. **Future Frontend Feature**
   - Dependency: This backend auth implementation
   - Integration: Frontend will call /register and /login endpoints
   - Impact: Frontend must store and send JWT tokens
   - Note: Frontend integration is out of scope for this feature

## Risk Mitigation

### Technical Risks

1. **Better Auth Integration Complexity**
   - Risk: Better Auth library may not integrate smoothly with FastAPI
   - Impact: HIGH - Core authentication functionality
   - Mitigation: Research Better Auth Python adapter in Phase 0, create proof-of-concept
   - Fallback: Use python-jose directly for JWT handling

2. **Token Validation Performance**
   - Risk: JWT validation on every request may add significant latency
   - Impact: MEDIUM - Performance requirement is <50ms overhead
   - Mitigation: Benchmark token validation, optimize if needed, consider caching
   - Fallback: Accept slightly higher latency if within acceptable range

3. **Rate Limiting Accuracy**
   - Risk: In-memory rate limiting may not work correctly with multiple server instances
   - Impact: LOW - Single server deployment for MVP
   - Mitigation: Document limitation, plan Redis-based rate limiting for production scale
   - Fallback: Accept potential rate limit bypass in multi-instance deployment

### Security Risks

1. **Secret Key Exposure**
   - Risk: BETTER_AUTH_SECRET could be committed to version control
   - Impact: CRITICAL - Complete authentication bypass
   - Mitigation: Use .env.example template, add .env to .gitignore, document in README
   - Detection: Pre-commit hooks to scan for secrets

2. **Password Storage**
   - Risk: Weak password hashing could compromise user accounts
   - Impact: HIGH - User data security
   - Mitigation: Use bcrypt with appropriate cost factor, test hash strength
   - Validation: Security audit of password handling code

3. **Token Expiration**
   - Risk: 24-hour expiration may be too long if token is compromised
   - Impact: MEDIUM - Extended unauthorized access window
   - Mitigation: Document token expiration policy, plan token refresh for future
   - Monitoring: Log token usage patterns for anomaly detection

## Success Metrics

### Functional Metrics

- ✅ All 25 functional requirements (FR-001 through FR-026) implemented and tested
- ✅ All 5 user stories have passing acceptance tests
- ✅ All edge cases handled with correct error responses
- ✅ 100% of task endpoints protected with authentication

### Performance Metrics

- ✅ Registration completes in <3 seconds (SC-001)
- ✅ Login completes in <2 seconds (SC-002)
- ✅ Token validation adds <50ms latency (SC-008)
- ✅ System handles 100 concurrent auth requests (SC-007)

### Security Metrics

- ✅ 100% password hashing compliance (SC-006)
- ✅ 100% user isolation enforcement (SC-004)
- ✅ 100% invalid token rejection (SC-005)
- ✅ All security events logged correctly (FR-026)

### Quality Metrics

- ✅ Test coverage >80% for auth code
- ✅ All tests passing (unit, integration, contract)
- ✅ No security vulnerabilities in dependencies
- ✅ Code review approval from security perspective

## Next Steps

1. **Complete Phase 0**: Run research tasks to resolve all technical unknowns
2. **Generate Phase 1 Artifacts**: Create data-model.md, contracts/openapi.yaml, quickstart.md
3. **Update Agent Context**: Run update-agent-context.sh to add auth technologies
4. **Generate Tasks**: Run `/sp.tasks` to create detailed task breakdown
5. **Begin Implementation**: Start with Phase 1 tasks (Database & Models)

## Appendix

### Environment Variables

```bash
# .env.example
BETTER_AUTH_SECRET=<generate-32-char-secret>  # Required: JWT signing key
DATABASE_URL=<neon-postgres-url>               # Existing from Spec 1
LOG_LEVEL=INFO                                  # Optional: logging verbosity
RATE_LIMIT_ENABLED=true                         # Optional: enable rate limiting
```

### Key Files Modified

**New Files**:
- `backend/src/models/user.py`
- `backend/src/services/auth.py`
- `backend/src/services/password.py`
- `backend/src/services/rate_limit.py`
- `backend/src/api/auth.py`
- `backend/src/api/dependencies.py`
- `backend/src/middleware/auth.py`
- `backend/src/middleware/logging.py`
- `backend/src/core/security.py`
- `backend/alembic/versions/002_add_users_table.py`

**Modified Files**:
- `backend/requirements.txt` (add auth dependencies)
- `backend/.env.example` (add BETTER_AUTH_SECRET)
- `backend/src/models/task.py` (add user_id foreign key)
- `backend/src/api/tasks.py` (add authentication dependency)
- `backend/src/core/config.py` (add auth configuration)

### References

- [Better Auth Documentation](https://better-auth.com)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [RFC 7807 Problem Details](https://tools.ietf.org/html/rfc7807)
- [RFC 5322 Email Format](https://tools.ietf.org/html/rfc5322)
- [OWASP Authentication Cheat Sheet](https://cheatsheetsecurity.org/cheatsheets/authentication-cheat-sheet/)
