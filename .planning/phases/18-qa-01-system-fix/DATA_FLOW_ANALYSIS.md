# Backend → Frontend Data Flow Analysis

## Phase 1: Event Types Emitted by Backend

### From audit_runner.py (58 events):
| Event Type | Data Fields | Status in Store |
|------------|------------|-----------------|
| phase_start | phase, message | ✓ handled |
| phase_complete | phase, message, pct, summary | ✓ handled |
| phase_error | phase, error | ✓ handled |
| log_entry | timestamp, agent, message, level | ✓ handled |
| agent_personality | agent, context, timestamp, params | ✓ handled |
| screenshot | url, label, index, data | ✓ handled |
| site_type | site_type, confidence | ✓ handled |
| knowledge_graph | graph | ✓ handled |
| dark_pattern_finding | finding (object) | ✓ handled |
| temporal_finding | analysis_type, findings | ✓ handled |
| verdict_technical | verdict (object) | ✓ handled |
| verdict_nontechnical | verdict (object) | ✓ handled |
| dual_verdict_complete | dual_verdict | ✓ handled |
| audit_result | result (full summary) | ✓ handled |
| audit_complete | audit_id, elapsed | ✓ handled |
| audit_error | audit_id, error | ✓ handled |
| stats_update | stats | ✓ handled |
| security_result | category, result | ✓ handled |
| security_module_result | module, result | ✓ handled |
| owasp_module_result | module, vulnerability | ✓ handled |
| ioc_indicator | indicator | ✓ handled |
| mitre_technique_mapped | technique | ✓ handled |
| threat_attribution | apt, techniques | ✓ handled |
| cve_detected | cve | ✓ handled |
| cvss_metrics | metrics, base_score | ✓ handled |
| graph_analysis | analysis | ✓ handled |
| graph_inconsistency | inconsistency | ✓ handled |
| verification_result | result | ✓ handled |
| osint_result | source, result | ✓ handled |
| darknet_threat | threat | ✓ handled |
| marketplace_threat | listing, threat | ✓ handled |
| green_flags | flags, green_flags | ✓ handled |
| agent_performance | performance | ✓ handled |
| navigation_start | url, timestamp | ✓ handled |
| | | |
| **NEW: sequence** | sequence (added to ALL events) | ✓ |

## Phase 2: Frontend Store Field Mappings

| Store Field | From Event | UI Usage |
|-------------|------------|----------|
| status | audit_complete, audit_error | Global state |
| url | audit_result | Header display |
| currentPhase | phase_start, phase_complete | AgentProcState |
| logs | log_entry | SysLogStream |
| screenshots | screenshot | ScreenshotGrid |
| findings | dark_pattern_finding | FindingPanel |
| result.trust_score | audit_result | VerdictPanel |
| result.risk_level | audit_result | VerdictPanel |
| result.narrative | audit_result | Report |
| graphData | knowledge_graph | KnowledgeGraph |
| siteType | site_type | Classification |

## Phase 3: Known Issues

### 3.1 Field Name Mismatches (FIXED ✓)
- `seq` → `sequence` in ProgressEmitter
- Added sequence counter to AuditRunner (after fix)
- VerdictPanel: `executive_summary` → `summary` fallback

### 3.2 Remaining Field Issues
- Need to verify audit_result structure matches types.ts AuditResult interface

### 3.3 Test Environment Issues
- Multiprocessing queue fails in Windows test environment
- Need to run live test or mock the IPC layer

## Next Steps
1. Commit the sequence counter fix (recursion fix applied)
2. Check audit_result data structure matches frontend types
3. Run live test with real site if possible
4. Add any missing defensive checks