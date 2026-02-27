# Phase 8: OSINT & CTI Integration - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

## Phase Boundary

Deliver open-source intelligence gathering with multi-source cross-referencing for entity verification and threat exposure monitoring. Build intelligent OSINT/CTI orchestrator with API resource management, reputation-based source weighting, and data persistence for complete audit trails.

**Scope:**
- 15+ OSINT intelligence sources (focus on reliable free APIs, not just famous ones)
- Multi-source verification and conflict resolution with contradiction preservation
- Data persistence and caching with source-specific TTLs
- Graph Investigator enhancement with OSINT integration
- Cyber Threat Intelligence mini-version (IOCs, MITRE ATT&CK)
- Smart intelligence network with advanced reasoning

**Out of Scope:** Darknet integration - deferred as premium feature category for future discussion.

---

## Implementation Decisions

### API Tiering Strategy

**Hybrid Access Model:**
- Core OSINT domains work without API keys: DNS records, WHOIS, SSL certificate validation
- Threat intelligence sources require API keys for enhanced tier: VirusTotal, AbuseIPDB, AlienVault, etc.
- Baseline functionality operates without configuration; premium features require keys

**API Research Focus:**
- Prioritize reliable free APIs over famous/paid options
- Research lesser-known but dependable OSINT sources
- Don't focus solely on VirusTotal, PhishTank - find better alternatives

**Intelligent CTI/OSINT Orchestrator:**
- Create dedicated orchestrator class specialized for CTI and OSINT management
- Implements smart fallback: when API fails, intelligently try other sources
- Proper API resource management: queueing, throttling, circuit breaker pattern

**Failure Handling:**
- Graceful degradation: try alternative sources in same category first
- If no alternatives available, continue without the source
- Prominently log all failures for monitoring and debugging

### Cross-Referencing Model

**Dynamic Reputation System:**
- Sources build trust/reputation over time through accurate threat predictions
- Self-correcting system: sources that consistently get predictions right gain weight
- Reputation influences agreement threshold calculations

**Conflict Resolution:**
- Preserve contradictions with detailed reasoning
- Show conflicting results transparently: "Source A says safe (weight 0.9), Source B says malicious (weight 0.7)"
- Let user make final decision based on presented evidence
- No forced consensus - uncertainty is explicit

**Confirmation Thresholds:**
- Primary: 3+ source agreement required for "confirmed" status
- Exception: 2 high-trust sources can also confirm
- High-confidence single-source exception: reputable source + high confidence (e.g., VirusTotal 70+ engines flagged malicious)

### Data Persistence & Caching

**Persistence Strategy:**
- All OSINT results persist in SQLite for complete audit trail and historical analysis
- Single source of truth: OSINT cache table in main audit database
- Enables forensic investigation and time-series threat analysis

**Source-Specific TTLs:**
- WHOIS: 7 days (domain infrastructure changes slowly)
- SSL certificates: 30 days (certificate validity periods)
- Threat intelligence: 4-24 hours based on severity (critical=4h, moderate=12h, low=24h)
- Social media presence: 24 hours (dynamic social landscape)

**Cache Invalidation:**
- Hybrid approach balancing proactive and efficiency
- Automatic refresh on critical findings (new threats, exposure detected)
- Manual refresh available by user request
- Invalidated cache entries trigger fresh OSINT queries

**Storage Architecture:**
- SQLite same database approach for simplicity
- OSINT cache table in main audit DB
- Enables cross-referencing OSINT with audit results in queries

### Claude's Discretion

The following areas are left to Claude's technical judgment during planning and implementation:

- Exact API quota management implementation (queue sizing, backoff algorithms)
- Specific free API sources to research and integrate (reliability criteria)
- Source reputation scoring algorithm (how to measure accuracy over time)
- Cache table schema design (columns, indexes for performance)
- Tor/onion crawler implementation details (for future premium feature)
- OSINT data structures for Graph Investigator integration

---

## Specific Ideas

**User Notes from Discussion:**
- "Find better free API options - don't just focus on this famous ones" - need deep research for lesser-known but reliable sources
- "Create new orchestrator like manager that is intelligent and specially designed for intelligent cti and osint" - dedicated class for this capability
- "No restriction against accessing illegal content as we are verifying not using it - this will help aware people" - darknet for educational/defensive purposes (deferred)
- For darknet: comprehensive monitoring including data breach markets, threat actor forums, marketplace listings
- Hybrid storage approach for darknet data: structured metadata + document storage for raw content
- Entity correlation for darknet matching: build OSINT entity profiles and cross-reference

**No specific UI/UX requirements** - Phase 8 is infrastructure/agent-focused. Frontend integration happens in later phases.

---

## Deferred Ideas

### Darknet Integration (Premium Feature)

**Decision:** Darknet/Tor onion crawling should NOT be added to normal audit workflow.

**Rationale:** Save time in normal audits by making darknet integration a separate premium feature category.

**Deferred for Future Discussion:**
- Detailed design of premium audit tier with darknet monitoring
- Tor onion crawlers using Python's stem library
- Target focus: data breach markets, threat actor forums, marketplace listings
- Deep crawl strategy within target onion services
- Entity correlation: build OSINT entity profiles and match across darknet
- Full context reporting with marketplace names, dates, sample data
- Verification methods: cross-reference, metadata analysis, external validation

**Implementation Context:** User emphasized verification purpose (not consumption) for educational/defensive intent to help protect people. Legal/ethical considerations to be addressed during premium feature planning.

**Expected Outcome:** 4th audit category (premium) with optional darknet integration. Normal audits skip darknet for faster execution.

---

## Success Criteria for Planning

The planner should create executable plans that:

1. **Source Discovery:** Research and identify 15+ reliable free APIs for OSINT (beyond famous ones)
2. **Orchestrator Design:** Create intelligent CTI/OSINT orchestrator with smart resource management and fallback
3. **Reputation System:** Design dynamic reputation tracking for source reliability over time
4. **Cross-Reference:** Implement conflict preservation with reasoning (not forced consensus)
5. **Persistence:** Design SQLite cache schema with source-specific TTL management
6. **Integration:** Enhance Graph Investigator to consume OSINT data for entity verification
7. **CTI Features:** Implement IOCs detection and MITRE ATT&CK framework alignment
8. **Documentation:** Clearly document free API sources, rate limits, and configuration requirements

*Note: Darknet integration is OUT OF SCOPE for Phase 8 - deferred as premium feature discussion.*

---

*Phase: 08-osint-cti-integration*
*Context gathered: 2026-02-27*
