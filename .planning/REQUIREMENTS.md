# Requirements: VERITAS Masterpiece Upgrade

**Defined:** 2026-02-20
**Core Value:** Every implementation works at commit time. Build incrementally with explicit tests, verify each phase before proceeding.

## v1 Requirements (Core Stabilization)

Requirements for Milestone v1.0: Fix critical technical debt and establish production-grade foundation.

### IPC Communication

- [x] **CORE-02**: Backend can receive structured progress events from Veritas subprocess without parsing stdout
- [x] **CORE-02-2**: Implement multiprocessing.Queue for Windows + Python 3.14 subprocess communication
- [x] **CORE-02-3**: Replace `##PROGRESS:` marker parsing with Queue-based event streaming
- [x] **CORE-02-4**: Implement fallback to stdout mode for instant rollback capability
- [x] **CORE-02-5**: Dual-mode support with `--use-queue-ipc` CLI flag for gradual migration

### Agent Architecture

- [x] **CORE-01**: SecurityAgent class matches VisionAgent and JudgeAgent patterns
- [x] **CORE-01-2**: SecurityAgent has async analyze() method returning SecurityResult dataclass
- [x] **CORE-01-3**: SecurityAgent includes all security modules (headers, phishing, redirects, JS analysis, form validation)
- [x] **CORE-01-4**: feature flag enables gradual migration from function to class-based agent

### State Machine

- [ ] **CORE-03**: LangGraph StateGraph executes via ainvoke() without Python 3.14 CancelledError
  - Partial: Minimal graph test shows ainvoke works on Python 3.11.5; full VERITAS graph not yet tested
- [ ] **CORE-03-2**: Proper LangGraph debugging, visualization, and checkpointing enabled
  - Partial: Graph structure verified (grandalf visualization optional); checkpointing not implemented
- [x] **CORE-03-3**: Isolated reproduction test documents root cause of CancelledError
  - Complete: test_01_minimal_graph.py created with 5 tests, shows LangGraph works on Python 3.11.5
- [ ] **CORE-03-4**: Workaround documented if version pin or hybrid execution needed
  - Pending: Resolution depends on Phase 02 full audit test results
- [ ] **CORE-03-5**: Sequential execution fallback maintained for instant rollback
  - Pending: Current sequential execution can serve as fallback; migration path TBD

### Code Quality

- [x] **CORE-04**: Empty return stubs replaced with NotImplementedError or proper implementations
  - Complete: evidence_store.py stubs replaced with context-specific exceptions (ValueError, FileNotFoundError, RuntimeError)
- [x] **CORE-04-2**: evidence_store.py stubs (lines 207, 250, 309, 327, 351, 362) raise context-specific exceptions
  - Complete: 6 stubs replaced, all tests pass
- [ ] **CORE-04-3**: judge.py empty returns (lines 943, 960) raise NotImplementedError
- [ ] **CORE-04-4**: dom_analyzer.py empty return (line 345 only - _check_dark_patterns_css placeholder) raises NotImplementedError. Line 318 returns [] for acceptable tracking levels (intentional business logic, not a stub)
- [ ] **CORE-04-5**: dark_patterns.py empty return (line 407) raise NotImplementedError

### Data Persistence

- [x] **CORE-05**: Audit results persist across backend restart in SQLite database
- [x] **CORE-05-2**: SQLite uses WAL mode for concurrent write support
- [x] **CORE-05-3**: Dual-write migration (memory + SQLite) enables gradual data migration
- [x] **CORE-05-4**: Screenshots stored in filesystem, references stored in database
- [x] **CORE-05-5**: Audit history API supports historical audit retrieval and comparison

### Testing

- [x] **CORE-06**: IPC Queue communication has unit and integration tests
- [ ] **CORE-06-2**: SecurityAgent class follows same test pattern as VisionAgent/JudgeAgent
- [ ] **CORE-06-3**: LangGraph reproduction test covers Python 3.14 async behavior
- [x] **CORE-06-4**: Stub cleanup verified by tests that raise context-specific exceptions
  - Complete: evidence_store.py tests pass with new exceptions (TestEvidenceStore suite)
- [x] **CORE-06-5**: SQLite persistence tested with concurrent audit simulation

## v2 Requirements (Masterpiece Features)

Deferred to Milestone v2.0. Implement features incrementally after stabilization complete.

### Vision Agent Enhancement

- **VISION-01**: Implement 5-pass Vision Agent with multi-pass pipeline
- **VISION-02**: Design sophisticated VLM prompts for each pass
- **VISION-03**: Implement computer vision temporal analysis
- **VISION-04**: Build progress showcase emitter for frontend

### OSINT & Graph Power-Up

- **OSINT-01**: Implement 15+ OSINT intelligence sources
- **OSINT-02**: Build Darknet analyzer (6 marketplaces)
- **OSINT-03**: Enhance Graph Investigator with OSINT integration

### Judge System Dual-Tier

- **JUDGE-01**: Design dual-tier verdict data classes
- **JUDGE-02**: Implement site-type-specific scoring strategies
- **JUDGE-03**: Build Judge Agent with dual-tier generation

### Cybersecurity Deep Dive

- **SEC-01**: Implement 25+ enterprise security modules
- **SEC-02**: Build darknet-level threat detection

### Content Showcase & UX

- **SHOWCASE-01**: Design psychology-driven content flow
- **SHOWCASE-02**: Implement real-time Agent Theater components
- **SHOWCASE-03**: Build Screenshot Carousel with gradual reveal
- **SHOWCASE-04**: Build Running Log with task flexing

## Out of Scope

Explicitly excluded from both v1 and v2. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Authentication system | Public API suitable for thesis/portfolio demo |
| Multi-user/tenant deployment | Single-server deployment sufficient |
| Production hosting infrastructure | Local/dev deployment only |
| Real-time alerting/analytics | Focus on audit execution, not monitoring |
| Alternative AI providers | Sticking with NVIDIA NIM (already working) |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-02 | Phase 1 | COMPLETE |
| CORE-02-2 | Phase 1 | COMPLETE |
| CORE-02-3 | Phase 1 | COMPLETE |
| CORE-02-4 | Phase 1 | COMPLETE |
| CORE-02-5 | Phase 1 | COMPLETE |
| CORE-01 | Phase 2 | COMPLETE |
| CORE-01-2 | Phase 2 | COMPLETE |
| CORE-01-3 | Phase 2 | COMPLETE |
| CORE-01-4 | Phase 2 | COMPLETE |
| CORE-03 | Phase 3 | In Progress |
| CORE-03-2 | Phase 3 | In Progress |
| CORE-03-3 | Phase 3 | COMPLETE |
| CORE-03-4 | Phase 3 | Pending |
| CORE-03-5 | Phase 3 | Pending |
| CORE-04 | Phase 4 | In Progress |
| CORE-04-2 | Phase 4 | COMPLETE |
| CORE-04-3 | Phase 4 | Pending |
| CORE-04-4 | Phase 4 | Pending |
| CORE-04-5 | Phase 4 | Pending |
| CORE-05 | Phase 5 | Complete |
| CORE-05-2 | Phase 5 | Complete |
| CORE-05-3 | Phase 5 | Complete |
| CORE-05-4 | Phase 5 | Complete |
| CORE-05-5 | Phase 5 | COMPLETE |
| CORE-06 | All phases | COMPLETE |
| CORE-06-2 | Phase 2 | Pending |
| CORE-06-3 | Phase 3 | Pending |
| CORE-06-4 | Phase 4 | COMPLETE |
| CORE-06-5 | Phase 5 | Complete |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-20 after Milestone v1.0 started*
*Last updated: 2026-02-23 after Phase 5 completion*
*18 requirements complete (Phase 1 IPC: 5, Phase 2 Agent: 4, Phase 3 State Machine: 1, Phase 4 Stub Cleanup: 2, Phase 5 Persistence: 6)*
*2 requirements in progress (Phase 4: CORE-04 - partial, Phase 3: CORE-03, CORE-03-2)*
*12 requirements remaining*