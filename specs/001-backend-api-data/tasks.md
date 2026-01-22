# Tasks: Backend API & Data Layer

**Input**: Design documents from `/specs/001-backend-api-data/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Not requested in specification - implementation tasks only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend code: `backend/` directory at repository root
- All Python modules in `backend/` (flat structure)
- Tests in `backend/tests/` (not included - tests not requested)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend/ directory structure with subdirectories: routers/, tests/
- [x] T002 Create backend/requirements.txt with dependencies: fastapi==0.109.0, sqlmodel==0.0.14, asyncpg==0.29.0, pydantic==2.5.0, uvicorn[standard]==0.27.0, python-dotenv==1.0.0
- [x] T003 Create backend/.env.example with DATABASE_URL and ENVIRONMENT placeholders
- [x] T004 Create backend/.gitignore to exclude .env, __pycache__, *.pyc, venv/, .venv/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create backend/models.py with User model (UUID id, email string, SQLModel table=True)
- [x] T006 [P] Create backend/models.py with Task model (UUID id, user_id FK, title, description, status enum, created_at, updated_at with auto-update)
- [x] T007 Create backend/database.py with async engine setup using create_async_engine with asyncpg driver
- [x] T008 Create backend/database.py with AsyncSession factory using sessionmaker with expire_on_commit=False
- [x] T009 Create backend/database.py with get_db() dependency function that yields AsyncSession
- [x] T010 [P] Create backend/schemas.py with RFC 7807 ProblemDetail schema (type, title, detail, status fields)
- [x] T011 [P] Create backend/schemas.py with TaskCreate request schema (title required, description optional)
- [x] T012 [P] Create backend/schemas.py with TaskUpdate request schema (title and description both optional, minProperties=1)
- [x] T013 [P] Create backend/schemas.py with TaskResponse schema matching Task model fields
- [x] T014 Create backend/main.py with FastAPI app initialization and CORS middleware configuration
- [x] T015 Create backend/main.py with X-User-ID header validation dependency that extracts UUID from header and returns 400 RFC 7807 error if missing/invalid
- [x] T016 Create backend/main.py with get_or_create_user() dependency that auto-creates user with placeholder email if user_id not in database
- [x] T017 Create backend/main.py with RFC 7807 exception handler for HTTPException that formats responses as ProblemDetail
- [x] T018 Create backend/main.py with health check endpoint GET /health returning status and timestamp
- [x] T019 Create backend/init_db.py script to initialize database schema using SQLModel.metadata.create_all()

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Personal Task List (Priority: P1) 🎯 MVP

**Goal**: Users can retrieve all their tasks to see what needs to be done

**Independent Test**: Create a user with multiple tasks via database, call GET /api/tasks with X-User-ID header, verify only that user's tasks are returned in response

### Implementation for User Story 1

- [x] T020 [US1] Create backend/routers/tasks.py with APIRouter configured with prefix="/api/tasks" and tags=["tasks"]
- [x] T021 [US1] Implement GET /api/tasks endpoint in backend/routers/tasks.py that queries tasks filtered by user_id from X-User-ID header dependency
- [x] T022 [US1] Add user_id filtering to query using WHERE user_id = $1 in backend/routers/tasks.py GET endpoint
- [x] T023 [US1] Add ordering by created_at DESC to task list query in backend/routers/tasks.py
- [x] T024 [US1] Return empty list [] when user has no tasks in backend/routers/tasks.py GET endpoint
- [x] T025 [US1] Include router in backend/main.py using app.include_router(tasks.router)
- [x] T026 [US1] Add RFC 7807 error handling for database connection failures (503 service-unavailable) in backend/routers/tasks.py

**Checkpoint**: At this point, User Story 1 should be fully functional - users can view their task list

---

## Phase 4: User Story 2 - Create New Task (Priority: P1) 🎯 MVP

**Goal**: Users can add new tasks to their list

**Independent Test**: Call POST /api/tasks with X-User-ID header and task data, verify task is created with status="pending" and appears in user's task list

### Implementation for User Story 2

- [x] T027 [US2] Implement POST /api/tasks endpoint in backend/routers/tasks.py accepting TaskCreate schema
- [x] T028 [US2] Generate UUID for new task using uuid4() in backend/routers/tasks.py POST endpoint
- [x] T029 [US2] Set default status="pending" for new tasks in backend/routers/tasks.py POST endpoint
- [x] T030 [US2] Associate task with user_id from X-User-ID header dependency in backend/routers/tasks.py
- [x] T031 [US2] Trigger user auto-creation via get_or_create_user() dependency before task creation in backend/routers/tasks.py
- [x] T032 [US2] Validate title is not empty (1-200 chars) using Pydantic validation in TaskCreate schema
- [x] T033 [US2] Validate description max length (2000 chars) using Pydantic validation in TaskCreate schema
- [x] T034 [US2] Return 201 Created with TaskResponse body including all fields in backend/routers/tasks.py POST endpoint
- [x] T035 [US2] Add RFC 7807 error handling for validation errors (400 validation-error) in backend/routers/tasks.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users can create and view tasks

---

## Phase 5: User Story 3 - Mark Task as Complete (Priority: P2)

**Goal**: Users can toggle task completion status to track progress

**Independent Test**: Create a pending task, call PATCH /api/tasks/{task_id}/complete with X-User-ID header, verify status changes to "completed", call again to verify it toggles back to "pending"

### Implementation for User Story 3

- [x] T036 [US3] Implement PATCH /api/tasks/{task_id}/complete endpoint in backend/routers/tasks.py
- [x] T037 [US3] Query task by id AND user_id to enforce ownership in backend/routers/tasks.py PATCH endpoint
- [x] T038 [US3] Return 404 RFC 7807 error (task-not-found) if task doesn't exist or belongs to different user in backend/routers/tasks.py
- [x] T039 [US3] Return 403 RFC 7807 error (access-denied) if user_id doesn't match task owner in backend/routers/tasks.py
- [x] T040 [US3] Toggle status between "pending" and "completed" in backend/routers/tasks.py PATCH endpoint
- [x] T041 [US3] Update updated_at timestamp automatically via onupdate trigger in backend/routers/tasks.py
- [x] T042 [US3] Return 200 OK with updated TaskResponse in backend/routers/tasks.py PATCH endpoint
- [x] T043 [US3] Add RFC 7807 error handling for invalid task_id UUID format (400 invalid-identifier) in backend/routers/tasks.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work - users can create, view, and complete tasks

---

## Phase 6: User Story 4 - Update Task Details (Priority: P2)

**Goal**: Users can modify task title and description to correct mistakes or update information

**Independent Test**: Create a task, call PUT /api/tasks/{task_id} with X-User-ID header and updated data, verify changes persist and updated_at timestamp is refreshed

### Implementation for User Story 4

- [x] T044 [US4] Implement PUT /api/tasks/{task_id} endpoint in backend/routers/tasks.py accepting TaskUpdate schema
- [x] T045 [US4] Query task by id AND user_id to enforce ownership in backend/routers/tasks.py PUT endpoint
- [x] T046 [US4] Return 404 RFC 7807 error (task-not-found) if task doesn't exist in backend/routers/tasks.py
- [x] T047 [US4] Return 403 RFC 7807 error (access-denied) if user_id doesn't match task owner in backend/routers/tasks.py
- [x] T048 [US4] Update only provided fields (title and/or description) in backend/routers/tasks.py PUT endpoint
- [x] T049 [US4] Preserve status and created_at fields unchanged in backend/routers/tasks.py PUT endpoint
- [x] T050 [US4] Update updated_at timestamp automatically in backend/routers/tasks.py PUT endpoint
- [x] T051 [US4] Validate at least one field is provided using minProperties=1 in TaskUpdate schema
- [x] T052 [US4] Return 200 OK with updated TaskResponse in backend/routers/tasks.py PUT endpoint

**Checkpoint**: At this point, User Stories 1-4 should all work - users can create, view, complete, and update tasks

---

## Phase 7: User Story 5 - View Single Task Details (Priority: P3)

**Goal**: Users can view complete details of a specific task

**Independent Test**: Create a task, call GET /api/tasks/{task_id} with X-User-ID header, verify all task details are returned correctly

### Implementation for User Story 5

- [x] T053 [US5] Implement GET /api/tasks/{task_id} endpoint in backend/routers/tasks.py
- [x] T054 [US5] Query task by id AND user_id to enforce ownership in backend/routers/tasks.py GET endpoint
- [x] T055 [US5] Return 404 RFC 7807 error (task-not-found) if task doesn't exist in backend/routers/tasks.py
- [x] T056 [US5] Return 403 RFC 7807 error (access-denied) if user_id doesn't match task owner in backend/routers/tasks.py
- [x] T057 [US5] Return 200 OK with TaskResponse including all fields in backend/routers/tasks.py GET endpoint
- [x] T058 [US5] Add RFC 7807 error handling for invalid task_id UUID format (400 invalid-identifier) in backend/routers/tasks.py

**Checkpoint**: At this point, User Stories 1-5 should all work - users can perform all read operations

---

## Phase 8: User Story 6 - Delete Task (Priority: P3)

**Goal**: Users can permanently remove tasks they no longer need

**Independent Test**: Create a task, call DELETE /api/tasks/{task_id} with X-User-ID header, verify task is removed and no longer appears in task list

### Implementation for User Story 6

- [x] T059 [US6] Implement DELETE /api/tasks/{task_id} endpoint in backend/routers/tasks.py
- [x] T060 [US6] Query task by id AND user_id to enforce ownership in backend/routers/tasks.py DELETE endpoint
- [x] T061 [US6] Return 404 RFC 7807 error (task-not-found) if task doesn't exist in backend/routers/tasks.py
- [x] T062 [US6] Return 403 RFC 7807 error (access-denied) if user_id doesn't match task owner in backend/routers/tasks.py
- [x] T063 [US6] Delete task from database using DELETE query in backend/routers/tasks.py
- [x] T064 [US6] Return 204 No Content on successful deletion in backend/routers/tasks.py DELETE endpoint
- [x] T065 [US6] Add RFC 7807 error handling for invalid task_id UUID format (400 invalid-identifier) in backend/routers/tasks.py

**Checkpoint**: All user stories should now be independently functional - complete CRUD operations available

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T066 [P] Add connection pooling configuration to database.py with pool_size=10 and max_overflow=20
- [x] T067 [P] Add database connection retry logic with exponential backoff in database.py
- [x] T068 [P] Add request logging middleware to main.py for all API calls
- [x] T069 [P] Update backend/.env.example with complete configuration examples and comments
- [x] T070 [P] Add API documentation strings to all endpoints in backend/routers/tasks.py for OpenAPI generation
- [x] T071 Verify all RFC 7807 error responses include correct type, title, detail, and status fields
- [x] T072 Verify all timestamps are stored in UTC and timezone-aware
- [x] T073 Verify user auto-creation works correctly with placeholder email format
- [x] T074 Verify X-User-ID header validation rejects missing, empty, and invalid UUID formats
- [x] T075 Run through quickstart.md setup instructions to validate completeness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories (operates on existing tasks)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories (operates on existing tasks)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories (read operation)
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories (operates on existing tasks)

### Within Each User Story

- Models before services (already in Foundational phase)
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 (Setup)**: All tasks can run in parallel
- **Phase 2 (Foundational)**: Tasks T005-T006 (models), T010-T013 (schemas) can run in parallel
- **Phase 3-8 (User Stories)**: Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- **Phase 9 (Polish)**: Tasks T066-T070 can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all model definitions together:
Task T005: "Create User model in backend/models.py"
Task T006: "Create Task model in backend/models.py"

# Launch all schema definitions together:
Task T010: "Create ProblemDetail schema in backend/schemas.py"
Task T011: "Create TaskCreate schema in backend/schemas.py"
Task T012: "Create TaskUpdate schema in backend/schemas.py"
Task T013: "Create TaskResponse schema in backend/schemas.py"
```

## Parallel Example: User Stories (with team)

```bash
# After Foundational phase completes, launch all user stories in parallel:
Developer A: Phase 3 (User Story 1 - View task list)
Developer B: Phase 4 (User Story 2 - Create task)
Developer C: Phase 5 (User Story 3 - Mark complete)
Developer D: Phase 6 (User Story 4 - Update task)
Developer E: Phase 7 (User Story 5 - View single task)
Developer F: Phase 8 (User Story 6 - Delete task)
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (View task list)
4. Complete Phase 4: User Story 2 (Create task)
5. **STOP and VALIDATE**: Test that users can create and view tasks
6. Deploy/demo if ready

**Rationale**: User Stories 1 & 2 (both P1) provide the core value - users can add tasks and see them. This is the minimum viable product.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + 2 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 → Test independently → Deploy/Demo (can now complete tasks)
4. Add User Story 4 → Test independently → Deploy/Demo (can now edit tasks)
5. Add User Story 5 → Test independently → Deploy/Demo (can now view task details)
6. Add User Story 6 → Test independently → Deploy/Demo (can now delete tasks)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (View list)
   - Developer B: User Story 2 (Create)
   - Developer C: User Story 3 (Complete)
   - Developer D: User Story 4 (Update)
   - Developer E: User Story 5 (View single)
   - Developer F: User Story 6 (Delete)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All endpoints enforce ownership via X-User-ID header and user_id filtering
- All errors follow RFC 7807 Problem Details format
- All identifiers (user_id, task_id) are UUIDs
- User auto-creation happens automatically on first task operation
