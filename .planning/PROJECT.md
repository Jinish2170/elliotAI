# VERITAS Masterpiece Upgrade

## What This Is

VERITAS is an autonomous multi-modal forensic web auditing platform that analyzes websites for trust, safety, dark patterns, and security vulnerabilities. It combines 5 specialized AI agents (Scout, Security, Vision, Graph, Judge) with visual analysis, graph investigation, and multi-signal scoring to produce comprehensive trust reports. This project is a college master's final year thesis being upgraded to "masterpiece" quality with advanced features and production-grade stability.

## Core Value

**Every implementation works at commit time.** Build incrementally with explicit tests, verify each phase before proceeding, and deliver a production-ready system suitable for portfolio/job demonstration. Quality over speed - broken code is unacceptable.

## Requirements

### Validated

- ✓ **5-agent pipeline working** — Scout → Security → Vision → Graph → Judge (existing)
- ✓ **Next.js frontend** — Landing, live audit view, forensic report (existing)
- ✓ **FastAPI backend** — REST endpoints + WebSocket streaming (existing)
- ✓ **NVIDIA NIM integration** — VLM for screenshot analysis (existing)
- ✓ **20/20 Python tests passing** — Core engine validation (existing)

### Active

- [ ] **CORE-01**: Fix missing SecurityAgent class - implement proper agent pattern
- [ ] **CORE-02**: Replace fragile subprocess stdout parsing with proper IPC
- [ ] **CORE-03**: Enable proper LangGraph state machine execution
- [ ] **CORE-04**: Replace empty return stubs with proper implementations
- [ ] **CORE-05**: Implement persistent audit storage (not in-memory)
- [ ] **CORE-06**: Add comprehensive test coverage for critical paths
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

**Current State (from codebase analysis):**

VERITAS is functional but has significant technical debt that must be addressed before implementing new features:

**Critical Issues:**
- Security analysis is implemented as a function instead of an agent class, breaking the agent architecture pattern
- Communication between backend and veritas subprocess depends on parsing stdout for `##PROGRESS:` markers - fragile and non-standard
- Orchestrator manually executes nodes sequentially instead of using LangGraph's state machine - defeats purpose of using LangGraph
- Multiple functions return empty lists/dicts with no implementation, masking runtime issues
- Audit results stored only in process-local dictionary, lost on restart or failure

**Architecture:**
- 3-tier Async Event-Stream Architecture (Frontend → Backend → Veritas Engine)
- LangGraph StateGraph for agent orchestration (currently not used via ainvoke)
- Subprocess isolation for Python 3.14 asyncio compatibility
- WebSocket streaming for real-time progress updates
- 4-level AI fallback (Primary NIM VLM → Fallback VLM → Tesseract OCR → Manual)

**Tech Stack:**
- Backend: Python 3.14, FastAPI, LangGraph, NVIDIA NIM, Playwright, LanceDB
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS 4
- Tests: 20/20 Python tests passing

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
| Two-milestone approach | Stabilization first prevents accumulation of broken code from new features | — Pending |
| Sequential execution with verification | Each phase must work before proceeding; no "ship broken, fix later" mentality | ✓ Good |
| Test-driven approach | Every new feature requires tests; empty implementations must raise NotImplementedError | — Pending |
| Proper IPC for subprocess communication | Replace fragile stdout parsing with SQLite or proper message queue for reliability | — Pending |
| Database persistence for audits | In-memory storage loses data; SQLite for v1, PostgreSQL for production | — Pending |

---
*Last updated: 2026-02-20 after project initialization*
