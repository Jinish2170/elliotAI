# VERITAS Masterpiece Upgrade

## What This Is

VERITAS is an autonomous multi-modal forensic web auditing platform that analyzes websites for trust, safety, dark patterns, and security vulnerabilities. It combines 5 specialized AI agents (Scout, Security, Vision, Graph, Judge) with visual analysis, graph investigation, and multi-signal scoring to produce comprehensive trust reports. This project is a college master's final year thesis being upgraded to "masterpiece" quality with advanced features and production-grade stability.

## Core Value

**Every implementation works at commit time.** Build incrementally with explicit tests, verify each phase before proceeding, and deliver a production-ready system suitable for portfolio/job demonstration. Quality over speed - broken code is unacceptable.

## Current Milestone: v2.0 Masterpiece Features

**Goal:** Implement masterpiece-quality features (Vision Agent enhancement, OSINT integration, Judge system, Cybersecurity, Content showcase) on top of the stabilized foundation.

**Previous Milestone:** v1.0 Core Stabilization (SHIPPED 2026-02-23)

---

## v1.0 Delivered (2026-02-23)

**Core Stabilization Complete** — All critical technical debt resolved, production-grade foundation established.

### Delivered Features
- **IPC Communication:** multiprocessing.Queue-based inter-process communication with dual-mode support (40 passing tests)
- **Agent Architecture:** SecurityAgent class matching VisionAgent/JudgeAgent patterns
- **State Machine:** LangGraph Python 3.14 CancelledError resolved with sequential execution tracking
- **Code Quality:** Empty return stubs replaced with context-specific exceptions
- **Persistence:** SQLite audit storage with WAL mode, AuditRepository CRUD operations, history/compare APIs

---

## Requirements

### Validated

- ✓ **5-agent pipeline working** — Scout → Security → Vision → Graph → Judge (v1.0)
- ✓ **Next.js frontend** — Landing, live audit view, forensic report (v1.0)
- ✓ **FastAPI backend** — REST endpoints + WebSocket streaming (v1.0)
- ✓ **NVIDIA NIM integration** — VLM for screenshot analysis (v1.0)
- ✓ **CORE-01**: SecurityAgent class matching agent architecture pattern (v1.0)
- ✓ **CORE-02**: multiprocessing.Queue IPC with dual-mode support (v1.0)
- ✓ **CORE-03**: LangGraph sequential execution with enhanced tracking (v1.0)
- ✓ **CORE-04**: Empty return stubs replaced with context-specific exceptions (v1.0)
- ✓ **CORE-05**: SQLite audit persistence with WAL mode (v1.0)
- ✓ **CORE-06**: Comprehensive test coverage (140 tests passing, v1.0)

### Active

- [ ] **VISION-01**: Implement 5-pass Vision Agent with multi-pass pipeline
- [ ] **VISION-01**: Implement 5-pass Vision Agent with multi-pass pipeline
- [ ] **VISION-02**: Design sophisticated VLM prompts for each pass
- [ ] **VISION-03**: Implement computer vision temporal analysis
- [ ] **VISION-04**: Build progress showcase emitter for frontend
- [ ] **OSINT-01**: Implement 15+ OSINT intelligence sources
- [ ] **OSINT-02**: Build Darknet analyzer (6 marketplaces)
- [ ] **OSINT-03**: Enhance Graph Investigator with OSINT integration
- [ ] **JUDGE-01**: Design dual-tier verdict data classes
- [ ] **JUDGE-02**: Implement site-type-specific scoring strategies
- [ ] **JUDGE-03**: Build Judge Agent with dual-tier generation
- [ ] **SEC-01**: Implement 25+ enterprise security modules
- [ ] **SEC-02**: Build darknet-level threat detection
- [ ] **SHOWCASE-01**: Design psychology-driven content flow
- [ ] **SHOWCASE-02**: Implement real-time Agent Theater components
- [ ] **SHOWCASE-03**: Build Screenshot Carousel with gradual reveal
- [ ] **SHOWCASE-04**: Build Running Log with task flexing

### Out of Scope

- Authentication system — Public API suitable for thesis/portfolio demo
- Multi-user/tenant deployment — Single-server deployment sufficient
- Production hosting infrastructure — Local/dev deployment only
- Real-time alerting/analytics — Focus on audit execution, not monitoring
- Alternative AI providers — Sticking with NVIDIA NIM (already working)

## Context

**Current State (post v1.0):**

VERITAS is now production-ready with stabilized foundation. All critical technical debt has been resolved:

**Foundation Complete (v1.0):**
- SecurityAgent class properly implements agent architecture pattern
- Queue-based IPC replaces fragile stdout parsing with dual-mode fallback
- LangGraph sequential execution with enhanced tracking documentation
- Fail-loud error handling eliminates silent failures from empty stubs
- SQLite persistence with WAL mode for audit history and forensic evidence

**Tech Stack:**
- Backend: Python 3.14, FastAPI, LangGraph, NVIDIA NIM, Playwright, LanceDB, SQLAlchemy
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS 4
- Tests: 140+ Python tests passing (CORE stabilization complete)
- Database: SQLite with WAL mode (migration path to PostgreSQL)
- IPC: multiprocessing.Queue with automatic stdout fallback

**Ready for Masterpiece Features:**
With production-grade foundation established, ready to implement advanced features:
- 5-pass Vision Agent with multi-modal analysis
- 15+ OSINT intelligence sources integration
- Darknet analyzer for threat detection
- Dual-tier Judge Agent with site-type strategies
- 25+ enterprise security modules
- Agent Theater with real-time showcase components

**Implementation Plan Context:**

The IMPLEMENTATION_PLAN.md outlines a 6-week masterpiece upgrade:
- **Week 1-2**: Vision Agent Enhancement (5-pass pipeline, VLM prompts, CV temporal analysis)
- **Week 3**: OSINT & Graph Power-Up (15+ OSINT sources, darknet analyzer)
- **Week 4**: Judge System Dual-Tier (Dual-tier verdicts, 11 site-type strategies)
- **Week 5**: Cybersecurity Deep Dive (25+ security modules, darknet threat detection)
- **Week 6**: Content Showcase & UX (Agent theater, screenshot carousel, running log)

**Implementation Philosophy:**

The user is explicitly prioritizing stabilization before feature implementation. This means:
1. **FIRST MILESTONE**: Fix all critical concerns in the existing codebase
2. **SECOND MILESTONE**: Implement the masterpiece features incrementally with proper testing

This ensures that when features are added, they're building on a solid foundation rather than accumulating debt.

## Constraints

- **Timeline**: Realistic (4-6 weeks) for Core Stabilization, then additional time for Full Implementation Plan
- **Quality**: Portfolio/Job ready - must be production-quality code suitable for showcasing to employers
- **Testing**: Every feature must have tests passing before commit
- **Stability**: No broken code allowed. If a phase breaks tests, fix before proceeding.
- **Incremental**: Each phase must complete and be verified before starting the next
- **Python Version**: 3.14 (currently causing LangGraph async issues - may need workaround or pin)
- **External APIs**: NVIDIA NIM quota limits, Tavily API costs

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-milestone approach | Stabilization first prevents accumulation of broken code from new features | ✓ Good - v1.0 complete, starting v2.0 |
| Sequential execution with verification | Each phase must work before proceeding; no "ship broken, fix later" mentality | ✓ Good - enforced across v1.0, continuing for v2.0 |
| Test-driven approach | Every new feature requires tests; empty implementations must raise NotImplementedError | ✓ Good - 140+ tests passing, continuing for v2.0 |
| Proper IPC for subprocess communication | Replace fragile stdout parsing with multiprocessing.Queue for reliability | ✓ Good - dual-mode IPC with fallback implemented |
| Database persistence for audits | In-memory storage loses data; SQLite for v1, PostgreSQL for production | ✓ Good - WAL mode implemented with migration path |

---
*Last updated: 2026-02-23 after v1.0 Core Stabilization milestone, starting v2.0 Masterpiece Features*
