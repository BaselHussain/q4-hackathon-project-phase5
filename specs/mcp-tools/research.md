# Research: MCP Server & Tools

**Feature**: MCP Server & Tools
**Date**: 2026-02-03
**Purpose**: Resolve technical unknowns and establish best practices for MCP implementation

## Research Summary

### 1. Official MCP SDK Selection

**Decision**: Use `mcp` package (Official Python SDK) with FastMCP pattern

**Rationale**:
- Official SDK maintained by modelcontextprotocol organization
- FastMCP provides decorator-based tool definition (`@mcp.tool()`)
- Stable v1.x recommended for production (v2 expected Q1 2026)
- Designed specifically for LLM interactions with standardized patterns

**Alternatives Considered**:
- Custom tool implementation: Rejected - doesn't follow MCP standard
- Third-party SDKs: Rejected - not official, less maintained

**Installation**:
```bash
pip install mcp
```

### 2. MCP Server Integration with FastAPI

**Decision**: Run MCP server as separate process, connect via Streamable HTTP transport

**Rationale**:
- MCP servers expose tools via HTTP endpoints (similar to REST APIs)
- Streamable HTTP is the current recommended transport (SSE deprecated)
- Allows independent scaling of MCP server and FastAPI backend
- Stateless design maintained - no shared memory between processes

**Alternatives Considered**:
- Embed MCP in FastAPI: Rejected - violates separation, harder to test
- SSE transport: Rejected - deprecated by MCP project
- Stdio transport: Rejected - requires subprocess management in production

### 3. Tool Definition Pattern

**Decision**: Use FastMCP decorator pattern with type-annotated functions

**Pattern**:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Todo MCP Server", json_response=True)

@mcp.tool()
async def add_task(user_id: str, title: str, description: str = None) -> dict:
    """Add a new task for the user"""
    # Database interaction here
    return {"task_id": "...", "status": "pending", ...}
```

**Rationale**:
- Type hints enable automatic schema generation
- Docstrings become tool descriptions for AI agent
- Async functions support database operations
- `json_response=True` ensures structured output

### 4. Database Integration Strategy

**Decision**: Create dedicated database session per tool invocation (stateless)

**Pattern**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create engine once at module level
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)

@mcp.tool()
async def add_task(user_id: str, title: str, description: str = None) -> dict:
    async with AsyncSessionLocal() as session:
        # Perform DB operations
        await session.commit()
        return result
```

**Rationale**:
- Each tool call gets fresh session (stateless)
- Reuses existing SQLAlchemy engine configuration
- Compatible with existing Phase 1/2 database setup
- Proper connection pooling via engine

### 5. Error Handling Pattern

**Decision**: Return structured error responses (never raise exceptions to MCP layer)

**Pattern**:
```python
@mcp.tool()
async def delete_task(user_id: str, task_id: str) -> dict:
    try:
        # Validate UUID format
        user_uuid = UUID(user_id)
        task_uuid = UUID(task_id)
    except ValueError:
        return {"success": False, "error": "Invalid ID format"}

    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_uuid)
        if not task or str(task.user_id) != user_id:
            return {"success": False, "error": "Task not found or access denied"}
        # ...
```

**Rationale**:
- Friendly error messages for AI agent interpretation
- No stack traces exposed
- Consistent response structure (success/error + data)

### 6. OpenAI Agents SDK Integration

**Decision**: Agent connects to MCP server via `MCPServerStreamableHttp`

**Pattern** (for Spec 2):
```python
from agents import Agent
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="Todo MCP Server",
    params={"url": "http://localhost:8001/mcp"}
) as server:
    agent = Agent(
        name="Todo Assistant",
        mcp_servers=[server]
    )
```

**Rationale**:
- Standard MCP client pattern from OpenAI Agents SDK
- Agent auto-discovers tools via `list_tools()`
- Tools invoked automatically based on user intent

### 7. Tool Response Schema

**Decision**: Consistent JSON structure for all tool responses

**Schema**:
```json
{
  "success": true,
  "data": {
    "task_id": "uuid",
    "title": "string",
    "description": "string|null",
    "status": "pending|completed",
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
}
```

Or for errors:
```json
{
  "success": false,
  "error": "User-friendly error message"
}
```

**Rationale**:
- Predictable structure for AI agent parsing
- `success` boolean simplifies agent decision logic
- `data` contains the actual payload
- `error` provides human-readable message

## Sources

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python SDK Documentation](https://modelcontextprotocol.github.io/python-sdk/)
- [OpenAI Agents SDK - MCP Integration](https://openai.github.io/openai-agents-python/mcp/)
- [MCP on PyPI](https://pypi.org/project/mcp/)
