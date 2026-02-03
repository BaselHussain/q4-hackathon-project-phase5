# Data Model: MCP Server & Tools

**Feature**: MCP Server & Tools
**Date**: 2026-02-03

## Existing Entities (From Phase 1 & 2)

### Task (Existing - No Changes)

Defined in `backend/src/models/task.py`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key, Auto-generated | Unique task identifier |
| user_id | UUID | Foreign Key → users.id, NOT NULL, Indexed | Owner of the task |
| title | VARCHAR(200) | NOT NULL, min 1 char | Task title |
| description | VARCHAR(2000) | NULL | Optional task description |
| status | ENUM('pending', 'completed') | NOT NULL, default 'pending' | Task status |
| created_at | TIMESTAMP WITH TIMEZONE | NOT NULL, auto-generated | Creation timestamp |
| updated_at | TIMESTAMP WITH TIMEZONE | NOT NULL, auto-updated | Last modification timestamp |

**Relationships**:
- Belongs to User (user_id → users.id)
- ON DELETE CASCADE when user is deleted

### User (Existing - No Changes)

Defined in `backend/src/models/user.py`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key, Auto-generated | Unique user identifier |
| email | VARCHAR(254) | UNIQUE, NOT NULL, Indexed | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| created_at | TIMESTAMP WITH TIMEZONE | NOT NULL, auto-generated | Account creation timestamp |
| last_login_at | TIMESTAMP WITH TIMEZONE | NULL | Last successful login |

## MCP Tool Response Schemas

### ToolResponse (New - Runtime Only)

Used for all tool responses. Not persisted to database.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| success | boolean | YES | Whether operation succeeded |
| data | object/array | NO | Payload on success |
| error | string | NO | Error message on failure |

### TaskData (Subset of Task for Tool Responses)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| task_id | string (UUID) | YES | Task identifier |
| title | string | YES | Task title |
| description | string | NO | Task description |
| status | string | YES | "pending" or "completed" |
| created_at | string (ISO8601) | YES | Creation timestamp |
| updated_at | string (ISO8601) | YES | Last update timestamp |

## Tool Parameter Schemas

### add_task Parameters

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| user_id | string (UUID) | YES | Valid UUID format |
| title | string | YES | 1-200 characters |
| description | string | NO | 0-2000 characters |

### list_tasks Parameters

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| user_id | string (UUID) | YES | Valid UUID format |
| status | string | NO | "all", "pending", or "completed" (default: "all") |

### complete_task Parameters

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| user_id | string (UUID) | YES | Valid UUID format |
| task_id | string (UUID) | YES | Valid UUID format |

### delete_task Parameters

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| user_id | string (UUID) | YES | Valid UUID format |
| task_id | string (UUID) | YES | Valid UUID format |

### update_task Parameters

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| user_id | string (UUID) | YES | Valid UUID format |
| task_id | string (UUID) | YES | Valid UUID format |
| title | string | NO | 1-200 characters |
| description | string | NO | 0-2000 characters |

**Note**: At least one of `title` or `description` must be provided.

## State Transitions

### Task Status State Machine

```
[Created] ──add_task──▶ [Pending] ──complete_task──▶ [Completed]
                            │                              │
                            │      (complete_task on       │
                            │       completed = no-op)     │
                            │                              │
                            ▼                              ▼
                      [Deleted]◀──delete_task────────[Deleted]
```

## No New Tables Required

This feature uses existing Phase 1 tables only:
- `tasks` table: No schema changes
- `users` table: No schema changes (referenced for ownership validation)

The MCP server operates as a stateless layer that reads/writes to existing tables.
