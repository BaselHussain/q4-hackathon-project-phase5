<!--
  Sync Impact Report
  ==================
  Version change: 1.0.0 → 2.0.0

  Modified principles:
    - I. Spec-Driven Development → I. Spec-Driven Development (unchanged)
    - II. Full-Stack Modern Architecture → II. AI-First Stateless Architecture (major revision)
    - III. Secure Authentication & Authorization → III. Secure Authentication & Authorization (unchanged, leverages Phase 2)
    - IV. Persistent Data Storage → IV. Persistent Data & Conversation State (expanded)
    - V. Test-First Development → (removed - not required for Phase 3 hackathon)
    - VI. REST API Security → VI. Stateless Tool Design (replaced with MCP focus)
    - VII. Responsive & Accessible UI → VII. Conversational UI Experience (refocused)

  Added sections:
    - V. OpenAI Agents SDK Integration (NEW)
    - VIII. MCP Server Protocol (NEW)
    - Phase 3 Technology Stack Requirements (NEW)
    - Three-Spec Development Approach (NEW)
    - Deployment Requirements (NEW)

  Removed sections:
    - Test-First Development (not required for hackathon scope)
    - Generic Testing Requirements (consolidated)

  Templates requiring updates:
    - .specify/templates/plan-template.md: ✅ No changes needed (generic)
    - .specify/templates/spec-template.md: ✅ No changes needed (generic)
    - .specify/templates/tasks-template.md: ✅ No changes needed (generic)

  Follow-up TODOs:
    - None
-->

# Todo AI Chatbot Constitution (Phase 3)

## Core Purpose

Build a conversational AI-powered todo management interface demonstrating natural-language task management with stateless agent architecture, persistent conversation history, and production-grade AI tooling. All implementation MUST be via Claude Code only - no manual coding allowed.

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)

All development MUST follow Spec-Driven Development (SDD) methodology. Features MUST be fully specified before implementation. Specs MUST include clear acceptance criteria, error paths, and constraints. No manual coding allowed - all implementation MUST be agent-driven using Claude Code tools.

**Phase 3 requires three separate specs in this order:**
1. **MCP Server & Tools** - Stateless task tools + database interaction
2. **AI Agent & Chat Logic** - Agent setup + stateless chat endpoint
3. **Frontend Chat Interface** - ChatKit UI + API integration

Every feature MUST be traceable to a spec.

### II. AI-First Stateless Architecture

The application MUST use OpenAI Agents SDK for core AI logic and tool calling. The MCP server MUST implement stateless tools using the official MCP SDK. All tools MUST remain stateless - state stored in database only, never in tool memory. The `/api/{user_id}/chat` endpoint MUST be stateless.

**Architecture requirements:**
- OpenAI Agents SDK handles all AI reasoning and tool orchestration
- MCP server exposes stateless tools for task operations
- Agent invokes tools via MCP protocol
- Database is the single source of truth for all state

### III. Secure Authentication & Authorization

User authentication MUST use existing Phase 2 Better Auth with JWT tokens. All API endpoints MUST have JWT verification middleware. User isolation MUST be strictly enforced - each user can only access their own tasks and conversations. Conversation history MUST be private per user.

**Leverage existing Phase 2 implementation:**
- Better Auth for signup/signin
- JWT tokens for API authentication
- User isolation already implemented

### IV. Persistent Data & Conversation State

All data MUST be stored in Neon Serverless PostgreSQL. Database schema MUST include:
- Existing `users` table (from Phase 2)
- Existing `tasks` table (from Phase 1)
- New `conversations` table for chat sessions
- New `messages` table for conversation history

**Persistence requirements:**
- Conversation history MUST persist after server restart
- Message history MUST be retrievable for context
- All state changes MUST be reflected in database

### V. OpenAI Agents SDK Integration

The AI agent MUST be implemented using OpenAI Agents SDK. The agent MUST understand natural language for all 5 todo features:
1. **Add** - Create new tasks from natural language
2. **List** - Show tasks with filtering (all, completed, pending)
3. **Complete** - Mark tasks as done
4. **Delete** - Remove tasks
5. **Update** - Modify task details

**Agent requirements:**
- Agent MUST use tools via MCP protocol
- Agent MUST maintain conversation context from database
- Errors MUST be handled gracefully with friendly responses
- Agent MUST NOT store state in memory between requests

### VI. Stateless Tool Design (MCP Protocol)

All task management tools MUST be implemented as stateless MCP tools using the official MCP SDK. Tools MUST NOT maintain any internal state - all state MUST be read from and written to the database.

**MCP tool requirements:**
- Each tool performs a single operation
- Tools read current state from database
- Tools write changes to database
- Tools return results to agent
- No caching or state retention in tools

### VII. Conversational UI Experience

Frontend MUST use ChatKit for the chat interface. UI MUST provide intuitive conversational experience for task management. The interface MUST display conversation history and task operation results clearly.

**UI requirements:**
- ChatKit integration for chat interface
- Real-time message display
- Clear feedback for task operations
- Responsive design for all devices
- Integration with existing Phase 2 authentication UI

### VIII. MCP Server Protocol

The MCP server MUST follow the official Model Context Protocol specification. Server MUST expose tools for task CRUD operations. Server MUST handle tool calls from the OpenAI agent.

**Protocol requirements:**
- Implement official MCP SDK server
- Expose tools: add_task, list_tasks, complete_task, delete_task, update_task
- Each tool MUST interact with database directly
- Tools MUST return structured responses for agent interpretation

## Technology Stack Requirements

### Phase 3 Stack (Additions to Phase 1 & 2)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI Agent** | OpenAI Agents SDK | Core AI logic and tool calling |
| **MCP Server** | Official MCP SDK (Python) | Stateless tool server |
| **Chat UI** | ChatKit | Frontend chat interface |
| **Database** | Neon PostgreSQL | Conversations + messages tables |
| **Backend** | FastAPI (existing) | Chat endpoint + MCP integration |
| **Frontend** | Next.js (existing) | ChatKit integration |
| **Auth** | Better Auth + JWT (existing) | User authentication |

### New Dependencies (Phase 3)

**Backend:**
- `openai-agents` - OpenAI Agents SDK
- `mcp` - Official MCP SDK for Python
- Additional database models for conversations/messages

**Frontend:**
- `@chatkit/react` or equivalent ChatKit package
- Chat state management integration

### Existing Stack (Preserved from Phase 1 & 2)

- Python 3.11+ with FastAPI 0.109+
- SQLModel 0.0.14+ for ORM
- asyncpg 0.29+ for async PostgreSQL
- Next.js 16+ with App Router
- Better Auth for authentication
- Neon Serverless PostgreSQL

## Development Workflow

### Code Quality Standards

- All code MUST follow consistent style guidelines
- Meaningful commit messages following conventional commits
- All implementation via Claude Code only
- No direct pushes to main branch

### Documentation Standards

- README.md MUST contain complete setup instructions (frontend + backend + MCP)
- CLAUDE.md MUST have complete agentic workflow
- All environment variables MUST be documented in `.env.example`
- API documentation MUST be up-to-date

### Three-Spec Development Approach

Phase 3 development MUST follow this spec order:

1. **Spec 1: MCP Server & Tools**
   - Define stateless tool interfaces
   - Implement database interaction layer
   - Test tools in isolation

2. **Spec 2: AI Agent & Chat Logic**
   - Configure OpenAI Agents SDK
   - Implement `/api/{user_id}/chat` endpoint
   - Connect agent to MCP tools
   - Implement conversation persistence

3. **Spec 3: Frontend Chat Interface**
   - Integrate ChatKit component
   - Connect to chat API endpoint
   - Display conversation history
   - Handle authentication flow

## Deployment Requirements

### Local Development

- MUST be runnable locally with exact commands
- All dependencies installable via UV (Python) and npm/pnpm (Node.js)
- `.env.example` MUST contain all required variables

### Production Deployment

- Backend deployable on Render
- Frontend deployable on Vercel
- Database on Neon (existing)
- Environment variables configured per platform

## Governance

The constitution supersedes all other development practices. Amendments require:
- Documentation of the change and rationale
- Version update following semantic versioning
- Migration plan for existing code if needed

All development MUST verify compliance with this constitution. Use CLAUDE.md for runtime development guidance and tool usage.

**Version**: 2.0.0 | **Ratified**: 2026-01-19 | **Last Amended**: 2026-02-03
