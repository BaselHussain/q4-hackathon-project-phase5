---
id: 2
title: Create MCP Tools Implementation Plan
stage: plan
date: 2026-02-03
surface: agent
model: claude-opus-4-5-20251101
feature: mcp-tools
branch: mcp-tools
user: developer
command: /sp.plan
labels: ["mcp", "implementation", "plan", "phase3", "tools"]
links:
  spec: specs/mcp-tools/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/mcp-tools/plan.md
  - specs/mcp-tools/research.md
  - specs/mcp-tools/data-model.md
  - specs/mcp-tools/quickstart.md
  - specs/mcp-tools/contracts/mcp-tools.yaml
tests:
  - null
---

## Prompt

MCP Server & Tools (Spec 4)

Follow the approved spec in specs/mcp-tools/spec.md exactly.

Create full execution plan:

1. Detailed folder/file structure changes:
   - backend/requirements.txt (add official-mcp-sdk)
   - backend/mcp_server.py (MCP server setup)
   - backend/tools/tasks.py (5 MCP tool functions)
   - backend/dependencies.py (update for MCP tools)

2. Step-by-step integration plan:
   - Install Official MCP SDK in backend
   - Create MCP server instance in FastAPI
   - Define 5 stateless tools using @tool decorator
   - Integrate tools with SQLModel + Neon DB (from Phase 2)
   - Add JWT dependency to verify user ownership
   - Handle tool errors with structured responses
   - Expose tools via MCP endpoint

3. Decision table:
   - In-memory vs DB for tools (choose DB — stateless)
   - Manual vs SDK tool registration (choose SDK)

4. Testing strategy with exact commands:
   - Run backend → test MCP endpoint with curl or MCP client
   - Call add_task → verify task in Neon DB
   - Call list_tasks → verify filtered output
   - Test ownership: wrong user_id → error
   - Test complete/delete/update → confirm changes

5. Risk mitigation:
   - DB connection fail → tool error response
   - Invalid user_id → 403 early
   - Tool timeout → graceful fallback

Output in specs/mcp-tools/PLAN.md

## Response snapshot

Created comprehensive implementation plan with:

**Phase 0: Research (research.md)**
- Official MCP SDK selection (mcp>=1.0.0 from PyPI)
- FastMCP pattern with @mcp.tool() decorator
- Streamable HTTP transport (SSE deprecated)
- Database integration via fresh session per tool
- Error handling pattern (return structured JSON, never raise)

**Phase 1: Design Artifacts**
- data-model.md: Tool parameter/response schemas
- contracts/mcp-tools.yaml: Complete tool definitions with examples
- quickstart.md: Testing guide with curl commands

**Implementation Plan (plan.md)**
- Technical Context: Python 3.11+, mcp, SQLModel, asyncpg
- Project Structure: New backend/tools/ directory, mcp_server.py
- Decision Table: DB storage, SDK registration, Streamable HTTP
- 3 new files, 1 modified file
- Testing strategy with exact curl commands
- Risk mitigation table

**Constitution Check**: All 6 relevant principles PASS

## Outcome

- Impact: Created complete implementation plan for MCP Server & Tools
- Tests: Manual curl testing commands documented in quickstart.md
- Files: 5 created (plan.md, research.md, data-model.md, quickstart.md, mcp-tools.yaml)
- Next prompts: /sp.tasks to generate implementation task list
- Reflection: Plan aligns with constitution - stateless tools, DB as source of truth, official MCP SDK

## Evaluation notes (flywheel)

- Failure modes observed: None - clean planning
- Graders run and results (PASS/FAIL): Constitution check PASS on all principles
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate MCP SDK import during implementation
