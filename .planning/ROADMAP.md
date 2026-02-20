# Roadmap: VERITAS Masterpiece Upgrade

**Milestone:** v1.0 - Core Stabilization
**Created:** 2026-02-20
**Mode:** yolo (GO) | Depth: Standard | Parallelization: Enabled

## Phases

- [ ] **Phase 1: IPC Communication Stabilization** - Replace fragile stdout parsing with multiprocessing.Queue
- [ ] **Phase 2: Agent Architecture Refactor** - Create proper SecurityAgent class matching agent patterns
- [ ] **Phase 3: LangGraph State Machine Investigation** - Investigate and enable proper LangGraph execution
- [ ] **Phase 4: Stub Cleanup & Code Quality** - Replace empty return stubs with NotImplementedError
- [ ] **Phase 5: Persistent Audit Storage** - Implement SQLite database for audit persistence

## Phase Details

### Phase 1: IPC Communication Stabilization

**Goal**: Backend can receive structured progress events from Veritas subprocess without parsing stdout

**Depends on**: None (first phase)

**Requirements**: CORE-02, CORE-02-2, CORE-02-3, CORE-02-4, CORE-02-5, CORE-06

**Success Criteria** (what must be TRUE):
1. Backend receives structured progress events from Veritas subprocess via multiprocessing.Queue
2. Audit completes without parsing `##PROGRESS:` markers from stdout
3. Fallback to stdout mode works for instant rollback (flag-controlled)
4. Dual-mode operation enabled via `--use-queue-ipc` CLI flag for gradual migration
5. Unit and integration tests verify Queue-based communication works correctly

**Plans**: TBD

---

### Phase 2: Agent Architecture Refactor

**Goal**: SecurityAgent class matches VisionAgent and JudgeAgent patterns with feature-flagged migration

**Depends on**: Phase 1

**Requirements**: CORE-01, CORE-01-2, CORE-01-3, CORE-01-4, CORE-06-2

**Success Criteria** (what must be TRUE):
1. SecurityAgent class exists with async analyze() method returning SecurityResult dataclass
2. SecurityAgent includes all security modules (headers, phishing, redirects, JS analysis, form validation)
3. SecurityAgent matches VisionAgent and JudgeAgent patterns (consistent interface)
4. Feature flag enables gradual migration from function to class-based agent
5. SecurityAgent class follows same test pattern as VisionAgent/JudgeAgent

**Plans**: TBD

---

### Phase 3: LangGraph State Machine Investigation

**Goal**: Investigate Python 3.14 CancelledError and enable proper LangGraph execution or document workaround

**Depends on**: Phase 2

**Requirements**: CORE-03, CORE-03-2, CORE-03-3, CORE-03-4, CORE-03-5, CORE-06-3

**Success Criteria** (what must be TRUE):
1. LangGraph StateGraph executes via ainvoke() without Python 3.14 CancelledError OR workaround documented
2. Proper LangGraph debugging, visualization, and checkpointing are enabled
3. Isolated reproduction test documents root cause of CancelledError
4. Resolution documented: version pin, hybrid execution, or sequential with tracking
5. Sequential execution fallback maintained for instant rollback
6. LangGraph reproduction test covers Python 3.14 async behavior

**Plans**: TBD

---

### Phase 4: Stub Cleanup & Code Quality

**Goal**: All empty return stubs replaced with NotImplementedError or proper implementations

**Depends on**: Phase 3

**Requirements**: CORE-04, CORE-04-2, CORE-04-3, CORE-04-4, CORE-04-5, CORE-06-4

**Success Criteria** (what must be TRUE):
1. evidence_store.py stubs (lines 207, 250, 309, 327, 351, 362) raise NotImplementedError
2. judge.py empty returns (lines 943, 960) raise NotImplementedError
3. dom_analyzer.py empty returns (lines 318, 345) raise NotImplementedError
4. dark_patterns.py empty return (line 407) raise NotImplementedError
5. Tests verify NotImplementedError is raised for incomplete features
6. No silent failures from empty return stubs

**Plans**: TBD

---

### Phase 5: Persistent Audit Storage

**Goal**: Audit results persist across backend restart in SQLite database with dual-write migration

**Depends on**: Phase 4

**Requirements**: CORE-05, CORE-05-2, CORE-05-3, CORE-05-4, CORE-05-5, CORE-06-5

**Success Criteria** (what must be TRUE):
1. Audit results persist across backend restart in SQLite database
2. SQLite uses WAL mode for concurrent write support
3. Dual-write migration (memory + SQLite) enables gradual data migration
4. Screenshots stored in filesystem, references stored in database
5. Audit history API supports historical audit retrieval and comparison
6. SQLite persistence tested with concurrent audit simulation

**Plans**: TBD

---

## Progress Tracking

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. IPC Communication Stabilization | 0/3 | Not started | - |
| 2. Agent Architecture Refactor | 0/2 | Not started | - |
| 3. LangGraph State Machine Investigation | 0/2 | Not started | - |
| 4. Stub Cleanup & Code Quality | 0/2 | Not started | - |
| 5. Persistent Audit Storage | 0/3 | Not started | - |

---

## Coverage Summary

**v1 Requirements:** 30 total
**Phases:** 5
**Depth:** Standard (5-8 phases)
**Coverage:** 30/30 requirements mapped (100%)

| Requirement Category | Count | Phase |
|---------------------|-------|-------|
| IPC Communication | 6 | Phase 1 |
| Agent Architecture | 5 | Phase 2 |
| State Machine | 6 | Phase 3 |
| Code Quality | 6 | Phase 4 |
| Data Persistence | 6 | Phase 5 |

---

## Notes

- **Phase Ordering**: Based on research recommendation from STABILIZATION.md - IPC first (most fragile), then architecture pattern, then state machine, then stub cleanup, then persistence
- **Feature Flags**: All major refactors use feature flags for gradual migration (CORE-02-5, CORE-01-4, CORE-03-5, CORE-05-3)
- **Testing**: Each phase includes corresponding test requirements (CORE-06 series)
- **Rollback**: Each phase maintains fallback paths for instant rollback capability
- **Research Flags**: Phase 3 (LangGraph) has LOW confidence due to Python 3.14 CancelledError root cause requiring investigation

---

*Last updated: 2026-02-20*
