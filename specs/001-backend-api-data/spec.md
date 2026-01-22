# Feature Specification: Backend API & Data Layer

**Feature Branch**: `001-backend-api-data`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "Backend API & Data Layer (Spec 1) - Build a new FastAPI backend from scratch for multi-user todo app with persistent storage in Neon PostgreSQL."

## Clarifications

### Session 2026-01-21

- Q: How should errors be communicated to API clients (format and structure)? → A: HTTP status codes + JSON body with error details following RFC 7807 format (type, title, detail, status)
- Q: How is the user identifier transmitted in API requests and what format does it use? → A: User ID in custom header `X-User-ID` with UUID format
- Q: What format should task identifiers use? → A: UUID (globally unique, non-sequential)
- Q: How are user records created and what happens when a request arrives with a user ID that doesn't exist? → A: Auto-create user records on first task operation if user ID doesn't exist (with placeholder email)
- Q: What happens when the X-User-ID header is missing, empty, or contains an invalid UUID format? → A: Return 400 Bad Request with RFC 7807 error

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Personal Task List (Priority: P1)

A user wants to see all their tasks in one place to understand what needs to be done. The system retrieves and displays only the tasks that belong to the requesting user, ensuring privacy and data isolation between users.

**Why this priority**: This is the core read operation that enables users to interact with their task data. Without this, users cannot see what tasks exist, making all other operations meaningless.

**Independent Test**: Can be fully tested by creating a user with several tasks, requesting their task list, and verifying that only their tasks are returned (not tasks from other users).

**Acceptance Scenarios**:

1. **Given** a user has 5 tasks in the system, **When** they request their task list, **Then** all 5 tasks are returned with complete details
2. **Given** a user has no tasks, **When** they request their task list, **Then** an empty list is returned
3. **Given** multiple users exist with tasks, **When** User A requests their task list, **Then** only User A's tasks are returned (not User B's tasks)

---

### User Story 2 - Create New Task (Priority: P1)

A user wants to add a new task to their list so they can track something they need to do. The system creates the task with the provided information and associates it with the user.

**Why this priority**: This is the core write operation that allows users to populate their task list. Without this, users cannot add tasks and the system has no data to work with.

**Independent Test**: Can be fully tested by submitting a new task with title and description, then verifying it appears in the user's task list with correct details and default status.

**Acceptance Scenarios**:

1. **Given** a user provides a task title and description, **When** they create a task, **Then** the task is saved with status "pending" and appears in their task list
2. **Given** a user provides only a task title (no description), **When** they create a task, **Then** the task is saved successfully with an empty description
3. **Given** a user creates a task, **When** the task is saved, **Then** it includes creation and update timestamps

---

### User Story 3 - Mark Task as Complete (Priority: P2)

A user wants to mark a task as complete to track their progress and distinguish finished work from pending items. The system updates the task status and preserves the completion state.

**Why this priority**: This enables the primary workflow of task management - marking things as done. It's essential for the app's core value proposition but depends on tasks existing first.

**Independent Test**: Can be fully tested by creating a pending task, marking it complete, and verifying the status changes and persists across requests.

**Acceptance Scenarios**:

1. **Given** a user has a pending task, **When** they mark it as complete, **Then** the task status changes to "completed"
2. **Given** a user has a completed task, **When** they toggle completion again, **Then** the task status changes back to "pending"
3. **Given** a user marks a task complete, **When** they retrieve their task list, **Then** the task shows as completed

---

### User Story 4 - Update Task Details (Priority: P2)

A user wants to modify a task's title or description to correct mistakes or update information as their needs change. The system updates the task while preserving its identity and history.

**Why this priority**: This provides flexibility for users to refine their tasks over time. It's important for usability but not critical for the MVP.

**Independent Test**: Can be fully tested by creating a task, updating its title and/or description, and verifying the changes persist while other attributes remain unchanged.

**Acceptance Scenarios**:

1. **Given** a user has a task, **When** they update the title, **Then** the new title is saved and the update timestamp is refreshed
2. **Given** a user has a task, **When** they update the description, **Then** the new description is saved
3. **Given** a user updates a task, **When** they retrieve it, **Then** all other attributes (status, creation date) remain unchanged

---

### User Story 5 - View Single Task Details (Priority: P3)

A user wants to view the complete details of a specific task to review all information about it. The system retrieves and displays the full task information.

**Why this priority**: This is a convenience feature for detailed task inspection. Users can already see tasks in the list view, so this is lower priority.

**Independent Test**: Can be fully tested by creating a task and requesting it by its identifier, verifying all details are returned correctly.

**Acceptance Scenarios**:

1. **Given** a user has a task, **When** they request it by identifier, **Then** all task details are returned
2. **Given** a user requests a task that doesn't exist, **When** the system processes the request, **Then** an appropriate error is returned
3. **Given** a user requests another user's task, **When** the system processes the request, **Then** access is denied

---

### User Story 6 - Delete Task (Priority: P3)

A user wants to permanently remove a task they no longer need. The system deletes the task and removes it from the user's list.

**Why this priority**: This is a cleanup operation that's useful but not essential for core functionality. Users can work around this by marking tasks complete.

**Independent Test**: Can be fully tested by creating a task, deleting it, and verifying it no longer appears in the task list or can be retrieved.

**Acceptance Scenarios**:

1. **Given** a user has a task, **When** they delete it, **Then** the task is permanently removed from the system
2. **Given** a user deletes a task, **When** they request their task list, **Then** the deleted task does not appear
3. **Given** a user tries to delete another user's task, **When** the system processes the request, **Then** access is denied

---

### Edge Cases

- What happens when the X-User-ID header is missing, empty, or not a valid UUID? → Return 400 with RFC 7807 error body (type: "invalid-user-id", title: "Invalid User ID", detail: specific validation message, status: 400)
- What happens when a user tries to access a task that doesn't exist? → Return 404 with RFC 7807 error body (type: "task-not-found", title: "Task Not Found", detail: specific message, status: 404)
- What happens when a user tries to access another user's task? → Return 403 with RFC 7807 error body (type: "access-denied", title: "Access Denied", detail: "You do not have permission to access this task", status: 403)
- What happens when a user provides an invalid task identifier format? → Return 400 with RFC 7807 error body (type: "invalid-identifier", title: "Invalid Identifier", detail: specific validation message, status: 400)
- What happens when a user tries to create a task with an extremely long title or description? → Return 400 with RFC 7807 error body (type: "validation-error", title: "Validation Error", detail: field-specific message about length limits, status: 400)
- What happens when the database connection is lost during an operation? → Return 503 with RFC 7807 error body (type: "service-unavailable", title: "Service Unavailable", detail: "Database temporarily unavailable", status: 503)
- What happens when a user tries to update a task that was deleted by another process? → Return 404 with RFC 7807 error body (same as task-not-found)
- What happens when multiple requests try to update the same task simultaneously? → Last write wins (database-level handling with updated_at timestamp refresh)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store tasks persistently so they survive application restarts
- **FR-002**: System MUST associate each task with exactly one user (owner)
- **FR-003**: System MUST prevent users from accessing tasks they don't own
- **FR-004**: System MUST allow users to create tasks with a title and optional description
- **FR-005**: System MUST track task status as either "pending" or "completed"
- **FR-006**: System MUST record creation timestamp for each task
- **FR-007**: System MUST record last update timestamp for each task
- **FR-008**: System MUST allow users to retrieve all their tasks
- **FR-009**: System MUST allow users to retrieve a specific task by identifier
- **FR-010**: System MUST allow users to update task title and description
- **FR-011**: System MUST allow users to toggle task completion status
- **FR-012**: System MUST allow users to permanently delete tasks
- **FR-013**: System MUST validate that task titles are not empty
- **FR-014**: System MUST update the task's update timestamp whenever any field changes
- **FR-015**: System MUST store user information (identifier and email) for task ownership
- **FR-016**: System MUST auto-create user records on first task operation if the user ID from `X-User-ID` header doesn't exist, using a placeholder email format (e.g., "{user_id}@placeholder.local")

### Key Entities

- **User**: Represents a person using the application. Has a unique UUID identifier and email address. Owns zero or more tasks.
- **Task**: Represents a single item on a user's todo list. Contains a UUID identifier, title (required), optional description, completion status (pending or completed), owner reference (user UUID), creation timestamp, and last update timestamp. Belongs to exactly one user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new task and see it in their list within 2 seconds
- **SC-002**: Users can retrieve their complete task list (up to 100 tasks) within 1 second
- **SC-003**: Users can update or delete tasks and see changes reflected immediately in subsequent requests
- **SC-004**: System correctly enforces task ownership - users cannot access other users' tasks (100% isolation)
- **SC-005**: All task operations persist correctly - data survives application restarts with no loss
- **SC-006**: System handles at least 100 concurrent users performing task operations without errors

## Assumptions *(mandatory)*

- Users are identified by a UUID passed in the `X-User-ID` request header (authentication mechanism is out of scope for this feature)
- Task titles have a reasonable maximum length of 200 characters
- Task descriptions have a reasonable maximum length of 2000 characters
- When a user is deleted, their tasks are also deleted (cascade delete)
- The system will initially support up to 1000 tasks per user
- Database connection details are provided via environment configuration
- The application runs in a single region (no multi-region considerations)

## Out of Scope *(mandatory)*

- User authentication and authorization (JWT middleware will be added in a future feature)
- User registration and login flows
- Task sharing or collaboration between users
- Task categories, tags, or labels
- Task due dates or reminders
- Task priority levels
- Task search or filtering capabilities
- Task sorting options
- Pagination for large task lists
- Real-time updates or notifications
- Task history or audit trail
- Soft delete or task archiving
- Bulk operations (delete multiple tasks, mark multiple complete)
- Task templates or recurring tasks

## Dependencies *(mandatory)*

- Database service must be provisioned and accessible (Neon PostgreSQL)
- Database connection credentials must be available in environment configuration
- Network connectivity between application and database must be reliable

## Constraints *(mandatory)*

- All data operations must maintain ACID properties (atomicity, consistency, isolation, durability)
- Task ownership must be enforced at the data layer - no task can exist without an owner
- All timestamps must be stored in UTC
- Task identifiers must be UUIDs and unique across the entire system (not just per user)
- User identifiers must be UUIDs and unique across the entire system
- The `X-User-ID` header is mandatory for all API requests and must contain a valid UUID format
- All error responses must follow RFC 7807 Problem Details format

## Risks *(optional)*

- **Risk**: Database connection failures could cause data loss if not handled properly
  - **Mitigation**: Implement proper error handling and transaction management

- **Risk**: Without authentication, the API is vulnerable to unauthorized access
  - **Mitigation**: Document that this is intentional for this phase; authentication will be added in next feature

- **Risk**: Lack of pagination could cause performance issues with users who have many tasks
  - **Mitigation**: Document the 1000 task per user limit; pagination can be added later if needed
