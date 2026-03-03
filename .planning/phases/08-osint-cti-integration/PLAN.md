# Plan: Phase 8 - OSINT & CTI Integration

**Phase ID:** 8
**Milestone:** v2.0 Masterpiece Features
**Depends on:** Phase 6 (Vision Agent Enhancement) - Vision Pass 4 needs cross-reference with OSINT
**Status:** planning
**Created:** 2026-02-27
**Updated:** 2026-02-27

---

## Context

### Current State (Pre-Phase)

**Graph Investigator (`veritas/agents/graph_investigator.py`):**
- Basic WHOIS, DNS, SSL certificate verification (synchronous)
- Tavily search for entity verification
- Simple domain intel gathering
- No external threat intelligence feeds
- No social media presence verification
- No multi-source cross-referencing with conflict detection
- No confidence scoring for OSINT results

**External Intelligence:**
- Tavily search API (optional, may not be configured)
- VirusTotal (placeholder, not implemented)
- No rate limiting or API quota management
- No caching for OSINT results
- No offline threat feeds

**Quality Management:**
- ConsensusEngine exists for Vision/Security multi-source validation
- No OSINT-specific consensus rules
- No dynamic source reputation tracking
- No conflict preservation for OSINT sources

### Goal State (Post-Phase)

**6+ Extensible OSINT Intelligence Sources:**
- Core sources (DNS, WHOIS, SSL) - no API keys required
- Threat intelligence (URLVoid, AbuseIPDB) - with optional API keys
- Extensible framework for adding 9+ future sources (documented in FUTURE_EXPANSION.md)
- Source-specific caching with TTLs (WHOIS 7d, SSL 30d, threat intel 4-24h)

**Intelligent OSINT Orchestrator:**
- Centralized source management and auto-discovery
- Rate limiting with circuit breaker pattern
- Smart fallback to alternative sources on failure
- Graceful degradation continues without problematic sources

**Dynamic Reputation System:**
- Source accuracy tracking over time
- False positive and false negative rates
- Weighted consensus calculation
- Recent performance factors

**Multi-Source Consensus:**
- 3+ source agreement for "confirmed" status
- 2 high-trust source exception
- Conflict detection and preservation
- Explainable confidence scoring

**CTI-lite Features:**
- IOCs (Indicators of Compromise) detection
- MITRE ATT&CK technique mapping
- Threat attribution suggestions
- Pattern recognition for dark patterns

**Enhanced Graph Investigator:**
- OSINTOrchestrator integration
- Multi-source entity profiles
- Knowledge graph with OSINT nodes
- Enhanced graph scoring with OSINT/CTI factors

---

## Plans Overview

Phase 8 is divided into 5 plans organized by execution waves for parallel optimization:

| Plan | Description | Wave | Dependencies | Requirements |
|------|-------------|------|-------------|--------------|
| 08-01 | Core OSINT Sources (DNS, WHOIS, SSL) | 1 | None | OSINT-01 (partial) |
|      | File: 08-01-core-osint-sources.md | | | |
| 08-02 | OSINT Orchestrator with Smart Fallback | 2 | 08-01 | OSINT-01 (partial), CTI-02 (partial) |
|      | File: 08-02-osint-orchestrator.md | | | |
| 08-03 | Source Reputation & Multi-Source Consensus | 3 | 08-02 | OSINT-03, CTI-02 |
|      | File: 08-03-reputation-consensus.md | | | |
| 08-04 | CTI-lite: IOCs & MITRE ATT&CK | 4 | 08-03 | CTI-03 (partial) |
|      | File: 08-04-cti-features.md | | | |
| 08-05 | Graph Investigator Integration | 5 | 08-04 | OSINT-03, CTI-01, CTI-04 |
|      | File: 08-05-graph-integration.md | | | |
| EXT  | Future Expansion APIs Documentation | - | - | OSINT-01 (future) |
|      | File: FUTURE_EXPANSION.md | | | |

---

## Critical Implementation Risks

### 1. API Rate Limiting Risk (CRITICAL)

**Risk:** Multiple OSINT sources have strict rate limits. Uncontrolled queries will exhaust quotas quickly.

**Mitigation:**
- OSINTOrchestrator implements RateLimiter with per-source tracking
- Circuit breaker pattern prevents repeated failures
- Source-specific RPM/RPH limits enforced before queries
- Cache with TTLs reduces repeated queries

### 2. Blocking I/O in Async Context (HIGH)

**Risk:** WHOIS and DNS queries are blocking by default. Direct calls block entire event loop.

**Mitigation:**
- All OSINT sources wrapped in asyncio.run_in_executor()
- Thread pool execution for blocking operations
- Async HTTP clients (aiohttp) for API queries

### 3. Single Source False Positives (HIGH)

**Risk:** Trusting single OSINT source leads to incorrect threat assessments.

**Mitigation:**
- 3+ source agreement required for "confirmed" status
- Conflict detection preserves contradictory findings
- Dynamic reputation weights less reliable sources
- Confidence scoring requires multi-source agreement

### 4. Cache Poisoning/Stale Data (MEDIUM)

**Risk:** Cached OSINT results not expired can lead to outdated threat intelligence.

**Mitigation:**
- Source-specific TTLs (WHOIS 7d, SSL 30d, threat intel 4-24h)
- Automatic cache invalidation on critical findings
- Manual refresh endpoint for user-triggered queries

---

## Locked Decisions (from 08-CONTEXT.md)

These decisions are NON-NEGOTIABLE and must be honored:

1. **API Tiering Strategy:** Core OSINT (DNS, WHOIS, SSL) works without API keys; threat intel needs keys for enhanced tier.

2. **Intelligent CTI/OSINT Orchestrator:** Dedicated orchestrator class with smart fallback to alternative sources.

3. **Dynamic Reputation System:** Sources build trust through accurate predictions; self-correcting over time.

4. **Conflict Resolution:** Preserve contradictions with detailed reasoning; no forced consensus.

5. **Confirmation Thresholds:** 3+ source agreement for "confirmed"; 2 high-trust source exception.

6. **Data Persistence:** All OSINT results persist in SQLite for audit trail.

7. **Source-Specific TTLs:** WHOIS 7d, SSL 30d, threat intel 4-24h based on severity.

8. **Darknet Integration:** DEFERRED as premium feature. Not in Phase 8 scope.

---

## Success Criteria (When Phase 8 Is Done)

### Must Have
1. ✅ 6+ OSINT sources implemented with extensible architecture (DNS, WHOIS, SSL, URLVoid, AbuseIPDB)
2. ✅ OSINTOrchestrator manages sources with rate limiting and fallback
3. ✅ Source reputation tracking with weighted consensus calculation
4. ✅ Multi-source consensus with 3+ source agreement threshold
5. ✅ Conflict detection preserves contradictory findings with reasoning
6. ✅ SQLite OSINTCache with source-specific TTLs
7. ✅ Graph Investigator integrated with OSINT and CTI capabilities
8. ✅ IOCs detection and MITRE ATT&CK technique mapping
9. ✅ FUTURE_EXPANSION.md documents 9+ additional APIs for future implementation

### Should Have
1. ✅ 10+ OSINT sources (progress toward 15+ requirement)
2. ✅ Async wrappers for all sources prevent blocking
3. ✅ Circuit breaker prevents API throttling
4. ✅ CTI-lite analysis generates threat attribution
5. ✅ Knowledge graph nodes for OSINT sources and IOCs
6. ✅ Enhanced graph score includes OSINT/CTI factors

### Nice to Have
1. ✅ 15+ OSINT sources (full requirement)
2. ✅ Social media presence verification
3. ✅ Progress streaming during OSINT queries
4. ✅ Manual refresh endpoint for OSINT data

---

## Requirements Coverage

| Requirement | Status | Plans |
|-------------|--------|-------|
| OSINT-01 | 📝 Partially Rescoped | 08-01, 08-02 (6+ extensible sources with 9+ future APIs documented in FUTURE_EXPANSION.md) |
| OSINT-02 | ⏸️ Deferred | Darknet deferred as premium feature |
| OSINT-03 | 📝 Covered | 08-05 (Graph Investigator integration) |
| CTI-01 | ⚠️ Partial | 08-05 (entity profile building within GraphInvestigator, but cross-platform social engineering intelligence gathering is future enhancement - see 08-05 notes) |
| CTI-02 | 📝 Covered | 08-02, 08-03 (multi-source verification) |
| CTI-03 | 📝 Covered | 08-04 (IOCs detection, MITRE ATT&CK) |
| CTI-04 | 📝 Covered | 08-05 (smart intelligence network) |

**Excluded:**
- OSINT-02: Darknet analyzer - explicitly deferred as premium feature per 08-CONTEXT.md

**Notes:**

**Fixed Issues (Revision Phase 08):**

**Blocker 1 - OSINT-01 source requirement gap:**
- **Issue:** Original requirement "15+ OSINT intelligence sources" but only 5 sources planned
- **Resolution:** Re-scoped to "6+ extensible sources with document 9+ future APIs"
- Changes:
  - Added FUTURE_EXPANSION.md documenting 9 verified free API targets
  - Updated success criteria to include FUTURE_EXPANSION.md requirement
  - Framework designed for easy extension (OSINTOrchestrator auto-discovery pattern)
  - Marked OSINT-01 as "Partially Rescoped" in Requirements Coverage

**Blocker 2 - CTI-01 social engineering pattern gap:**
- **Issue:** CTI-01 requires "social engineering intelligence gathering pattern (follow trails across platforms, build entity profiles)" but 08-05 only implemented IOC detection and MITRE ATT&CK mapping
- **Resolution:** Marked CTI-01 as "PARTIAL" with detailed gap analysis
- Acknowledged in 08-05:
  - Entity profile building within GraphInvestigator IS implemented
  - Cross-referencing OSINT sources for entity data IS implemented
  - Knowledge graph entity correlation IS implemented
  - NOT implemented: Cross-platform entity tracking (business registries, social networks, etc.)
  - Gap justification documented (limited free social verification APIs per RESEARCH.md)

**Blocker 3 - Task format conversion:**
- **Issue:** Plans used YAML `tasks: [...]` format lacking XML `<task>` elements with verification
- **Resolution:** Converted all 5 plans (08-01 through 08-05) to GSD XML format
- Changes:
  - Each task now has `<task><description><files><verification><done>` structure
  - Frontmatter updated with correct `tasks: N` count
  - Added `must_haves` section with truths, artifacts, key_links
  - Verification criteria now explicit within each task

**Warnings (noted but not fixed in this revision):**

**Warning 1 - Task count exceeded:**
- Plan 08-05 has 7 tasks, above recommended 2-3 threshold
- Noted in frontmatter with explanation
- Consider splitting into 08-05a (integration setup) and 08-05b (graph enhancement) if execution priority allows

**Warning 2 - Task count above limit:**
- Plan 08-01 has 6 tasks, above recommended limit
- Tasks are logically grouped (types, 3 sources, cache, model)
- Could consider splitting if needed for parallelization

**OSINT-01 Re-scoping:**
Original requirement: "15+ OSINT intelligence sources"
Current implementation: 6 sources (DNS, WHOIS, SSL, URLVoid, AbuseIPDB, 1 placeholder for future)
Gap: 9 additional sources needed

**Resolution:**
1. Implement extensible OSINT source framework in 08-01 and 08-02
2. Document 9+ verified free APIs in FUTURE_EXPANSION.md
3. Mark OSINT-01 as "Partially Rescoped" with clear TODOs for future expansion

---

## Implementation Waves

### Wave 1: Core OSINT Infrastructure (Plan 08-01)
**Dependencies:** None

Create foundational OSINT module structure:
- OSINT data types (OSINTResult, SourceConfig, enums)
- Async DNS lookup source
- Async WHOIS lookup source
- SSL certificate validation
- OSINT cache with source-specific TTLs
- OSINTCache database model

**Duration:** ~15-20 minutes

### Wave 2: OSINT Orchestrator (Plan 08-02)
**Dependencies:** 08-01

Intelligent source management:
- OSINTOrchestrator with auto-discovery
- Rate limiter with per-source tracking
- Circuit breaker for failing sources
- Smart fallback to alternative sources
- URLVoid API integration
- AbuseIPDB API integration

**Duration:** ~20-25 minutes

### Wave 3: Reputation & Consensus (Plan 08-03)
**Dependencies:** 08-02

Multi-source validation:
- SourceReputation tracking
- ReputationManager with weighted consensus
- Extended ConsensusEngine for OSINT
- Conflict detection and preservation
- Enhanced ConfidenceScorer for OSINT

**Duration:** ~15-20 minutes

### Wave 4: CTI-lite Features (Plan 08-04)
**Dependencies:** 08-03

Threat intelligence:
- IOCs detector (URLs, domains, IPs, emails, hashes)
- MITRE ATT&CK technique mapping
- Threat attribution suggestions
- CThreatIntelligence integration class

**Duration:** ~20-25 minutes

### Wave 5: Graph Investigator Integration (Plan 08-05)
**Dependencies:** 08-04

End-to-end integration:
- OSINTOrchestrator integration into GraphInvestigator
- OSINT investigation method
- Extended GraphResult with OSINT/CTI fields
- Knowledge graph OSINT nodes
- Enhanced graph score calculation
- Configuration settings

**Duration:** ~20-30 minutes

**Total Estimated Duration:** ~90-120 minutes (1.5-2 hours)

---

## Verification Criteria

After completing all plans, verify:

1. **Core OSINT:**
   - [ ] DNS, WHOIS, SSL sources return valid data
   - [ ] Async wrappers don't block event loop
   - [ ] Cache hit rates >60% on repeated queries

2. **Orchestration:**
   - [ ] Rate limiter enforces RPM/RPH limits
   - [ ] Circuit breaker opens after 5 failures
   - [ ] Fallback tries 2 alternative sources on failure

3. **Reputation & Consensus:**
   - [ ] 3+ source agreement yields "confirmed" status
   - [ ] 2 high-trust sources can confirm
   - [ ] Conflicts preserved with reasoning

4. **CTI-lite:**
   - [ ] IOCs detected in page content
   - [ ] MITRE ATT&CK techniques matched
   - [ ] Threat attribution generated

5. **Graph Integration:**
   - [ ] OSINT data added to knowledge graph
   - [ ] Graph score incorporates OSINT/CTI factors
   - [ ] GraphInvestigator end-to-end works

---

## Next Phase

Phase 9: Judge System & Orchestrator
- Dual-tier verdict data classes
- Site-type-specific scoring strategies (11 strategies)
- Judge Agent with dual-tier generation
- Advanced time management orchestration
- Comprehensive error handling and backup plans

---

*Plan updated: 2026-02-27*
*Based on 08-CONTEXT.md and 08-RESEARCH.md*
*Phase 8 ready for execution*
