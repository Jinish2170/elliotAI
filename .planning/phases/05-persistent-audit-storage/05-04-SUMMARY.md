---
phase: 05-persistent-audit-storage
plan: 04
subsystem: "Dual-write migration strategy"
tags: ["persistence", "dual-write", "migration", "feature-flag"]
priority: high

# Dependency Graph
requires_provides:
  requires:
    - "05-01: SQLAlchemy models and database initialization"
    - "05-02: Database session and audit repository"
    - "05-03: ScreenshotStorage filesystem service"
  provides:
    - "05-05: In-memory to database transition"
    - "05-06: Full persistence integration verification"

tech_stack:
  added:
    - "USE_DB_PERSISTENCE feature flag"
  patterns:
    - "Dual-write pattern for gradual migration"
    - "Feature flag for instant rollback"

# Key Files
created: []
modified:
  - "veritas/config/settings.py: Added USE_DB_PERSISTENCE flag and helper"
  - "backend/routes/audit.py: Implemented database write handlers"

key_files:
  - "veritas/config/settings.py: Feature flag configuration"
  - "backend/routes/audit.py: Dual-write implementation with handlers"
  - "veritas/screenshots/storage.py: Screenshot filesystem storage"
  - "veritas/db/repositories.py: Audit repository for CRUD operations"

# Decisions Made
key_decisions:
  - "Feature flag pattern: USE_DB_PERSISTENCE defaults to 'true' for immediate activation"
  - "Dual-write approach: Write to both in-memory dict and database simultaneously"
  - "Read path upgrade: audit_status() reads database first, falls back to in-memory"
  - "Lazy repository initialization: Create AuditRepository per-request using DbSession"
  - "Screenshot events: Already correct structure in audit_runner.py, no changes needed"

# Metrics
completed_date: "2026-02-23"
duration_minutes: 7
tasks_completed: 3
---

# Phase 5 Plan 04: Dual-Write Migration Strategy Summary

Implemented dual-write migration strategy enabling gradual transition from in-memory to persistent storage using a feature flag for instant rollback. Audit routes now write to both in-memory dict and SQLite database when USE_DB_PERSISTENCE=true (default).

### Overview

The dual-write migration strategy allows immediate activation of database persistence while maintaining compatibility with existing in-memory storage. Key achievements:

1. **Feature Flag Infrastructure** - Added USE_DB_PERSISTENCE flag (defaults to true) with helper function following Phase 2 SecurityAgent pattern
2. **Database Write Handlers** - Implemented three event handlers for audit lifecycle: on_audit_started, on_audit_completed, on_audit_error
3. **Screenshot Persistence** - Integrated ScreenshotStorage to save screenshots to filesystem and create database references
4. **Read Path Upgrade** - Modified audit_status endpoint to read from database first, falling back to in-memory dict

### Implementation Details

#### 1. Feature Flag (veritas/config/settings.py)

Added USE_DB_PERSISTENCE setting following the SecurityAgent pattern for consistency:

```python
# Database Persistence (Plan 04-04 - Dual-write migration)
USE_DB_PERSISTENCE: bool = os.getenv("USE_DB_PERSISTENCE", "true").lower() == "true"

def should_use_db_persistence() -> bool:
    """Determine if database persistence should be used."""
    return USE_DB_PERSISTENCE
```

- Default value: `true` (enabled by default for immediate activation)
- Environment variable: `USE_DB_PERSISTENCE`
- Helper function: `should_use_db_persistence()` mirrors SecurityAgent pattern

#### 2. Database Write Handlers (backend/routes/audit.py)

Implemented three asynchronous event handlers for audit lifecycle management:

**on_audit_started(audit_id, data, db):**
- Creates Audit record with RUNNING status
- Stores URL, tier, verdict_mode
- Checks USE_DB_PERSISTENCE flag before writing

**on_audit_completed(audit_id, result, db):**
- Updates Audit with final trust score, risk level, narrative
- Stores signal_scores, site_type, security_results
- Populates AuditFinding records from dark_pattern_summary
- Updates status to COMPLETED, sets completed_at timestamp

**on_audit_error(audit_id, error, db):**
- Updates Audit status to ERROR
- Stores error_message for debugging
- Creates audit record if not found (handles edge cases)

**_handle_screenshot_event(audit_id, event, db):**
- Saves screenshots to filesystem via ScreenshotStorage.save()
- Creates AuditScreenshot records with file_path, label, index_num, file_size_bytes
- Extracts base64_data from event["data"]
- Handles errors gracefully with logging

#### 3. Read Path Upgrade

Modified audit_status endpoint to read from database first:

```python
if should_use_db_persistence():
    audit = await repo.get_by_id(audit_id)
    if audit:
        return formatted_database_record

# Fallback to in-memory store
info = _audits.get(audit_id)
```

The dual-read approach ensures data availability during transition period.

#### 4. Screenshot Event Integration

Modified stream_audit's send_event wrapper to detect screenshot events:

```python
elif event_type == "screenshot":
    # Handle screenshot persistence (Plan 05-04)
    await _handle_screenshot_event(audit_id, data, db)
```

Screenshot events from audit_runner.py already include correct structure:
- `type`: "screenshot"
- `data`: base64-encoded image data
- `index`: sequential screenshot number
- `label`: human-readable description

No changes to audit_runner.py were required.

### Rollback Procedure

To rollback to in-memory only mode:

1. Set environment variable:
   ```bash
   export USE_DB_PERSISTENCE=false
   ```

2. Restart backend server

3. Database writes stop immediately, in-memory operations continue uninterrupted

### Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| veritas/config/settings.py | +31 lines | Added USE_DB_PERSISTENCE flag and helper |
| backend/routes/audit.py | +213 insertions, -12 deletions | Implemented database write handlers and read path upgrade |

### Deviations from Plan

**None** - Plan executed exactly as written. All three tasks completed without deviations.

### Success Criteria Verification

- [x] USE_DB_PERSISTENCE flag defaults to true and can be toggled via environment variable
- [x] Audit routes write to both in-memory dict and database when flag is true
- [x] Screenshots saved to filesystem and references stored in AuditScreenshot table
- [x] /audit/{audit_id}/status reads from database first, falls back to in-memory
- [x] Setting USE_DB_PERSISTENCE=false immediately reverts to in-memory only
- [x] All handlers implemented: on_audit_started, on_audit_completed, on_audit_error, _handle_screenshot_event

### Integration Notes

1. **Dual-write overhead**: Minimal - database writes are asynchronous (await) but don't block WebSocket streaming
2. **Screenshot storage**: Files organized in `data/screenshots/{audit_id}/` with timestamp-based filenames
3. **Finding aggregation**: AuditFinding records populated from result["dark_pattern_summary"]["findings"]
4. **Error handling**: All handlers include try-except with logging, failures don't break WebSocket streaming

### Next Steps

Plan 05-05 will transition the in-memory dict to database-primary storage with fallback, completing the migration path established by this plan.
