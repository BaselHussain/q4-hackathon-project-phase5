---
id: 0004
title: Advanced Todo Features Clarifications
stage: spec
date: 2026-02-09
surface: agent
model: claude-sonnet-4-5
feature: 007-advanced-todo-features
branch: 007-advanced-todo-features
user: system
command: /sp.clarify
labels: ["clarifications", "spec", "ambiguity-resolution", "timezone", "tags", "sorting", "recurring-tasks"]
links:
  spec: specs/007-advanced-todo-features/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-advanced-todo-features/spec.md
tests:
  - none
---

## Prompt

/sp.clarify

(No additional user input provided)

## Response snapshot

Completed clarification session with 5 questions asked and answered. All recommendations accepted by user. Spec updated with clarifications and functional requirements modified to reflect decisions.

**Questions Asked & Answered**:
1. Timezone handling for due dates → Store UTC, display in user's timezone
2. Sort behavior for null due dates → Nulls last (bottom of list)
3. Tag case sensitivity and deduplication → Case-insensitive, normalize to lowercase
4. Tag validation limits → Max 10 tags per task, max 50 chars per tag
5. Recurring task metadata storage → Simple enum only, defer metadata to Spec 8

**Sections Updated**:
- Added "Clarifications" section with Session 2026-02-09
- Updated FR-012 (Due Dates) - added FR for UTC storage
- Updated FR-029 (Sort) - specified nulls last behavior
- Updated FR-013-019 (Tags) - normalized storage, validation limits
- Updated FR-034-041 (Recurring) - clarified simple enum approach, deferred metadata
- Updated User Story 3 acceptance scenario 6 - aligned with simple enum
- Removed ambiguous "assume UTC or user's local time" from Out of Scope

## Outcome

- ✅ Impact: Resolved 5 critical ambiguities that would have caused implementation inconsistencies. Timezone handling now follows industry standard (UTC storage). Sort behavior clarified for null handling. Tag normalization prevents duplicate tags with different cases. Tag limits prevent abuse. Recurring task scope simplified to align with incremental delivery strategy.
- 🧪 Tests: No test changes (specification phase). Clarifications will inform test scenarios during implementation.
- 📁 Files: Updated specs/007-advanced-todo-features/spec.md with clarifications section and 8 functional requirement updates
- 🔁 Next prompts: Spec is now unambiguous and ready for `/sp.plan` (already exists) or `/sp.implement` to begin implementation
- 🧠 Reflection: All 5 clarifications addressed high-impact areas (data consistency, user experience, validation, scope management). User accepted all recommendations, indicating alignment with best practices. Timezone clarification prevents future bugs with overdue detection. Tag normalization prevents user confusion. Recurring task simplification keeps Spec 7 focused and defers complexity to Spec 8 where it belongs.

## Evaluation notes (flywheel)

- Failure modes observed: None - all clarifications successfully integrated into spec
- Graders run and results (PASS/FAIL): PASS - All 5 questions answered, spec updated incrementally after each answer, no contradictions remain, markdown structure valid
- Prompt variant (if applicable): Standard /sp.clarify workflow with sequential questioning
- Next experiment (smallest change to try): Proceed with implementation using existing plan.md and tasks.md, or re-run /sp.plan if clarifications significantly changed approach (not needed in this case)
