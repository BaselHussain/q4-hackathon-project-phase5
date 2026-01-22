# Implementation Plan: Backend API & Data Layer

**Branch**: `001-backend-api-data` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-backend-api-data/spec.md`

## Summary

Build a FastAPI backend from scratch for a multi-user todo application with persistent storage in Neon PostgreSQL. The backend will provide REST API endpoints for CRUD operations on tasks, enforce task ownership at the data layer, and use SQLModel for ORM with async PostgreSQL engine. Authentication middleware is deferred to a future feature - this phase focuses on data persistence and API structure.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.109+, SQLModel 0.0.14+, asyncpg 0.29+, pydantic 2.5+, uvicorn 0.27+
**Storage**: Neon Serverless PostgreSQL (async connection via asyncpg)
**Testing**: pytest 8.0+, pytest-asyncio 0.23+, httpx 0.26+ (for async API testing)
**Target Platform**: Linux/Windows server (containerizable)
**Project Type**: Web backend (REST API)
**Performance Goals**: <1s response time for list operations (up to 100 tasks), <2s for create/update operations, support 100 concurrent users
**Constraints**: <200ms p95 latency for single task operations, ACID compliance for all database operations, UTC timestamps only
**Scale/Scope**: Support 1000 tasks per user, 100 concurrent users initially, single region deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Assessment

✅ **I. Spec-Driven Development**: This plan follows approved spec.md with clear acceptance criteria and constraints

✅ **II. Full-Stack Modern Architecture**: Using FastAPI + SQLModel for backend as specified in constitution. REST API contracts will be defined. Backend is independently deployable.

⚠️ **III. Secure Authentication & Authorization**: **DEFERRED** - JWT authentication explicitly out of scope per spec (FR-001 to FR-015 do not include auth). User identification via user_id parameter only. This is documented in spec Assumptions and Out of Scope sections. Future feature will add Better Auth + JWT.

✅ **IV. Persistent Data Storage**: Using Neon Serverless PostgreSQL with proper schema design (User and Task entities with relationships)

✅ **V. Test-First Development**: TDD will be followed in implementation phase (/sp.tasks will generate test-first tasks)

⚠️ **VI. REST API Security**: **PARTIAL** - Endpoints will enforce ownership filtering but lack authentication middleware (deferred to next feature per spec)

❌ **VII. Responsive & Accessible UI**: **NOT APPLICABLE** - This feature is backend-only, no frontend components

### Gate Decision

**PASS WITH DOCUMENTED EXCEPTIONS**

Exceptions justified:
1. Authentication deferred: Explicitly documented in spec Out of Scope section. Allows independent testing of data layer before adding auth complexity.
2. No UI: Backend-only feature per spec scope.

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-api-data/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── openapi.yaml     # OpenAPI 3.1 specification
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── main.py              # FastAPI app initialization, CORS, health check
├── database.py          # Async engine, session factory, get_db dependency
├── models.py            # SQLModel models: User, Task
├── schemas.py           # Pydantic request/response schemas
├── routers/
│   └── tasks.py         # Task CRUD endpoints
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── tests/
    ├── conftest.py      # Pytest fixtures (test DB, client)
    ├── test_models.py   # Unit tests for models
    ├── test_database.py # Database connection tests
    └── test_tasks.py    # Integration tests for task endpoints

.env                     # Environment variables (gitignored)
├── DATABASE_URL         # Neon PostgreSQL connection string
└── ENVIRONMENT          # dev/test/prod
```

**Structure Decision**: Web application structure with backend-only implementation. Frontend will be added in future feature. Using flat structure within backend/ for simplicity (single router module initially). Tests colocated with source for easy discovery.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| No authentication middleware | Allows independent testing and validation of data layer before adding auth complexity | Adding auth now would couple two concerns and make debugging harder. Spec explicitly defers auth to next feature. |
| Async database operations | Required for Neon Serverless PostgreSQL and FastAPI async support | Sync operations would block event loop and reduce concurrency under load (100 concurrent users requirement). |

## Phase 0: Research & Decisions

### Research Tasks

1. **SQLModel async patterns with PostgreSQL**
   - How to configure async engine with asyncpg
   - Session management patterns for FastAPI dependencies
   - Best practices for async CRUD operations

2. **Neon PostgreSQL connection configuration**
   - Connection string format for Neon
   - Connection pooling settings for serverless
   - SSL/TLS requirements

3. **FastAPI project structure best practices**
   - Router organization patterns
   - Dependency injection for database sessions
   - Error handling and exception patterns

4. **Testing strategy for async FastAPI**
   - pytest-asyncio configuration
   - Test database setup/teardown
   - httpx AsyncClient for endpoint testing

5. **Timestamp handling in SQLModel**
   - Auto-updating updated_at fields
   - UTC enforcement patterns
   - SQLAlchemy onupdate behavior

### Key Decisions

**Decision 1: SQLModel vs SQLAlchemy Core**
- **Chosen**: SQLModel
- **Rationale**: Combines Pydantic validation with SQLAlchemy ORM, reducing boilerplate. Native FastAPI integration. Simpler for async patterns.
- **Alternatives**: SQLAlchemy Core (more verbose, no Pydantic integration), Raw SQL (no ORM benefits, more error-prone)

**Decision 2: Async vs Sync Database Operations**
- **Chosen**: Async (asyncpg + async SQLAlchemy engine)
- **Rationale**: Required for non-blocking I/O under concurrent load (100 users). FastAPI is async-native.
- **Alternatives**: Sync operations (would block event loop, reduce throughput)

**Decision 3: Router Organization**
- **Chosen**: Single tasks.py router initially
- **Rationale**: Only one resource type (tasks). Can split later if needed.
- **Alternatives**: Separate routers per operation (over-engineering for current scope)

**Decision 4: Error Response Format**
- **Chosen**: RFC 7807 Problem Details format (type, title, detail, status)
- **Rationale**: Industry standard for REST API errors, provides structured error information for clients, enables consistent error handling patterns
- **Alternatives**: Simple HTTPException with detail only (less structured, harder for clients to parse programmatically)

**Decision 5: User Identification Mechanism**
- **Chosen**: X-User-ID request header with UUID format
- **Rationale**: Keeps API paths clean and resource-focused. Separates user context from resource identifiers. Aligns with deferred authentication approach (easy to replace with JWT token extraction later). Prevents user ID enumeration in URLs.
- **Alternatives**: User ID in path (couples user context to every endpoint, verbose URLs), Query parameter (less standard, harder to enforce as required)

**Decision 6: User Record Management**
- **Chosen**: Auto-create user records on first task operation with placeholder email
- **Rationale**: Enables independent API operation without separate user provisioning system. Pragmatic for MVP where authentication is deferred. Maintains referential integrity.
- **Alternatives**: Require pre-created users (adds complexity, needs separate user management), Reject unknown users (blocks testing without user setup)

**Decision 7: Database Migration Strategy**
- **Chosen**: Manual schema creation via SQLModel.metadata.create_all() for MVP
- **Rationale**: Simple, sufficient for initial development. Alembic can be added later.
- **Alternatives**: Alembic migrations (adds complexity, not needed for first iteration)

## Phase 1: Design Artifacts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions, relationships, and validation rules.

**Summary**:
- **User** entity: id (UUID primary key), email (unique, indexed, placeholder format for auto-created users)
- **Task** entity: id (UUID primary key), user_id (UUID FK to User), title (max 200 chars), description (max 2000 chars, nullable), status (enum: pending/completed), created_at (UTC), updated_at (UTC, auto-update)
- **Relationship**: User 1:N Task (cascade delete)
- **User Auto-Creation**: Users are automatically created on first task operation if X-User-ID header contains a UUID not in the database. Email set to "{user_id}@placeholder.local"

### API Contracts

See [contracts/openapi.yaml](./contracts/openapi.yaml) for complete OpenAPI 3.1 specification.

**Endpoints**:
- `GET /api/tasks` - List all tasks for user (user from X-User-ID header)
- `POST /api/tasks` - Create new task (user from X-User-ID header)
- `GET /api/tasks/{task_id}` - Get single task (user from X-User-ID header)
- `PUT /api/tasks/{task_id}` - Update task (user from X-User-ID header)
- `DELETE /api/tasks/{task_id}` - Delete task (user from X-User-ID header)
- `PATCH /api/tasks/{task_id}/complete` - Toggle completion status (user from X-User-ID header)
- `GET /health` - Health check endpoint

**Request Headers**:
- `X-User-ID` (required, UUID format) - Identifies the requesting user

**Error Responses**:
- All errors follow RFC 7807 Problem Details format with fields: type, title, detail, status

### Quickstart Guide

See [quickstart.md](./quickstart.md) for setup instructions, environment configuration, and local development workflow.

## Phase 2: Task Generation

**NOT INCLUDED IN THIS COMMAND** - Run `/sp.tasks` to generate implementation tasks following TDD methodology.

## Implementation Notes

### Critical Path
1. Database connection and models (User, Task with UUID primary keys)
2. X-User-ID header validation middleware (UUID format check, RFC 7807 error responses)
3. User auto-creation logic (on first task operation)
4. Basic CRUD endpoints (GET list, POST create)
5. Ownership filtering (user from X-User-ID header)
6. Remaining endpoints (GET single, PUT, DELETE, PATCH)
7. RFC 7807 error handling for all edge cases
8. Integration tests

### Risk Mitigation
- **Database connection failures**: Implement retry logic and connection pooling, return 503 with RFC 7807 error
- **Concurrent updates**: Use database transactions and optimistic locking if needed (last write wins for MVP)
- **Invalid or missing X-User-ID header**: Validate UUID format and presence, return 400 with RFC 7807 error
- **User auto-creation race conditions**: Use database UPSERT or INSERT ... ON CONFLICT to handle concurrent first requests from same user

### Testing Strategy
- Unit tests for models (validation, relationships, UUID generation)
- Integration tests for each endpoint (happy path + error cases)
- Test database isolation (separate test DB or in-memory SQLite)
- Ownership enforcement tests (cross-user access attempts)
- X-User-ID header validation tests (missing, empty, invalid UUID format)
- User auto-creation tests (first request creates user, subsequent requests reuse)
- RFC 7807 error response format validation for all error scenarios

## Next Steps

1. Review and approve this plan
2. Run `/sp.tasks` to generate test-first implementation tasks
3. Execute tasks following TDD red-green-refactor cycle
4. Run `/sp.adr` if architectural decisions need formal documentation
