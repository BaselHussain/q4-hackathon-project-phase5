---
id: 2
title: Phase 3 AI Chatbot Constitution Update
stage: constitution
date: 2026-02-03
surface: agent
model: claude-opus-4-5-20251101
feature: phase3-ai-chatbot
branch: main
user: developer
command: /sp.constitution
labels: ["constitution", "phase3", "ai-chatbot", "mcp", "openai-agents"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

Hackathon Phase 3 - Todo AI Chatbot

Project: Build a conversational AI-powered todo management interface using OpenAI Agents SDK, official MCP server with stateless tools, ChatKit frontend, and persistent conversation state in Neon PostgreSQL.

Core purpose: Demonstrate natural-language todo management with stateless agent architecture, persistent history, and production-grade AI tooling. No manual coding allowed.

Constitution Check (must PASS all for entire Phase 3):

I. Educational Clarity
- All specs, plans, and tasks clearly documented with exact commands
- README.md updated with full setup (frontend + backend + MCP)
- CLAUDE.md with complete agentic workflow

II. Engineering Accuracy
- OpenAI Agents SDK for core AI logic and tool calling
- Official MCP SDK for stateless tool server
- Stateless /api/{user_id}/chat endpoint
- Persistent conversation state (conversations + messages tables in Neon DB)
- ChatKit frontend integration
- Tools remain stateless — all state stored in DB only
- Use existing Phase 2 auth (Better Auth + JWT)

III. Practical Applicability
- Runnable locally with exact commands
- Chatbot understands natural language for all 5 todo features (add/list/complete/delete/update)
- Conversation history persists after server restart
- Errors handled gracefully with friendly responses
- Deployable on Render (backend) + Vercel (frontend)

IV. Spec-Driven Development
- Three separate specs in this order:
  1. MCP Server & Tools (stateless task tools + DB interaction)
  2. AI Agent & Chat Logic (agent setup + stateless endpoint)
  3. Frontend Chat Interface (ChatKit UI + API integration)
- Every feature traceable to spec
- All implementation via Claude Code only

V. Ethical Responsibility
- Secure auth (use Phase 2 Better Auth + JWT)
- Conversation history private per user
- No unnecessary data collection or external calls

VI. Reproducibility & Open Knowledge
- Public GitHub repository
- Reproducible with .env.example, UV, npm/pnpm
- All files version-controlled

VII. Zero Broken State
- Ma[truncated in input]

## Response snapshot

Updated constitution from v1.0.0 to v2.0.0 with major revisions for Phase 3 - Todo AI Chatbot:

**Key Changes:**
- Added Core Purpose section defining the AI chatbot project goals
- Revised Principle II from "Full-Stack Modern Architecture" to "AI-First Stateless Architecture"
- Expanded Principle IV to include conversation state persistence (conversations + messages tables)
- Added Principle V: OpenAI Agents SDK Integration with 5 natural language features
- Replaced Principle VI with "Stateless Tool Design (MCP Protocol)"
- Refocused Principle VII as "Conversational UI Experience" for ChatKit
- Added Principle VIII: MCP Server Protocol requirements
- Removed Test-First Development (not required for hackathon scope)
- Added Phase 3 Technology Stack table
- Added Three-Spec Development Approach section
- Added Deployment Requirements for Render + Vercel

**Version Bump Rationale:** MAJOR (1.0.0 → 2.0.0) because:
- Backward incompatible principle redefinitions (II, VI, VII)
- New mandatory principles added (V, VIII)
- Architectural shift to AI-first stateless design

## Outcome

- Impact: Major constitution revision establishing Phase 3 AI chatbot architecture
- Tests: N/A (constitution document)
- Files: 1 modified (.specify/memory/constitution.md)
- Next prompts: /sp.specify for MCP Server & Tools spec (Spec 1 of 3)
- Reflection: Constitution now reflects three-spec approach with clear technology stack for OpenAI Agents SDK + MCP + ChatKit integration

## Evaluation notes (flywheel)

- Failure modes observed: None - clean update
- Graders run and results (PASS/FAIL): Manual review PASS - all principles testable, no vague language
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate constitution gates during spec creation
