# Feature Specification: Advanced Todo Features

**Feature Branch**: `007-advanced-todo-features`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Spec 7 - Advanced Todo Features - Add recurring tasks, due dates, reminders, priorities, tags, search/filter/sort to existing Phase 3 chatbot"

## Clarifications

### Session 2026-02-09

- Q: How should timezone handling work for due dates to ensure consistent overdue detection? → A: Store due dates in UTC, but allow frontend to display in user's local timezone
- Q: When sorting tasks by due_date, where should tasks with null due_date appear in the sorted list? → A: Nulls last (tasks without due dates appear at the bottom)
- Q: Should tags be case-sensitive or case-insensitive, and how should duplicates be handled? → A: Case-insensitive: deduplicate and normalize to lowercase
- Q: What validation limits should be enforced for tags? → A: Max 10 tags per task, max 50 characters per tag
- Q: Should recurring task metadata (day-of-month, day-of-week) be stored now or deferred to Spec 8? → A: Simple enum only (none/daily/weekly/monthly/yearly), defer day-of-week/day-of-month to Spec 8

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Task Priorities and Due Dates (Priority: P1)

Users need to prioritize their tasks and set deadlines to manage their workload effectively. This story adds priority levels and due dates to tasks, enabling users to focus on what matters most and meet deadlines.

**Why this priority**: Foundation for all other features. Priorities and due dates are the most commonly used task management features and provide immediate value. Due dates are required for reminders and recurring tasks.

**Independent Test**: Can be fully tested by creating tasks with different priorities and due dates via the chatbot, then verifying they're stored correctly and can be retrieved. Delivers immediate value by enabling deadline tracking and work prioritization.

**Acceptance Scenarios**:

1. **Given** a user is chatting with the AI assistant, **When** they say "Add high priority task: Finish project proposal by Friday", **Then** the system creates a task with priority=high and due_date set to the next Friday
2. **Given** a user has tasks with different priorities, **When** they ask "Show my high priority tasks", **Then** the system lists only tasks with priority=high
3. **Given** a user has a task with a due date, **When** they ask "What's due this week?", **Then** the system lists all tasks with due dates in the current week
4. **Given** a user creates a task without specifying priority, **When** the task is saved, **Then** it defaults to priority=medium
5. **Given** a user has a task, **When** they say "Change task priority to low", **Then** the system updates the task's priority to low

---

### User Story 2 - Tags and Advanced Search/Filter/Sort (Priority: P2)

Users need to organize tasks by categories and quickly find specific tasks. This story adds tags for categorization and comprehensive search, filter, and sort capabilities.

**Why this priority**: Builds on P1 foundation. As users accumulate more tasks with priorities and due dates, they need better organization and discovery tools. Independent of recurring tasks.

**Independent Test**: Can be fully tested by creating tasks with various tags, then using search, filter, and sort commands via the chatbot. Delivers value by enabling efficient task organization and retrieval.

**Acceptance Scenarios**:

1. **Given** a user is creating a task, **When** they say "Add task: Review code #work #urgent", **Then** the system creates a task with tags ["work", "urgent"]
2. **Given** a user has tasks with different tags, **When** they ask "Show me all #work tasks", **Then** the system lists only tasks tagged with "work"
3. **Given** a user has multiple tasks, **When** they say "Search for tasks about 'meeting'", **Then** the system returns tasks where title or description contains "meeting"
4. **Given** a user has tasks with different priorities and due dates, **When** they ask "Show my tasks sorted by priority", **Then** the system lists tasks ordered by priority (high → medium → low)
5. **Given** a user has completed and pending tasks, **When** they say "Show only pending tasks", **Then** the system filters out completed tasks
6. **Given** a user has tasks with various due dates, **When** they ask "Sort by due date", **Then** the system lists tasks ordered by due date (earliest first)
7. **Given** a user has tasks, **When** they say "Show overdue tasks", **Then** the system lists tasks where due_date is in the past and status is pending

---

### User Story 3 - Recurring Tasks (Priority: P3)

Users need to create tasks that repeat on a schedule (daily, weekly, monthly, yearly) to manage routine activities without manual recreation.

**Why this priority**: Most complex feature requiring due dates (P1) to be implemented first. Provides significant value for routine task management but can be delivered after core features are stable.

**Independent Test**: Can be fully tested by creating recurring tasks via the chatbot, then verifying the recurrence pattern is stored correctly. The actual creation of next occurrences will be handled by the recurring engine service (Spec 8), but the data model and API support can be tested independently.

**Acceptance Scenarios**:

1. **Given** a user is creating a task, **When** they say "Add daily task: Check emails", **Then** the system creates a task with recurrence=daily
2. **Given** a user is creating a task, **When** they say "Add weekly task: Team meeting every Monday", **Then** the system creates a task with recurrence=weekly
3. **Given** a user has a recurring task, **When** they view the task details, **Then** the system shows the recurrence pattern (e.g., "Repeats: Daily")
4. **Given** a user has a recurring task, **When** they complete it, **Then** the task is marked complete but the recurrence pattern is preserved for the recurring engine to create the next occurrence
5. **Given** a user has a recurring task, **When** they say "Stop recurring task", **Then** the system sets recurrence=none and no future occurrences will be created
6. **Given** a user creates a monthly recurring task, **When** they specify "Pay rent on the 1st of every month", **Then** the system stores recurrence=monthly (detailed scheduling metadata handled by Spec 8 recurring engine)

---

### User Story 4 - Frontend Task Management UI (Priority: P1)

Users need to manage advanced task features (priority, due dates, tags, recurrence) directly from the frontend task management UI, not just via the chatbot.

**Why this priority**: The frontend already has a full task management UI (/tasks page) but only supports title and description. Users should be able to use all task features from both the chatbot and the direct UI.

**Independent Test**: Can be tested by creating, editing, and filtering tasks from the /tasks page with all new fields.

**Acceptance Scenarios**:

1. **Given** a user is on the /tasks page, **When** they click "New Task", **Then** the modal shows fields for title, description, priority, due date, tags, and recurrence
2. **Given** a user creates a task with priority=high, **When** viewing the task list, **Then** a red priority badge is displayed on the task card
3. **Given** a user creates a task with a past due date and status=pending, **When** viewing the task list, **Then** the due date is shown in red as overdue
4. **Given** a user creates a task with tags, **When** viewing the task list, **Then** tags are displayed as small badges on the task card
5. **Given** a user edits an existing task, **When** the edit modal opens, **Then** all fields (priority, due date, tags, recurrence) are pre-populated with current values
6. **Given** a user is on the /tasks page, **When** they use the priority filter, **Then** only tasks matching the selected priority are shown

---

### Edge Cases

- What happens when a user sets a due date in the past? System accepts it and marks it as overdue.
- What happens when a user adds multiple tags to a task? System stores all tags as an array and supports filtering by any tag.
- What happens when a user searches with no matching results? System returns a friendly message: "No tasks found matching your search."
- What happens when a user tries to sort by an invalid field? System returns an error message suggesting valid sort options (priority, due_date, created_at).
- What happens when a user creates a recurring task without a due date? System allows it - recurrence pattern is stored, and the recurring engine will create occurrences based on the pattern starting from creation date.
- What happens when a user updates a recurring task's title or description? Only the current instance is updated; future occurrences use the updated template.
- What happens when a user deletes a recurring task? The current instance is deleted, but the recurrence pattern determines if future occurrences should still be created (implementation detail for Spec 8).
- What happens when a user has tasks with the same priority? Secondary sort by due date (earliest first), then by created_at (newest first).
- What happens when a user filters by multiple criteria (e.g., "Show high priority work tasks")? System applies all filters (priority=high AND tags contains "work").

## Requirements *(mandatory)*

### Functional Requirements

**Task Priority Management:**
- **FR-001**: System MUST support three priority levels: high, medium, low
- **FR-002**: System MUST default new tasks to priority=medium if not specified
- **FR-003**: Users MUST be able to create tasks with a specified priority via natural language (e.g., "high priority task")
- **FR-004**: Users MUST be able to update a task's priority after creation
- **FR-005**: Users MUST be able to filter tasks by priority level

**Due Dates and Deadlines:**
- **FR-006**: System MUST support due dates for tasks (date and time)
- **FR-007**: System MUST accept due dates in natural language (e.g., "by Friday", "next Monday", "in 3 days")
- **FR-008**: System MUST allow tasks without due dates (due_date is nullable)
- **FR-009**: Users MUST be able to update or remove a task's due date
- **FR-010**: System MUST identify overdue tasks (due_date in past and status=pending)
- **FR-011**: System MUST support filtering tasks by due date ranges (e.g., "due this week", "due today")
- **FR-012**: System MUST store due dates in UTC for consistent overdue detection across timezones

**Tags and Categorization:**
- **FR-013**: System MUST support multiple tags per task (maximum 10 tags)
- **FR-014**: Users MUST be able to add tags using hashtag syntax (e.g., #work, #urgent)
- **FR-015**: System MUST store tags as an array, normalized to lowercase and deduplicated (e.g., "#Work" and "#work" become one tag: "work")
- **FR-016**: System MUST validate that each tag is between 1 and 50 characters in length
- **FR-017**: System MUST be able to filter tasks by one or more tags
- **FR-018**: Users MUST be able to add or remove tags from existing tasks
- **FR-019**: System MUST support tag-based search (case-insensitive)

**Search Functionality:**
- **FR-018**: System MUST support keyword search across task title and description
- **FR-019**: Search MUST be case-insensitive
- **FR-020**: Search MUST return partial matches (e.g., "meet" matches "meeting")
- **FR-021**: System MUST return a clear message when no tasks match the search

**Filter Functionality:**
- **FR-022**: System MUST support filtering by status (pending, completed)
- **FR-023**: System MUST support filtering by priority (high, medium, low)
- **FR-024**: System MUST support filtering by tags
- **FR-025**: System MUST support filtering by due date ranges
- **FR-026**: System MUST support combining multiple filters (AND logic)
- **FR-027**: System MUST support filtering for overdue tasks

**Sort Functionality:**
- **FR-028**: System MUST support sorting by priority (high → medium → low)
- **FR-029**: System MUST support sorting by due date (earliest first, tasks without due dates appear last)
- **FR-030**: System MUST support sorting by created date (newest first)
- **FR-031**: System MUST support sorting by completion status
- **FR-032**: System MUST apply secondary sorting when primary sort values are equal (priority → due_date → created_at)

**Recurring Tasks:**
- **FR-034**: System MUST support recurring task patterns: none, daily, weekly, monthly, yearly
- **FR-035**: Users MUST be able to create recurring tasks via natural language (e.g., "daily task", "weekly meeting")
- **FR-036**: System MUST store the recurrence pattern with the task as a simple enum (none/daily/weekly/monthly/yearly)
- **FR-037**: Users MUST be able to view the recurrence pattern for a task
- **FR-038**: Users MUST be able to stop a recurring task (set recurrence=none)
- **FR-039**: System MUST preserve recurrence pattern when a recurring task is completed
- **FR-040**: System MUST allow recurring tasks with or without due dates
- **FR-041**: Detailed recurrence metadata (day-of-week, day-of-month, time-of-day) is deferred to Spec 8 recurring engine service

**Data Model Updates:**
- **FR-040**: Task model MUST include due_date field (datetime, nullable)
- **FR-041**: Task model MUST include priority field (enum: high/medium/low, default=medium, not nullable)
- **FR-042**: Task model MUST include tags field (array or string, nullable)
- **FR-043**: Task model MUST include recurrence field (enum or string: none/daily/weekly/monthly/yearly, default=none)

**API Endpoint Updates:**
- **FR-044**: POST /api/{user_id}/tasks MUST accept due_date, priority, tags, recurrence in request body
- **FR-045**: GET /api/{user_id}/tasks MUST support query parameters: filter, sort, search
- **FR-046**: PUT /api/{user_id}/tasks/{task_id} MUST support updating due_date, priority, tags, recurrence
- **FR-047**: All endpoints MUST maintain existing JWT authentication and user isolation

**MCP Tool Updates:**
- **FR-048**: add_task tool MUST accept due_date, priority, tags, recurrence parameters
- **FR-049**: update_task tool MUST accept due_date, priority, tags, recurrence parameters
- **FR-050**: list_tasks tool MUST accept filter, sort, search parameters
- **FR-051**: MCP tools MUST reflect changes in chatbot responses

**Integration with Existing Features:**
- **FR-052**: All new features MUST work with existing Phase 2 authentication (Better Auth + JWT)
- **FR-053**: All new features MUST work with existing Phase 3 chatbot interface
- **FR-054**: All new features MUST maintain user isolation (users can only access their own tasks)
- **FR-055**: System MUST preserve backward compatibility with existing tasks (tasks without new fields remain valid)

**Future Integration Preparation:**
- **FR-056**: Due dates MUST be stored in a format compatible with reminder event publishing (Spec 8)
- **FR-057**: Recurrence patterns MUST be stored in a format compatible with the recurring engine service (Spec 8)
- **FR-058**: All task state changes MUST be structured to support event publishing in Spec 8

**Frontend UI Updates:**
- **FR-059**: Task creation form MUST include fields for priority, due date, tags, and recurrence
- **FR-060**: Task edit form MUST pre-populate all fields including priority, due date, tags, and recurrence
- **FR-061**: Task cards MUST display priority as a color-coded badge (high=red, medium=amber, low=blue)
- **FR-062**: Task cards MUST display due date with overdue indicator (red text if past due + pending)
- **FR-063**: Task cards MUST display tags as small badges
- **FR-064**: Task cards MUST display recurrence indicator if not "none"
- **FR-065**: Task filter MUST support filtering by priority level (All/High/Medium/Low)

### Key Entities

- **Task (Enhanced)**: Represents a user's task with new attributes:
  - Existing: id, user_id, title, description, status, created_at, updated_at
  - New: due_date (when task should be completed), priority (importance level), tags (categorization labels), recurrence (repeat pattern)
  - Relationships: Belongs to User (existing), will publish events to Kafka (Spec 8)

- **Priority**: Enumeration of task importance levels (high, medium, low)

- **Recurrence**: Enumeration or pattern defining task repetition (none, daily, weekly, monthly, yearly)

- **Tag**: Label for categorizing tasks (stored as array or comma-separated string)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create tasks with priorities and due dates via natural language in under 30 seconds
- **SC-002**: Users can find specific tasks using search in under 10 seconds
- **SC-003**: Users can filter and sort their task list to view relevant tasks in under 5 seconds
- **SC-004**: Users can create recurring tasks that automatically generate future occurrences (once Spec 8 is implemented)
- **SC-005**: 95% of natural language date inputs (e.g., "next Friday", "in 3 days") are correctly parsed and stored
- **SC-006**: Task list with 100+ tasks can be filtered and sorted without noticeable delay (under 1 second)
- **SC-007**: Users can organize tasks with multiple tags and retrieve them by any tag
- **SC-008**: Overdue tasks are correctly identified and can be filtered
- **SC-009**: All new features work seamlessly with existing chatbot interface without breaking existing functionality
- **SC-010**: Task data model supports future event-driven architecture (Spec 8) without requiring schema changes

### Assumptions

- Natural language date parsing will use standard libraries or existing chatbot capabilities
- Tags will be stored as a PostgreSQL array or JSON array for efficient querying
- Recurrence patterns will be stored as enum values or JSON for flexibility
- The recurring engine service (Spec 8) will handle automatic creation of next occurrences
- Reminder notifications (Spec 8) will be triggered by events, not by this spec
- Existing Neon PostgreSQL database will be used with schema migration
- All API changes maintain RESTful conventions and existing authentication patterns

### Out of Scope

- Kafka event publishing (handled in Spec 8)
- Dapr integration (handled in Spec 8)
- Recurring engine service implementation (handled in Spec 8)
- Reminder notification service (handled in Spec 8)
- Real-time sync via WebSocket (handled in Spec 8)
- Audit logging (handled in Spec 8)
- Advanced recurrence patterns (e.g., "every 2nd Tuesday", custom cron expressions)
- Bulk operations (e.g., "mark all high priority tasks as complete")
- Task dependencies (e.g., "task B depends on task A")
- Subtasks or task hierarchies
- Task attachments or file uploads
- Task sharing or collaboration features
