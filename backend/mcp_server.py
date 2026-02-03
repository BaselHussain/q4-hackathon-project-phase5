"""
MCP Server for Todo Task Management.

Exposes 5 stateless tools: add_task, list_tasks, complete_task, delete_task, update_task
All tools interact with Neon PostgreSQL database.

Usage:
    python mcp_server.py

The server runs on port 8001 (separate from FastAPI on 8000).
Endpoint: http://localhost:8001/mcp
"""
import os
from dotenv import load_dotenv

# Load environment variables before importing local modules
load_dotenv()

from mcp.server.fastmcp import FastMCP
from tools import register_tools

# Initialize MCP server with JSON response format
# Configure to run on port 8001 to avoid conflict with FastAPI on 8000
mcp = FastMCP(
    "Todo MCP Server",
    json_response=True,
    port=8001
)

# Register all task management tools
register_tools(mcp)

if __name__ == "__main__":
    # Run using streamable HTTP transport
    print("Starting MCP Server on http://localhost:8001/mcp")
    mcp.run(transport="streamable-http")
