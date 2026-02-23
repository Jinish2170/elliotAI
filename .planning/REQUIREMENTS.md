# Requirements: VERITAS Masterpiece Upgrade

**Defined:** 2026-02-23
**Core Value:** Every implementation works at commit time. Build incrementally with explicit tests, verify each phase before proceeding, and deliver a production-ready system suitable for portfolio/job demonstration. Quality over speed - broken code is unacceptable.

## v2 Requirements (Masterpiece Features)

Requirements for Milestone v2.0: Masterpiece-quality features implemented on top of stabilized v1.0 foundation. 36 requirements across 9 categories.

### Vision Agent Enhancement

- [ ] **VISION-01**: Implement 5-pass Vision Agent with multi-pass pipeline
  - Pass 1: Initial visual scan - quick threat detection
  - Pass 2: Dark pattern detection - sophisticated UI manipulation
  - Pass 3: Temporal dynamics - detect dynamic scams
  - Pass 4: Cross-reference with graph - entity verification
  - Pass 5: Final synthesis - multi-pass confidence scoring
- [ ] **VISION-02**: Design sophisticated VLM prompts for each pass
  - Pass-specific prompts optimized for each analysis target
  - Iterative prompt engineering with test dataset validation
  - Confidence normalization across passes
- [ ] **VISION-03**: Implement computer vision temporal analysis
  - SSIM (Structural Similarity) for screenshot comparison
  - Optical flow for detecting dynamic content changes
  - Screenshot diff with fixed viewport alignment
  - Memory monitoring for screenshot resource cleanup
- [ ] **VISION-04**: Build progress showcase emitter for frontend
  - WebSocket event streaming for vision pass progress
  - Event throttling (max 5/sec) to prevent flooding
  - Batch findings for efficient transmission
- [ ] **SMART-VIS-01**: Visual intelligent agent with real-time knowledge verification
  - Cross-reference visual findings with external threat intel
  - Verify suspicious elements against known threat patterns
  - Real-time fact-checking of observed elements
- [ ] **SMART-VIS-02**: Expert-level screenshot auditing capabilities
  - Specialize in detecting sophisticated scams/dark patterns
  - Multi-layer analysis: UI elements + behavioral patterns + context
  - Confidence weighted by external intelligence sources

### Scout/Vision Agent Navigation

- [ ] **SCROLL-01**: Scout/Vision Agent can scroll pages and capture full screenshot series
  - Scroll trigger for lazy loading components
  - Capture screenshots at scroll intervals
  - Handle infinite scroll patterns
- [ ] **SCROLL-02**: Scout can navigate to multiple pages beyond initial landing page
  - Detect and follow navigation links
  - Explore site structure (About, Contact, Privacy, etc.)
  - Limit exploration depth to prevent runaway navigation
- [ ] **SCROLL-03**: Lazy loading detection and handling for complete capture
  - Wait for lazy-loaded content before screenshot
  - Detect dynamic content loading completion
  - Handle AJAX/React/Vue page transitions

### OSINT & Graph Power-Up

- [ ] **OSINT-01**: Implement 15+ OSINT intelligence sources
  - Domain verification (whois, DNS records)
  - SSL certificate validation
  - Malicious URL checking (VirusTotal, PhishTank)
  - Social media presence verification
  - Company database lookups
  - Threat intelligence feeds
- [ ] **OSINT-02**: Build Darknet analyzer (6 marketplaces)
  - Dark marketplace monitoring or threat feed integration
  - Threat attribution suggestions
  - Darknet exposure indicators
- [ ] **OSINT-03**: Enhance Graph Investigator with OSINT integration
  - Multi-source entity profile building
  - Cross-reference findings across sources
  - Confidence scoring for OSINT data
- [ ] **CTI-01**: Social engineering intelligence gathering pattern
  - Mimic OSINT researcher investigation methodology
  - Follow trails across platforms (social media, company databases, threat feeds)
  - Build comprehensive entity profiles
- [ ] **CTI-02**: Multi-source verification and cross-referencing
  - Verify information from 15+ OSINT sources with confidence scoring
  - Cross-reference findings across sources
  - Flag conflicting information for human review
- [ ] **CTI-03**: Cyber Threat Intelligence mini-version (CTI-lite)
  - Indicators of Compromise (IOCs) detection
  - Threat attribution suggestions
  - Attack pattern recognition frameworks (MITRE ATT&CK)
- [ ] **CTI-04**: Smart intelligence network with advanced reasoning
  - Contextual reasoning about collected intelligence
  - Pattern recognition across datasets
  - Generate actionable intelligence reports

### Judge System Dual-Tier

- [ ] **JUDGE-01**: Design dual-tier verdict data classes
  - Technical tier: CWE, CVSS, IOCs for security pros
  - Non-technical tier: plain English, actionable advice for general users
  - DualVerdict dataclass containing both VerdictTechnical and VerdictNonTechnical
- [ ] **JUDGE-02**: Implement site-type-specific scoring strategies
  - 11 site-type strategies (e-commerce, social media, news, etc.)
  - Context-aware scoring based on detected site type
  - Base strategy class with shared configuration
- [ ] **JUDGE-03**: Build Judge Agent with dual-tier generation
  - Single trust score calculation shared between tiers
  - Versioned verdict data classes (V1/V2 transition path)
  - Strategy pattern for site-type-specific logic

### Cybersecurity Deep Dive

- [ ] **SEC-01**: Implement 25+ enterprise security modules
  - OWASP Top 10 compliance checks
  - PCI DSS compliance checks
  - GDPR compliance checks
  - Advanced threat detection patterns
  - Group parallel execution (fast/medium/deep tiers)
- [ ] **SEC-02**: Build darknet-level threat detection
  - Darknet threat feed integration
  - Enterprise-grade security detection
  - CVSS scoring for findings
  - Calibration baseline from known-safe sites

### Smart Orchestrator Framework

- [ ] **ORCH-01**: Advanced time management orchestration
  - Dynamic priority adjustment based on complexity
  - Adaptive timeout strategies (adjust based on page size, complexity)
  - Parallel execution optimization of independent tasks
  - Estimated completion time with countdown for frontend
- [ ] **ORCH-02**: Comprehensive error handling and backup plans
  - Detect agent failures immediately
  - Automatic fallback to alternative analysis methods
  - Graceful degradation - partial results if agent crashes
  - "Show must go on" policy - always return something usable
- [ ] **ORCH-03**: Complexity-aware orchestration
  - Detect when processing time is exceeding thresholds
  - Simplify analysis if time constraints hit (skip optional passes)
  - Prioritize high-value findings over comprehensive coverage
  - Progressive refinement - return initial results, improve over time

### Real-time Progress Updates

- [ ] **PROG-01**: Progressive screenshot streaming to frontend
  - Send screenshots as soon as captured (don't wait for full audit)
  - Thumbnail size for quick delivery, full res on demand
  - Live scroll visualization while Scout explores pages
  - Maintain connection health during long audits
- [ ] **PROG-02**: Real-time pattern/discovery notifications
  - Send findings as soon as detected (don't batch until end)
  - "Live feed" of discovered threats/patterns
  - Color-coded alerts based on severity (red for critical, yellow for warnings)
  - Incremental confidence updates as more analysis completes
- [ ] **PROG-03**: User engagement pacing during long audits
  - Maintain "something happening" signal every 5-10 seconds
  - Agent activity indicators ("👁️ Vision analyzing...", "🔍 OSINT checking...")
  - Progress bars with countdown timers
  - Interesting highlights during waiting periods

### Quality & False Positive Management

- [ ] **QUAL-01**: False positive detection criteria
  - Multi-factor validation (2+ sources must agree before flagging as threat)
  - Historical baseline comparison (is this finding typical for this site type?)
  - Confidence thresholds with explainable reasoning
  - "Review required" category for ambiguous findings
- [ ] **QUAL-02**: Deep statistics and confidence scoring
  - Per-finding confidence score (0-100% with justification)
  - Aggregated trust score with component breakdown
  - Risk level assignment with supporting evidence count
  - Statistical comparison against historical audits
- [ ] **QUAL-03**: Incremental verification and refinement
  - Initial alerts can be downgraded after cross-verification
  - "Likely" → "Confirmed" → "Verified" progression
  - Allow user to mark findings as false positives (learning system)

### Content Showcase & UX

- [ ] **SHOWCASE-01**: Design psychology-driven content flow
  - Gradual reveal patterns for maintaining engagement
  - Agent personality and finding "flexing"
  - Green flag celebration for good results
- [ ] **SHOWCASE-02**: Implement real-time Agent Theater components
  - Event sequencing (sequence numbers) for WebSocket events
  - Frontend reordering buffers for out-of-order events
  - Message acknowledgment and retransmission queue
- [ ] **SHOWCASE-03**: Build Screenshot Carousel with gradual reveal
  - Highlight overlays for detected dark patterns
  - Carousel navigation through screenshot series
  - Comparison views (before/after, with/without findings)
- [ ] **SHOWCASE-04**: Build Running Log with task flexing
  - Log windowing (max 100 entries) with memory monitoring
  - Agent activity streaming with timestamps
  - Task completion celebration and flexing

## v3 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Future Enhancements

- [ ] **PERF-01**: Automated VLM prompt optimization through A/B testing
- [ ] **PERF-02**: Distributed execution for parallel audits
- [ ] **PERF-03**: Machine learning false positive classifier
- [ ] **PERF-04**: Real-time threat feed integration (paid APIs)

## Out of Scope

Explicitly excluded from v2.0. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Authentication system | Public API suitable for thesis/portfolio demo |
| Multi-user/tenant deployment | Single-server deployment sufficient |
| Production hosting infrastructure | Local/dev deployment only |
| Real-time alerting/analytics | Focus on audit execution, not monitoring |
| Alternative AI providers | Sticking with NVIDIA NIM (already working) |
| Port scanning (NMAP) | Requires sudo, not web-app applicable |
| Paid API integrations (Shodan, Censys) | Budget constraints |
| Full automated exploitation | Ethical/legal concerns |
| Tor/onion service scraping | Legal risk |
| Social media login automation | Privacy concerns |
| 3D visualization | Unnecessary for 2D screenshots |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| VISION-01 | Phase 6 | Pending |
| VISION-02 | Phase 6 | Pending |
| VISION-03 | Phase 6 | Pending |
| VISION-04 | Phase 6 | Pending |
| SMART-VIS-01 | Phase 6 | Pending |
| SMART-VIS-02 | Phase 6 | Pending |
| SCROLL-01 | Phase 7 | Pending |
| SCROLL-02 | Phase 7 | Pending |
| SCROLL-03 | Phase 7 | Pending |
| QUAL-01 | Phase 7 | Pending |
| QUAL-02 | Phase 7 | Pending |
| QUAL-03 | Phase 7 | Pending |
| OSINT-01 | Phase 8 | Pending |
| OSINT-02 | Phase 8 | Pending |
| OSINT-03 | Phase 8 | Pending |
| CTI-01 | Phase 8 | Pending |
| CTI-02 | Phase 8 | Pending |
| CTI-03 | Phase 8 | Pending |
| CTI-04 | Phase 8 | Pending |
| JUDGE-01 | Phase 9 | Pending |
| JUDGE-02 | Phase 9 | Pending |
| JUDGE-03 | Phase 9 | Pending |
| ORCH-01 | Phase 9 | Pending |
| ORCH-02 | Phase 9 | Pending |
| ORCH-03 | Phase 9 | Pending |
| PROG-01 | Phase 9 | Pending |
| PROG-02 | Phase 9 | Pending |
| PROG-03 | Phase 9 | Pending |
| SEC-01 | Phase 10 | Pending |
| SEC-02 | Phase 10 | Pending |
| SHOWCASE-01 | Phase 11 | Pending |
| SHOWCASE-02 | Phase 11 | Pending |
| SHOWCASE-03 | Phase 11 | Pending |
| SHOWCASE-04 | Phase 11 | Pending |

**Coverage:**
- v2 requirements: 36 total
- Mapped to phases: 36 (roadmap created)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 - detailed phase plans created (6 phases with implementation strategies)*
