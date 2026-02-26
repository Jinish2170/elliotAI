# Roadmap: VERITAS

## Overview

VERITAS's journey from initial concept to production masterpiece: v1.0 established a production-grade foundation with stabilized architecture (IPC, state management, persistence). v2.0 adds masterpiece features (5-pass Vision Agent, OSINT integration, dual-tier Judge, 25+ security modules, agent theater) that differentiate it as a portfolio-ready thesis project demonstrating expert-level capabilities in autonomous multi-modal web forensics.

## Milestones

- ✅ **v1.0 Core Stabilization** - Phases 1-5 (shipped 2026-02-23)
- 📋 **v2.0 Masterpiece Features** - Phases 6-11 (planned)

## Phases

<details>
<summary>✅ v1.0 Core Stabilization (Phases 1-5) - SHIPPED 2026-02-23</summary>

**Phases completed:** 5 phases, 22 plans

**Key accomplishments:**
- Replaced fragile stdout parsing with multiprocessing.Queue IPC (40 passing tests)
- Created SecurityAgent class matching agent architecture patterns
- Resolved LangGraph Python 3.14 CancelledError with sequential execution tracking
- Replaced empty return stubs with context-specific exceptions for fail-loud error handling
- Implemented SQLite audit persistence with WAL mode and AuditRepository CRUD operations
- Built audit history and compare API endpoints for forensic evidence management

</details>

### 📋 v2.0 Masterpiece Features (In Progress)

**Milestone Goal:** Implement masterpiece-quality features (40 requirements) on top of the stabilized foundation.

- ✅ **Phase 6: Vision Agent Enhancement** - 5-pass pipeline with CV temporal analysis for sophisticated dark pattern detection (6 reqs) - **COMPLETE 2026-02-24**
- [x] **Phase 7: Scout Navigation & Quality Foundation** - Multi-page scrolling coverage with false positive protection (6 reqs) (completed 2026-02-26)
- [ ] **Phase 8: OSINT & CTI Integration** - 15+ intelligence sources with cross-referencing for entity verification (7 reqs)
- [ ] **Phase 9: Judge System & Orchestrator** - Dual-tier verdicts with site-type strategies in smart orchestration framework (9 reqs)
- [ ] **Phase 10: Cybersecurity Deep Dive** - 25+ enterprise modules with darknet threat detection (2 reqs)
- [ ] **Phase 11: Agent Theater & Content Showcase** - Engaging real-time UI with progressive visual feedback (4 reqs)

## Phase Details

### Phase 6: Vision Agent Enhancement
**Goal**: Deliver sophisticated 5-pass visual analysis pipeline with computer vision temporal analysis for detecting dark patterns and dynamic scams, providing visual intelligence foundation for all downstream features
**Depends on**: v1.0 Core Stabilization (Phases 1-5)
**Requirements**: VISION-01, VISION-02, VISION-03, VISION-04, SMART-VIS-01, SMART-VIS-02
**Success Criteria** (what must be TRUE):
  1. User can observe Vision Agent complete 5-pass analysis (initial scan, dark patterns, temporal dynamics, graph cross-reference, final synthesis)
  2. User can see findings detected from sophisticated dark patterns (urgency tactics, fake social proof, etc.) with confidence scores
  3. User can view temporal analysis results showing dynamic content changes detected between screenshots
  4. System emits progress events during vision analysis (not batched until end) showing which pass is active
  5. Vision findings are cross-referenced with external threat intelligence sources for verification
**Plans**: [phase-6/PLAN.md](.planning/phase-6/PLAN.md)

### Phase 7: Scout Navigation & Quality Foundation
**Goal**: Deliver complete page coverage via scrolling and multi-page exploration, with quality management foundation preventing false positives through multi-factor validation
**Depends on**: Phase 6
**Requirements**: SCROLL-01, SCROLL-02, SCROLL-03, QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. User can view full screenshot series captured during scroll-based lazy loading
  2. User can see exploration beyond landing page including About, Contact, Privacy pages
  3. System waits for lazy-loaded content before capturing screenshots
  4. Threat findings require 2+ source agreement before appearing as "confirmed" (prevents solo-source false positives)
  5. Each finding displays confidence score (0-100%) with supporting reasoning
**Plans**: [phase-7/PLAN.md](.planning/phase-7/PLAN.md)

### Phase 8: OSINT & CTI Integration
**Goal**: Deliver open-source intelligence from 15+ sources with multi-source cross-referencing, providing entity verification data for Judge Agent and threat exposure monitoring
**Depends on**: Phase 6 (Vision screenshots provide OSINT context)
**Requirements**: OSINT-01, OSINT-02, OSINT-03, CTI-01, CTI-02, CTI-03, CTI-04
**Success Criteria** (what must be TRUE):
  1. User can view domain verification data (whois, DNS records, SSL certificate)
  2. User can see malicious URL check results from VirusTotal and PhishTank databases
  3. User can observe social media presence verification (linked accounts, authenticity checks)
  4. System detects and displays darknet exposure indicators
  5. OSINT findings are cross-referenced across sources with conflict detection and confidence scoring
**Plans**: [phase-8/PLAN.md](.planning/phase-8/PLAN.md)

### Phase 9: Judge System & Orchestrator
**Goal**: Deliver dual-tier verdict system (technical CWE/CVSS + plain English recommendations) with site-type-specific scoring strategies, integrated into smart orchestration framework with adaptive time management
**Depends on**: Phase 7 (Quality foundation), Phase 8 (OSINT data for technical verdicts)
**Requirements**: JUDGE-01, JUDGE-02, JUDGE-03, ORCH-01, ORCH-02, ORCH-03, PROG-01, PROG-02, PROG-03
**Success Criteria** (what must be TRUE):
  1. User can access dual-tier verdict: technical details (CWE IDs, CVSS scores) and plain language explanation
  2. User can observe context-aware scoring based on detected site type (e-commerce, financial, portfolio, etc.)
  3. System adapts timeout strategies based on page complexity during audit execution
  4. System provides estimated completion time countdown during long audits
  5. Graceful degradation ensures partial results return even if agents crash ("show must go on")
**Plans**: [phase-9/PLAN.md](.planning/phase-9/PLAN.md)

### Phase 10: Cybersecurity Deep Dive
**Goal**: Deliver 25+ enterprise-grade security modules (OWASP Top 10, PCI DSS, GDPR compliance) with CVSS scoring and darknet threat detection fed into Judge verdict scores
**Depends on**: Phase 9 (Security findings feed Judge verdict)
**Requirements**: SEC-01, SEC-02
**Success Criteria** (what must be TRUE):
  1. User can view OWASP Top 10 compliance status with per-vulnerability findings
  2. User can see PCI DSS and GDPR compliance check results
  3. Each security finding displays CVSS 3.1 severity score
  4. System correlates darknet threat intelligence with security findings
  5. Security modules are grouped by execution tier (fast/medium/deep) with appropriate timeout configuration
**Plans**: [phase-10/PLAN.md](.planning/phase-10/PLAN.md)

### Phase 11: Agent Theater & Content Showcase
**Goal**: Deliver engaging real-time UI showcase with all 5 agents in Agent Theater, screenshot carousel with highlight overlays, and running log with personality - the key differentiator for portfolio/thesis presentation
**Depends on**: Phase 9 (Orchestrator), Phase 10 (Cybersecurity data)
**Requirements**: SHOWCASE-01, SHOWCASE-02, SHOWCASE-03, SHOWCASE-04
**Success Criteria** (what must be TRUE):
  1. User experiences "always something happening" every 5-10 seconds during ~3-5 minute audits via live feed
  2. User can navigate through screenshot carousel with highlight overlays for detected patterns (coordinates align visually)
  3. User reads running log showing agent activities with timestamps and task completion celebrations ("Vision found 3 dark patterns!")
  4. Green flag celebrations appear prominently when audits return positive results (no major issues)
  5. Personality elements (agent emojis, finding "flexing", interesting highlights during waiting periods) maintain engagement throughout audit
**Plans**: [phase-11/PLAN.md](.planning/phase-11/PLAN.md)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1 | v1.0 | 22/22 | ✅ Complete | 2026-02-23 |
| 6 | v2.0 | 6/6 | ✅ Complete | 2026-02-24 |
| 7 | v2.0 | Complete    | 2026-02-26 | 2026-02-26 |
| 8 | v2.0 | 0/2 | 📝 Planned | - |
| 9 | v2.0 | 0/2 | 📝 Planned | - |
| 10 | v2.0 | 0/2 | 📝 Planned | - |
| 11 | v2.0 | 0/2 | 📝 Planned | - |

Coverage:
- v1 phases: 5 phases, 22 plans
- v2 phases: 6 phases, 18 total plans (8 complete, 10 in progress/planned)
- Total: 11 phases, 40 plans
