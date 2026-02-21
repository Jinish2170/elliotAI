---
phase: 02-agent-architecture-refactor
plan: 03
subsystem: [agent-architecture, feature-flags, security]
tags: [feature-flags, rollout, hashing, agent-migration, auto-fallback]

# Dependency graph
requires:
  - phase: 02-agent-architecture-refactor
    provides: [SecurityAgent class, module auto-discovery, SecurityResult aggregation]
provides:
  - Feature flag routing between SecurityAgent and security_node function
  - Consistent hash-based rollout (0.0-1.0) for gradual production deployment
  - Auto-fallback mechanism from SecurityAgent to security_node function
  - SecurityMode progress events for monitoring mode selection
  - Mode tracking in AuditState (agent/function/function_fallback)
affects: [04-unit-tests, 05-integration-tests, 03-langgraph-refactor]

# Tech tracking
tech-stack:
  added: [hashlib, consistent-hashing, feature-flags]
  patterns: [strangler-fig-migration, gradual-rollout, auto-fallback]

key-files:
  created: []
  modified:
    - veritas/config/settings.py - Rollout helpers (get_security_agent_rollout, should_use_security_agent)
    - veritas/core/ipc.py - SecurityModeStarted and SecurityModeCompleted events
    - veritas/agents/security_agent.py - Mode selection methods (is_enabled, get_env_mode, initialize)
    - veritas/core/orchestrator.py - security_node_with_agent wrapper routing logic

key-decisions:
  - "Consistent hash-based routing (MD5 from URL) ensures same URL always gets same mode"
  - "Auto-fallback to security_node function prevents audit failures during migration"
  - "Default SecurityAgent mode (USE_SECURITY_AGENT=true) for agent-first approach"
  - "Environment-driven configuration enables instant rollback without code changes"

patterns-established:
  - "Strangler Fig pattern: new SecurityAgent class wraps old security_node function"
  - "Feature flag routing wrapper: security_node_with_agent routes based on flags"
  - "Gradual rollout via percentage: SECURITY_AGENT_ROLLOUT 0.0-1.0 controls traffic"
  - "Auto-fallback on exception:SecurityAgent errors fall back to function mode"

requirements-completed: [CORE-01-4]

# Metrics
duration: 11min
completed: 2026-02-21
---

# Phase 2 Plan 3: Feature Flag Infrastructure and Migration Path Summary

**Feature flag routing with consistent hash-based rollout, auto-fallback from SecurityAgent to security_node, and SecurityMode progress events for gradual production deployment**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-21T05:40:12Z
- **Completed:** 2026-02-21T05:51:08Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- Implemented `security_node_with_agent()` wrapper that routes between SecurityAgent (agent mode) and security_node (function mode) based on feature flags
- Added consistent hash-based rollout using MD5 of URL to ensure same URL always gets same mode (for debugging reproducibility)
- Added auto-fallback mechanism: if SecurityAgent raises exception, falls back to security_node function and marks mode as "function_fallback"
- Added SecurityModeStarted and SecurityModeCompleted progress events in ipc.py for monitoring security mode selection and execution metrics
- Added rollout helpers to settings.py: `get_security_agent_rollout()` and `should_use_security_agent(url)`
- Added SecurityAgent mode selection methods: `is_enabled()`, `get_env_mode()`, `initialize()`
- Added security_mode field to AuditState TypedDict for tracking which mode was used per audit

## Task Commits

Each task was committed atomically:

1. **Task 1: Add rollout percentage helpers to settings** - `daee0b2` (feat)
2. **Task 2: Add SecurityMode progress events to ipc.py** - `2bb5978` (feat)
3. **Task 3: Add SecurityAgent mode selection methods** - `463c7de` (feat)
4. **Task 4: Implement feature flag routing in orchestrator** - `e55f646` (feat)

## Files Created/Modified

- `veritas/config/settings.py` - Added `get_security_agent_rollout()` and `should_use_security_agent(url)` functions with consistent hash-based routing; imported hashlib and logging
- `veritas/core/ipc.py` - Added `SecurityModeStarted` and `SecurityModeCompleted` progress event dataclasses for monitoring security mode selection and execution
- `veritas/agents/security_agent.py` - Added `is_enabled()` class method, `get_env_mode()` static method, and `initialize()` async method for mode detection and pre-analysis setup
- `veritas/core/orchestrator.py` - Added `security_node_with_agent()` wrapper with feature flag routing, auto-fallback mechanism, and mode tracking; updated graph builder and audit method to use new wrapper

## Decisions Made

- **Consistent hash-based routing**: MD5 hash of URL ensures same URL always maps to same mode, critical for debugging and reproducibility
- **Rollout percentage approach**: SECURITY_AGENT_ROLLOUT 0.0-1.0 enables gradual production deployment (10% -> 25% -> 50% -> 75% -> 100%)
- **Auto-fallback first principle**: SecurityAgent exceptions trigger immediate fallback to security_node function, preventing audit failures
- **Agent-first default**: USE_SECURITY_AGENT=true is default, requiring explicit opt-out for function mode
- **Environment-driven configuration**: Feature flags controlled via environment variables enable instant rollback without code changes

## Deviations from Plan

None - plan executed exactly as specified. All tasks completed without requiring auto-fixes or architectural changes.

## Verification Criteria Met

- `USE_SECURITY_AGENT=true` → SecurityAgent.get_env_mode() returns "agent"
- `USE_SECURITY_AGENT=false` → SecurityAgent.get_env_mode() returns "function"
- `SECURITY_AGENT_ROLLOUT=1.0` → SecurityAgent.is_enabled() always returns True
- Consistent hash routing verified: same URL always gets same mode decision
- SecurityModeStarted and SecurityModeCompleted events create successfully
- security_node_with_agent function callable and accessible
- All 42 existing tests passing (IPC tests, config tests, veritas tests)
- Feature flag verification tests all passed

## Issues Encountered

None - all implementations worked as expected on first attempt.

## Next Phase Readiness

Feature flag infrastructure complete and verified. Ready for:
- Phase 2 Plan 04: Unit tests for SecurityAgent feature flag routing
- Phase 2 Plan 05: Integration tests for full agent/function mode workflows
- Gradual production rollout starting at 10% and monitoring SecurityModeCompleted events

---
*Phase: 02-agent-architecture-refactor*
*Completed: 2026-02-21*
