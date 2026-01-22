# Data Model

**Feature**: Backend API & Data Layer
**Date**: 2026-01-20
**Status**: Complete

## Overview

This document defines the data entities, relationships, and validation rules for the multi-user todo application backend. The model enforces task ownership at the database level and maintains data integrity through constraints and relationships.

## Entity Definitions

### User Entity

Represents a person using the application. Users own tasks and are identified by a unique UUID.

**Table Name**: `users`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the user |
| email | String(255) | UNIQUE, NOT NULL, INDEXED | User's email address |

**Validation Rules**:
- `email` must be a valid email format (validated at application layer)
- `email` must be unique across all users (enforced by database constraint)
- `id` is auto-generated as UUID v4

**Indexes**:
- Primary key index on `id` (automatic)
- Unique index on `email` for fast lookup and uniqueness enforcement

**SQLModel Definition**:
```python
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
```

---

### Task Entity

Represents a single item on a user's todo list. Tasks belong to exactly one user and track completion status with timestamps.

**Table Name**: `tasks`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the task |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL, INDEXED | Owner of the task |
| title | String(200) | NOT NULL | Task title/summary |
| description | String(2000) | NULLABLE | Detailed task description |
| status | Enum | NOT NULL, DEFAULT 'pending' | Task completion status (pending/completed) |
| created_at | DateTime(UTC) | NOT NULL, DEFAULT now() | Timestamp when task was created |
| updated_at | DateTime(UTC) | NOT NULL, DEFAULT now(), ON UPDATE now() | Timestamp when task was last modified |

**Validation Rules**:
- `title` must not be empty (length >= 1, <= 200 characters)
- `description` is optional, max 2000 characters if provided
- `status` must be one of: "pending", "completed"
- `user_id` must reference an existing user (foreign key constraint)
- `created_at` and `updated_at` must be timezone-aware (UTC)
- `updated_at` automatically updates on any field change

**Indexes**:
- Primary key index on `id` (automatic)
- Foreign key index on `user_id` for efficient ownership queries
- Composite index on `(user_id, created_at)` for sorted task lists

**Relationships**:
- Many-to-One relationship with User (many tasks belong to one user)
- Cascade delete: when a user is deleted, all their tasks are deleted

**SQLModel Definition**:
```python
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, Enum as SQLEnum, func
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column(SQLEnum(TaskStatus))
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )

    # Relationship (optional, for ORM navigation)
    # user: User = Relationship(back_populates="tasks")
```

---

## Entity Relationships

### User → Task (One-to-Many)

**Relationship Type**: One-to-Many
**Cardinality**: One User has zero or more Tasks
**Foreign Key**: `tasks.user_id` → `users.id`
**Cascade Behavior**: DELETE CASCADE (deleting a user deletes all their tasks)

**Rationale**:
- Each task must have exactly one owner (enforced by NOT NULL constraint on user_id)
- Users can have multiple tasks (no upper limit at database level)
- Cascade delete ensures no orphaned tasks remain when a user is deleted

**Database Constraint**:
```sql
ALTER TABLE tasks
ADD CONSTRAINT fk_task_user
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE CASCADE;
```

---

## Data Integrity Rules

### Constraints

1. **Primary Key Constraints**:
   - `users.id` is unique and not null
   - `tasks.id` is unique and not null

2. **Foreign Key Constraints**:
   - `tasks.user_id` must reference a valid `users.id`
   - Cascade delete: deleting a user deletes all their tasks

3. **Unique Constraints**:
   - `users.email` must be unique across all users

4. **Not Null Constraints**:
   - All fields except `tasks.description` are required

5. **Check Constraints** (application-level):
   - `tasks.title` length: 1-200 characters
   - `tasks.description` length: 0-2000 characters (if provided)
   - `tasks.status` must be "pending" or "completed"

### Validation Rules (Application Layer)

1. **User Validation**:
   - Email format validation (RFC 5322 compliant)
   - Email uniqueness check before insert

2. **Task Validation**:
   - Title must not be empty or whitespace-only
   - Description is optional but limited to 2000 characters
   - Status must be valid enum value
   - User ID must exist in users table

3. **Timestamp Validation**:
   - All timestamps stored in UTC
   - `created_at` is immutable after creation
   - `updated_at` automatically updates on modification

---

## State Transitions

### Task Status State Machine

```
┌─────────┐
│ pending │ ◄──┐
└────┬────┘    │
     │         │
     │ PATCH   │ PATCH
     │ /complete│ /complete
     │         │
     ▼         │
┌───────────┐ │
│ completed ├─┘
└───────────┘
```

**Valid Transitions**:
- `pending` → `completed` (via PATCH /api/tasks/{user_id}/{task_id}/complete)
- `completed` → `pending` (via PATCH /api/tasks/{user_id}/{task_id}/complete - toggle)

**Invalid Transitions**:
- None (only two states, toggle is always valid)

**Business Rules**:
- Tasks are created with status "pending" by default
- Status can be toggled between pending and completed any number of times
- Deleting a task removes it regardless of status

---

## Database Schema (SQL DDL)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE INDEX idx_users_email ON users(email);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(2000),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_user_created ON tasks(user_id, created_at);

-- Trigger for auto-updating updated_at (PostgreSQL)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tasks_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

## Data Access Patterns

### Common Queries

1. **Get all tasks for a user** (sorted by creation date):
   ```sql
   SELECT * FROM tasks
   WHERE user_id = $1
   ORDER BY created_at DESC;
   ```
   - Uses index: `idx_tasks_user_created`
   - Expected performance: O(log n) + O(k) where k = number of user's tasks

2. **Get single task with ownership check**:
   ```sql
   SELECT * FROM tasks
   WHERE id = $1 AND user_id = $2;
   ```
   - Uses index: Primary key on `id`
   - Expected performance: O(log n)

3. **Create task**:
   ```sql
   INSERT INTO tasks (id, user_id, title, description, status)
   VALUES ($1, $2, $3, $4, 'pending')
   RETURNING *;
   ```
   - Expected performance: O(log n) for index updates

4. **Update task with ownership check**:
   ```sql
   UPDATE tasks
   SET title = $1, description = $2, updated_at = NOW()
   WHERE id = $3 AND user_id = $4
   RETURNING *;
   ```
   - Expected performance: O(log n)

5. **Delete task with ownership check**:
   ```sql
   DELETE FROM tasks
   WHERE id = $1 AND user_id = $2
   RETURNING id;
   ```
   - Expected performance: O(log n)

---

## Performance Considerations

1. **Indexes**:
   - Primary key indexes on `id` fields for fast lookups
   - Index on `users.email` for authentication queries
   - Index on `tasks.user_id` for ownership filtering
   - Composite index on `(user_id, created_at)` for sorted task lists

2. **Query Optimization**:
   - Always include `user_id` in WHERE clause for task queries (uses index)
   - Limit result sets at application layer (max 1000 tasks per user)
   - Use prepared statements to avoid SQL injection and improve performance

3. **Connection Pooling**:
   - Use asyncpg connection pool (default 10 connections)
   - Configure based on expected concurrent users (100 users → 10-20 connections)

4. **Scalability**:
   - Current design supports up to 1000 tasks per user efficiently
   - For larger datasets, consider pagination (not in current scope)
   - Indexes support efficient queries up to millions of tasks

---

## Migration Strategy

**Initial Schema Creation**:
- Use SQLModel `metadata.create_all()` for MVP
- Creates tables, indexes, and constraints automatically

**Future Migrations**:
- Add Alembic before production deployment
- Track schema changes in version-controlled migration files
- Support rollback for failed migrations

**Data Seeding** (for testing):
- Create test users and tasks in test fixtures
- Use factory pattern for generating test data
- Ensure test data cleanup between test runs
