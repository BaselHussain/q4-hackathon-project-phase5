# Tasks: MCP Server & Tools

**Input**: Design documents from `/specs/mcp-tools/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/mcp-tools.yaml

**Tests**: Not requested - manual curl testing per quickstart.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/` at repository root
- MCP server runs as separate process on port 8001

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Add MCP SDK dependency and create project structure

- [x] T001 Add mcp>=1.0.0 to backend/requirements.txt
- [x] T002 Create backend/tools/ directory structure
- [x] T003 [P] Create backend/tools/__init__.py with package exports
- [x] T004 [P] Create backend/mcp_server.py with FastMCP server initialization

**Checkpoint**: MCP server can start (no tools yet) ✓

---

## Phase 2: Foundational (Shared Tool Infrastructure)

**Purpose**: Create helper utilities used by all 5 tools

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create UUID validation helper function in backend/tools/tasks.py
- [x] T006 [P] Create task serialization helper (Task model → JSON dict) in backend/tools/tasks.py
- [x] T007 [P] Create error response helper function in backend/tools/tasks.py
- [x] T008 Create database session context manager for tools in backend/tools/tasks.py
- [x] T009 Import existing Task model and TaskStatus enum from backend/src/models/task.py
- [x] T010 Import AsyncSessionLocal from backend/database.py into tools module

**Checkpoint**: Foundation ready - tool implementation can now begin ✓

---

## Phase 3: User Story 1 - Add Task Tool (Priority: P1)

**Goal**: AI agent can create new tasks for users via MCP tool

**Independent Test**: `curl -X POST http://localhost:8001/mcp/tools/add_task -d '{"user_id": "UUID", "title": "Test"}'` returns task with status "pending"

### Implementation for User Story 1

- [x] T011 [US1] Implement add_task tool function with @mcp.tool() decorator in backend/tools/tasks.py
- [x] T012 [US1] Add title validation (required, 1-200 chars) in add_task tool
- [x] T013 [US1] Add description validation (optional, max 2000 chars) in add_task tool
- [x] T014 [US1] Implement database INSERT for new task with status="pending" in add_task tool
- [x] T015 [US1] Return structured JSON response {success: true, data: {task_id, title, status, timestamps}} from add_task

**Checkpoint**: add_task tool works - can create tasks via MCP ✓

---

## Phase 4: User Story 2 - List Tasks Tool (Priority: P1)

**Goal**: AI agent can retrieve user's tasks with optional status filter

**Independent Test**: `curl -X POST http://localhost:8001/mcp/tools/list_tasks -d '{"user_id": "UUID", "status": "pending"}'` returns filtered task array

### Implementation for User Story 2

- [x] T016 [US2] Implement list_tasks tool function with @mcp.tool() decorator in backend/tools/tasks.py
- [x] T017 [US2] Add status parameter validation (all/pending/completed, default "all") in list_tasks tool
- [x] T018 [US2] Implement database SELECT with user_id filter in list_tasks tool
- [x] T019 [US2] Add status filter to query when status != "all" in list_tasks tool
- [x] T020 [US2] Return structured JSON response {success: true, data: [array of tasks]} from list_tasks

**Checkpoint**: add_task + list_tasks work - can create and view tasks via MCP ✓

---

## Phase 5: User Story 3 - Complete Task Tool (Priority: P2)

**Goal**: AI agent can mark tasks as completed

**Independent Test**: Create pending task, call complete_task, verify status changes to "completed"

### Implementation for User Story 3

- [x] T021 [US3] Implement complete_task tool function with @mcp.tool() decorator in backend/tools/tasks.py
- [x] T022 [US3] Add task_id UUID validation in complete_task tool
- [x] T023 [US3] Implement ownership check (task.user_id == user_id) in complete_task tool
- [x] T024 [US3] Implement database UPDATE to set status="completed" in complete_task tool
- [x] T025 [US3] Handle idempotency - already completed task returns success in complete_task tool
- [x] T026 [US3] Return "Task not found or access denied" error for invalid/unauthorized task_id

**Checkpoint**: add_task + list_tasks + complete_task work ✓

---

## Phase 6: User Story 4 - Delete Task Tool (Priority: P2)

**Goal**: AI agent can permanently remove tasks

**Independent Test**: Create task, call delete_task, verify task no longer exists in database

### Implementation for User Story 4

- [x] T027 [US4] Implement delete_task tool function with @mcp.tool() decorator in backend/tools/tasks.py
- [x] T028 [US4] Add task_id UUID validation in delete_task tool
- [x] T029 [US4] Implement ownership check (task.user_id == user_id) in delete_task tool
- [x] T030 [US4] Implement database DELETE for the task in delete_task tool
- [x] T031 [US4] Return {success: true, data: {task_id, message: "Task deleted successfully"}} from delete_task

**Checkpoint**: add_task + list_tasks + complete_task + delete_task work ✓

---

## Phase 7: User Story 5 - Update Task Tool (Priority: P3)

**Goal**: AI agent can modify task title and/or description

**Independent Test**: Create task, call update_task with new title, verify title changed in database

### Implementation for User Story 5

- [x] T032 [US5] Implement update_task tool function with @mcp.tool() decorator in backend/tools/tasks.py
- [x] T033 [US5] Add task_id UUID validation in update_task tool
- [x] T034 [US5] Validate at least one of title/description provided in update_task tool
- [x] T035 [US5] Add title validation (1-200 chars if provided) in update_task tool
- [x] T036 [US5] Add description validation (max 2000 chars if provided) in update_task tool
- [x] T037 [US5] Implement ownership check (task.user_id == user_id) in update_task tool
- [x] T038 [US5] Implement database UPDATE for provided fields only in update_task tool
- [x] T039 [US5] Return updated task data from update_task tool

**Checkpoint**: All 5 tools work - full MCP tool suite complete ✓

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [x] T040 Register all 5 tools with MCP server in backend/mcp_server.py via register_tools() call
- [x] T041 [P] Add database connection error handling to all tools (return "Service temporarily unavailable")
- [x] T042 [P] Verify all tools return valid JSON (test with `curl ... | jq .`)
- [x] T043 Run ownership enforcement test per quickstart.md (wrong user_id returns error)
- [x] T044 Run stateless verification test per quickstart.md (restart server, data persists)
- [x] T045 Verify MCP server starts in <5 seconds (SC-001)
- [x] T046 Verify tool responses complete in <2 seconds (SC-002)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately ✓
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories ✓
- **Phases 3-7 (User Stories)**: All depend on Phase 2 completion ✓
  - US1 (add_task) and US2 (list_tasks) can run in parallel
  - US3 (complete_task) and US4 (delete_task) can run in parallel after US1
  - US5 (update_task) can run after US1
- **Phase 8 (Polish)**: Depends on all user stories complete (in progress)

### User Story Dependencies

- **US1 (add_task)**: Can start after Phase 2 - No dependencies on other stories ✓
- **US2 (list_tasks)**: Can start after Phase 2 - No dependencies on other stories ✓
- **US3 (complete_task)**: Logically requires US1 for testing (need task to complete) ✓
- **US4 (delete_task)**: Logically requires US1 for testing (need task to delete) ✓
- **US5 (update_task)**: Logically requires US1 for testing (need task to update) ✓

### Within Each User Story

- Tool function skeleton first
- Validation logic second
- Database operations third
- Response formatting last

### Parallel Opportunities

- T003, T004 can run in parallel (different files)
- T006, T007 can run in parallel (different helper functions)
- US1 and US2 can run in parallel (independent tools)
- US3 and US4 can run in parallel (both modify existing tasks)
- T041, T042 can run in parallel (different validation checks)

---

## Parallel Example: Phase 2

```bash
# Launch foundational helpers together:
Task: "Create UUID validation helper function in backend/tools/tasks.py"
Task: "Create task serialization helper in backend/tools/tasks.py"
Task: "Create error response helper function in backend/tools/tasks.py"
```

## Parallel Example: User Stories 1 & 2

```bash
# After Phase 2, launch both P1 tools together:
Task: "Implement add_task tool function with @mcp.tool() decorator in backend/tools/tasks.py"
Task: "Implement list_tasks tool function with @mcp.tool() decorator in backend/tools/tasks.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup ✓
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) ✓
3. Complete Phase 3: User Story 1 (add_task) ✓
4. Complete Phase 4: User Story 2 (list_tasks) ✓
5. **STOP and VALIDATE**: Test add_task and list_tasks independently
6. Deploy/demo if ready (MVP!)

### Incremental Delivery

1. Setup + Foundational → Foundation ready ✓
2. Add US1 (add_task) → Test → Can create tasks ✓
3. Add US2 (list_tasks) → Test → Can view tasks (MVP complete) ✓
4. Add US3 (complete_task) → Test → Can mark done ✓
5. Add US4 (delete_task) → Test → Can remove tasks ✓
6. Add US5 (update_task) → Test → Can edit tasks ✓
7. Each tool adds value without breaking previous tools

### Sequential Execution Order

```
T001 → T002 → T003,T004 (parallel) → T005 → T006,T007 (parallel) → T008 → T009 → T010
  → T011-T015 (US1) → T016-T020 (US2) → T021-T026 (US3) → T027-T031 (US4) → T032-T039 (US5)
  → T040 → T041,T042 (parallel) → T043 → T044 → T045 → T046
```

---

## Notes

- [P] tasks = different files or no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- Verify each tool works before moving to next
- Commit after each phase or logical group
- Stop at any checkpoint to validate progress
- No test tasks included (manual testing per quickstart.md)

---

## Implementation Summary

**Completed**: 2026-02-03

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: Setup | T001-T004 | COMPLETE |
| Phase 2: Foundational | T005-T010 | COMPLETE |
| Phase 3: US1 (add_task) | T011-T015 | COMPLETE |
| Phase 4: US2 (list_tasks) | T016-T020 | COMPLETE |
| Phase 5: US3 (complete_task) | T021-T026 | COMPLETE |
| Phase 6: US4 (delete_task) | T027-T031 | COMPLETE |
| Phase 7: US5 (update_task) | T032-T039 | COMPLETE |
| Phase 8: Polish | T040-T046 | COMPLETE |

**Files Created**:
- `backend/requirements.txt` (modified - added mcp>=1.0.0)
- `backend/tools/__init__.py` (new)
- `backend/tools/tasks.py` (new - all 5 tools)
- `backend/mcp_server.py` (new)
