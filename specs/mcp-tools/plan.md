# Implementation Plan: MCP Server & Tools

**Branch**: `mcp-tools` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/mcp-tools/spec.md`

## Summary

Build a stateless MCP server using the Official MCP SDK (Python) that exposes 5 task management tools for the AI agent. All tools interact with existing Neon PostgreSQL database via SQLModel. Tools are stateless - no in-memory state between invocations.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: mcp>=1.0.0, SQLModel 0.0.22+, asyncpg 0.30+, FastAPI 0.109+
**Storage**: Neon Serverless PostgreSQL (existing from Phase 1/2)
**Testing**: Manual curl testing + MCP client verification
**Target Platform**: Linux server (Render deployment)
**Project Type**: Web application (backend extension)
**Performance Goals**: Tool response <2 seconds, server startup <5 seconds
**Constraints**: Stateless tools, all state in database, no shared memory
**Scale/Scope**: Single MCP server, 5 tools, existing user base

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | ✅ PASS | Spec created at specs/mcp-tools/spec.md |
| II. AI-First Stateless Architecture | ✅ PASS | MCP tools stateless, DB is source of truth |
| III. Secure Authentication | ✅ PASS | Tools trust user_id from agent (JWT at API layer) |
| IV. Persistent Data & Conversation | ✅ PASS | Uses existing tasks table |
| VI. Stateless Tool Design | ✅ PASS | Each tool creates fresh DB session |
| VIII. MCP Server Protocol | ✅ PASS | Uses official MCP SDK with FastMCP pattern |

## Project Structure

### Documentation (this feature)

```text
specs/mcp-tools/
├── spec.md              # Feature specification
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 output (MCP SDK research)
├── data-model.md        # Phase 1 output (tool schemas)
├── quickstart.md        # Phase 1 output (testing guide)
├── contracts/           # Phase 1 output
│   └── mcp-tools.yaml   # MCP tool definitions
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── requirements.txt          # Add: mcp>=1.0.0 [MODIFY]
├── mcp_server.py             # MCP server entry point [NEW]
├── tools/                    # [NEW DIRECTORY]
│   ├── __init__.py           # [NEW]
│   └── tasks.py              # 5 MCP tool functions [NEW]
├── src/
│   └── models/
│       └── task.py           # Existing Task model [NO CHANGE]
├── database.py               # Existing DB config [NO CHANGE]
└── main.py                   # Existing FastAPI app [NO CHANGE]
```

**Structure Decision**: Extend existing backend with separate `tools/` directory for MCP tool functions. MCP server runs as separate process on different port (8001) from FastAPI (8000).

## Decision Table

| Decision | Options Considered | Chosen | Rationale |
|----------|-------------------|--------|-----------|
| State storage | In-memory vs Database | Database | Constitution requires stateless tools |
| Tool registration | Manual vs SDK decorator | SDK (@mcp.tool()) | Cleaner, auto-generates schemas |
| Transport | SSE vs Streamable HTTP | Streamable HTTP | SSE deprecated by MCP project |
| Server architecture | Embed in FastAPI vs Separate | Separate process | Better isolation, independent scaling |
| Error handling | Raise exceptions vs Return errors | Return structured errors | Friendly for AI agent parsing |
| DB sessions | Shared vs Per-tool | Per-tool | Stateless requirement |

## File Changes Summary

### New Files

| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `backend/mcp_server.py` | MCP server setup and startup | ~50 |
| `backend/tools/__init__.py` | Package init, export tools | ~10 |
| `backend/tools/tasks.py` | 5 MCP tool implementations | ~200 |

### Modified Files

| File | Change | Lines Changed (Est.) |
|------|--------|---------------------|
| `backend/requirements.txt` | Add mcp>=1.0.0 | +1 |

### Unchanged Files

- `backend/src/models/task.py` - Reuse existing Task model
- `backend/database.py` - Reuse existing engine/session
- `backend/main.py` - No changes needed

## Implementation Details

### 1. backend/mcp_server.py

```python
"""
MCP Server for Todo Task Management.

Exposes 5 stateless tools: add_task, list_tasks, complete_task, delete_task, update_task
All tools interact with Neon PostgreSQL database.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from tools.tasks import register_tools

# Initialize MCP server
mcp = FastMCP("Todo MCP Server", json_response=True)

# Register all task tools
register_tools(mcp)

if __name__ == "__main__":
    # Run on port 8001 (separate from FastAPI on 8000)
    mcp.run(transport="streamable-http", port=8001)
```

### 2. backend/tools/tasks.py

```python
"""
Stateless MCP tools for task management.

Each tool:
- Creates fresh database session (stateless)
- Validates user ownership
- Returns structured JSON response
- Handles errors gracefully
"""
from uuid import UUID
from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from src.models.task import Task, TaskStatus

def register_tools(mcp):
    """Register all task tools with MCP server."""

    @mcp.tool()
    async def add_task(user_id: str, title: str, description: str = None) -> dict:
        """Add a new task for the user."""
        # Implementation...

    @mcp.tool()
    async def list_tasks(user_id: str, status: str = "all") -> dict:
        """List tasks for the user with optional status filter."""
        # Implementation...

    @mcp.tool()
    async def complete_task(user_id: str, task_id: str) -> dict:
        """Mark a task as completed."""
        # Implementation...

    @mcp.tool()
    async def delete_task(user_id: str, task_id: str) -> dict:
        """Permanently delete a task."""
        # Implementation...

    @mcp.tool()
    async def update_task(user_id: str, task_id: str,
                          title: str = None, description: str = None) -> dict:
        """Update a task's title and/or description."""
        # Implementation...
```

### Tool Response Format

All tools return consistent JSON:

```python
# Success
{"success": True, "data": {...}}

# Error
{"success": False, "error": "User-friendly message"}
```

### Error Handling Pattern

```python
try:
    user_uuid = UUID(user_id)
except ValueError:
    return {"success": False, "error": "Invalid ID format"}

async with AsyncSessionLocal() as session:
    task = await session.get(Task, task_uuid)
    if not task or str(task.user_id) != user_id:
        return {"success": False, "error": "Task not found or access denied"}
```

## Testing Strategy

### Manual Testing Commands

```bash
# 1. Start MCP server
cd backend && python mcp_server.py

# 2. Test add_task
curl -X POST http://localhost:8001/mcp/tools/add_task \
  -H "Content-Type: application/json" \
  -d '{"user_id": "UUID", "title": "Test task"}'

# 3. Test list_tasks
curl -X POST http://localhost:8001/mcp/tools/list_tasks \
  -H "Content-Type: application/json" \
  -d '{"user_id": "UUID", "status": "all"}'

# 4. Test complete_task
curl -X POST http://localhost:8001/mcp/tools/complete_task \
  -H "Content-Type: application/json" \
  -d '{"user_id": "UUID", "task_id": "TASK_UUID"}'

# 5. Test delete_task
curl -X POST http://localhost:8001/mcp/tools/delete_task \
  -H "Content-Type: application/json" \
  -d '{"user_id": "UUID", "task_id": "TASK_UUID"}'

# 6. Test update_task
curl -X POST http://localhost:8001/mcp/tools/update_task \
  -H "Content-Type: application/json" \
  -d '{"user_id": "UUID", "task_id": "TASK_UUID", "title": "Updated"}'
```

### Ownership Enforcement Test

```bash
# Create task as User A
curl -X POST http://localhost:8001/mcp/tools/add_task \
  -d '{"user_id": "USER_A_UUID", "title": "A task"}'

# Try to delete as User B (should fail)
curl -X POST http://localhost:8001/mcp/tools/delete_task \
  -d '{"user_id": "USER_B_UUID", "task_id": "TASK_FROM_A"}'
# Expected: {"success": false, "error": "Task not found or access denied"}
```

### Stateless Verification Test

```bash
# 1. Add task
curl ... add_task ...

# 2. Stop server (Ctrl+C)

# 3. Restart server
python mcp_server.py

# 4. List tasks - should still show the task
curl ... list_tasks ...
```

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| DB connection failure | Tool returns error | Return `{"success": false, "error": "Service temporarily unavailable"}` |
| Invalid user_id format | Tool crashes | Validate UUID format, return friendly error |
| Task not found | Operation fails silently | Return explicit error message |
| Tool timeout | Agent hangs | Set 30s timeout, return error on exceed |
| Concurrent modifications | Data race | Last write wins (DB handles, acceptable) |

## Dependencies

```text
Phase 1/2 (Required):
├── backend/database.py (AsyncSessionLocal, engine)
├── backend/src/models/task.py (Task model)
├── Neon PostgreSQL (tasks table)
└── .env (DATABASE_URL)

This Feature (New):
├── mcp>=1.0.0 (Official MCP SDK)
└── backend/tools/ (new directory)
```

## Deployment Notes

### Local Development

```bash
cd backend
pip install -r requirements.txt
python mcp_server.py  # Runs on port 8001
```

### Render Deployment

Add to `render.yaml` or create new service:
```yaml
services:
  - type: web
    name: mcp-server
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python mcp_server.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: neon-db
          property: connectionString
```

## Success Criteria Verification

| Criteria | Verification Method |
|----------|---------------------|
| SC-001: Server starts <5s | `time python mcp_server.py` |
| SC-002: Tool response <2s | Check response time in curl |
| SC-003: Ownership enforced | Run ownership test |
| SC-004: User-friendly errors | Test invalid inputs |
| SC-005: Valid JSON | `curl ... | jq .` |
| SC-006: Stateless | Run restart test |
| SC-007: DB persistence | Query database after operations |

## Next Steps

After `/sp.tasks`:
1. Implement MCP server setup (mcp_server.py)
2. Implement 5 tool functions (tools/tasks.py)
3. Test each tool manually
4. Verify success criteria
5. Proceed to Spec 2 (AI Agent & Chat Logic)
