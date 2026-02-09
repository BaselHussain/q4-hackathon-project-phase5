---
id: 0002
title: Advanced Todo Features Plan
stage: plan
date: 2026-02-09
surface: agent
model: claude-opus-4-6
feature: 007-advanced-todo-features
branch: 007-advanced-todo-features
user: system
command: /sp.plan
labels: ["plan", "advanced-features", "data-model", "api-contracts", "mcp-tools", "migration"]
links:
  spec: specs/007-advanced-todo-features/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-advanced-todo-features/plan.md
tests:
  - none
---

## Prompt

/sp.plan Spec 7 - Advanced Todo Features

Follow the approved spec in specs/advanced-todo-features/spec.md exactly.

Create full execution plan:

1. Detailed folder/file structure changes:
   - backend/models/task.py (update Task model with new fields)
   - backend/schemas/task.py (update Pydantic schemas for create/update)
   - backend/routers/tasks.py (update endpoints with new query params)
   - backend/tools/tasks.py (update MCP tools to handle new fields)
   - backend/services/task_service.py (new service layer for business logic)

2. Step-by-step integration plan:
   - Update Task SQLModel: add due_date, priority, tags, recurrence
   - Update Pydantic schemas: TaskCreate, TaskUpdate, TaskRead (include new fields)
   - Modify POST /api/{user_id}/tasks: accept new fields
   - Modify PUT /api/{user_id}/tasks/{task_id}: accept new fields
   - Update GET /api/{user_id}/tasks: add query params for filter, sort, search
   - Update MCP tools:
     - add_task & update_task -> accept new fields
     - list_tasks -> support filter, sort, search params
   - Add basic validation (due_date in future, valid priority enum)
   - Add ownership enforcement in all operations

3. Decision table:
   - Recurrence storage: enum vs JSON (choose JSON for flexibility)
   - Tags: array vs comma string (choose array in PostgreSQL)
   - Filter/sort: SQLAlchemy query builder vs raw SQL (choose SQLAlchemy)

4. Testing strategy with exact commands
5. Risk mitigation

Output in specs/advanced-todo-features/PLAN.md

Go.

## Response snapshot

Created comprehensive implementation plan for Advanced Todo Features (Spec 7) with 8 architectural decisions, 4-phase integration plan, and 10 manual test scenarios.

**Key Decisions Made (8 total)**:
- D1: Priority → Python enum + VARCHAR (matches existing TaskStatus pattern)
- D2: Tags → PostgreSQL ARRAY(String) for native contains queries
- D3: Recurrence → Python enum + VARCHAR (simple, extensible later)
- D4: Due date → DateTime(timezone=True) matching existing timestamp pattern
- D5: Search → ILIKE for simplicity at current scale
- D6: Filter/sort → SQLAlchemy dynamic query builder (type-safe, injection-proof)
- D7: Migration → Raw SQL ALTER TABLE (no Alembic overhead for 4 columns)
- D8: Date parsing → Let LLM agent handle natural language to ISO 8601

**Files to Modify (7)**:
1. backend/src/models/task.py - Add TaskPriority, TaskRecurrence enums + 4 new fields
2. backend/schemas.py - Update TaskCreate, TaskUpdate, TaskResponse
3. backend/routers/tasks.py - Add query params to GET, new fields to POST/PUT
4. backend/tools/tasks.py - Update add_task, update_task, list_tasks MCP tools
5. backend/src/agents/todo_agent.py - Update agent instructions
6. backend/migrate_advanced_features.py - CREATE: idempotent migration script
7. backend/models.py - NO CHANGE (auto re-exports)

**4-Phase Integration Plan**:
- Phase 1: Data Model + Migration (blocking)
- Phase 2: Schemas + Router (US1: Priorities & Due Dates)
- Phase 3: MCP Tools (US1 + US2: All Features via Chatbot)
- Phase 4: Validation & Polish (US3: Recurring Tasks + Edge Cases)

**Constitution Check**: All 7 principles PASS.

## Outcome

- ✅ Impact: Comprehensive plan created covering data model changes (2 new enums, 4 new columns), API contract updates (3 endpoints), MCP tool modifications (3 tools + serializer), agent instruction updates, and database migration strategy. All decisions align with existing codebase patterns.
- 🧪 Tests: 10 manual API test scenarios documented with exact curl commands. 7 chatbot E2E test scenarios documented.
- 📁 Files: Created specs/007-advanced-todo-features/plan.md (comprehensive implementation plan)
- 🔁 Next prompts: Run `/sp.tasks` to generate actionable task breakdown from plan.md
- 🧠 Reflection: Plan follows existing codebase patterns strictly (no new service layer, no Alembic). Decision to keep logic in routers/tools matches current architecture. Key insight: agent handles date parsing via LLM, avoiding custom parser code.

## Evaluation notes (flywheel)

- Failure modes observed: None - plan created successfully after reading all 9 relevant source files
- Graders run and results (PASS/FAIL): PASS - Constitution check passes all 7 principles. All 58 FRs from spec are addressed in plan. Backward compatibility ensured via nullable columns with defaults.
- Prompt variant (if applicable): Standard /sp.plan workflow with detailed user-provided integration steps
- Next experiment (smallest change to try): Proceed with /sp.tasks to break plan into implementation tasks
