# Tasks: Advanced Todo Features

**Input**: Design documents from `/specs/007-advanced-todo-features/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: No automated test tasks — spec does not request TDD. Manual API testing documented in plan.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` at repository root
- Paths reference existing files from Phase 2/3 codebase

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and model changes that ALL user stories depend on

- [x] T001 Add `TaskPriority` enum (HIGH/MEDIUM/LOW) and `TaskRecurrence` enum (NONE/DAILY/WEEKLY/MONTHLY/YEARLY) to `backend/src/models/task.py` after the existing `TaskStatus` enum. Add import for `ARRAY` from sqlalchemy. Follow the existing `TaskStatus(str, enum.Enum)` pattern exactly.
- [x] T002 Add four new fields to the `Task` model in `backend/src/models/task.py`: `priority` (TaskPriority, default=MEDIUM, not nullable), `due_date` (Optional[datetime], nullable DateTime(timezone=True)), `tags` (Optional[list[str]], nullable ARRAY(String(50))), `recurrence` (TaskRecurrence, default=NONE, not nullable). Place fields after the `status` field. Use `sa_column=Column(...)` pattern matching existing fields.
- [x] T003 Update `backend/models.py` re-export to include `TaskPriority` and `TaskRecurrence` in the imports from `src.models.task` and in `__all__`.
- [x] T004 Create `backend/migrate_advanced_features.py` — async migration script that connects to the existing database using `database.py` engine and executes idempotent ALTER TABLE statements: add `priority` (VARCHAR(10) NOT NULL DEFAULT 'medium'), `due_date` (TIMESTAMPTZ), `tags` (TEXT[]), `recurrence` (VARCHAR(10) NOT NULL DEFAULT 'none'). Create indexes: `ix_tasks_priority`, `ix_tasks_due_date`, `ix_tasks_user_priority`, `ix_tasks_user_due_date`. All statements use IF NOT EXISTS. Print success confirmation.
- [x] T005 Run migration: execute `python migrate_advanced_features.py` from `backend/` directory against the Neon database. Verify columns exist by querying `information_schema.columns` for the tasks table.

**Checkpoint**: Database schema updated with 4 new columns + indexes. All existing tasks have priority='medium' and recurrence='none' defaults.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update Pydantic schemas that all endpoints and MCP tools depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Update `TaskCreate` schema in `backend/schemas.py`: add `due_date` (Optional[datetime], default=None), `priority` (Optional[str], default="medium"), `tags` (Optional[list[str]], default=None), `recurrence` (Optional[str], default="none"). Add field validators for priority (must be high/medium/low) and recurrence (must be none/daily/weekly/monthly/yearly). Import `TaskPriority` and `TaskRecurrence` from `src.models.task` for validation.
- [x] T007 Update `TaskUpdate` schema in `backend/schemas.py`: add `due_date` (Optional[datetime], default=None), `priority` (Optional[str], default=None), `tags` (Optional[list[str]], default=None), `recurrence` (Optional[str], default=None). Update `model_post_init` to check all 6 fields (title, description, due_date, priority, tags, recurrence) — at least one must be provided. Add same field validators as TaskCreate.
- [x] T008 Update `TaskResponse` schema in `backend/schemas.py`: add `priority` (str), `due_date` (Optional[datetime]), `tags` (Optional[list[str]]), `recurrence` (str). These fields are returned from the Task model via `from_attributes = True`.

**Checkpoint**: Schemas ready. All API endpoints and MCP tools can now use the new fields. Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 — Task Priorities and Due Dates (Priority: P1)

**Goal**: Users can create, update, and filter tasks by priority and due date. Overdue tasks are detected.

**Independent Test**: Create tasks with different priorities and due dates via API. Filter by priority, due date range, and overdue status. Verify correct results.

### Implementation for User Story 1

- [x] T009 [US1] Update `create_task` endpoint in `backend/routers/tasks.py`: pass `task_data.priority`, `task_data.due_date`, `task_data.tags`, `task_data.recurrence` to the `Task()` constructor. Convert priority string to `TaskPriority` enum and recurrence string to `TaskRecurrence` enum before assignment. Import `TaskPriority`, `TaskRecurrence` from `src.models.task`.
- [x] T010 [US1] Update `update_task` endpoint in `backend/routers/tasks.py`: handle `task_data.due_date`, `task_data.priority`, `task_data.tags`, `task_data.recurrence` in the update logic. For each field, only update if the value is not None. Convert string values to enums. For `due_date`, support explicit null to clear the value (use a sentinel or check if key was present in request).
- [x] T011 [US1] Update `list_tasks` endpoint in `backend/routers/tasks.py`: add query parameters — `status` (str, default="all"), `priority` (Optional[str]), `tags` (Optional[str] comma-separated), `due_before` (Optional[datetime]), `due_after` (Optional[datetime]), `overdue` (Optional[bool], default=False), `search` (Optional[str]), `sort` (str, default="created_at"), `order` (str, default="desc"). Build dynamic SQLAlchemy query using `.where()` chain. Import `func` from sqlalchemy for ILIKE and datetime comparisons.
- [x] T012 [US1] Implement priority filter in `list_tasks` in `backend/routers/tasks.py`: when `priority` param is provided, add `.where(Task.priority == TaskPriority(priority))` to the query. Return 422 if priority value is invalid.
- [x] T013 [US1] Implement due date range filter in `list_tasks` in `backend/routers/tasks.py`: when `due_before` is provided, add `.where(Task.due_date <= due_before)`. When `due_after` is provided, add `.where(Task.due_date >= due_after)`. When `overdue` is True, add `.where(Task.due_date < func.now(), Task.status == TaskStatus.PENDING)`.
- [x] T014 [US1] Implement sort logic in `list_tasks` in `backend/routers/tasks.py`: map `sort` param to Task field — "priority" → custom ordering (high=1, medium=2, low=3 via `case()`), "due_date" → `Task.due_date`, "created_at" → `Task.created_at`, "status" → `Task.status`. Apply `order` direction (asc/desc). Add secondary sort: when primary values are equal, sort by due_date asc then created_at desc. Return 422 for invalid sort fields.
- [x] T015 [US1] Verify US1 by starting the backend (`cd backend && uv run uvicorn main:app --reload`) and testing with curl: (1) POST task with `priority=high, due_date=2026-02-14T23:59:00Z` → 201 with correct fields, (2) POST task with no new fields → 201 with priority=medium defaults, (3) GET with `?priority=high` → only high priority tasks, (4) GET with `?overdue=true` → only overdue tasks, (5) GET with `?sort=priority&order=asc` → sorted correctly, (6) PUT with `priority=low` → updated.

**Checkpoint**: At this point, User Story 1 should be fully functional. Tasks can be created/updated with priorities and due dates, and filtered/sorted via API.

---

## Phase 4: User Story 2 — Tags and Advanced Search/Filter/Sort (Priority: P2)

**Goal**: Users can tag tasks, search across titles/descriptions, filter by tags, and combine multiple filters.

**Independent Test**: Create tasks with various tags. Search by keyword. Filter by tags. Combine priority + tags + search filters.

### Implementation for User Story 2

- [x] T016 [US2] Implement search filter in `list_tasks` in `backend/routers/tasks.py`: when `search` param is provided, add `.where(or_(Task.title.ilike(f"%{search}%"), Task.description.ilike(f"%{search}%")))`. Import `or_` from sqlalchemy. Ensure search is case-insensitive and matches partial strings (FR-019, FR-020).
- [x] T017 [US2] Implement tags filter in `list_tasks` in `backend/routers/tasks.py`: when `tags` param is provided (comma-separated string), parse into list, and add `.where(Task.tags.contains(tag_list))` using PostgreSQL array `@>` operator via SQLAlchemy's `.contains()` method. This ensures AND logic — task must have ALL specified tags (FR-024, FR-026).
- [x] T018 [US2] Verify US2 by testing with curl: (1) POST task with `tags=["work","urgent"]` → 201 with tags in response, (2) GET with `?tags=work` → tasks containing "work" tag, (3) GET with `?search=meeting` → tasks with "meeting" in title/description, (4) GET with `?priority=high&tags=work&search=proposal` → combined AND filters, (5) PUT with new tags → updated.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work. Full search/filter/sort functionality available via API.

---

## Phase 5: User Story 3 — Recurring Tasks (Priority: P3)

**Goal**: Users can create tasks with recurrence patterns (daily/weekly/monthly/yearly). Pattern is stored and preserved on completion. Actual recurrence engine deferred to Spec 8.

**Independent Test**: Create tasks with different recurrence patterns. Complete a recurring task and verify pattern is preserved. Stop recurrence on a task.

### Implementation for User Story 3

- [x] T019 [US3] Verify recurrence field handling in create/update endpoints in `backend/routers/tasks.py`: confirm that `recurrence` is correctly stored as TaskRecurrence enum when creating/updating tasks (already handled by T009/T010). Verify that completing a recurring task via PATCH `/{task_id}/complete` preserves the recurrence pattern (existing toggle logic does not touch recurrence field — confirm this).
- [x] T020 [US3] Verify US3 by testing with curl: (1) POST task with `recurrence=daily` → 201 with recurrence=daily, (2) POST task with `recurrence=weekly, tags=["meeting"]` → 201, (3) PATCH complete a recurring task → status=completed, recurrence=daily preserved, (4) PUT with `recurrence=none` → recurrence stopped, (5) POST with invalid `recurrence=biweekly` → 422.

**Checkpoint**: All user stories (US1, US2, US3) are now functional and independently testable via API.

---

## Phase 6: MCP Tools & Agent (Chatbot Integration)

**Purpose**: Update MCP tools so the AI chatbot can use all new features via natural language

- [x] T021 Update `serialize_task()` helper in `backend/tools/tasks.py`: add `priority` (task.priority.value), `due_date` (ISO string or None), `tags` (list or empty list), `recurrence` (task.recurrence.value) to the returned dict. Import `TaskPriority`, `TaskRecurrence` from `src.models.task`.
- [x] T022 Update `add_task` MCP tool in `backend/tools/tasks.py`: add parameters `due_date` (str, default=None), `priority` (str, default="medium"), `tags` (str, default=None — comma-separated), `recurrence` (str, default="none"). Validate priority against ["high","medium","low"]. Validate recurrence against ["none","daily","weekly","monthly","yearly"]. Parse tags string into list. Parse due_date ISO string to datetime. Pass new fields to `Task()` constructor with enum conversions.
- [x] T023 Update `update_task` MCP tool in `backend/tools/tasks.py`: add parameters `due_date` (str, default=None), `priority` (str, default=None), `tags` (str, default=None), `recurrence` (str, default=None). Same validation as add_task. Only update fields that are not None. Update the "at least one field" check to include all 6 fields.
- [x] T024 Update `list_tasks` MCP tool in `backend/tools/tasks.py`: add parameters `priority` (str, default=None), `tags` (str, default=None — comma-separated), `search` (str, default=None), `sort` (str, default="created_at"), `order` (str, default="desc"), `overdue` (str, default="false"). Build dynamic SQLAlchemy query: add priority filter, tags filter (ARRAY contains), search ILIKE filter, overdue filter (due_date < now AND status=pending). Apply sort with direction. Import `or_`, `func`, `case` from sqlalchemy.
- [x] T025 Update `AGENT_INSTRUCTIONS` in `backend/src/agents/todo_agent.py`: expand capabilities list to include priority, due dates, tags, recurrence, search, filter, sort. Add guidelines for the LLM: (1) extract priority from user input, (2) convert natural language dates to ISO 8601, (3) extract hashtags as tags, (4) detect recurrence patterns, (5) use search/filter/sort params, (6) format output with new fields.
- [x] T026 Verify chatbot integration by starting both servers (`uv run uvicorn main:app --reload` and `uv run python mcp_server.py`) and testing via the chat API: (1) "Add high priority task: Review PR by tomorrow #work" → creates task with correct fields, (2) "Show my high priority tasks" → filters correctly, (3) "What's overdue?" → returns overdue tasks, (4) "Search for meeting" → searches correctly, (5) "Add daily task: Check emails" → recurrence=daily.

**Checkpoint**: Full chatbot integration working. All new features accessible via natural language.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, validation hardening, and backward compatibility verification

- [x] T027 [P] Add tag validation in `backend/schemas.py`: max 10 tags per task, max 50 characters per tag. Add `field_validator` for tags in both `TaskCreate` and `TaskUpdate`. Return clear error messages for violations.
- [x] T028 [P] Handle edge case: empty tags list in `backend/routers/tasks.py` and `backend/tools/tasks.py` — if user sends `tags=[]`, store as NULL in database (not empty array). Normalize in both router and MCP tool code.
- [x] T029 [P] Handle edge case: invalid sort field in `list_tasks` in `backend/routers/tasks.py` — return RFC 7807 422 error with message "Invalid sort field. Must be one of: priority, due_date, created_at, status" (FR-032).
- [x] T030 Verify backward compatibility: (1) existing tasks (no new fields) still return correctly via GET with defaults, (2) POST with only `{"title": "..."}` still works, (3) existing chatbot conversations continue to work, (4) existing frontend API calls are not broken. Test all existing endpoints without new params to confirm no regressions.
- [x] T031 Verify complete E2E flow across all user stories: create task with all fields via chatbot → filter by priority → search by keyword → filter by tags → sort by due date → mark as complete (recurrence preserved) → filter overdue → update priority/tags. Confirm all operations work in a single conversation session.

---

## Phase 8: Frontend UI (User Story 4)

**Purpose**: Update the Next.js frontend task management UI to support all advanced task fields and add priority filtering.

**Goal**: Users can create, edit, and filter tasks with priority, due date, tags, and recurrence from the /tasks page — not just the chatbot.

**Independent Test**: Create a task from the /tasks page with all new fields, verify display on task cards, filter by priority, edit a task and verify fields are pre-populated.

### Implementation for User Story 4

- [x] T032 [US4] Update the `Task` TypeScript interface and API transform functions in `frontend/lib/api.ts`: add `priority` (TaskPriority type), `dueDate` (string | null), `tags` (string[] | null), `recurrence` (TaskRecurrence type) to the Task type. Update the `transformTask` function to map snake_case backend fields to camelCase. Ensure `createTask` and `updateTask` API functions pass the new fields in the request body with proper snake_case conversion.
- [x] T033 [US4] Update the `TaskData` interface in `frontend/hooks/useTasks.ts`: add `priority` (TaskPriority | undefined), `dueDate` (string | null | undefined), `tags` (string[] | null | undefined), `recurrence` (TaskRecurrence | undefined) fields with exactOptionalPropertyTypes compatibility so that task forms can capture and submit the new data.
- [x] T034 [US4] Add priority, due date, tags, and recurrence fields to the task creation/edit form in `frontend/components/TaskForm.tsx`: add a Select for priority (High/Medium/Low), an Input with `type="datetime-local"` for due date, a text Input for comma-separated tags with badge preview and removal, and a Select for recurrence (None/Daily/Weekly/Monthly/Yearly). Use existing shadcn/ui components (Select, Input, Badge). Wire field values to form state with proper pre-population for edit mode.
- [x] T035 [US4] Update `frontend/components/TaskModal.tsx` type signatures: ensure the modal's `onCreateTask` and `onUpdateTask` handlers accept `TaskFormData` type which includes the new fields (priority, dueDate, tags, recurrence). Verify that edit mode pre-populates all new fields from the existing task data.
- [x] T036 [US4] Display priority badge, due date, tags, and recurrence indicator on `frontend/components/TaskCard.tsx`: render priority as a color-coded Badge (high=red, medium=amber, low=blue), display dueDate with red "Overdue:" text if past due + status pending, render tags as small Badge components with Tag icon, and show recurrence label (e.g., "Daily") with Repeat icon if recurrence is not "none".
- [x] T037 [US4] Add a priority filter to `frontend/components/TaskFilter.tsx`: add a second filter group with buttons for All Priorities, High, Medium, Low. When the user selects a priority, update the priorityFilter state. Follow the existing pattern used for the status filter with matching styling.
- [x] T038 [US4] Wire the priority filter into `frontend/components/TaskList.tsx`: add `priorityFilter` state, pass it to TaskFilter component, and apply client-side filtering in the `filteredTasks` logic to filter by both status and priority. Update empty state messages to reflect combined filters.

**Checkpoint**: Frontend task management UI fully supports all advanced task fields. Users can create, edit, view, and filter tasks with priority, due date, tags, and recurrence from the /tasks page.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (model changes must exist before schemas reference them)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (schemas must be ready)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (schemas must be ready). Can run in parallel with US1 if different developers.
- **User Story 3 (Phase 5)**: Depends on Phase 2. Can run in parallel with US1/US2.
- **MCP Tools (Phase 6)**: Depends on Phase 1 (model enums). Can be done in parallel with Phases 3-5 since MCP tools are in a separate file.
- **Polish (Phase 7)**: Depends on all previous phases
- **Frontend UI (Phase 8)**: Depends on Phase 2 (schemas define the API contract). Can run in parallel with Phases 3-7 since frontend is a separate codebase.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 — No dependencies on other stories (tags filter is independent)
- **User Story 3 (P3)**: Can start after Phase 2 — No dependencies on other stories (recurrence is just an enum field)
- **MCP Tools (Phase 6)**: Can start after Phase 1 — Independent file from routers

### Within Each Phase

- Models before schemas (Phase 1 before Phase 2)
- Schemas before routers (Phase 2 before Phase 3-5)
- Core implementation before verification tasks
- Commit after each phase or logical group

### Parallel Opportunities

- T001 + T004 can start in parallel (model changes + migration script are different files)
- T006, T007, T008 can all run in parallel (different schema classes in same file, but independent edits)
- US1 (T009-T015), US2 (T016-T018), US3 (T019-T020) can run in parallel after Phase 2
- MCP tools (T021-T025) can run in parallel with router changes (T009-T020) — different files
- T027, T028, T029 (Polish tasks) can all run in parallel

---

## Parallel Example: Phase 6 (MCP Tools)

```bash
# Launch all MCP tool updates together (different functions, same file but independent edits):
Task: "Update serialize_task() helper in backend/tools/tasks.py"
Task: "Update add_task MCP tool in backend/tools/tasks.py"
Task: "Update update_task MCP tool in backend/tools/tasks.py"
Task: "Update list_tasks MCP tool in backend/tools/tasks.py"
Task: "Update AGENT_INSTRUCTIONS in backend/src/agents/todo_agent.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005) — model + migration
2. Complete Phase 2: Foundational (T006-T008) — schemas
3. Complete Phase 3: User Story 1 (T009-T015) — priorities + due dates
4. **STOP and VALIDATE**: Test priorities, due dates, overdue, sort via API
5. Deploy if ready — priorities and due dates provide immediate value

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready
2. Add User Story 1 (Phase 3) → Test independently → **MVP: Priority + Due Dates**
3. Add User Story 2 (Phase 4) → Test independently → **Search/Filter/Sort + Tags**
4. Add User Story 3 (Phase 5) → Test independently → **Recurring Tasks**
5. Add MCP Tools (Phase 6) → Test chatbot → **Full Chatbot Integration**
6. Polish (Phase 7) → Final validation → **Production Ready**
7. Add Frontend UI (Phase 8) → Test /tasks page → **Full UI Integration**

Each story adds value without breaking previous stories.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No automated tests (spec does not require TDD; manual testing via curl/Postman)
- Commit after each phase or logical group
- Stop at any checkpoint to validate story independently
- MCP tools can be developed in parallel with router changes (separate files)
- All new fields have defaults or are nullable — zero risk to existing data
