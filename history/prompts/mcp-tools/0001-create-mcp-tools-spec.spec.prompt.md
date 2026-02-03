---
id: 1
title: Create MCP Server Tools Specification
stage: spec
date: 2026-02-03
surface: agent
model: claude-opus-4-5-20251101
feature: mcp-tools
branch: mcp-tools
user: developer
command: /sp.specify
labels: ["mcp", "tools", "stateless", "phase3", "ai-chatbot"]
links:
  spec: specs/mcp-tools/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/mcp-tools/spec.md
  - specs/mcp-tools/checklists/requirements.md
tests:
  - null
---

## Prompt

MCP Server & Tools (Spec 4)

Create folder: specs/mcp-tools/ only (no number prefix)

Core goal: Build a stateless MCP server using Official MCP SDK that exposes todo task operations as tools for the AI agent in Phase 3.

Key requirements:
- Use Official MCP SDK to create the MCP server
- Expose exactly 5 stateless tools (all interact with Neon DB via SQLModel from Phase 2):
  - add_task(user_id, title, description) → create task, return task_id + status
  - list_tasks(user_id, status=all/pending/completed) → return array of tasks
  - complete_task(user_id, task_id) → mark complete, return updated status
  - delete_task(user_id, task_id) → delete task, return status
  - update_task(user_id, task_id, title?, description?) → update fields, return updated task
- All tools must be stateless — fetch/store data from Neon DB (tasks table from Phase 2)
- Use existing Phase 2 auth (JWT) to verify user_id ownership
- Handle errors gracefully (task not found → friendly error)
- Tools must return structured JSON (task_id, status, title, etc.)

Constraints:
- Stateless server (no in-memory state)
- Use Neon PostgreSQL (DATABASE_URL in .env)
- Integrate with existing FastAPI backend from Phase 2
- No direct frontend interaction — tools only for AI agent

Success criteria:
- MCP server runs and exposes all 5 tools
- Tools correctly read/write to Neon DB
- Ownership enforced (wrong user_id → error)
- Test with MCP client or direct call → add/list/complete/delete/update works

Use Context7 MCP for Official MCP SDK examples and tool patterns if needed.

## Response snapshot

Created comprehensive MCP Server & Tools specification at specs/mcp-tools/spec.md with:

**5 User Stories (prioritized)**:
- P1: AI Agent Adds Task via MCP Tool
- P1: AI Agent Lists Tasks via MCP Tool
- P2: AI Agent Completes Task via MCP Tool
- P2: AI Agent Deletes Task via MCP Tool
- P3: AI Agent Updates Task via MCP Tool

**14 Functional Requirements** covering:
- 5 stateless tools with exact signatures
- User isolation and ownership enforcement
- Structured JSON responses
- Graceful error handling
- Database integration via existing schema

**7 Success Criteria** (measurable, technology-agnostic):
- Server startup time (<5s)
- Tool response time (<2s)
- 100% ownership enforcement
- User-friendly error messages
- Valid JSON responses
- Zero in-memory state
- Correct database persistence

**Edge Cases** documented:
- Concurrent modifications
- Invalid UUID format
- Database connection failures
- Field length validation

Quality checklist created and validated - all items PASS.

## Outcome

- Impact: Created Spec 1 of 3 for Phase 3 AI Chatbot - MCP tools foundation
- Tests: N/A (specification document)
- Files: 2 created (spec.md, checklists/requirements.md)
- Next prompts: /sp.plan to create implementation plan for MCP tools
- Reflection: Spec aligns with Phase 3 constitution requiring stateless tools and database-only state

## Evaluation notes (flywheel)

- Failure modes observed: None - clean specification
- Graders run and results (PASS/FAIL): Quality checklist PASS - all items validated
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate tool signatures during planning phase
