---
phase: 05-persistent-audit-storage
plan: 02
subsystem: Database Persistence
tags: [repository, dependency-injection, sqlalchemy]
depends_on: []
provides: [05-03, 05-04]
affects: [backend/routes/audit.py]
tech-stack:
  added: []
  patterns:
    - Repository pattern with AsyncSession
    - FastAPI dependency injection
key-files:
  created:
    - path: veritas/db/repositories.py
      description: AuditRepository class with CRUD operations
  modified:
    - path: backend/routes/audit.py
      description: Added DbSession dependency injection and event handler skeletons
decisions: []
metrics:
  duration: 6 minutes
  completed: 2026-02-23
  tasks: 2
  files: 2
---

# Phase 5, Plan 02: Database Session and Audit Repository Summary

**One-liner:** Repository pattern implementation for audit CRUD operations with AsyncSession and FastAPI dependency injection.

## Objective

Create repository layer for database operations and integrate FastAPI dependency injection for AsyncSession. Encapsulate all database CRUD operations in AuditRepository class, providing a clean interface for audit persistence.

## Tasks Completed

### Task 1: Create AuditRepository with CRUD Operations

**Status:** Complete
**Commit:** a2c51ac

Created `veritas/db/repositories.py` with AuditRepository class implementing 6 methods:

- **get_by_id(audit_id)** - Fetch audit by ID with eager loading of findings and screenshots via selectinload
- **create(audit)** - Save audit record with cascade to related objects (findings, screenshots, events)
- **update(audit)** - Update existing audit record with automatic change tracking
- **update_status(audit_id, status, error_message)** - Efficient status-only update without loading full object
- **list_recent(limit, offset, status_filter)** - Paginated audit listing with optional status filtering
- **get_by_url(url, limit)** - Fetch historical audits for a specific URL (for comparison)

All methods use AsyncSession for async database operations, following SQLAlchemy 2.0 async patterns.

### Task 2: Update Audit Routes with DbSession Dependency Injection

**Status:** Complete
**Commit:** ca24053

Updated `backend/routes/audit.py` to add database session support:

- Added imports: `Annotated`, `Depends`, `AsyncSession`, `get_db`
- Created `DbSession` type alias: `Annotated[AsyncSession, Depends(get_db)]`
- Updated all three route functions with `db: DbSession` parameter:
  - `start_audit()`
  - `stream_audit()` (WebSocket)
  - `audit_status()`
- Added database event handler skeletons (implementation deferred to Plan 05-04):
  - `on_audit_started()` - called when audit transitions to running status
  - `on_audit_completed()` - called when audit completes successfully
  - `on_audit_error()` - called when audit fails
- Updated `stream_audit` to call event handlers at appropriate times in the try/except/finally flow

**Important:** Actual database writes are NOT implemented in this plan - they are deferred to Plan 05-04. Only dependency injection and skeleton handlers are added.

## Deviations from Plan

None - plan executed exactly as written.

## Verification

All verification criteria passed:

1. **Repository methods verified:**
   - `AuditRepository.get_by_id` - EXISTS
   - `AuditRepository.create` - EXISTS
   - `AuditRepository.update` - EXISTS
   - `AuditRepository.update_status` - EXISTS
   - `AuditRepository.list_recent` - EXISTS
   - `AuditRepository.get_by_url` - EXISTS

2. **Imports verified:** Database imports (`get_db`, `AsyncSession`) work correctly

3. **Route signatures verified:** All three route functions have `db: DbSession` parameter:
   - `async def start_audit(req: AuditStartRequest, db: DbSession):`
   - `async def stream_audit(ws: WebSocket, audit_id: str, db: DbSession):`
   - `async def audit_status(audit_id: str, db: DbSession):`

4. **Event handlers verified:** All three event handlers exist and are called:
   - `on_audit_started()` called after setting status to "running"
   - `on_audit_completed()` called when audit completes successfully
   - `on_audit_error()` called when audit fails

## Success Criteria Met

- [x] AuditRepository class with 6 methods (get_by_id, create, update, update_status, list_recent, get_by_url)
- [x] All three audit route functions have db: DbSession parameter
- [x] Event handler skeletons exist and are called in stream_audit
- [x] No actual database writes yet (deferred to Plan 05-04)

## Next Steps

Plan 05-03 - Create ScreenshotStorage filesystem service
- Screenshot metadata management on filesystem
- File operations with path traversal protection

## Technical Notes

### AsyncSession Best Practices

The repository uses AsyncSession with `expire_on_commit=False` to allow accessing relationships after commit. This pattern is recommended by FastAPI SQLAlchemy tutorial.

### selectinload for Eager Loading

The `get_by_id()` method uses `selectinload` to eagerly load findings and screenshots relationships, preventing N+1 query problems when accessing related data.

### Status-Only Updates

The `update_status()` method demonstrates an efficient pattern for updating only status without loading the full audit object, reducing database roundtrips.

### Event Handler Flow

The event handlers follow this flow in `stream_audit`:
1. `on_audit_started()` called after status set to "running"
2. `on_audit_completed()` called when `audit_info["result"]` exists
3. `on_audit_error()` called in exception handler with error message

This ensures database events fire at precise moments in the audit lifecycle.
