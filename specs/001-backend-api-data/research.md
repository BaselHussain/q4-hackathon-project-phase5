# Research & Technical Decisions

**Feature**: Backend API & Data Layer
**Date**: 2026-01-20
**Status**: Complete

## Research Tasks Completed

### 1. SQLModel Async Patterns with PostgreSQL

**Research Question**: How to configure async engine with asyncpg and manage sessions in FastAPI?

**Findings**:
- SQLModel supports async operations via SQLAlchemy 2.0+ async engine
- Use `create_async_engine()` from `sqlalchemy.ext.asyncio`
- Connection string format: `postgresql+asyncpg://user:pass@host/db`
- Session management via `AsyncSession` from `sqlalchemy.ext.asyncio`
- FastAPI dependency pattern: yield session, ensure cleanup in finally block

**Implementation Pattern**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
```

**Best Practices**:
- Set `expire_on_commit=False` to avoid lazy loading issues after commit
- Use `async with` for automatic session cleanup
- Enable `echo=True` in development for SQL logging
- Configure pool size based on expected concurrency (default 5-20 connections)

---

### 2. Neon PostgreSQL Connection Configuration

**Research Question**: What are the connection requirements and best practices for Neon Serverless PostgreSQL?

**Findings**:
- Neon provides standard PostgreSQL connection strings
- Format: `postgresql://user:password@host/dbname?sslmode=require`
- SSL/TLS is required (sslmode=require)
- Supports connection pooling via PgBouncer (built-in)
- Serverless architecture: connections auto-scale, no manual pool management needed
- Async driver (asyncpg) recommended for FastAPI

**Connection String Example**:
```
DATABASE_URL=postgresql+asyncpg://user:password@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Best Practices**:
- Store connection string in environment variable (never commit)
- Use connection pooling (asyncpg handles this automatically)
- Set reasonable timeout values (connect_timeout=10)
- Enable SSL verification in production

---

### 3. FastAPI Project Structure Best Practices

**Research Question**: What is the recommended structure for FastAPI projects with routers and dependencies?

**Findings**:
- Flat structure acceptable for small projects (<5 routers)
- Separate routers by resource type (tasks, users, etc.)
- Database dependencies injected via `Depends(get_db)`
- Exception handling via FastAPI exception handlers or HTTPException
- CORS middleware configured in main.py

**Recommended Structure**:
```
backend/
├── main.py           # App initialization, middleware, health check
├── database.py       # Engine, session, dependencies
├── models.py         # SQLModel ORM models
├── schemas.py        # Pydantic request/response schemas
└── routers/
    └── tasks.py      # Task endpoints
```

**Best Practices**:
- Separate SQLModel models (DB) from Pydantic schemas (API)
- Use APIRouter with prefix and tags for organization
- Include health check endpoint for monitoring
- Configure CORS for frontend access

---

### 4. Testing Strategy for Async FastAPI

**Research Question**: How to test async FastAPI endpoints with pytest?

**Findings**:
- Use `pytest-asyncio` for async test support
- Use `httpx.AsyncClient` for API testing (replaces TestClient for async)
- Create test database fixtures in conftest.py
- Use `@pytest.mark.asyncio` decorator for async tests
- Override dependencies for testing (e.g., test database)

**Test Setup Pattern**:
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_task(test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/tasks/user1", json={...})
        assert response.status_code == 201
```

**Best Practices**:
- Use in-memory SQLite for fast tests (or separate test PostgreSQL DB)
- Reset database between tests (fixtures with cleanup)
- Test both success and error cases
- Use parametrized tests for multiple scenarios

---

### 5. Timestamp Handling in SQLModel

**Research Question**: How to auto-update `updated_at` fields and enforce UTC timestamps?

**Findings**:
- Use SQLAlchemy `func.now()` for default timestamps
- Use `onupdate=func.now()` for auto-updating updated_at
- Store as `DateTime(timezone=True)` for UTC enforcement
- Python datetime objects should use `datetime.utcnow()` or `datetime.now(timezone.utc)`

**Implementation Pattern**:
```python
from datetime import datetime
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

class Task(SQLModel, table=True):
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
```

**Best Practices**:
- Always use timezone-aware datetime objects
- Store in UTC, convert to local timezone in presentation layer
- Use database-level defaults (func.now()) for consistency
- Test timestamp behavior in unit tests

---

## Key Decisions Summary

### Decision 1: SQLModel vs SQLAlchemy Core
- **Chosen**: SQLModel
- **Rationale**: Combines Pydantic validation with SQLAlchemy ORM, reducing boilerplate. Native FastAPI integration. Simpler for async patterns.
- **Alternatives Considered**:
  - SQLAlchemy Core: More verbose, no Pydantic integration, steeper learning curve
  - Raw SQL: No ORM benefits, more error-prone, harder to maintain
- **Trade-offs**: SQLModel is less mature than SQLAlchemy, but benefits outweigh risks for this use case

### Decision 2: Async vs Sync Database Operations
- **Chosen**: Async (asyncpg + async SQLAlchemy engine)
- **Rationale**: Required for non-blocking I/O under concurrent load (100 users requirement). FastAPI is async-native, sync operations would block event loop.
- **Alternatives Considered**:
  - Sync operations: Simpler but would block event loop, reducing throughput
  - Threading: Adds complexity, doesn't scale as well as async
- **Trade-offs**: Async code is slightly more complex, but necessary for performance requirements

### Decision 3: Router Organization
- **Chosen**: Single tasks.py router initially
- **Rationale**: Only one resource type (tasks). Premature abstraction would add unnecessary complexity.
- **Alternatives Considered**:
  - Separate routers per operation: Over-engineering for 6 endpoints
  - Multiple resource routers: No other resources in this feature
- **Trade-offs**: May need to refactor if more resources added, but that's acceptable

### Decision 4: Error Response Format
- **Chosen**: FastAPI HTTPException with detail field
- **Rationale**: Standard FastAPI pattern, automatic OpenAPI documentation, consistent error format
- **Alternatives Considered**:
  - Custom exception classes: Unnecessary complexity for current scope
  - Plain JSON responses: Loses FastAPI integration benefits
- **Trade-offs**: Less flexibility for complex error structures, but sufficient for current needs

### Decision 5: Database Migration Strategy
- **Chosen**: Manual schema creation via SQLModel.metadata.create_all() for MVP
- **Rationale**: Simple, sufficient for initial development. No production deployment yet.
- **Alternatives Considered**:
  - Alembic migrations: Adds complexity, overkill for first iteration
  - Manual SQL scripts: More error-prone, harder to maintain
- **Trade-offs**: Not suitable for production schema changes, but acceptable for MVP. Alembic can be added before production deployment.

### Decision 6: Test Database Strategy
- **Chosen**: In-memory SQLite for unit tests, separate PostgreSQL instance for integration tests
- **Rationale**: SQLite is fast for unit tests, PostgreSQL for realistic integration testing
- **Alternatives Considered**:
  - PostgreSQL only: Slower test execution
  - SQLite only: Doesn't test PostgreSQL-specific behavior
- **Trade-offs**: Need to maintain two database configurations, but worth it for speed and accuracy

### Decision 7: User ID Format
- **Chosen**: UUID (string representation in API, UUID type in database)
- **Rationale**: Globally unique, no collision risk, standard for distributed systems
- **Alternatives Considered**:
  - Integer IDs: Simpler but risk of collision, sequential IDs leak information
  - Custom string IDs: More complexity, no clear benefit
- **Trade-offs**: UUIDs are longer (36 chars), but benefits outweigh storage cost

---

## Unresolved Questions

None - all technical unknowns from Phase 0 have been resolved.

---

## References

- SQLModel Documentation: https://sqlmodel.tiangolo.com/
- FastAPI Async SQL Databases: https://fastapi.tiangolo.com/advanced/async-sql-databases/
- Neon Documentation: https://neon.tech/docs/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- SQLAlchemy 2.0 Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
