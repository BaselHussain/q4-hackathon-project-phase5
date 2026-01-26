# Data Model: Authentication & User Management

**Feature**: 002-auth-user-management
**Date**: 2026-01-22
**Purpose**: Define database schema and entity relationships for user authentication

## Overview

This document defines the data model for user authentication, including the new `users` table and updates to the existing `tasks` table to support user ownership and isolation.

## Entity Relationship Diagram

```
┌─────────────────────────┐
│        users            │
├─────────────────────────┤
│ id (UUID, PK)          │
│ email (VARCHAR, UNIQUE)│
│ password_hash (VARCHAR)│
│ created_at (TIMESTAMP) │
│ last_login_at (TIMESTAMP)│
└─────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────┐
│        tasks            │
├─────────────────────────┤
│ id (UUID, PK)          │
│ user_id (UUID, FK) ←───┘
│ title (VARCHAR)        │
│ description (TEXT)     │
│ status (VARCHAR)       │
│ created_at (TIMESTAMP) │
│ updated_at (TIMESTAMP) │
└─────────────────────────┘
```

**Relationship**: One user owns many tasks (1:N)
**Cascade**: When a user is deleted, all their tasks are deleted (ON DELETE CASCADE)

## Entities

### User Entity

**Purpose**: Represents a registered user with authentication credentials

**Table Name**: `users`

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique user identifier |
| email | VARCHAR(254) | NOT NULL, UNIQUE | User's email address (lowercase) |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password with salt |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |
| last_login_at | TIMESTAMP | NULL | Last successful login timestamp |

**Indexes**:
- PRIMARY KEY on `id` (automatic)
- UNIQUE INDEX on `email` (automatic with UNIQUE constraint)

**Validation Rules**:
- Email must be valid RFC 5322 format
- Email max length: 254 characters
- Email stored in lowercase for case-insensitive comparison
- Password hash must be bcrypt format (60 characters)
- Password hash never exposed in API responses

**SQLModel Definition**:

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=254, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    # Relationship (not stored in DB, for ORM navigation)
    # tasks: List["Task"] = Relationship(back_populates="user")
```

**Business Rules**:
1. Email must be unique across all users
2. Email is case-insensitive (stored lowercase)
3. Password must meet complexity requirements before hashing:
   - Minimum 8 characters
   - Maximum 128 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number
   - At least one special character
4. `last_login_at` updated on successful login
5. User deletion cascades to all owned tasks

### Task Entity (Updated)

**Purpose**: Represents a todo item owned by a user

**Table Name**: `tasks`

**Columns** (NEW column in bold):

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique task identifier |
| **user_id** | **UUID** | **NOT NULL, FOREIGN KEY → users(id)** | **Owner of this task** |
| title | VARCHAR(200) | NOT NULL | Task title |
| description | TEXT | NULL | Task description (optional) |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Task status (pending/completed) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Task creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
- PRIMARY KEY on `id` (existing)
- **INDEX on `user_id` (NEW)** - For efficient user task queries
- FOREIGN KEY `user_id` REFERENCES `users(id)` ON DELETE CASCADE

**Validation Rules**:
- Title max length: 200 characters
- Description max length: 2000 characters
- Status must be 'pending' or 'completed'
- user_id must reference existing user

**SQLModel Definition** (Updated):

```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)  # NEW
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: str = Field(default="pending", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship (not stored in DB, for ORM navigation)
    # user: Optional[User] = Relationship(back_populates="tasks")
```

**Business Rules**:
1. Every task must have an owner (user_id NOT NULL)
2. Tasks are isolated by user - users can only access their own tasks
3. When user is deleted, all their tasks are deleted (CASCADE)
4. `updated_at` refreshed on any field change

## Database Migration

### Migration Script: 002_add_users_table.py

**Purpose**: Add users table and update tasks table with user_id foreign key

**Alembic Migration**:

```python
"""Add users table and user_id to tasks

Revision ID: 002
Revises: 001
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(254), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.TIMESTAMP, nullable=True)
    )

    # Create index on email
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Add user_id column to tasks table
    op.add_column('tasks', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create index on user_id
    op.create_index('ix_tasks_user_id', 'tasks', ['user_id'])

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_tasks_user_id',
        'tasks', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

    # Note: Existing tasks will have NULL user_id
    # Manual data migration required if existing tasks need to be assigned to users

def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_tasks_user_id', 'tasks', type_='foreignkey')

    # Drop index
    op.drop_index('ix_tasks_user_id', 'tasks')

    # Remove user_id column
    op.drop_column('tasks', 'user_id')

    # Drop users table indexes
    op.drop_index('ix_users_email', 'users')

    # Drop users table
    op.drop_table('users')
```

**Migration Notes**:
1. Existing tasks will have NULL `user_id` after migration
2. If existing tasks need to be preserved, manual data migration required
3. After migration, all new tasks must have `user_id` (enforced by application)
4. Consider making `user_id` NOT NULL in a follow-up migration after data cleanup

## Data Access Patterns

### Common Queries

**1. Find user by email (login)**:
```sql
SELECT id, email, password_hash, last_login_at
FROM users
WHERE email = LOWER($1);
```

**2. Get all tasks for a user**:
```sql
SELECT id, title, description, status, created_at, updated_at
FROM tasks
WHERE user_id = $1
ORDER BY created_at DESC;
```

**3. Get specific task with ownership check**:
```sql
SELECT id, title, description, status, created_at, updated_at
FROM tasks
WHERE id = $1 AND user_id = $2;
```

**4. Create new user**:
```sql
INSERT INTO users (email, password_hash)
VALUES (LOWER($1), $2)
RETURNING id, email, created_at;
```

**5. Update last login timestamp**:
```sql
UPDATE users
SET last_login_at = CURRENT_TIMESTAMP
WHERE id = $1;
```

### Performance Considerations

**Indexes**:
- `users.email` (UNIQUE): Fast login lookups
- `tasks.user_id`: Fast user task queries
- `tasks.id` (PRIMARY KEY): Fast individual task lookups

**Query Optimization**:
- Email lookups use index (O(log n))
- User task queries use index (O(log n))
- Ownership checks combine both indexes efficiently

**Expected Query Performance**:
- User lookup by email: <5ms
- Get all user tasks: <10ms (for 100 tasks)
- Task ownership check: <5ms

## Data Integrity

### Constraints

**Primary Keys**:
- `users.id`: Ensures unique user identification
- `tasks.id`: Ensures unique task identification

**Foreign Keys**:
- `tasks.user_id → users.id`: Ensures referential integrity
- ON DELETE CASCADE: Automatic cleanup of orphaned tasks

**Unique Constraints**:
- `users.email`: Prevents duplicate accounts

**Not Null Constraints**:
- `users.email`: Every user must have email
- `users.password_hash`: Every user must have password
- `tasks.user_id`: Every task must have owner (after migration)
- `tasks.title`: Every task must have title

### Data Validation

**Application-Level Validation** (before database):
1. Email format (RFC 5322)
2. Email length (max 254 chars)
3. Password complexity (before hashing)
4. Password length (8-128 chars)
5. Task title length (max 200 chars)
6. Task description length (max 2000 chars)

**Database-Level Validation**:
1. Email uniqueness (UNIQUE constraint)
2. Foreign key validity (FK constraint)
3. Not null requirements (NOT NULL constraints)
4. Length limits (VARCHAR constraints)

## Security Considerations

### Sensitive Data

**Password Storage**:
- Never store plain text passwords
- Use bcrypt hashing with automatic salt
- Password hash stored in `password_hash` column
- Hash format: `$2b$12$...` (60 characters)

**Data Exposure**:
- Password hash NEVER returned in API responses
- Email addresses may be logged for security events
- User IDs are UUIDs (not sequential, harder to enumerate)

### Access Control

**User Isolation**:
- All task queries filtered by `user_id`
- Authorization check: JWT user_id must match path user_id
- Database-level isolation via foreign key constraints

**Audit Trail**:
- `created_at`: Track when user registered
- `last_login_at`: Track user activity
- Security events logged separately (not in database)

## Testing Data

### Test Users

```sql
-- Test user 1
INSERT INTO users (id, email, password_hash, created_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    'alice@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sC',
    '2026-01-22 10:00:00'
);

-- Test user 2
INSERT INTO users (id, email, password_hash, created_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440002',
    'bob@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS.sD',
    '2026-01-22 10:05:00'
);

-- Test tasks for Alice
INSERT INTO tasks (id, user_id, title, status, created_at)
VALUES (
    '660e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440001',
    'Alice Task 1',
    'pending',
    '2026-01-22 10:10:00'
);

-- Test tasks for Bob
INSERT INTO tasks (id, user_id, title, status, created_at)
VALUES (
    '660e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440002',
    'Bob Task 1',
    'pending',
    '2026-01-22 10:15:00'
);
```

## Future Enhancements

### Potential Schema Changes

1. **User Profiles**: Add `name`, `avatar_url`, `bio` columns
2. **Email Verification**: Add `email_verified`, `verification_token` columns
3. **Account Status**: Add `is_active`, `is_locked` columns
4. **Password Reset**: Add `reset_token`, `reset_token_expires` columns
5. **Session Tracking**: New `sessions` table for active token management
6. **Audit Log**: New `audit_log` table for user activity tracking

### Scalability Considerations

**Current Design** (sufficient for MVP):
- Single database instance
- Simple indexes
- No partitioning

**Future Scaling** (if needed):
- Partition `tasks` table by `user_id` for large datasets
- Add read replicas for query performance
- Consider caching layer (Redis) for frequent queries
- Archive old tasks to separate table

## Summary

**New Tables**: 1 (users)
**Modified Tables**: 1 (tasks - add user_id)
**New Indexes**: 2 (users.email, tasks.user_id)
**Foreign Keys**: 1 (tasks.user_id → users.id)
**Migration Complexity**: Low (straightforward schema addition)

**Data Model Status**: ✅ Complete and ready for implementation
