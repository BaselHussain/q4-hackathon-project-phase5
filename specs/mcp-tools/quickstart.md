# Quickstart: MCP Server & Tools

**Feature**: MCP Server & Tools
**Date**: 2026-02-03

## Prerequisites

- Python 3.11+
- Existing backend from Phase 1/2 running
- Neon PostgreSQL database configured (DATABASE_URL in .env)
- UV package manager (recommended) or pip

## Installation

### 1. Add MCP SDK to Backend Dependencies

```bash
cd backend
pip install mcp
```

Or add to `requirements.txt`:
```
mcp>=1.0.0
```

### 2. Environment Variables

Ensure `.env` contains:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

No additional environment variables required for MCP tools.

## Running the MCP Server

### Start MCP Server (Standalone)

```bash
cd backend
python -m mcp_server
```

The MCP server will start on port 8001 by default (separate from FastAPI on 8000).

### Verify Server is Running

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{"status": "healthy", "tools": 5}
```

## Testing Tools Manually

### Test add_task

```bash
curl -X POST http://localhost:8001/mcp/tools/add_task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_UUID",
    "title": "Test task from MCP",
    "description": "Created via MCP tool"
  }'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "task_id": "generated-uuid",
    "title": "Test task from MCP",
    "description": "Created via MCP tool",
    "status": "pending",
    "created_at": "2026-02-03T10:00:00Z",
    "updated_at": "2026-02-03T10:00:00Z"
  }
}
```

### Test list_tasks

```bash
curl -X POST http://localhost:8001/mcp/tools/list_tasks \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_UUID",
    "status": "all"
  }'
```

### Test complete_task

```bash
curl -X POST http://localhost:8001/mcp/tools/complete_task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_UUID",
    "task_id": "TASK_UUID_FROM_ADD"
  }'
```

### Test delete_task

```bash
curl -X POST http://localhost:8001/mcp/tools/delete_task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_UUID",
    "task_id": "TASK_UUID_TO_DELETE"
  }'
```

### Test update_task

```bash
curl -X POST http://localhost:8001/mcp/tools/update_task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_UUID",
    "task_id": "TASK_UUID_TO_UPDATE",
    "title": "Updated title"
  }'
```

## Verifying Stateless Behavior

1. Add a task via MCP tool
2. Stop the MCP server (`Ctrl+C`)
3. Restart the MCP server
4. List tasks - the task should still be there (stored in DB)

This confirms the server is stateless and all data persists in database.

## Testing Ownership Enforcement

1. Create a task with user_id A
2. Try to complete/delete/update with user_id B
3. Should receive error: `"Task not found or access denied"`

```bash
# Create with user A
curl -X POST http://localhost:8001/mcp/tools/add_task \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-a-uuid", "title": "User A task"}'

# Try to complete with user B (should fail)
curl -X POST http://localhost:8001/mcp/tools/complete_task \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-b-uuid", "task_id": "task-from-user-a"}'
```

## Connecting from OpenAI Agent (Preview for Spec 2)

```python
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="Todo MCP Server",
    params={"url": "http://localhost:8001/mcp"}
) as server:
    # Agent can now use add_task, list_tasks, etc.
    pass
```

## Troubleshooting

### MCP Server Won't Start

1. Check DATABASE_URL is set: `echo $DATABASE_URL`
2. Verify database is accessible: `psql $DATABASE_URL -c "SELECT 1"`
3. Check port 8001 is available: `lsof -i :8001`

### Tools Return Database Errors

1. Verify tasks table exists in database
2. Check user_id format is valid UUID
3. Review server logs for detailed error

### Tool Returns "Invalid ID format"

Ensure user_id and task_id are valid UUID v4 strings:
- Valid: `550e8400-e29b-41d4-a716-446655440000`
- Invalid: `12345`, `not-a-uuid`, `null`

## Success Criteria Verification

| Criteria | How to Verify |
|----------|---------------|
| SC-001: Server starts in <5s | Time the startup: `time python -m mcp_server` |
| SC-002: Tool response <2s | Check X-Response-Time header in curl output |
| SC-003: Ownership enforced | Run ownership test above |
| SC-004: User-friendly errors | Try invalid UUID, check error message |
| SC-005: Valid JSON | Pipe curl output to `jq .` |
| SC-006: Stateless | Run restart test above |
| SC-007: DB persistence | Query database after tool operations |
