---
id: "0005"
title: Implement Advanced Todo Features
stage: green
date: 2026-02-09
surface: agent
model: claude-opus-4-6
feature: 007-advanced-todo-features
branch: 007-advanced-todo-features
user: CW
command: /sp.implement
labels: ["implementation", "priority", "due-date", "tags", "recurrence", "search", "filter", "sort"]
links:
  spec: specs/007-advanced-todo-features/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/models/task.py
  - backend/models.py
  - backend/schemas.py
  - backend/routers/tasks.py
  - backend/tools/tasks.py
  - backend/src/agents/todo_agent.py
  - backend/migrate_advanced_features.py
  - specs/007-advanced-todo-features/tasks.md
tests:
  - "Import verification: models, schemas, router, tools, agent all import successfully"
  - "Migration verification: 4 new columns confirmed via information_schema query"
---

## Prompt

/sp.implement

## Response snapshot

Implemented all 31 tasks (T001-T031) across 7 phases for the Advanced Todo Features specification:

**Phase 1 (Setup):** Added TaskPriority and TaskRecurrence enums to task model. Added 4 new fields (priority, due_date, tags, recurrence) to Task model. Updated models.py re-exports. Created and ran idempotent migration script against Neon PostgreSQL — 4 columns + 4 indexes added successfully.

**Phase 2 (Schemas):** Updated TaskCreate, TaskUpdate, TaskResponse with new fields. Added field validators for priority, recurrence, and tags (max 10 tags, max 50 chars, lowercase normalization, deduplication). Updated model_post_init to check all 6 fields.

**Phase 3-5 (User Stories):** Updated list_tasks endpoint with 9 query parameters (status, priority, tags, due_before, due_after, overdue, search, sort, order). Implemented priority filter, due date range filter, overdue filter, search (ILIKE), tags filter (PostgreSQL ARRAY contains), and sort with custom priority ordering via case(). Updated create_task and update_task to handle all new fields.

**Phase 6 (MCP Tools):** Updated serialize_task, add_task, update_task, list_tasks MCP tools with all new parameters and validation. Updated AGENT_INSTRUCTIONS with new capabilities and guidelines for natural language processing.

**Phase 7 (Polish):** Tag validation, empty tags normalization, invalid sort field 422 error — all implemented inline during earlier phases.

## Outcome

- ✅ Impact: Full advanced task management (priorities, due dates, tags, recurrence, search/filter/sort) via both REST API and chatbot
- 🧪 Tests: All imports verified; migration verified against Neon DB
- 📁 Files: 7 files modified/created
- 🔁 Next prompts: Manual API testing (curl), chatbot E2E testing, commit and PR
- 🧠 Reflection: Explicit SQL statement lists are more reliable than string-splitting for migration scripts

## Evaluation notes (flywheel)

- Failure modes observed: SQL migration script splitting by semicolons stripped ALTER TABLE statements due to leading comment lines — fixed by using explicit statement list
- Graders run and results (PASS/FAIL): Import verification PASS, Migration PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
