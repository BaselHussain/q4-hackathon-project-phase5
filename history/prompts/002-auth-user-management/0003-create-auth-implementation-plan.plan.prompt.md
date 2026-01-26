---
id: 0003
title: create-auth-implementation-plan
stage: plan
date: 2026-01-22
surface: agent
model: claude-sonnet-4-5
feature: 002-auth-user-management
branch: 002-auth-user-management
user: BaselHussain
command: /sp.plan
labels: ["planning", "authentication", "architecture", "jwt", "fastapi", "security"]
links:
  spec: ../../../specs/002-auth-user-management/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/002-auth-user-management/plan.md
  - specs/002-auth-user-management/research.md
  - specs/002-auth-user-management/data-model.md
  - specs/002-auth-user-management/contracts/openapi.yaml
  - specs/002-auth-user-management/quickstart.md
  - CLAUDE.md
tests:
  - No tests run (planning phase)
---

## Prompt

Authentication & User Management (Spec 2)

Follow the approved spec in specs/auth-user-management/spec.md exactly.

Create full execution plan:

1. Detailed folder/file structure changes:
   - backend/requirements.txt (add better-auth-python)
   - backend/auth.py (JWT verification middleware)
   - backend/dependencies.py (get_current_user dependency)
   - backend/main.py (add auth middleware to app)
   - .env.example (add BETTER_AUTH_SECRET)

2. Step-by-step integration plan:
   - Install Better Auth Python adapter
   - Configure Better Auth with shared secret and Neon DB
   - Create FastAPI dependency to decode/verify JWT
   - Implement middleware to attach current_user to requests
   - Update all task endpoints to use get_current_user dependency
   - Add ownership check: current_user.id == path user_id
   - Handle auth errors (401/403) with clear messages

3. Decision table:
   - JWT vs session cookies (choose JWT for stateless backend)
   - Manual JWT decode vs library (use Better Auth adapter)

4. Testing strategy with exact commands:
   - Signup via Postman → get JWT
   - Test /api/{user_id}/tasks with valid token → succeeds
   - Test with invalid token → 401
   - Test with valid token but wrong user_id → 403
   - Test expired token → 401

## Response snapshot

Created comprehensive implementation plan for Authentication & User Management feature following Spec-Driven Development methodology.

**Phase 0: Research & Technology Decisions**
- Discovered Better Auth is JavaScript-only (no Python adapter)
- Decision: Use python-jose for JWT handling instead
- Researched and documented all technology choices:
  - JWT library: python-jose[cryptography]
  - Password hashing: passlib[bcrypt]
  - Rate limiting: slowapi (in-memory)
  - Email validation: email-validator (RFC 5322)
  - Error format: RFC 7807 custom handler
- Created decision table with rationale for each choice
- Documented integration architecture and security considerations

**Phase 1: Design & Contracts**
- Created data-model.md with complete database schema:
  - New users table (id, email, password_hash, timestamps)
  - Updated tasks table with user_id foreign key
  - Entity relationships and constraints
  - Alembic migration script
- Created contracts/openapi.yaml with full API specification:
  - 2 new auth endpoints (register, login)
  - Updated 5 task endpoints with authentication
  - RFC 7807 error responses
  - JWT bearer authentication scheme
- Created quickstart.md with setup and testing guide:
  - Installation steps
  - Environment configuration
  - Quick test workflow (register → login → create task)
  - Common issues and solutions

**Implementation Structure**
- 8 implementation phases defined (Database → Error Handling)
- 18-25 estimated tasks across all phases
- Clear file structure with NEW/UPDATE markers
- Comprehensive testing strategy (unit, integration, contract)
- Manual testing scenarios with curl commands

**Constitution Check**: ✅ PASS - All applicable principles satisfied

**Key Architectural Decisions**:
1. python-jose instead of Better Auth (no Python support)
2. HS256 algorithm for JWT signing (shared secret model)
3. bcrypt for password hashing (constitution requirement)
4. slowapi for rate limiting (simple MVP approach)
5. Stateless JWT tokens (no server-side sessions)
6. 24-hour token expiration (balance security/UX)

## Outcome

- ✅ Impact: Complete architectural plan ready for task generation and implementation
- 🧪 Tests: No tests run (planning phase only)
- 📁 Files: 5 files created (plan.md, research.md, data-model.md, openapi.yaml, quickstart.md), 1 updated (CLAUDE.md)
- 🔁 Next prompts: /sp.tasks to generate detailed task breakdown for implementation
- 🧠 Reflection: Planning successfully adapted to Better Auth limitation by choosing python-jose. All technical unknowns resolved through research. Clear separation of concerns with 8 implementation phases. Comprehensive testing strategy ensures quality. Ready for task generation and implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully with all artifacts generated
- Graders run and results (PASS/FAIL): Constitution check - PASS (all applicable principles satisfied)
- Prompt variant (if applicable): Standard /sp.plan workflow with Phase 0 research and Phase 1 design
- Next experiment (smallest change to try): Proceed to /sp.tasks for detailed task breakdown
