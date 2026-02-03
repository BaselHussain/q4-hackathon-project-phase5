# Feature Specification: MCP Server & Tools

**Feature Branch**: `mcp-tools`
**Created**: 2026-02-03
**Status**: Draft
**Input**: Build a stateless MCP server using Official MCP SDK that exposes todo task operations as tools for the AI agent in Phase 3.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Agent Adds Task via MCP Tool (Priority: P1)

The AI agent receives a natural language request from a user to add a task. The agent invokes the `add_task` MCP tool with the user's ID, task title, and optional description. The tool creates the task in the database and returns confirmation with the new task ID.

**Why this priority**: Adding tasks is the foundational operation. Without the ability to create tasks, no other task management is possible. This enables the core "add a todo" conversational feature.

**Independent Test**: Can be fully tested by invoking `add_task` tool directly with valid parameters and verifying task appears in database with correct owner.

**Acceptance Scenarios**:

1. **Given** a valid user_id and task title, **When** add_task is invoked, **Then** a new task is created in the database with status "pending" and the tool returns task_id, title, status, and created timestamp
2. **Given** a valid user_id, title, and description, **When** add_task is invoked, **Then** the task is created with both title and description stored
3. **Given** an empty or missing title, **When** add_task is invoked, **Then** a friendly error is returned stating "Task title is required"

---

### User Story 2 - AI Agent Lists Tasks via MCP Tool (Priority: P1)

The AI agent needs to retrieve a user's tasks to answer questions like "what are my tasks?" or "show completed todos". The agent invokes `list_tasks` with user_id and optional status filter. The tool queries the database and returns an array of tasks.

**Why this priority**: Listing tasks is essential for the AI to provide context-aware responses. Users frequently want to see their tasks, making this a core interaction.

**Independent Test**: Can be fully tested by creating sample tasks for a user, then invoking `list_tasks` and verifying the returned array matches expected tasks.

**Acceptance Scenarios**:

1. **Given** a user_id with existing tasks, **When** list_tasks is invoked with no status filter, **Then** all tasks (pending and completed) for that user are returned
2. **Given** a user_id, **When** list_tasks is invoked with status="pending", **Then** only pending tasks for that user are returned
3. **Given** a user_id, **When** list_tasks is invoked with status="completed", **Then** only completed tasks for that user are returned
4. **Given** a user_id with no tasks, **When** list_tasks is invoked, **Then** an empty array is returned (not an error)

---

### User Story 3 - AI Agent Completes Task via MCP Tool (Priority: P2)

The AI agent receives a request to mark a task as done. The agent invokes `complete_task` with user_id and task_id. The tool updates the task status to "completed" in the database.

**Why this priority**: Completing tasks is a key user action but depends on tasks existing first. This enables the "mark done" conversational feature.

**Independent Test**: Can be fully tested by creating a pending task, invoking `complete_task`, and verifying the task status changed to "completed".

**Acceptance Scenarios**:

1. **Given** a valid user_id and task_id for a pending task, **When** complete_task is invoked, **Then** the task status is updated to "completed" and the tool returns the updated task
2. **Given** a valid user_id and task_id for an already completed task, **When** complete_task is invoked, **Then** the task remains completed and no error is thrown
3. **Given** a task_id that belongs to a different user, **When** complete_task is invoked, **Then** a friendly error is returned: "Task not found or access denied"
4. **Given** a non-existent task_id, **When** complete_task is invoked, **Then** a friendly error is returned: "Task not found or access denied"

---

### User Story 4 - AI Agent Deletes Task via MCP Tool (Priority: P2)

The AI agent receives a request to remove a task. The agent invokes `delete_task` with user_id and task_id. The tool permanently removes the task from the database.

**Why this priority**: Deleting tasks allows users to clean up their todo list. Important but less frequent than add/list/complete operations.

**Independent Test**: Can be fully tested by creating a task, invoking `delete_task`, and verifying the task no longer exists in the database.

**Acceptance Scenarios**:

1. **Given** a valid user_id and task_id, **When** delete_task is invoked, **Then** the task is permanently removed and the tool returns confirmation
2. **Given** a task_id that belongs to a different user, **When** delete_task is invoked, **Then** a friendly error is returned: "Task not found or access denied"
3. **Given** a non-existent task_id, **When** delete_task is invoked, **Then** a friendly error is returned: "Task not found or access denied"

---

### User Story 5 - AI Agent Updates Task via MCP Tool (Priority: P3)

The AI agent receives a request to modify a task's title or description. The agent invokes `update_task` with user_id, task_id, and optional new title/description. The tool updates the specified fields.

**Why this priority**: Updating tasks is useful but least frequent among the five operations. Users more commonly add, complete, or delete rather than edit.

**Independent Test**: Can be fully tested by creating a task, invoking `update_task` with new values, and verifying the changes are persisted.

**Acceptance Scenarios**:

1. **Given** a valid user_id, task_id, and new title, **When** update_task is invoked, **Then** the task title is updated and the tool returns the updated task
2. **Given** a valid user_id, task_id, and new description, **When** update_task is invoked, **Then** the task description is updated
3. **Given** both title and description provided, **When** update_task is invoked, **Then** both fields are updated
4. **Given** neither title nor description provided, **When** update_task is invoked, **Then** a friendly error is returned: "At least one field (title or description) must be provided"
5. **Given** a task_id that belongs to a different user, **When** update_task is invoked, **Then** a friendly error is returned: "Task not found or access denied"

---

### Edge Cases

- **Concurrent modifications**: If two requests try to modify the same task simultaneously, the last write wins (database handles this)
- **Invalid UUID format**: If task_id or user_id is not a valid UUID, return friendly error: "Invalid ID format"
- **Database connection failure**: If database is unreachable, return friendly error: "Service temporarily unavailable, please try again"
- **Title length validation**: If title exceeds 200 characters, return friendly error: "Task title must be 200 characters or less"
- **Description length validation**: If description exceeds 2000 characters, return friendly error: "Task description must be 2000 characters or less"

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: MCP server MUST expose exactly 5 tools: add_task, list_tasks, complete_task, delete_task, update_task
- **FR-002**: All tools MUST be stateless - no in-memory state between invocations, all data read from and written to database
- **FR-003**: All tools MUST accept user_id as a parameter to enforce user isolation
- **FR-004**: All tools MUST verify task ownership before performing operations (user can only access their own tasks)
- **FR-005**: All tools MUST return structured responses with consistent format (task_id, status, title, description, timestamps as applicable)
- **FR-006**: All tools MUST handle errors gracefully with user-friendly messages (no stack traces or technical jargon)
- **FR-007**: The add_task tool MUST create tasks with status "pending" by default
- **FR-008**: The list_tasks tool MUST support filtering by status (all, pending, completed)
- **FR-009**: The complete_task tool MUST update task status to "completed"
- **FR-010**: The delete_task tool MUST permanently remove tasks from the database
- **FR-011**: The update_task tool MUST allow updating title and/or description fields only
- **FR-012**: MCP server MUST use the existing tasks table schema from Phase 1 (UUID id, user_id, title, description, status, created_at, updated_at)
- **FR-013**: MCP server MUST connect to Neon PostgreSQL using DATABASE_URL from environment
- **FR-014**: Tool responses MUST be JSON-formatted for AI agent parsing

### Key Entities

- **Task**: Represents a user's todo item with id (UUID), user_id (UUID), title (string, max 200), description (string, max 2000, optional), status (pending/completed), created_at (timestamp), updated_at (timestamp)
- **Tool Response**: Structured JSON returned by each tool containing success/error status, data payload (task or array of tasks), and optional error message

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: MCP server starts and registers all 5 tools within 5 seconds of launch
- **SC-002**: Each tool operation completes and returns response within 2 seconds under normal conditions
- **SC-003**: 100% of tool invocations enforce user ownership (no cross-user data access possible)
- **SC-004**: All tool errors return user-friendly messages (no technical stack traces exposed)
- **SC-005**: Tool responses are valid JSON parseable by standard JSON parsers
- **SC-006**: Server maintains zero in-memory state between requests (verified by server restart having no impact on data)
- **SC-007**: All CRUD operations correctly persist to database (add creates row, complete updates status, delete removes row, update modifies fields)

## Assumptions

- The existing tasks table from Phase 1 is available and has the schema: id (UUID), user_id (UUID), title (VARCHAR 200), description (VARCHAR 2000), status (enum: pending/completed), created_at, updated_at
- The existing User model and users table from Phase 2 are available for user_id validation
- DATABASE_URL environment variable is configured with valid Neon PostgreSQL connection string
- The MCP server will be invoked by the AI agent (Spec 2) - no direct user interaction with MCP tools
- JWT authentication happens at the API layer (Spec 2), not within MCP tools - tools trust the user_id passed to them
