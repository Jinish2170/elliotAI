# VERITAS Advanced Integration - Context for Resume

**Last Updated:** 2026-03-07
**Project Phase:** v2.0 Masterpiece Features - Advanced Data Integration
**Branch:** consolidated/ALL-11-phases-plus-darknet

---

## Project Overview

VERITAS is an autonomous multi-modal forensic web auditing platform with 5 specialized AI agents (Scout, Security, Vision, Graph, Judge). This session focused on integrating **ALL advanced backend data** to the frontend Agent Theater.

### Goal
Get the system backend to emit ALL its advanced process data to the frontend theater, specifically focusing on **premium darknet audit features** that were missing.

---

## What Was Completed This Session ✅

### 1. TypeScript Type System (COMPLETE)

**File:** `frontend/src/lib/types.ts` (958 lines)

All advanced data types now defined:
- Vision Agent: DarkPatternFinding, TemporalFinding, VisionPassSummary
- Scout Agent: ScrollState, ExplorationResult, PageVisit, LinkInfo
- OSINT: OSINTResult (15+ sources), MarketplaceThreatData, IOCIndicator, ThreatAttribution
- Premium Darknet: DarknetAnalysisResult, Tor2WebThreatData, DarknetMarketplaceDetail, MarketplaceListing
- CVE/CVSS: CVEEntry, CVSSMetrics, CVSSMetric
- MITRE ATT&CK: MITRETechnique, TechniqueMatch, ThreatAttribution
- Exploitation: ExploitationAdvisory, AttackScenario, AttackScenarioStep
- Security: OWASPModuleResult, SecurityModuleResult
- Performance: AgentPerformance, TaskMetric
- Knowledge Graph: KnowledgeGraph, KnowledgeGraphNode, GraphEdge, GraphAnalysis
- Judge: VerdictTechnical, VerdictNonTechnical, DualVerdict, CWEEntry

**Premium Category System** with 6 tiers and pricing ($0-$999):
- onion_detection (Standard - Free)
- marketplace_monitoring (Premium - $99)
- credential_leak_check (Premium - $149)
- phishing_kit_detection (Darknet Premium - $499)
- exit_scam_tracking (Darknet Premium - $599)
- attribution_engine (Darknet Premium - $999)

---

### 2. Frontend Store - Basic Integration (COMPLETE)

**File:** `frontend/src/lib/store.ts`

Added state fields and event handlers for:
- darkPatternFindings, temporalFindings, visionPasses
- osintResults, marketplaceThreats, iocIndicators, iocDetection
- dualVerdict (technical + non-technical)

Added processSingleEvent() handlers for:
- dark_pattern_finding, temporal_finding
- osint_result, darknet_threat, ioc_indicator, ioc_detection_complete
- vision_pass_start, vision_pass_findings, vision_pass_complete
- verdict_technical, verdict_nontechnical, dual_verdict_complete

---

### 3. Frontend Store - Advanced Event Handlers (PATCH FILE)

**File:** `frontend/src/lib/store_patch.ts` (140 lines)

Created patch file with additional event handlers that failed to merge directly:
- darknet_analysis_result
- marketplace_threat
- tor2web_anonymous_breach
- exit_scam_detected
- cvss_metrics, cve_detected
- mitre_technique_mapped, threat_attribution, attack_pattern_detected
- exploitation_advisory, attack_scenario
- security_module_result
- knowledge_graph
- site_classification

**STATUS:** These handlers are NOT yet in the main store.ts file. They need to be merged manually.

---

### 4. Backend Event Emission (PARTIAL COMPLETE)

**File:** `backend/services/audit_runner.py`

Added comprehensive advanced event emission in `_handle_result()` method (lines ~700-1100):

**Darknet Events (lines ~760-870):**
- `darknet_analysis_result` - Full darknet analysis
- `marketplace_threat` - Individual marketplace threats
- `tor2web_anonymous_breach` - Tor2Web gateway detection
- `exit_scam_detected` - Exit scam alerts

**CVSS/CVE Events (lines ~880-950):**
- `cvss_metrics` - CVSS v4.0 breakdown
- `cve_detected` - Individual CVE entries with severity

**MITRE ATT&CK Events (lines ~960-1020):**
- `mitre_technique_mapped` - Top 10 ranked techniques
- `threat_attribution` - Threat actor attribution
- `apt_group_attribution` - APT group detection

**Exploitation Events (lines ~1030-1075):**
- `exploitation_advisory` - CRITICAL/HIGH severity remediation

**OSINT Events (lines ~875-935):**
- `osint_result` - All OSINT query results
- `darknet_threat` - Darknet marketplace threats
- `ioc_indicator` - Individual IOC detections
- `ioc_detection_complete` - Aggregate IOC analysis

**Judge Events (lines ~940-970):**
- `verdict_technical` - Expert technical verdict
- `verdict_nontechnical` - User-friendly verdict
- `dual_verdict_complete` - Combined dual verdict

---

## What's Pending 📋

### 1. Merge store_patch.ts into store.ts (HIGH PRIORITY)

**Files:**
- Source: `frontend/src/lib/store_patch.ts`
- Target: `frontend/src/lib/store.ts`

Add the following event handlers to `processSingleEvent()` function before the closing `}`:

```typescript
// Premium Darknet Events
case "darknet_analysis_result": { ... }
case "marketplace_threat": { ... }
case "tor2web_anonymous_breach": { ... }
case "exit_scam_detected": { ... }

// CVSS / CVE Technical Events
case "cvss_metrics": { ... }
case "cve_detected": { ... }

// MITRE ATT&CK Events
case "mitre_technique_mapped": { ... }
case "threat_attribution": { ... }
case "attack_pattern_detected": { ... }

// Exploitation & Scenario Events
case "exploitation_advisory": { ... }
case "attack_scenario": { ... }

// Security Module Results
case "security_module_result": { ... }

// Knowledge Graph Events
case "knowledge_graph": { ... }

// Site Classification Events
case "site_classification": { ... }
```

Also add corresponding state fields to AuditStore interface (line ~86-108):
- darknetAnalysisResult
- marketplaceDetails (or combine with marketplaceThreats)
- tor2WebThreats
- cveEntries
- cvssMetrics
- cvssScore
- mitreTechniques
- threatAttribution
- attackPatterns
- exploitationAdvisories
- attackScenarios
- securityModuleResults
- owaspResults
- agentPerformance
- taskMetrics
- knowledgeGraph
- graphAnalysis
- siteClassification
- businessEntities

---

### 2. Backend Helper Methods (NOT STARTED)

**Location:** End of `backend/services/audit_runner.py`

These helper methods were planned for complex event generation but not implemented:

```python
async def _generate_exploitation_advisories(self, findings: list) -> list:
    """Generate exploitation advisories from high-severity findings"""
    # Generate detailed remediation guidance
    # Map to CVE/CWE database
    # Create attack scenarios
    pass

async def _generate_attack_scenarios(self, cves: list) -> list:
    """Construct attack scenarios from detected CVEs"""
    # Chain attack steps
    # Map to MITRE techniques
    # Estimate complexity and impact
    pass

async def _construct_knowledge_graph(self, results: dict) -> dict:
    """Build knowledge graph from audit results"""
    # Create nodes (domain, entity, ioc, etc.)
    # Create edges with relationships
    # Calculate centrality metrics
    pass

async def _calculate_agent_performance(self, start_time: datetime, results: dict) -> list:
    """Calculate per-agent performance metrics"""
    # Task counts and completion rates
    # Processing times
    # Accuracy scores
    # Resource usage
    pass
```

---

### 3. Store State Initialization (NOT STARTED)

Initialize new state fields in `useAuditStore` creation (line ~135-196):

Add initialization for all new fields to match the interface:
```typescript
darknetAnalysisResult: null,
marketplaceDetails: [],  // or merge with marketplaceThreats
tor2WebThreats: [],
cveEntries: [],
cvssMetrics: [],
cvssScore: null,
mitreTechniques: [],
threatAttribution: null,
attackPatterns: [],
exploitationAdvisories: [],
attackScenarios: [],
securityModuleResults: [],
owaspResults: [],
agentPerformance: [],
taskMetrics: [],
knowledgeGraph: null,
graphAnalysis: null,
siteClassification: null,
businessEntities: [],
```

Also update the `reset()` function (line ~202-250) to reset these new fields.

---

### 4. Frontend UI Components (NOT STARTED)

**Directory:** `frontend/src/components/audit/theater/` (if exists) or `frontend/src/components/`

Components needed to display advanced data:
1. DarknetAnalysisPanel - Darknet risk assessment
2. MarketplaceThreatCards - Individual threat displays
3. Tor2WebAlertBanner - Gateway de-anonymization warning
4. CVSSDashboard - CVSS score breakdown visualization
5. CVEDetailCard - Individual CVE display
6. MITRETechniqueTags - Technique badges
7. ThreatAttributionPanel - APT group attribution
8. ExploitationAdvisoryList - Remediation guidance
9. AttackScenarioFlow - Step-by-step attack visualization
10. SecurityModuleResults - Per-module results
11. OWASPCategorySummary - OWASP Top 10 summary
12. AgentPerformanceChart - Performance metrics visualization
13. KnowledgeGraphViewer - Interactive graph visualization
14. SiteClassificationBadge - Site type indicator
15. BusinessEntityCard - Entity verification display

---

### 5. E2E Testing (NOT STARTED)

Verify complete data flow:
1. Start backend server
2. Run audit with darknet-enabled tier
3. Capture WebSocket events
4. Verify frontend receives all events
5. Check store state updates correctly
6. Test UI component rendering with real data
7. Verify error handling and edge cases

---

## Key File Locations

### Frontend TypeScript
- **Types:** `frontend/src/lib/types.ts` (958 lines - all advanced types)
- **Store:** `frontend/src/lib/store.ts` (651 lines - basic integration)
- **Patch:** `frontend/src/lib/store_patch.ts` (140 lines - pending merge)

### Backend Python
- **Audit Runner:** `backend/services/audit_runner.py` (advanced event emission added)
- **Vision Agent:** `veritas/agents/vision.py`
- **Scout Agent:** `veritas/agents/scout.py`
- **Security Agent:** `veritas/agents/security.py`
- **Graph Agent:** `veritas/agents/graph.py`
- **Judge Agent:** `veritas/agents/judge.py`

### Darknet Modules
- **Darknet Analysis:** `veritas/analysis/security/darknet.py`
- **Onion Detector:** `veritas/darknet/onion_detector.py`
- **Darknet Rules:** `veritas/config/darknet_rules.py`
- **Empire Monitor:** `veritas/osint/sources/darknet_empire.py`
- **Tor2Web Monitor:** `veritas/osint/sources/darknet_tor2web.py`

### CVSS/CVE
- **CVSS Calculator:** `veritas/cwe/cvss_calculator.py`
- **Attack Patterns:** `veritas/osint/attack_patterns.py`
- **Scenario Generator:** `veritas/analysis/scenario_generator.py`

### Planning
- **Plan:** `.planning/IMPLEMENTATION_PLAN.md`
- **Project:** `.planning/PROJECT.md`
- **Masterpiece:** `.planning/VERITAS_MASTERPIECE_PLAN.md`

### Documentation (Created This Session)
- **Complete Reference:** `ADVANCED_DATA_TYPES_COMPLETE.md` (comprehensive type reference)
- **Integration Summary:** `ADVANCED_INTEGRATION_SUMMARY.md` (from previous session)

---

## WebSocket Event Reference

### Basic Events (Already Integrated)
- `phase_start`, `phase_complete`, `phase_error`
- `finding`, `screenshot`, `stats_update`, `log_entry`
- `site_type`, `security_result`, `audit_result`, `green_flags`
- `audit_complete`, `audit_error`

### Advanced Events (Backend Emits, Frontend Partially Handles)
- `dark_pattern_finding` ✅, `temporal_finding` ✅, `vision_pass_*` ✅
- `osint_result` ✅, `darknet_threat` ✅, `ioc_indicator` ✅
- `ioc_detection_complete` ✅
- `verdict_technical` ✅, `verdict_nontechnical` ✅, `dual_verdict_complete` ✅

### Advanced Events (Backend Emits, Frontend Patch File)
- `darknet_analysis_result` ⚠️, `marketplace_threat` ⚠️, `tor2web_anonymous_breach` ⚠️
- `exit_scam_detected` ⚠️, `cvss_metrics` ⚠️, `cve_detected` ⚠️
- `mitre_technique_mapped` ⚠️, `threat_attribution` ⚠️, `attack_pattern_detected` ⚠️
- `exploitation_advisory` ⚠️, `attack_scenario` ⚠️, `security_module_result` ⚠️
- `knowledge_graph` ⚠️, `site_classification` ⚠️

---

## Premium Darknet Feature Details

### Monitored Marketplaces (6)
1. **AlphaBay** (revival) - Major drugs marketplace
2. **Empire** - General marketplace (exit scammed 2020)
3. **Dream** - Long-running marketplace
4. **Hansa** - Taken down by law enforcement
5. **WallStreet** - Crypto-focused
6. **Alpha2** - AlphaBay successor

### Monitored Threat Types
- Phishing kits
- Credential databases
- Credit card dumps
- Identity theft
- Bank account access
- Crypto wallets

### Tor2Web Gateways Monitored
- onion.to
- onion.link
- onion.lat
- onion.cab
- tor2web.org
- (and more)

---

## MITRE ATT&CK Techniques Mapped

| Technique ID | Name | Tactic |
|-------------|------|--------|
| T1566 | Spearphishing | Initial Access |
| T1566.001 | Spearphishing Link | Initial Access |
| T1056 | Input Capture | Credential Access |
| T1056.001 | GUI Keylogger | Credential Access |
| T1204 | User Execution | Execution |
| T1059 | Command Shell | Execution |
| T1059.001 | PowerShell | Execution |
| T1059.003 | CMD | Execution |
| T1106 | Native API | Execution |
| T1190 | Exploit Public-Facing | Initial Access |

---

## Quick Resume Commands

When resuming next session:

```bash
# Check git status
git status

# Check modified files
git diff --stat

# View recent commits
git log --oneline -10

# Run backend (if testing)
cd backend && python -m uvicorn app:main --reload

# Run frontend (if testing)
cd frontend && npm run dev
```

---

## Next Session Priorities (In Order)

1. **HIGH PRIORITY:** Merge `store_patch.ts` event handlers into `store.ts`
2. **HIGH PRIORITY:** Add missing state fields to AuditStore interface
3. **HIGH PRIORITY:** Initialize new state fields in useAuditStore
4. **HIGH PRIORITY:** Update reset() function for new fields
5. **MEDIUM PRIORITY:** Implement backend helper methods
6. **MEDIUM PRIORITY:** Create UI components for advanced data
7. **LOW PRIORITY:** E2E testing and verification

---

## Troubleshooting Notes

### Edit Errors Encountered
- Previous attempts to edit store.ts failed with "old_string missing" errors
- Workaround: Created store_patch.ts as standalone file
- Solution: Manual merge of patch file content needed

### Type System
- Note: Duplicate LogEntry definition exists in types.ts (lines 747-761)
- Clean up: Remove duplicate if found causing issues

### Backend Event Emission
- Events are emitted in `_handle_result()` method around lines 700-1100
- Uses `await send()` pattern for WebSocket emission
- Some events use temporary data structures that need refinement

---

## Summary of Session Work

| Task | Status | Files Modified |
|------|--------|----------------|
| TypeScript type definitions | ✅ Complete | types.ts
| Basic store handlers | ✅ Complete | store.ts |
| Advanced store handlers | ⚠️ Patch file | store_patch.ts
| Backend darknet events | ✅ Complete | audit_runner.py
| Backend CVSS events | ✅ Complete | audit_runner.py |
| Backend MITRE events | ✅ Complete | audit_runner.py |
| Backend exploitation events | ✅ Complete | audit_runner.py |
| Backend OSINT events | ✅ Complete | audit_runner.py |
| Backend judge events | ✅ Complete | audit_runner.py |
| Backend helper methods | ❌ Not started | - |
| Store state initialization | ❌ Not started | - |
| UI components | ❌ Not started | - |
| E2E testing | ❌ Not started | - |

---

**Session Complete.** Advanced type system and basic integration done. Main blocker: merging store_patch.ts into main store.ts file.
