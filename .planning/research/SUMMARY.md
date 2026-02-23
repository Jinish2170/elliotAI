# Research Summary: VERITAS v2.0 Masterpiece Features

**Project:** VERITAS Masterpiece Upgrade - v2.0 Masterpiece Features
**Domain:** Add masterpiece features to existing VERITAS forensic web auditing platform
**Researched:** 2026-02-23
**Confidence:** MEDIUM-HIGH

---

## Executive Summary

VERITAS v2.0 is an enhancement project building on a production-ready foundation from v1.0 Core Stabilization. The platform is an autonomous 5-agent forensic web auditing system (Scout, Security, Vision, Graph, Judge) that analyzes websites for trust, safety, dark patterns, and security vulnerabilities. Expert sources indicate this domain is best built using specialized AI agents with multi-modal analysis pipelines, layered async execution patterns, and real-time progress telemetry for engaging presentation.

Based on combined research, the recommended approach is **minimal technical complexity with maximum feature sophistication**. The existing stack (80% of needed libraries already installed) supports all masterpiece features with only 5 new Python packages. Critical risks center on three areas: computer vision image alignment causing false positives, WebSocket event flooding breaking the frontend, and API rate limits truncating OSINT data. These are actively mitigated through image normalization, event throttling, and tiered async execution patterns. The project requires a 5-phase implementation strategy starting with Vision Agent (highest complexity and visual payoff), followed by OSINT integration (data foundation for other agents), Judge system (requires OSINT data), Security modules (OWASP compliance), and finally Showcase components (requires all data streams).

---

## Key Findings

### Recommended Stack

**Only 5 new Python packages required:**

| Feature | New Packages | Existing Reused |
|---------|--------------|-----------------|
| Vision Agent (5-pass pipeline, CV temporal analysis) | opencv-contrib-python>=4.9.0.80, scikit-image>=0.24.0 | pillow, pytesseract, NVIDIA NIM |
| OSINT Integration (15+ intelligence sources) | requests>=2.31.0, cryptography>=42.0.0, beautifulsoup4>=4.12.0 | python-whois, dnspython, aiohttp |
| Judge System (dual-tier verdict, 11 site-type strategies) | NONE | pydantic, langchain, langgraph, NVIDIA NIM |
| Security Modules (25+ enterprise detectors, CVSS scoring) | sqlparse>=0.5.0, cvss>=2.4.0 | requests, aiohttp, beautifulsoup4 |
| Showcase (Agent Theater, Screenshot Carousel, Running Log) | NONE | framer-motion 12.34.0, lucide, radix, recharts, zustand |

**Why This Stack:** Minimal dependencies (200MB additional), leverages existing v1.0 foundation, no new frontend libraries needed, all libraries are production-age (10+ years stable).

---

### Critical Architecture Changes

**New Pattern 1: Agent Extension Pattern**
- Extend existing VisionAgent, GraphInvestigator, SecurityAgent, JudgeAgent rather than refactoring
- Preserve v1.0 architecture stability while adding capabilities
- Example: `EnhancedVisionAgent(VisionAgent)` adds 5-pass pipeline and CV temporal analysis

**New Pattern 2: Tiered Async Execution**
- Group async operations by timeout priority to maximize parallelism
- Critical for OSINT sources with varying response times (VirusTotal 4 req/min vs DNS fast checks)
- Example: fast tier (5s), medium tier (10s), slow tier (30s) with asyncio.gather

**Anti-Pattern to Avoid: Synchronous Remote API Calls**
- All OSINT and security module HTTP calls must use aiohttp
- Prevents blocking entire audit pipeline

**New Components:**
- `OSIntelligenceEngine`: 15+ intelligence sources aggregation
- `TemporalComputerVision`: SSIM, optical flow, screenshot diff
- `ProgressEmitter`: Real-time WebSocket event broadcasting
- `ComprehensiveSecurityAudit`: 25+ OWASP/PCI compliance detectors

---

### Feature Overview

**Table Stakes (Missing = Product Feels Incomplete):**
| Feature | Category | Complexity |
|---------|----------|------------|
| Real-time audit progress showcase | Showcase | Low |
| Screenshot visualization with highlights | Showcase | Medium |
| Domain verification (whois, DNS) | OSINT | Low |
| SSL certificate validation | OSINT | Low |
| Malicious URL checking (VirusTotal) | OSINT | Medium |
| SQL injection detection | Security | High |
| XSS detection | Security | Medium |
| Security headers analysis | Security | Low |
| Dark pattern detection | Vision | High |
| Dual-tier verdict (technical + non-technical) | Judge | Medium |

**Differentiators (Set VERITAS Apart):**
| Feature | Value | Complexity |
|---------|--------|------------|
| 5-pass Vision Agent pipeline | 95%+ dark pattern detection | High |
| 15+ OSINT intelligence sources | Deep entity verification | Medium |
| Darknet exposure monitoring | Unique threat surface | High |
| 11 site-type-specific strategies | Context-aware scoring | Medium |
| Computer vision temporal analysis | Detects dynamic scams | High |
| Psychology-driven agent showcase | Engaging presentation | Medium |

**Anti-Features:**
- Port scanning (NMAP) - requires sudo, not web-app applicable
- Paid API integrations (Shodan, Censys) - budget constraints
- Full automated exploitation - ethical/legal concerns
- Tor/onion service scraping - legal risk
- Social media login automation - privacy concerns
- 3D visualization - unnecessary for 2D screenshots
- Real-time threat alerting - out of thesis scope
- Multi-user authentication - single-server deployment only

---

### Critical Pitfalls

**Top 3 Critical Pitfalls:**

1. **Computer Vision Image Alignment**
   - **Risk:** SSIM and difference masks produce false positives/negatives when screenshots differ in resolution or crop
   - **Prevention:** Fixed viewport (1920x1080), image resize normalization, template matching alignment with `findHomography()`, focus CV on known element areas
   - **Detection:** SSIM < 0.7 on identical pages, diff masks show header/footer changes

2. **WebSocket Event Flooding**
   - **Risk:** 5-pass Vision Agent emits 50+ findings per pass, causing browser crashes, memory leaks
   - **Prevention:** Event throttling (max 5/sec), batch findings, progress summaries, debouncing, queue management with `asyncio.sleep(0.2)`
   - **Detection:** UI freezes, animation queues stack, WebSocket drops

3. **API Rate Limiting (OSINT Sources)**
   - **Risk:** VirusTotal (4 req/min), PhishTank (1 req/sec) block requests, causing incomplete data
   - **Prevention:** Document rate limits, per-source request queues, response caching (24-72h), tiered fallback, staggered execution
   - **Detection:** Rate-limited placeholders in reports

**Additional Moderate Pitfalls:**
- VLM Prompt Engineering Iteration - Initial prompts produce low-quality detections
- LangGraph State Explosion - State objects grow unbounded with findings
- Dual-Tier Verdict Inconsistency - Technical and non-technical verdicts disagree

---

## Implications for Roadmap

Based on combined research, the most effective approach is **5 sequential phases** reflecting feature dependencies, architectural complexity, and risk mitigation order.

### Phase 1: Vision Agent Enhancement (Weeks 1-2)
**Rationale:** Highest complexity with immediate visual payoff. Vision Agent output feeds all downstream features. Starting first provides maximum time for VLM prompt iteration.

**Delivers:**
- 5-pass Vision Agent with multi-modal analysis pipeline
- Computer vision temporal analysis (SSIM, optical flow, screenshot diff)
- Fixed viewport screenshot capture to prevent CV alignment issues
- Progress emitter skeleton for real-time showcases

**Features:** Dark pattern detection, screenshot visualization foundation, 5-pass pipeline, CV temporal analysis

**Must Avoid:** CV temporal false positives (implement image alignment from day one), VLM prompt iteration (start with 3 passes, iterate with labeled test pages), Progress emitter floods frontend (throttle/batch from day one)

**Research Flag:** Needs `/gsd:research-phase` for VLM prompt engineering patterns—highly iterative and domain-specific.

---

### Phase 2: OSINT Integration (Week 3)
**Rationale:** Foundation for downstream agents. API rate limiting is a critical pitfall requiring careful architecture. Starting second provides OSINT data for Phase 3-5.

**Delivers:**
- OSIntelligenceEngine with 15+ intelligence sources (start with 5, add incrementally)
- Tiered async execution (fast/mid/slow groups) to handle varying response times
- Per-source request queues and caching to prevent rate limit blocking
- Enhanced Graph Investigator with OSINT entity nodes
- Darknet threat feed integration (no direct scraping—legal risk)

**Features:** Domain verification, SSL validation, malicious URL checking, 15+ OSINT sources, darknet exposure monitoring

**Must Avoid:** API rate limits (document limits, implement caching, use async queues), Darknet legal concerns (use threat feeds only, no Tor/onion scraping)

**Research Flag:** NO `/gsd:research-phase` needed. OSINT APIs are well-documented and patterns from ARCHITECTURE.md provide sufficient guidance.

---

### Phase 3: Judge System Dual-Tier (Week 4)
**Rationale:** Depends on OSINT data from Phase 2. Requires minimal new tech stack. Site-type detection needs LLM + heuristics fallback.

**Delivers:**
- Dual-tier verdict data classes (technical + non-technical)
- 3-5 site-type-specific scoring strategies (e-commerce, financial, portfolio)
- Site type detection (LLM + heuristics fallback)
- Non-technical verdict templates with psychological explanations
- Unified score source to ensure tier consistency

**Features:** Dual-tier verdict, 11 site-type strategies (start with 3-5)

**Must Avoid:** Dual-tier inconsistency (unit tests for score alignment), Site type detection accuracy < 70% (use LLM + heuristics fallback)

**Research Flag:** Needs `/gsd:research-phase` for site-type detection strategy patterns. Context-aware scoring for different site types is domain-specific with limited documented patterns.

---

### Phase 4: Cybersecurity Deep Dive (Week 5)
**Rationale:** Depends on website crawling data from all prior phases. Security module results feed into Judge verdict scores. High module count requires time-boxed tiered approach.

**Delivers:**
- 10+ OWASP security modules (start with OWASP Top 10)
- SQL injection detection (sqlparse), XSS detection (beautifulsoup4), security headers analysis (requests)
- CVSS 3.1 scoring integration for vulnerability severity
- Darknet threat detection (correlate OSINT darknet data with security findings)
- Tiered timeout approach (fast groups vs. slow modules)

**Features:** SQL injection, XSS, security headers, 25+ enterprise security modules (start with 10)

**Must Avoid:** 25+ modules take too long (tiered timeout approach, prioritize OWASP Top 10), CVSS scoring complexity (start simplified, iterate later)

**Research Flag:** NO `/gsd:research-phase` needed. OWASP Top 10 patterns are well-documented. CVSS library provides standard scoring.

---

### Phase 5: Content Showcase & UX (Week 6)
**Rationale:** Depends on all data streams from prior phases. Frontend is fully equipped with required libraries. Final phase ensures complete system before showcase polish.

**Delivers:**
- Agent Theater with all 5 agents (Scout, Security, Vision, Graph, Judge)
- Screenshot Carousel with highlight overlays and gradual reveal
- Running Log with agent task flexing and personality
- Real-time progress showcase consuming WebSocket events from Phase 1 ProgressEmitter
- Complete integration of all showcase components

**Features:** Real-time progress showcase, screenshot visualization, psychology-driven agent showcase, gradual screenshot reveal

**Must Avoid:** Carousel coordinates don't align (store dimensions, convert to percentages), Agent Theater animations lag (test with 100+ events, batch from Phase 1)

**Research Flag:** NO `/gsd:research-phase` needed. Framer Motion patterns are standard. Component architecture from ARCHITECTURE.md provides sufficient guidance.

---

### Research Flags

**Phases needing `/gsd:research-phase`:**

| Phase | Research Needed | Why |
|-------|-----------------|-----|
| Phase 1: Vision | VLM prompt engineering patterns | Highly iterative, domain-specific |
| Phase 3: Judge | Site-type detection strategy patterns | Context-aware scoring is specialized |

**Phases with standard patterns (skip research):**

| Phase | Why Skip |
|-------|----------|
| Phase 2: OSINT | API patterns are standard, tiered async execution documented |
| Phase 4: Security | OWASP Top 10 well-documented, CVSS library standard |
| Phase 5: Showcase | Framer Motion patterns are standard, React patterns mature |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | VERITAS v1.0 foundation is excellent. Only 5 new packages, all are industry standards (10+ years production use). |
| Features | **MEDIUM-HIGH** | Table stakes and differentiators well-researched from OWASP, CVSS sources. Feature dependencies clearly mapped. |
| Architecture | **HIGH** | Agent Extension Pattern and Tiered Async Execution are solid patterns. Integration points clear. |
| Pitfalls | **HIGH** | Three critical pitfalls have detailed prevention and detection strategies. Moderate/minor pitfalls documented comprehensively. |

**Overall Confidence: MEDIUM-HIGH**

Research is actionable for planning. All major risks have mitigation strategies. Only two areas require phase-specific deep research (VLM prompts, site-type detection)—both are expected iterative processes.

**Gaps Identified:**

| Gap | Impact | Mitigation |
|-----|--------|------------|
| VLM prompt quality uncertain | Could reduce dark pattern detection accuracy below 95% goal | Plan for prompt iteration in Phase 1, create 50 labeled test pages early |
| Site-type detection accuracy unknown | Could produce incorrect scoring | Use LLM + heuristics fallback, add confidence scores |
| API rate limits undocumented | Could trigger blocking and incomplete data | Implement caching from day one, log API responses |

---

## Sources

### Research Files Synthesized
- **STACK.md**: Stack additions, package recommendations, integration points, version verification
- **FEATURES.md**: Table stakes, differentiators, anti-features, feature dependencies, MVP prioritization
- **ARCHITECTURE.md**: Component boundaries, Agent Extension Pattern, Tiered Async Execution, anti-patterns
- **PITFALLS.md**: Critical/moderate/minor pitfalls with prevention strategies, phase-specific warnings
- **PROJECT.md**: VERITAS v1.0 foundation, existing capabilities, implementation timeline, constraints

### External Sources Referenced
- **OWASP Top 10 2021**: Security module categories for Phase 4
- **CVSS v3.1**: Vulnerability scoring standard for Phase 4
- **OpenCV documentation**: SSIM, image alignment, coordinate systems for Phase 1
- **FastAPI WebSocket best practices**: Event throttling, message limits for Phase 5
- **VirusTotal API documentation**: Rate limits, quotas for Phase 2
- **LangGraph documentation**: State machine patterns, checkpointing for Phase 1

---

*Synthesized: 2026-02-23*
*Next Step: Requirements definition and roadmap creation*
