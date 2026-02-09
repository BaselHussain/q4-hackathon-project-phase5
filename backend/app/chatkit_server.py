"""
ChatKit Server Implementation
Integrates with existing todo agent and MCP server for task management
"""
import os
import asyncio
from typing import Any, AsyncIterator, Dict
from datetime import datetime
import logging

from chatkit.server import ChatKitServer
from chatkit.types import ThreadMetadata, UserMessageItem, AssistantMessageItem
from chatkit.agents import stream_agent_response, AgentContext
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")

AGENT_INSTRUCTIONS = """You are a helpful Todo Assistant that helps users manage their tasks through natural language.

CRITICAL: The current user's ID is: {user_id}
You MUST pass this user_id in EVERY tool call. Never omit it.

Your capabilities:
- Add new tasks with optional priority, due date, tags, and recurrence
- List tasks with filtering (status, priority, tags, overdue), sorting, and search
- Mark tasks as completed
- Delete tasks
- Update task titles, descriptions, priorities, due dates, tags, and recurrence

Guidelines:
1. Always confirm actions you take (e.g., "I've added 'Buy groceries' to your tasks")
2. When listing tasks, format them clearly including priority, due date, tags, and recurrence
3. If a user's request is ambiguous, ask for clarification
4. Be concise but friendly in your responses
5. If an operation fails, explain what went wrong in user-friendly terms
6. You can handle multiple operations in a single message
7. Priority: Extract priority from user input (e.g., "high priority", "urgent" = high, "low priority" = low). Default to medium.
8. Due dates: Convert natural language to ISO 8601 format (e.g., "by Friday" -> "2026-02-14T23:59:00Z"). Pass as due_date parameter.
9. Tags: Extract hashtags or categories (e.g., "#work #urgent" -> tags="work,urgent"). Pass as comma-separated string.
10. Recurrence: Detect patterns like "daily", "every week", "monthly" -> recurrence="daily"/"weekly"/"monthly"/"yearly".
11. Search: When users say "find tasks about X" or "search for X", use the search parameter.
12. Filter: When users say "show high priority" or "show overdue", use filter parameters.
13. Sort: When users say "sort by priority" or "sort by due date", use sort parameter.
"""


class AppChatKitServer(ChatKitServer):
    """
    ChatKit server that creates an Agent with MCP tools and streams responses
    """

    def __init__(self, store):
        super().__init__(store)

    async def respond(
        self,
        thread: ThreadMetadata,
        input: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator:
        """Respond to a chat request by creating an Agent and streaming its response"""

        # Extract user_id from JWT context (set by endpoint)
        user_id = context.get("user_id", "anonymous")
        logger.info(f"ChatKit respond() - user_id from context: {user_id}")

        # Prepare input for the agent
        if input:
            user_input_text = self._extract_text(input)
        else:
            user_input_text = ""

        logger.info(f"ChatKit respond() - user input: {user_input_text}")

        # Track ID mappings to ensure unique IDs (fix for Gemini ID collision)
        id_mapping: Dict[str, str] = {}
        assistant_message_text = ""

        try:
            # Create MCP connection and Agent inline so Runner.run_streamed gets an Agent
            async with MCPServerStreamableHttp(
                name="Todo MCP Server",
                params={"url": MCP_SERVER_URL},
                cache_tools_list=True,
                client_session_timeout_seconds=30,
            ) as server:
                logger.info(f"Connected to MCP server at {MCP_SERVER_URL}")

                agent = Agent(
                    name="Todo Assistant",
                    instructions=AGENT_INSTRUCTIONS.format(user_id=user_id),
                    mcp_servers=[server],
                    model="gpt-4o-mini",
                )

                logger.info(f"Agent created with user_id: {user_id}")
                logger.info(f"Agent instructions include: 'The current user's ID is: {user_id}'")

                # Run streamed with the Agent object (not a RunResult)
                result = Runner.run_streamed(agent, input=user_input_text)

                # Create AgentContext with required parameters
                agent_context = AgentContext(
                    thread=thread,
                    store=self.store,
                    request_context=context
                )

                # Stream the agent response with ID mapping fix
                async for event in stream_agent_response(agent_context, result):
                    if hasattr(event, 'type') and event.type == "thread.item.added":
                        if hasattr(event, 'item') and isinstance(event.item, AssistantMessageItem):
                            old_id = event.item.id
                            if old_id not in id_mapping:
                                new_id = self.store.generate_item_id("message", thread, context)
                                id_mapping[old_id] = new_id
                            event.item.id = id_mapping[old_id]
                    elif hasattr(event, 'type') and event.type == "thread.item.done":
                        if hasattr(event, 'item') and isinstance(event.item, AssistantMessageItem):
                            if event.item.id in id_mapping:
                                event.item.id = id_mapping[event.item.id]
                            assistant_message_text = self._extract_text(event.item)
                    elif hasattr(event, 'type') and event.type == "thread.item.updated":
                        if hasattr(event, 'item_id') and event.item_id in id_mapping:
                            event.item_id = id_mapping[event.item_id]

                    yield event

        except Exception as e:
            print(f"Error in ChatKit respond: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _extract_text(self, item) -> str:
        """Extract text from message content parts"""
        text = ""
        if hasattr(item, 'content') and item.content:
            for part in item.content:
                if hasattr(part, 'text'):
                    text += part.text
        return text
