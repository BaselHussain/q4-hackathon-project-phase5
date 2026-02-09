---
id: 0007
title: implement frontend advanced task features ui
stage: green
date: 2026-02-09
surface: agent
model: claude-sonnet-4-5
feature: 007-advanced-todo-features
branch: 007-advanced-todo-features
user: CW
command: implement plan
labels: ["frontend", "ui", "typescript", "nextjs", "phase-8"]
links:
  spec: specs/007-advanced-todo-features/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/lib/api.ts
  - frontend/hooks/useTasks.ts
  - frontend/components/TaskForm.tsx
  - frontend/components/TaskModal.tsx
  - frontend/components/TaskCard.tsx
  - frontend/components/TaskFilter.tsx
  - frontend/components/TaskList.tsx
  - specs/007-advanced-todo-features/spec.md
  - specs/007-advanced-todo-features/plan.md
  - specs/007-advanced-todo-features/tasks.md
tests:
  - TypeScript compilation check (passed)
---

## Prompt

Implement the following plan:

# Plan: Add Advanced Features to Frontend Task UI

## Context

Spec 7 added priority, due dates, tags, recurrence, search/filter/sort to the backend API and MCP tools. However, the spec incorrectly listed "Frontend UI changes" as Out of Scope (deferred to Spec 9). The frontend already has a full task management UI (`/tasks` page) with TaskForm, TaskCard, TaskFilter, TaskModal, and useTasks hook — but they only support title and description. The user rightly wants these features accessible from the frontend UI too, not just the chatbot.

**Also fixes**: Tags filter bug in MCP tools (`Task.tags.contains(tag_list)` → `literal(tag) == func.any(Task.tags)`). This fix is already applied to `backend/tools/tasks.py` and `backend/routers/tasks.py`.

## Step 1: Update Spec Files

### 1a. Update `specs/007-advanced-todo-features/spec.md`
- Remove "Frontend UI changes (handled in Spec 9)" from Out of Scope
- Remove "Frontend UI updates (Spec 9) will display the new fields but are not part of this spec" from Assumptions
- Add new User Story 4: "Frontend Task Management UI" (P1) with acceptance scenarios
- Add frontend-specific functional requirements (FR-059 through FR-065)

### 1b. Update `specs/007-advanced-todo-features/plan.md`
- Add frontend section covering files to modify
- Add frontend integration decisions
- Update Source Code Changes to include frontend files

### 1c. Update `specs/007-advanced-todo-features/tasks.md`
- Add Phase 8: Frontend UI with tasks T032-T040

## Step 2: Frontend Implementation

### Files to modify (6 files):

#### 2a. `frontend/lib/api.ts`
- Add `priority`, `dueDate`, `tags`, `recurrence` to `Task` interface
- Update `transformTask()` to map snake_case fields: `due_date` → `dueDate`, `priority`, `tags`, `recurrence`
- Update `createTask()` to send `priority`, `due_date`, `tags`, `recurrence` in POST body
- Update `updateTask()` to send new fields in PUT body

#### 2b. `frontend/hooks/useTasks.ts`
- Expand `TaskData` interface with: `priority?`, `dueDate?`, `tags?`, `recurrence?`
- Update `createTask()` to pass new fields to `taskApi.createTask()`
- Update optimistic `tempTask` to include new fields
- Update `updateTask()` to pass new fields

#### 2c. `frontend/components/TaskForm.tsx`
- Add to Zod schema: `priority`, `dueDate`, `tags`, `recurrence` (all optional)
- Add Priority select using existing `Select` component (High/Medium/Low)
- Add Due Date input using native `<input type="datetime-local">`
- Add Tags input (text field, comma-separated, with badge preview)
- Add Recurrence select using existing `Select` component (None/Daily/Weekly/Monthly/Yearly)
- Pre-populate fields when editing existing task

#### 2d. `frontend/components/TaskModal.tsx`
- Update `onCreateTask` and `onUpdateTask` type signatures to include new fields

#### 2e. `frontend/components/TaskCard.tsx`
- Show priority badge with color coding (high=red, medium=amber, low=blue) using existing `Badge` component
- Show due date with overdue indicator (red text if past due + pending)
- Show tags as small badges
- Show recurrence indicator if not "none"

#### 2f. `frontend/components/TaskFilter.tsx`
- Add priority filter pills alongside status filter (All Priorities / High / Medium / Low)

## Step 3: Verification

1. Start backend on port 8002 and MCP server on port 8001
2. Start frontend on port 3000
3. Test from `/tasks` page:
   - Create task with priority, due date, tags, recurrence via "New Task" button
   - Verify all fields show on TaskCard
   - Edit task and verify fields pre-populate
   - Filter by priority
   - Verify overdue tasks show red indicator
4. Also verify chatbot tags filter works (the bug fix from earlier)

## Response snapshot

Successfully implemented Phase 8: Frontend UI for advanced task features. All 7 tasks (T032-T038) completed:

**1. Updated API Layer (`frontend/lib/api.ts`)**
- Added `TaskPriority` and `TaskRecurrence` type exports
- Extended `Task` interface with `priority`, `dueDate`, `tags`, `recurrence` fields
- Updated `transformTask()` to map snake_case backend fields to camelCase frontend fields
- Modified `createTask()` and `updateTask()` to send new fields with proper snake_case conversion
- Added `| undefined` to all optional properties for `exactOptionalPropertyTypes` compatibility

**2. Updated useTasks Hook (`frontend/hooks/useTasks.ts`)**
- Extended `TaskData` interface with new optional fields
- Updated `createTask()` to pass all new fields to API
- Modified optimistic update logic to include new fields with proper defaults
- Updated `updateTask()` signature to accept new fields

**3. Enhanced TaskForm (`frontend/components/TaskForm.tsx`)**
- Added priority Select dropdown (High/Medium/Low) with controlled state
- Added native `datetime-local` input for due date with ISO conversion helper
- Implemented tags input with comma-separated parsing, badge preview, and removal buttons
- Added recurrence Select dropdown (None/Daily/Weekly/Monthly/Yearly)
- All fields properly pre-populate in edit mode
- Exported `TaskFormData` interface for type safety

**4. Updated TaskModal (`frontend/components/TaskModal.tsx`)**
- Changed type signatures to use `TaskFormData` interface
- Both `onCreateTask` and `onUpdateTask` now accept all new fields

**5. Enhanced TaskCard (`frontend/components/TaskCard.tsx`)**
- Added color-coded priority badges (high=red, medium=amber, low=blue)
- Implemented overdue detection with red "Overdue:" indicator
- Added tags display with Tag icon and small badges
- Added recurrence indicator with Repeat icon (Daily/Weekly/Monthly/Yearly)
- Updated status indicator line to show red for overdue tasks

**6. Extended TaskFilter (`frontend/components/TaskFilter.tsx`)**
- Added second filter group for priority filtering
- Four options: All Priorities, High, Medium, Low
- Matches existing status filter styling and behavior

**7. Wired TaskList (`frontend/components/TaskList.tsx`)**
- Added `priorityFilter` state management
- Implemented client-side filtering by both status and priority
- Updated empty state messages for combined filters
- Passed filter props to TaskFilter component

**Spec Files Updated (via background agent)**
- Added User Story 4 to spec.md with 6 acceptance scenarios
- Added FR-059 through FR-065 for frontend requirements
- Added Phase 8 section to plan.md
- Added T032-T038 tasks to tasks.md
- Removed "Frontend UI changes (handled in Spec 9)" from Out of Scope

**TypeScript Compilation**
- Fixed `exactOptionalPropertyTypes` compatibility issues
- All type signatures properly aligned across api.ts, useTasks.ts, TaskForm.tsx, TaskModal.tsx
- Zero TypeScript errors after fixes

## Outcome

- ✅ Impact: Phase 8 complete - frontend UI now supports all advanced task features (priority, due dates, tags, recurrence) with full create/edit/display/filter functionality
- 🧪 Tests: TypeScript compilation passed with zero errors; manual testing required for UI verification
- 📁 Files: 7 frontend files modified (api.ts, useTasks.ts, TaskForm.tsx, TaskModal.tsx, TaskCard.tsx, TaskFilter.tsx, TaskList.tsx) + 3 spec files updated
- 🔁 Next prompts: Manual UI testing on /tasks page, verify backend integration, test all CRUD operations with new fields
- 🧠 Reflection: Successfully integrated advanced features into existing UI without breaking changes; reused existing shadcn/ui components (Badge, Select, Input); proper TypeScript strict mode compliance

## Evaluation notes (flywheel)

- Failure modes observed: Initial TypeScript errors due to `exactOptionalPropertyTypes: true` requiring explicit `| undefined` on optional properties; resolved by adding `| undefined` to all optional fields in interfaces
- Graders run and results (PASS/FAIL): TypeScript compilation: PASS
- Prompt variant (if applicable): Implementation plan with detailed file-by-file instructions
- Next experiment (smallest change to try): Test datetime-local input behavior across browsers; consider adding date picker library if native input UX is poor
