# Project Research Summary

**Project:** Elliot (elliotAI) - VERITAS Forensic Web Auditing Platform
**Domain:** Brownfield stabilization, IPC refactoring, persistence layer
**Researched:** 2026-02-20
**Confidence:** MEDIUM

## Executive Summary

VERITAS is a functional forensic web auditing platform with significant technical debt accumulated during rapid development. The codebase exhibits classic brownfield challenges: fragile inter-process communication via stdout parsing, inconsistent architecture patterns (SecurityAgent as function instead of class), bypassed framework infrastructure (LangGraph ainvoke unused), and in-memory storage causing data loss on restart.

Stabilization should follow the **Strangler Fig pattern** with **feature-flagged refactoring**, systematically replacing fragile components while maintaining existing functionality through parallel implementations. The approach minimizes risk by running old and new code side-by-side with gradual cutover. The highest-impact sequence is: (1) Replace stdout IPC with multiprocessing.Queue for structured message passing, (2) Create proper SecurityAgent class, (3) Enable LangGraph proper execution or document the workaround, (4) Replace empty stubs with NotImplementedError, (5) Add SQLite persistence for audit history.

The critical pattern across all research is **dual-mode migration**: implement new systems while keeping legacy paths as fallbacks, switch over gradually with monitoring, and remove legacy code only after validation. This approach, documented in all three research files, ensures zero-downtime migration with instant rollback capability.

## Key Findings

### Recommended Stack

**Core technologies:**
- **multiprocessing.Queue (Python stdlib)** — Structured IPC replacement for stdout parsing — Windows-compatible, type-safe, real-time streaming, no dependencies
- **SQLite with WAL mode (v1) → PostgreSQL (v2)** — Audit persistence layer — Single-file simplicity for initial deployment, migration path to production-grade when scaling
- **SQLAlchemy async ORM** — Database abstraction — Enables seamless SQLite→PostgreSQL migration via engine swap
- **Feature flags (env vars)** — Safe deployment mechanism — Enables gradual cutover with instant rollback

### Critical Architecture Changes

**Major components:**
1. **IPC Layer** — Replace fragile stdout marker parsing (`##PROGRESS:`) with multiprocessing.Queue for structured event passing between backend and orchestrator subprocess
2. **SecurityAgent class** — Refactor security_node function into proper agent class following VisionAgent/JudgeAgent patterns, with feature flag for gradual migration
3. **Audit Repository** — Abstract persistence behind repository interface, enable SQLite storage with WAL mode for concurrent writes, keep filesystem storage for screenshots
4. **LangGraph ainvoke** — Investigate Python 3.14 CancelledError blocking proper execution, either fix or document sequential execution as temporary workaround

### Critical Pitfalls

1. **Fragile stdout parsing** — Subprocess output changes break entire audit pipeline → Use multiprocessing.Queue with typed ProgressEvent dataclass
2. **In-memory storage losing data** — Backend restart loses all audit history → SQLite persistence with dual-write migration
3. **Empty stubs masking bugs** — `return []` hides incomplete implementation → Replace with NotImplementedError and feature flags
4. **SecurityAgent as function** — Violates agent pattern consistency → Create class with feature flag for gradual cutover
5. **Blocked LangGraph ainvoke** — Missing state machine benefits → Investigate Python 3.14 compatibility or document workaround

## Implications for Roadmap

Based on combined research, suggested phase structure:
`
### Phase 1: IPC Stabilization
**Rationale:** Most fragile component, stdout parsing causes real production failures, blocks all downstream reliability
**Delivers:** Robust structured message passing with instant rollback capability
**Addresses:** Fragile stdout parsing, subprocess output variations, JSON parsing overhead
**Avoids:** Entire audit pipeline breaking on unexpected subprocess output
**Key changes:**
- Add `--use-queue-ipc` CLI flag to `veritas/__main__.py`
- Update `VeritasOrchestrator.__init__` to accept progress_queue parameter
- Modify `_emit()` to support both Queue and stdout modes
- Implement Queue-based polling in `AuditRunner._run_with_queue_ipc()`
- Remove `_extract_last_json_from_stdout()` fallback after validation

### Phase 2: SecurityAgent Refactor
**Rationale:** Corrects architectural violation, improves maintainability, sets pattern for future agents
**Delivers:** Consistent agent pattern across all orchestration nodes
**Uses:** Existing VisionAgent/JudgeAgent as templates, feature flag for safe migration
**Implements:** SecurityAgent class with analyze() method, SecurityResult dataclass
**Avoids:** Future refactoring pain, code style inconsistencies, unclear ownership

### Phase 3: LangGraph State Machine Investigation
**Rationale:** Unlock LangGraph debugging, visualization, check-pointing capabilities currently bypassed
**Delivers:** Either fixed ainvoke() execution or documented workaround with tracking issue
**Addresses:** Python 3.14 asyncio CancelledError blocking LangGraph
**Avoids:** Lost framework capabilities, manual state management errors, no audit resumption support
**Risk:** May require Python version pin if LangGraph incompatible with 3.14

### Phase 4: Stub Cleanup & Error Visibility
**Rationale:** Unmask silent failures, improve testability, prevent false confidence from partial results
**Delivers:** Explicit NotImplementedError for incomplete features, clear error tracking
**Addresses:** Empty return statements in evidence_store, judge verdict extraction
**Avoids:** Hidden bugs, tests passing for wrong reasons, partial results treated as complete
**Pattern:** Replace `return []` with `raise NotImplementedError("TODO: implement X")`

### Phase 5: Persistent Audit Storage
**Rationale:** Enable audit history, forensic evidence preservation, historical comparison
**Delivers:** SQLite-based audit repository with WAL mode, screenshot filesystem storage, audit history API
**Uses:** SQLAlchemy async engine, Repository pattern, dual-write migration
**Implements:** audits, audit_findings, audit_screenshots, audit_events tables
**Avoids:** Data loss on restart, no historical record, lost forensic evidence
**Migration:** Dual-write (memory + DB) → switch reads to DB → remove in-memory storage

### Phase Ordering Rationale

- **IPC first** because it's the most fragile component causing real failures — any subprocess output change breaks the entire audit pipeline
- **Architecture pattern second** because SecurityAgent inconsistency affects all future development speed and code clarity
- **State machine third** because LangGraph investigation may require version pin decision that affects all subsequent work
- **Stub cleanup fourth** because it improves error visibility and testability without architectural changes
- **Persistence last** because it's an enhancement that unlocks new capabilities (history, comparison) rather than fixing blocking issues

The order maximizes stability first (IPC), then architecture consistency, then investigation of major technical decision (LangGraph), then code quality, finally feature addition (persistence).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (LangGraph):** Python 3.14 compatibility not verified — need isolated reproduction test, may require version pin or upstream bug report
- **Phase 5 (Persistence):** Query pattern analysis missing — need to determine which historical queries users need, what analytics are valuable

Phases with standard patterns (skip research-phase):
- **Phase 1 (IPC):** multiprocessing.Queue well-documented in Python stdlib, pattern verified across both IPC and STABILIZATION research
- **Phase 2 (SecurityAgent):** Clear template from existing VisionAgent/JudgeAgent, straightforward class refactor
- **Phase 4 (Stub Cleanup):** Standard Python NotImplementedError pattern, grep-based audit sufficient

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| IPC replacement (multiprocessing.Queue) | HIGH | Verified in Python 3.14 docs, both IPC and STABILIZATION research converge on same solution |
| SecurityAgent refactor pattern | HIGH | Clear template from existing agents, straightforward class creation |
| LangGraph Python 3.14 compatibility | MEDIUM | Research completed with reproduction test plan, isolated investigation needed to determine root cause documented |
| Stub cleanup (NotImplementedError) | HIGH | Standard Python pattern, well-documented |
| Persistence (SQLite + WAL) | MEDIUM | Schema reasonable but untested with actual data volumes, migration path proven but needs careful dual-write implementation |

**Overall confidence:** MEDIUM

### Gaps to Address

- **LangGraph Python 3.14 CancelledError root cause**: Need isolated reproduction test to determine if fixable or requires version pin — handle by creating minimal StateGraph test case, try on Python 3.12/3.13, document workaround if pinning required
- **Actual audit data volume**: Need real-world size measurements (average audit JSON, screenshots per audit, events per audit) — handle by running 50 test audits with metrics collection during Phase 5 planning
- **Concurrent load testing**: SQLite WAL mode performance under concurrent audits not characterized — handle by load testing in Phase 1 (10 concurrent audits with monitoring)
- **Historical query requirements**: Which queries do users need for analytics/comparison not defined — handle by user interviews during Phase 5 planning or defer to v2 dashboard design

## Sources

### Primary (HIGH confidence)
- **Python 3.14 multiprocessing documentation** — Queue-based IPC patterns, Windows spawn context, Manager.Queue pickling — https://docs.python.org/3/library/multiprocessing.html
- **SQLite WAL mode documentation** — Concurrency improvements, checkpoint configuration, synchronous modes — https://www.sqlite.org/wal.html
- **SQLAlchemy 2.0 async documentation** — AsyncSession, connection pooling, engine configuration — https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Existing codebase analysis** — VisionAgent, JudgeAgent patterns for SecurityAgent template, backend/routes/audit.py for in-memory storage structure

### Secondary (MEDIUM confidence)
- **FastAPI database tutorial** — Repository pattern, dependency injection, async database operations — https://fastapi.tiangolo.com/tutorial/sql-databases/
- **Strangler Fig pattern** — Martin Fowler's gradual migration approach, feature flagging for safe deployment — https://martinfowler.com/bliki/StranglerFigApplication.html

### Tertiary (MEDIUM confidence, needs investigation)
- **LangGraph ainvoke behavior** — Research completed with detailed reproduction test plans, documented three hypotheses for CancelledError root cause (LangGraph internals, NIMClient async timeout, Windows+Python 3.14 specific) — https://langchain-ai.github.io/langgraph/ (needs isolated test execution)
- **Python 3.14 asyncio CancelledError changes** — No explicit changes documented in release notes, but TaskGroup and create_task() changes may affect LangGraph internals — https://docs.python.org/3.14/whatsnew/3.14.html

---
*Research completed: 2026-02-20*
*Ready for roadmap: yes*
*Synthesizer: GSD research synthesizer*
*Input files: STABILIZATION.md, IPC.md, PERSISTENCE.md, LANGGRAPH.md*
