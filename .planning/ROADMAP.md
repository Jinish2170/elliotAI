# Roadmap: VERITAS

## Overview

VERITAS's journey from initial concept to production masterpiece: v1.0 established a production-grade foundation with stabilized architecture (IPC, state management, persistence). v2.0 adds masterpiece features (5-pass Vision Agent, OSINT integration, dual-tier Judge, 25+ security modules, agent theater) that differentiate it as a portfolio-ready thesis project demonstrating expert-level capabilities in autonomous multi-modal web forensics.

## Milestones

- ✅ **v1.0 Core Stabilization** - Phases 1-5 (shipped 2026-02-23)
- ✅ **v2.0 Masterpiece Features** - Phases 6-11 (shipped 2026-02-28)

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

### ✅ v2.0 Masterpiece Features (SHIPPED 2026-02-28)

<details>
<summary>**Phases completed:** 6 phases, 28 plans</summary>

**Milestone Goal:** Implemented masterpiece-quality features (40 requirements) on top of the stabilized foundation.

**Key accomplishments:**
- 5-pass Vision Agent pipeline with temporal analysis and dark pattern detection
- Multi-page Scout navigation with lazy-loaded content capture
- 15+ OSINT/CTI intelligence sources with consensus-based verification
- Dual-tier Judge System (technical CWE/CVSS + plain English recommendations)
- 25+ enterprise security modules with tier-based parallel execution
- Agent Theater with personality system, carousel overlays, and celebration effects

</details>

**Phases:**
- ✅ **Phase 6: Vision Agent Enhancement** - 5-pass pipeline with CV temporal analysis for sophisticated dark pattern detection (6 reqs) - **COMPLETE 2026-02-24**
- [x] **Phase 7: Scout Navigation & Quality Foundation** - Multi-page scrolling coverage with false positive protection (6 reqs) (completed 2026-02-26)
- [x] **Phase 8: OSINT & CTI Integration** - 15+ intelligence sources with cross-referencing for entity verification (7 reqs) (completed 2026-02-28)
- [x] **Phase 9: Judge System & Orchestrator** - Dual-tier verdicts with site-type strategies in smart orchestration framework (9 reqs) (completed 2026-02-28)
- [x] **Phase 10: Cybersecurity Deep Dive** - 25+ enterprise modules with tier-based execution, CVSS scoring, darknet threat detection (2 reqs) - **COMPLETE 2026-02-28**
- [x] **Phase 11: Agent Theater & Content Showcase** - Engaging real-time UI with progressive visual feedback (4 reqs) - **COMPLETE 2026-02-28**

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
**Plans**: [phases/06-vision-enhancement/](.planning/phases/06-vision-enhancement/)

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
**Plans**: [phases/07-scout-navigation-quality-foundation/](.planning/phases/07-scout-navigation-quality-foundation/)

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
**Plans**: [phases/08-osint-cti-integration/](.planning/phases/08-osint-cti-integration/)

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
**Plans**: [phases/09-judge-orchestrator/](.planning/phases/09-judge-orchestrator/)

### Phase 10: Cybersecurity Deep Dive
**Goal**: Deliver 25+ enterprise-grade security modules (OWASP Top 10, PCI DSS, GDPR compliance) with CVSS scoring and darknet threat detection fed into Judge verdict scores
**Depends on**: Phase 9 (Security findings feed Judge verdict, CVSS/CWE integration)
**Requirements**: SEC-01, SEC-02
**Success Criteria** (what must be TRUE):
  1. User can view OWASP Top 10 compliance status with per-vulnerability findings
  2. User can see PCI DSS and GDPR compliance check results
  3. Each security finding displays CVSS 3.1 severity score
  4. System correlates darknet threat intelligence with security findings
  5. Security modules are grouped by execution tier (fast/medium/deep) with appropriate timeout configuration
**Plans**: [10-01-PLAN.md](.planning/phases/10-cybersecurity-deep-dive/10-01-PLAN.md) — Base architecture and FAST tier modules
**Plans**: [10-02-PLAN.md](.planning/phases/10-cybersecurity-deep-dive/10-02-PLAN.md) — OWASP Top 10 modules (A01-A10)
**Plans**: [10-03-PLAN.md](.planning/phases/10-cybersecurity-deep-dive/10-03-PLAN.md) — PCI DSS and GDPR compliance modules
**Plans**: [10-04-PLAN.md](.planning/phases/10-cybersecurity-deep-dive/10-04-PLAN.md) — SecurityAgent rewrite with tier execution and darknet correlation

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
**Plans**: [11-01-PLAN.md](.planning/phases/11-agent-theater-showcase/11-01-PLAN.md) — Agent Personality System & Event Sequencing
**Plans**: [11-02-PLAN.md](.planning/phases/11-agent-theater-showcase/11-02-PLAN.md) — Screenshot Carousel & Highlight Overlays
**Plans**: [11-03-PLAN.md](.planning/phases/11-agent-theater-showcase/11-03-PLAN.md) — Running Log & Celebration System


### Phase 13: Production Hardening & Workflow Repair
**Goal**: Repair all broken agent workflows, wire disconnected features, make all 4 audit tiers functionally correct, and eliminate fabricated data from the pipeline
**Depends on**: Phase 12 (TOR Client), Phases 6-11 (all features)
**Requirements**: REPAIR-01, REPAIR-02, REPAIR-03, REPAIR-04, REPAIR-05, REPAIR-06, REPAIR-07, REPAIR-08, REPAIR-09, REPAIR-10, REPAIR-11, REPAIR-12, REPAIR-13, REPAIR-14
**Success Criteria** (what must be TRUE):
  1. Scout captures real page_content and response_headers (no fabricated HTML)
  2. Each tier (quick_scan, standard_audit, deep_forensic, darknet_investigation) runs different module sets with different budgets
  3. Darknet tier routes traffic through TOR SOCKS5 proxy
  4. All duplicate modules consolidated (scout/scout_nav, two TORClients)
  5. All 8 currently failing tests pass (onion regex + tier count)
  6. Orchestrator nodes extracted into maintainable package structure
  7. Frontend store matches actual backend event schema
  8. Integration tests verify all 4 tier workflows end-to-end

Plans:
- [x] 13-01-PLAN.md — Scout data capture & module consolidation
- [x] 13-02-PLAN.md — Tier-aware node behavior
- [x] 13-03-PLAN.md — Fix broken tests & consolidate darknet
- [x] 13-04-PLAN.md — Orchestrator refactor into nodes/ package
- [x] 13-05-PLAN.md — Darknet pipeline wiring
- [x] 13-06-PLAN.md — Frontend store cleanup & data flow alignment
- [x] 13-07-PLAN.md — Integration tests for all 4 tier workflows
## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1 | v1.0 | 22/22 | ✅ Complete | 2026-02-23 |
| 6 | v2.0 | 6/6 | ✅ Complete | 2026-02-24 |
| 7 | v2.0 | 4/4 | ✅ Complete | 2026-02-26 |
| 8 | v2.0 | 6/6 | ✅ Complete | 2026-02-28 |
| 9 | v2.0 | 3/3 | ✅ Complete | 2026-02-28 |
| 10 | v2.0 | 4/4 | ✅ Complete | 2026-02-28 |
| 11 | v2.0 | 3/3 | ✅ Complete | 2026-02-28 |

| 13    | v2.1 | 7/7 | ✅ Complete | 2026-03-10 |

Coverage:
- v1 phases: 5 phases, 22 plans
- v2 phases: 6 phases, 28 total plans (28 complete) - v2.0 MILESTONE COMPLETE
- v2.1 phases: 1 phase, 7 plans (7 complete)
- Total: 13 phases, 57 plans (57 complete)

---
*Last updated: 2026-03-10 - Phase 13 Production Hardening complete (7/7 plans)*
