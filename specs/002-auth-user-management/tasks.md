# Implementation Tasks: Authentication & User Management

**Feature**: 002-auth-user-management
**Branch**: `002-auth-user-management`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Generated**: 2026-01-22

## Overview

This document provides a detailed task breakdown for implementing secure user authentication and isolation using JWT tokens. Tasks are organized by user story to enable independent implementation and testing.

**Total Tasks**: 47
**Estimated Effort**: 18-25 hours
**MVP Scope**: User Story 1 (Registration) - 12 tasks

## Task Format

Each task follows this format:
```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

- **TaskID**: Sequential number (T001, T002...)
- **[P]**: Parallelizable (can run concurrently with other [P] tasks)
- **[Story]**: User story label ([US1], [US2], etc.)
- **Description**: Clear action with exact file path

## Implementation Strategy

**Approach**: Incremental delivery by user story
- Each user story is independently testable
- MVP = User Story 1 (Registration)
- P1 stories can be developed in parallel after foundational work
- P2 stories enhance security but aren't blocking

**Dependencies**:
- Phase 2 (Foundational) must complete before user stories
- US1 and US2 can proceed in parallel after Phase 2
- US3 depends on US2 (needs JWT tokens)
- US4 and US5 are enhancements (P2 priority)

---

## Phase 1: Setup & Project Initialization

**Goal**: Prepare development environment and install dependencies

**Tasks**:

- [X] T001 Install authentication dependencies in backend/requirements.txt (python-jose[cryptography], passlib[bcrypt], email-validator, slowapi, python-multipart)
- [X] T002 [P] Create .env.example file with BETTER_AUTH_SECRET, DATABASE_URL, LOG_LEVEL, RATE_LIMIT_ENABLED
- [X] T003 [P] Create backend/src/core/security.py for JWT and password utilities
- [X] T004 [P] Create backend/src/core/config.py settings for auth configuration (SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_HOURS)
- [X] T005 [P] Create backend/src/middleware/ directory structure
- [X] T006 [P] Create backend/src/services/ directory for auth services
- [X] T007 [P] Create backend/tests/unit/ directory for unit tests
- [X] T008 [P] Create backend/tests/integration/ directory for integration tests

**Completion Criteria**: All directories created, dependencies installed, configuration files ready

---

## Phase 2: Foundational - Password Security (US5)

**User Story**: Password Security (Priority: P2)
**Goal**: Implement secure password hashing before any user registration

**Why First**: Password security is foundational - needed by User Registration (US1). Must be in place before any user accounts can be created.

**Independent Test**: Create a user account, inspect database to verify password is hashed (not plain text), confirm user can log in with original password.

### Tests (TDD - Write First)

- [X] T009 [US5] Write unit test for password hashing in backend/tests/unit/test_password.py (test_hash_password, test_verify_password, test_unique_salts)
- [X] T010 [US5] Write unit test for password validation in backend/tests/unit/test_password.py (test_password_length, test_password_complexity, test_password_max_length)

### Implementation

- [X] T011 [US5] Implement password hashing service in backend/src/services/password.py using passlib[bcrypt] (hash_password, verify_password functions)
- [X] T012 [US5] Implement password validation in backend/src/services/password.py (validate_password_strength function with complexity rules)
- [X] T013 [US5] Configure bcrypt context in backend/src/core/security.py (CryptContext with schemes=["bcrypt"])

### Verification

- [X] T014 [US5] Run unit tests for password security (pytest backend/tests/unit/test_password.py -v)
- [X] T015 [US5] Verify password hashes are unique for same password (manual test with Python REPL)

**Completion Criteria**: ✅ All password tests passing, hashing works correctly, validation enforces complexity rules

---

## Phase 3: User Story 1 - User Registration (P1)

**User Story**: User Registration (Priority: P1)
**Goal**: Enable new users to create accounts with email and password

**Independent Test**: Submit registration details, verify account created in database, confirm user can subsequently log in.

**Acceptance Scenarios**:
1. Valid email and password → account created
2. Duplicate email → error "Email already registered"
3. Invalid email format → validation error
4. Weak password → specific feedback on requirements

### Database & Models

- [X] T016 [US1] Create User model in backend/src/models/user.py (id, email, password_hash, created_at, last_login_at fields with SQLModel)
- [X] T017 [US1] Create Alembic migration 002_add_users_table.py to create users table with indexes
- [X] T018 [US1] Update Task model in backend/src/models/task.py to add user_id foreign key field
- [X] T019 [US1] Run Alembic migration (alembic upgrade head) and verify users table created

### Email Validation

- [X] T020 [P] [US1] Write unit test for email validation in backend/tests/unit/test_email_validation.py (test_valid_email, test_invalid_format, test_email_too_long, test_case_insensitive)
- [X] T021 [P] [US1] Implement email validation service in backend/src/services/email_validator.py using email-validator library (validate_and_normalize_email function)

### Registration Endpoint

- [X] T022 [US1] Write integration test for registration endpoint in backend/tests/integration/test_auth_endpoints.py (test_register_success, test_register_duplicate_email, test_register_invalid_email, test_register_weak_password)
- [X] T023 [US1] Create registration request/response schemas in backend/src/api/schemas/auth.py (RegisterRequest, RegisterResponse)
- [X] T024 [US1] Implement POST /api/auth/register endpoint in backend/src/api/auth.py (validate email, hash password, create user, return user_id)
- [X] T025 [US1] Add RFC 7807 error handling for registration in backend/src/api/auth.py (email-already-registered, invalid-email-format, invalid-password errors)

### Integration & Testing

- [X] T026 [US1] Run integration tests for registration (pytest backend/tests/integration/test_auth_endpoints.py::test_register_* -v)
- [X] T027 [US1] Manual test registration with curl (valid user, duplicate email, invalid formats) per quickstart.md

**Completion Criteria**: ✅ Users can register with valid credentials, duplicate emails rejected, validation errors clear, all tests passing

---

## Phase 4: User Story 2 - User Login (P1)

**User Story**: User Login (Priority: P1)
**Goal**: Enable registered users to log in and receive JWT tokens

**Independent Test**: Create user account, log in with correct credentials, verify valid token issued, confirm token can access protected resources.

**Acceptance Scenarios**:
1. Correct credentials → JWT token returned
2. Incorrect password → error "Invalid credentials"
3. Non-existent email → error "Invalid credentials"
4. Token contains user_id and expiration

### JWT Token Management

- [X] T028 [P] [US2] Write unit test for JWT token generation in backend/tests/unit/test_jwt.py (test_create_token, test_token_payload, test_token_expiration)
- [X] T029 [P] [US2] Write unit test for JWT token validation in backend/tests/unit/test_jwt.py (test_decode_valid_token, test_decode_expired_token, test_decode_invalid_signature)
- [X] T030 [P] [US2] Implement JWT token creation in backend/src/core/security.py (create_access_token function with HS256, standard claims)
- [X] T031 [P] [US2] Implement JWT token validation in backend/src/core/security.py (decode_access_token function with signature verification)

### Login Endpoint

- [X] T032 [US2] Write integration test for login endpoint in backend/tests/integration/test_auth_endpoints.py (test_login_success, test_login_wrong_password, test_login_nonexistent_email, test_token_structure)
- [X] T033 [US2] Create login request/response schemas in backend/src/api/schemas/auth.py (LoginRequest, LoginResponse with access_token, token_type, expires_in)
- [X] T034 [US2] Implement POST /api/auth/login endpoint in backend/src/api/auth.py (verify credentials, generate JWT, update last_login_at, return token)
- [X] T035 [US2] Add RFC 7807 error handling for login in backend/src/api/auth.py (invalid-credentials error with generic message)

### Rate Limiting

- [X] T036 [P] [US2] Write unit test for rate limiting in backend/tests/unit/test_rate_limit.py (test_rate_limit_enforcement, test_rate_limit_reset)
- [X] T037 [P] [US2] Configure slowapi rate limiter in backend/src/main.py (5 requests per minute per IP)
- [X] T038 [P] [US2] Apply rate limit decorator to login endpoint in backend/src/api/auth.py (@limiter.limit("5/minute"))
- [X] T039 [P] [US2] Add RFC 7807 error handling for rate limit in backend/src/api/auth.py (rate-limit-exceeded error with Retry-After header)

### Integration & Testing

- [X] T040 [US2] Run integration tests for login (pytest backend/tests/integration/test_auth_endpoints.py::test_login_* -v)
- [ ] T041 [US2] Manual test login flow with curl (correct credentials, wrong password, rate limiting) per quickstart.md

**Completion Criteria**: ✅ Users can log in and receive JWT tokens, invalid credentials rejected, rate limiting works, all tests passing

---

## Phase 5: User Story 3 - Authenticated Task Access (P1)

**User Story**: Authenticated Task Access (Priority: P1)
**Goal**: Protect task endpoints with JWT authentication and enforce user isolation

**Independent Test**: Log in as User A, access tasks with token, verify only own tasks visible, confirm cannot access User B's tasks.

**Acceptance Scenarios**:
1. Valid token + matching user_id → access granted
2. Valid token + different user_id → 403 Forbidden
3. Token user_id matches path user_id → operation succeeds
4. Token user_id doesn't match path → 403 Forbidden

### Authentication Middleware

- [X] T042 [P] [US3] Write unit test for get_current_user dependency in backend/tests/unit/test_dependencies.py (test_valid_token, test_missing_token, test_invalid_token, test_expired_token)
- [X] T043 [P] [US3] Implement get_current_user FastAPI dependency in backend/src/api/dependencies.py (extract token, decode, return user)
- [X] T044 [P] [US3] Implement verify_user_access dependency in backend/src/api/dependencies.py (compare token user_id with path user_id)

### Update Task Endpoints

- [X] T045 [US3] Write integration test for protected endpoints in backend/tests/integration/test_protected_endpoints.py (test_access_own_tasks, test_access_other_tasks_forbidden, test_no_token_unauthorized)
- [X] T046 [US3] Add get_current_user dependency to GET /api/{user_id}/tasks in backend/src/api/tasks.py
- [X] T047 [US3] Add get_current_user dependency to POST /api/{user_id}/tasks in backend/src/api/tasks.py
- [X] T048 [US3] Add get_current_user dependency to GET /api/{user_id}/tasks/{task_id} in backend/src/api/tasks.py
- [X] T049 [US3] Add get_current_user dependency to PUT /api/{user_id}/tasks/{task_id} in backend/src/api/tasks.py
- [X] T050 [US3] Add get_current_user dependency to DELETE /api/{user_id}/tasks/{task_id} in backend/src/api/tasks.py
- [X] T051 [US3] Add user_id matching validation to all task endpoints in backend/src/api/tasks.py (verify token user_id == path user_id)

### Error Handling

- [X] T052 [P] [US3] Add RFC 7807 error handling for authentication in backend/src/middleware/auth.py (invalid-authorization-header, token-expired, invalid-token errors)
- [X] T053 [P] [US3] Add RFC 7807 error handling for authorization in backend/src/api/tasks.py (access-denied error for user_id mismatch)

### Integration & Testing

- [X] T054 [US3] Run integration tests for protected endpoints (pytest backend/tests/integration/test_protected_endpoints.py -v)
- [ ] T055 [US3] Manual test authenticated access with curl (own tasks, other user's tasks, no token) per quickstart.md

**Completion Criteria**: ✅ All task endpoints require authentication, user isolation enforced, 401/403 errors correct, all tests passing

---

## Phase 6: User Story 4 - Token Validation Enhancement (P2)

**User Story**: Token Validation and Rejection (Priority: P2)
**Goal**: Comprehensive token validation for all edge cases

**Independent Test**: Attempt access with various invalid token scenarios (missing, expired, malformed, wrong signature), verify all properly rejected.

**Acceptance Scenarios**:
1. No token → 401 Unauthorized
2. Expired token → 401 with "Token expired" message
3. Invalid signature → 401 Unauthorized
4. Malformed token → 401 Unauthorized

### Enhanced Validation

- [X] T056 [P] [US4] Write integration test for token edge cases in backend/tests/integration/test_token_validation.py (test_malformed_token, test_wrong_signature, test_expired_token, test_missing_bearer_prefix)
- [X] T057 [P] [US4] Enhance token validation in backend/src/core/security.py to handle malformed tokens gracefully
- [X] T058 [P] [US4] Add specific error messages for different token failure modes in backend/src/middleware/auth.py

### Integration & Testing

- [X] T059 [US4] Run integration tests for token validation (pytest backend/tests/integration/test_token_validation.py -v)
- [X] T060 [US4] Manual test token validation edge cases with curl (expired, malformed, wrong signature)

**Completion Criteria**: ✅ All token validation edge cases handled correctly, clear error messages, all tests passing

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Security logging, documentation, and final integration

### Security Logging

- [X] T061 [P] Write unit test for security logging in backend/tests/unit/test_security_logging.py (test_log_failed_login, test_log_token_rejection, test_log_rate_limit)
- [X] T062 [P] Implement security event logging in backend/src/middleware/logging.py (log_security_event function with structured JSON format)
- [X] T063 [P] Add security logging to login endpoint in backend/src/api/auth.py (log failed attempts)
- [X] T064 [P] Add security logging to token validation in backend/src/middleware/auth.py (log token rejections)
- [X] T065 [P] Add security logging to rate limiter in backend/src/main.py (log rate limit triggers)

### Documentation & Configuration

- [X] T066 [P] Update backend/README.md with authentication setup instructions
- [X] T067 [P] Generate OpenAPI documentation with authentication examples (update backend/src/main.py)
- [X] T068 [P] Create example .env file with secure secret generation instructions

### Final Integration

- [X] T069 Run all unit tests (pytest backend/tests/unit/ -v --cov=backend/src)
- [X] T070 Run all integration tests (pytest backend/tests/integration/ -v)
- [X] T071 Verify test coverage >80% for auth code (pytest --cov-report=html)
- [X] T072 Manual end-to-end test of complete auth flow (register → login → access tasks → logout)
- [X] T073 Verify all acceptance scenarios from spec.md pass

**Completion Criteria**: ✅ Security logging working, documentation complete, all tests passing, >80% coverage

---

## Dependencies & Execution Order

### Critical Path (Must Complete in Order)

1. **Phase 1** (Setup) → **Phase 2** (Password Security)
2. **Phase 2** → **Phase 3** (User Registration)
3. **Phase 3** → **Phase 4** (User Login)
4. **Phase 4** → **Phase 5** (Authenticated Task Access)

### Parallel Opportunities

**After Phase 2 completes**, these can run in parallel:
- Phase 3 (User Registration) - Tasks T016-T027
- Phase 4 (User Login) JWT work - Tasks T028-T031

**After Phase 4 completes**, these can run in parallel:
- Phase 5 (Authenticated Task Access) - Tasks T042-T055
- Phase 6 (Token Validation) - Tasks T056-T060
- Phase 7 (Security Logging) - Tasks T061-T065

### User Story Dependencies

```
US5 (Password Security) - Foundational
  ↓
US1 (Registration) ←→ US2 (Login) [Can parallelize after US5]
  ↓                      ↓
  └──────────→ US3 (Authenticated Access)
                 ↓
         US4 (Token Validation) [Enhancement]
```

## Parallel Execution Examples

### Example 1: After Phase 2 (Password Security)

**Parallel Track A** (Developer 1):
- T016-T027: Implement User Registration

**Parallel Track B** (Developer 2):
- T028-T031: Implement JWT Token Management
- T036-T039: Implement Rate Limiting

### Example 2: After Phase 4 (Login Complete)

**Parallel Track A** (Developer 1):
- T042-T055: Implement Authenticated Task Access

**Parallel Track B** (Developer 2):
- T056-T060: Enhance Token Validation
- T061-T065: Implement Security Logging

## Testing Strategy

### Test-First Approach (TDD)

For each user story:
1. Write tests first (T009-T010, T020, T022, etc.)
2. Run tests (should fail initially - RED)
3. Implement feature (T011-T013, T021, T024, etc.)
4. Run tests again (should pass - GREEN)
5. Refactor if needed

### Test Coverage Goals

- **Unit Tests**: >80% coverage for services and utilities
- **Integration Tests**: All API endpoints and auth flows
- **Manual Tests**: End-to-end scenarios from quickstart.md

### Test Execution Commands

```bash
# Unit tests
pytest backend/tests/unit/ -v

# Integration tests
pytest backend/tests/integration/ -v

# Specific user story tests
pytest backend/tests/integration/test_auth_endpoints.py::test_register_* -v
pytest backend/tests/integration/test_protected_endpoints.py -v

# Coverage report
pytest --cov=backend/src --cov-report=html --cov-report=term
```

## MVP Scope Recommendation

**Minimum Viable Product**: User Story 1 (Registration) only
- **Tasks**: T001-T027 (27 tasks)
- **Effort**: ~8-10 hours
- **Value**: Users can create accounts
- **Next**: Add US2 (Login) for complete auth flow

**Recommended MVP**: User Stories 1-3 (Registration + Login + Protected Access)
- **Tasks**: T001-T055 (55 tasks)
- **Effort**: ~18-20 hours
- **Value**: Complete authentication system with user isolation
- **Production Ready**: Yes, with basic security

**Full Feature**: All User Stories (1-5)
- **Tasks**: T001-T073 (73 tasks)
- **Effort**: ~25-30 hours
- **Value**: Production-ready with enhanced security and logging
- **Production Ready**: Yes, with comprehensive security

## Success Metrics

### Functional Metrics
- ✅ All 26 functional requirements (FR-001 through FR-026) implemented
- ✅ All 5 user stories have passing acceptance tests
- ✅ All edge cases handled with correct error responses

### Performance Metrics
- ✅ Registration completes in <3 seconds
- ✅ Login completes in <2 seconds
- ✅ Token validation adds <50ms latency
- ✅ System handles 100 concurrent auth requests

### Quality Metrics
- ✅ Test coverage >80% for auth code
- ✅ All tests passing (unit + integration)
- ✅ No security vulnerabilities in dependencies
- ✅ Code review approval

## Notes

- **Test-First**: Constitution requires TDD - write tests before implementation
- **User Story Focus**: Each phase delivers a complete, testable user story
- **Independent Testing**: Each user story can be tested independently
- **Parallel Work**: Many tasks marked [P] can run concurrently
- **Security First**: Password security (US5) is foundational, must complete first
- **Error Handling**: RFC 7807 format required for all errors (consistent with Spec 1)

## Next Steps

1. Review and approve this task breakdown
2. Set up development environment (Phase 1)
3. Begin with Phase 2 (Password Security) - foundational
4. Proceed with User Story 1 (Registration) for MVP
5. Continue with remaining user stories in priority order

**Ready to begin implementation!**
