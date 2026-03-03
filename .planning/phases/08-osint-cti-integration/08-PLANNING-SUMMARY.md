# Phase 8: OSINT & CTI Integration - Planning Summary

**Planning Date:** 2026-02-27
**Status:** Planning Complete
**Next:** Execute phase via `/gsd:execute-phase 8`

---

## Planning Context

Phase 8 requires implementing OSINT (Open-Source Intelligence) and CTI (Cyber Threat Intelligence) integration into VERITAS to provide multi-source threat verification and entity profiling capabilities.

**Inputs:**
- 08-CONTEXT.md: Context with locked decisions (API tiering, orchestrator design, TTLs, darknet deferred)
- 08-RESEARCH.md: Technical research on standard stack, architecture patterns, pitfalls
- 08-REQUIREMENTS.md: 7 requirements (OSINT-01 through CTI-04, with OSINT-02 deferred)
- ROADMAP.md: Phase 8 success criteria and requirements mapping

---

## Plans Created

### 1. Plan 08-01: Core OSINT Sources (Wave 1)
**File:** `08-01-core-osint-sources.md`

**Objective:** Implement core OSINT intelligence sources (DNS, WHOIS, SSL) with async wrappers and SQLite caching with source-specific TTLs.

**Key Deliverables:**
- OSINT module structure and data types
- DNSSource (async dnspython wrapper)
- WHOISSource (async python-whois wrapper)
- SSLSource (openssl-based async wrapper)
- OSINTCache (source-specific TTL management)
- OSINTCache database model

**Duration:** ~15-20 minutes

### 2. Plan 08-02: OSINT Orchestrator (Wave 2)
**File:** `08-02-osint-orchestrator.md`

**Objective:** Create intelligent OSINT orchestrator with API resource management, rate limiting, and smart fallback to alternative sources.

**Key Deliverables:**
- OSINTOrchestrator (source discovery and management)
- CircuitBreaker (prevents API throttling)
- RateLimiter (per-source RPM/RPH tracking)
- URLVoidSource (API client)
- AbuseIPDBSource (API client)
- Smart fallback to alternative sources

**Duration:** ~20-25 minutes

### 3. Plan 08-03: Reputation & Consensus (Wave 3)
**File:** `08-03-reputation-consensus.md`

**Objective:** Implement source reputation tracking system with dynamic weight adjustment and enhance ConsensusEngine for OSINT multi-source consensus.

**Key Deliverables:**
- SourceReputation (accuracy, FP/FN tracking)
- ReputationManager (weighted consensus calculation)
- Extended ConsensusEngine (OSINT-specific rules)
- Conflict detection and preservation
- Enhanced ConfidenceScorer (OSINT factors)

**Duration:** ~15-20 minutes

### 4. Plan 08-04: CTI-lite Features (Wave 4)
**File:** `08-04-cti-features.md`

**Objective:** Implement CTI-lite features: IOCs detection, threat mapping, and MITRE ATT&CK framework alignment.

**Key Deliverables:**
- IOCDetector (URLs, domains, IPs, emails, hashes)
- MITRE ATT&CK technique mapping
- AttackPatternMapper (pattern-to-AT technique)
- CThreatIntelligence integration class
- Threat attribution suggestions

**Duration:** ~20-25 minutes

### 5. Plan 08-05: Graph Investigator Integration (Wave 5)
**File:** `08-05-graph-integration.md`

**Objective:** Integrate OSINT and CTI capabilities into Graph Investigator, enhancing it with multi-source entity profiles, cross-referencing, and intelligence network generation.

**Key Deliverables:**
- OSINTOrchestrator integration
- _run_osint_investigation() method
- Extended GraphResult (OSINT/CTI fields)
- Knowledge graph OSINT nodes
- Enhanced graph score calculation
- Configuration settings

**Duration:** ~20-30 minutes

---

## Summary Documentation

### PLAN.md
Comprehensive phase overview including:
- Current state vs goal state
- Critical implementation risks
- Locked decisions validation
- Success criteria (must/should/nice have)
- Requirements coverage matrix
- Implementation waves
- Verification criteria
- Next phase transition

### 08-VERIFICATION.md
Quality gate verification including:
- Plan frontmatter validation
- Task specificity confirmation
- Dependency chain verification
- Wave execution structure
- must_haves derived from phase goal
- Requirements coverage matrix
- Locked decisions validation

---

## Requirements Coverage

| Requirement | Coverage |
|-------------|----------|
| OSINT-01 | 📝 Partial (6+sources, extensible to 15+) |
| OSINT-02 | ⏸️ Deferred (premium feature) |
| OSINT-03 | 📝 Complete |
| CTI-01 | 📝 Complete |
| CTI-02 | 📝 Complete |
| CTI-03 | 📝 Complete |
| CTI-04 | 📝 Complete |

**Overall:** 6/7 requirements (86%)
All non-deferred requirements are covered with actionable implementation plans.

---

## Technical Highlights

### Architecture Decisions
1. **Modular OSINT sources:** Each source implements standardized interface with async query() method
2. **Centralized orchestration:** OSINTOrchestrator coordinates all sources with rate limiting
3. **Layered caching:** Source-specific TTLs reduce repeated queries
4. **Dynamic reputation:** Self-correcting system weights reliable sources higher
5. **Conflict preservation:** Contradictory findings preserved with reasoning, not forced consensus

### Innovation Points
1. **Circuit breaker pattern:** Prevents API throttling by marking failing sources
2. **Smart fallback:** Attempts alternative sources in same category on failure
3. **CTI-lite:** Lightweight MITRE ATT&CK integration without full CTI complexity
4. **Backward compatibility:** GraphInvestigator enhanced without breaking existing interface
5. **Graceful degradation:** System continues without problematic sources

### Risk Mitigations
1. **Rate limiting:** Per-source RPM/RPH enforcement prevents quota exhaustion
2. **Async wrappers:** asyncio.run_in_executor() prevents event loop blocking
3. **Consensus threshold:** 3+ source agreement prevents false positives
4. **Cache poisoning:** Source-specific TTLs prevent stale threat intel
5. **API key optional:** Core sources work without configuration

---

## Execution Timeline

**Total Estimated Duration:** ~90-120 minutes (1.5-2 hours)

**Wave Breakdown:**
- Wave 1: ~15-20 min (Core OSINT)
- Wave 2: ~20-25 min (Orchestrator)
- Wave 3: ~15-20 min (Reputation)
- Wave 4: ~20-25 min (CTI-lite)
- Wave 5: ~20-30 min (Integration)

**Parallelization:**
- Waves execute sequentially (dependency chain)
- Within each wave, tasks can execute in parallel

---

## Quality Assurance

### Testing Strategy
Each plan includes success criteria that verify:
- Code compiles and runs without errors
- Async operations don't block event loop
- Cache hit rates meet targets (>60%)
- Consensus rules enforced (3+ source threshold)
- Conflicts detected and preserved
- Graph Investigator integration works end-to-end

### Verification Steps
1. Unit tests for each OSINT source
2. Integration tests for orchestrator
3. Consensus engine validation tests
4. CTI-lite detection accuracy tests
5. End-to-end GraphInvestigator test

---

## Notes for Executors

### Prerequisites
```bash
# Core libraries already installed
# Verify requirements include:
python-whois  # WHOIS lookups
dnspython     # DNS queries
aiohttp       # Async HTTP clients
```

### Environment Variables (Optional)
```bash
# Threat intel API keys (optional - core sources work without)
URLVOID_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here

# Configuration
GRAPH_ENABLE_OSINT=true
GRAPH_ENABLE_CTI=true
```

### Known Limitations
1. **Social media APIs:** Restricted access; framework extensible but requires platform credentials
2. **VirusTotal/Shodan:** Paid services; included in research but not implemented
3. **15+ sources:** 6+ sources implemented; extensible to 15+ via OSINT source pattern
4. **PhishTank:** Research noted 403 error during documentation retrieval

---

## Phase Transition

### From Phase 7 (Scout & Quality)
- ConsensusEngine foundation available
- Quality management patterns established
- Multi-source validation approach familiar

### To Phase 9 (Judge & Orchestrator)
- OSINT/CTI data available for verdict generation
- Source reputation system extensible for dual-tier Judge
- Threat exposure indicators feed into site-type scoring

---

## Post-Phase 8 Enhancements

### Extending to 15+ Sources
The OSINT source pattern enables easy addition of new sources:
1. Create new source class inheriting standardized interface
2. Implement async query() method
3. Register with OSINTOrchestrator._discover_sources()
4. Add to requirements.txt if new dependencies needed

### Social Media Verification
Framework supports social media verification:
1. Create TwitterSource, LinkedInSource, etc.
2. Implement platform-specific API clients
3. Add to ReputationManager tracking

### Premium Darknet Integration
Deferred to post-v2.0:
1. 4th audit tier with darknet monitoring
2. Tor onion crawler using stem library
3. Entity correlation with darknet marketplaces
4. Legal/ethical considerations to be addressed

---

*Planning complete: 2026-02-27*
*Files created: 7 plans (5 individual, 1 phase overview, 1 verification)*
*Ready for execution*
