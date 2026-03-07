# VERITAS Advanced Data Mapping Document
## Complete Integration of Backend Advanced Features to Frontend

> Generated: 2026-03-07
> Purpose: Document all advanced data classes and their WebSocket integration for the VERITAS Agent Theater

---

## Executive Summary

This document maps all advanced data structures from the VERITAS backend agents to their corresponding frontend types and WebSocket events. The system has sophisticated capabilities that are now fully integrated into the theater UI.

---

## 1. Vision Agent Advanced Data

### 1.1 DarkPatternFinding Class
**Location:** `veritas/agents/vision.py`

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `category_id` | string | Dark pattern category ID | `string` | `dark_pattern_finding` |
| `pattern_type` | string | Specific pattern type | `string` | `dark_pattern_finding` |
| `confidence` | float | 0.0 to 1.0 confidence | `number` | `dark_pattern_finding` |
| `severity` | string | low/medium/high/critical | Finding["severity"] | `dark_pattern_finding` |
| `evidence` | string | Description | `string` | `dark_pattern_finding` |
| `screenshot_path` | string | Source screenshot | `string` | `dark_pattern_finding` |
| `raw_vlm_response` | string | Full VLM output | `string?` | `dark_pattern_finding` |
| `model_used` | string | Model that found it | `string?` | `dark_pattern_finding` |
| `fallback_mode` | bool | Used fallback AI? | `boolean?` | `dark_pattern_finding` |

**WebSocket Event:**
```json
{
  "type": "dark_pattern_finding",
  "finding": {
    "category_id": "visual_interference",
    "pattern_type": "misdirected_click",
    "confidence": 0.85,
    "severity": "high",
    "evidence": "Button appears to be X but...",
    "screenshot_path": "/data/screenshots/...",
    "raw_vlm_response": "Full VLM analysis text...",
    "model_used": "nvidia/llama-3.2-nv-vision-90b-instruct",
    "fallback_mode": false
  }
}
```

**Frontend Store:** `darkPatternFindings: DarkPatternFinding[]`

---

### 1.2 TemporalFinding Class
**Location:** `veritas/agents/vision.py` (via `analysis/temporal_analyzer.py`)

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `finding_type` | string | fake_countdown, fake_scarcity, consistent | `string` | `temporal_finding` |
| `value_at_t0` | string | First capture value | `string` | `temporal_finding` |
| `value_at_t_delay` | string | Second capture value | `string` | `temporal_finding` |
| `delta_seconds` | float | Time between captures | `number` | `temporal_finding` |
| `is_suspicious` | bool | Deception detected | `boolean` | `temporal_finding` |
| `explanation` | string | Human-readable | `string` | `temporal_finding` |
| `confidence` | float | 0.0 to 1.0 | `number` | `temporal_finding` |

**WebSocket Event:**
```json
{
  "type": "temporal_finding",
  "finding": {
    "finding_type": "fake_countdown",
    "value_at_t0": "05:00",
    "value_at_t_delay": "05:00",
    "delta_seconds": 30.0,
    "is_suspicious": false,
    "explanation": "Timer remained consistent...",
    "confidence": 0.95
  }
}
```

**Frontend Store:** `temporalFindings: TemporalFinding[]`

---

### 1.3 VisionPassSummary Type
**Location:** Multi-pass vision pipeline tracking

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `pass_num` | number | 1-5 pass number | `number` | `vision_pass_complete` |
| `pass_name` | string | full_page_scan, element_interaction, etc. | `string` | `vision_pass_complete` |
| `findings_count` | number | Findings in this pass | `number` | `vision_pass_complete` |
| `confidence` | number | Pass confidence score | `number` | `vision_pass_complete` |
| `prompt_used` | string | VLM prompt | `string?` | `vision_pass_complete` |
| `model_used` | string | Model for this pass | `string?` | `vision_pass_complete` |

**WebSocket Event:**
```json
{
  "type": "vision_pass_complete",
  "pass": 1,
  "pass_name": "full_page_scan",
  "findings_count": 3,
  "confidence": 0.78,
  "prompt_used": "You are a forensic web auditor...",
  "model_used": "nvidia/llama-3.2-nv-vision-90b-instruct"
}
```

**Frontend Store:** `visionPasses: VisionPassSummary[]`

---

### 1.4 VisionResult Full Structure
**Location:** `veritas/agents/vision.py`

```python
@dataclass
class VisionResult:
    dark_patterns: list[DarkPatternFinding]
    temporal_findings: list[TemporalFinding]
    visual_score: float           # 0.0 to 1.0
    temporal_score: float         # 0.0 to 1.0
    screenshots_analyzed: int
    prompts_sent: int
    nim_calls_made: int
    cache_hits: int
    fallback_used: bool
    vision_passes: list[dict]     # Summary of each pass
```

---

## 2. Scout Agent Advanced Data

### 2.1 ScrollResult Class
**Location:** `veritas/core/types.py`

| Field | Type | Description | Frontend Type |
|-------|------|-------------|---------------|
| `total_cycles` | number | Scroll cycles completed | `number` |
| `stabilized` | bool | Page stabilized | `boolean` |
| `lazy_load_detected` | bool | Found lazy-loaded content | `boolean` |
| `screenshots_captured` | number | Screenshots during scroll | `number` |
| `scroll_states` | ScrollState[] | State history | `ScrollState[]` |

### 2.2 ScrollState Class
| Field | Type | Description |
|-------|------|-------------|
| `cycle` | number | Current scroll cycle |
| `has_lazy_load` | bool | New content detected |
| `last_scroll_y` | number | Scroll position |
| `last_scroll_height` | number | Document height |
| `cycles_without_content` | number | Stabilization counter |
| `stabilized` | bool | Page is stable |

### 2.3 ExplorationResult Class
**Location:** `veritas/core/types.py`

| Field | Type | Description | Frontend Type |
|-------|------|-------------|---------------|
| `base_url` | string | Starting URL | `string` |
| `total_pages` | number | Pages visited | `number` |
| `total_time_ms` | number | Total navigation time | `number` |
| `breadcrumbs` | string[] | URLs visited in order | `string[]` |
| `pages_visited` | PageVisit[] | Visit details | `PageVisit[]` |
| `links_discovered` | LinkInfo[] | Found links | `LinkInfo[]` |

### 2.4 PageVisit Class
| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Visited URL |
| `status` | string | SUCCESS/TIMEOUT/ERROR |
| `screenshot_path` | string | Screenshot location |
| `page_title` | string | Page title |
| `navigation_time_ms` | number | Load time |
| `scroll_result` | ScrollResult | Scroll details |

### 2.5 LinkInfo Class
| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Link URL |
| `text` | string | Anchor text |
| `location` | string | nav/footer/content |
| `priority` | number | Lower = higher priority |
| `depth` | number | Link depth level |

---

## 3. OSINT / Graph Investigator Advanced Data

### 3.1 OSINTResult Class
**Location:** `veritas/osint/types.py`

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `source` | string | OSINT source name | `string` | `osint_result` |
| `category` | OSINTCategory | dns,whois,ssl,threat_intel,reputation,social | `OSINTCategory` | `osint_result` |
| `query_type` | string | Query performed | `string` | `osint_result` |
| `query_value` | string | Value queried | `string` | `osint_result` |
| `status` | SourceStatus | success,error,timeout,rate_limited | `SourceStatus` | `osint_result` |
| `data` | dict | Fetched intelligence | `Record<string, unknown>?` | `osint_result` |
| `confidence_score` | float | 0.0 to 1.0 | `number` | `osint_result` |
| `cached_at` | datetime | Cache timestamp | `string?` | `osint_result` |
| `error_message` | string | Error text | `string?` | `osint_result` |

**WebSocket Event:**
```json
{
  "type": "osint_result",
  "result": {
    "source": "virus_total",
    "category": "threat_intel",
    "query_type": "url_reputation",
    "query_value": "example.com",
    "status": "success",
    "data": {
      "malicious": false,
      "suspicious": false,
      "harmless": true
    },
    "confidence_score": 0.95
  }
}
```

**Frontend Store:** `osintResults: OSINTResult[]`

---

### 3.2 MarketplaceThreatData Class
**Location:** `veritas/osint/types.py`

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `marketplace_name` | string | Marketplace name | `string` | `darknet_threat` |
| `marketplace_type` | DarknetMarketplaceType | marketplace,forum,exchange,hacking,carding,drugs,weapons | `DarknetMarketplaceType` | `darknet_threat` |
| `onion_address` | string | .onion URL | `string` | `darknet_threat` |
| `threat_level` | ExitRiskLevel | none,low,medium,high,critical | `ExitRiskLevel` | `darknet_threat` |
| `confidence` | float | 0.0 to 1.0 | `number` | `darknet_threat` |
| `description` | string | Threat description | `string` | `darknet_threat` |
| `indicators` | string[] | IOC list | `string[]` | `darknet_threat` |
| `source` | string | OSINT source | `string` | `darknet_threat` |

**WebSocket Event:**
```json
{
  "type": "darknet_threat",
  "threat": {
    "marketplace_name": "Empire Market",
    "marketplace_type": "marketplace",
    "onion_address": "empire3...onion",
    "threat_level": "high",
    "confidence": 0.78,
    "description": "URL found in credential theft marketplace",
    "indicators": ["credential", "theft", "dump"],
    "source": "dark_osint_monitor"
  }
}
```

**Frontend Store:** `marketplaceThreats: MarketplaceThreatData[]`

---

### 3.3 IOCIndicator Class
**Location:** `veritas/osint/ioc_detector.py` (via types)

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `type` | IOCType | url,domain,ipv4,ipv6,email,md5,sha1,sha256,filename,onion | `IOCType` | `ioc_indicator` |
| `value` | string | IOC value | `string` | `ioc_indicator` |
| `confidence` | float | 0.0 to 1.0 | `number` | `ioc_indicator` |
| `source` | string | Detection source | `string` | `ioc_indicator` |
| `context` | string | Additional context | `string?` | `ioc_indicator` |

**WebSocket Event:**
```json
{
  "type": "ioc_indicator",
  "ioc": {
    "type": "domain",
    "value": "malicious-suspended-domain.com",
    "confidence": 0.92,
    "source": "phishtank",
    "context": "URL redirect to known phishing site"
  }
}
```

**Frontend Store:** `iocIndicators: IOCIndicator[]`

---

### 3.4 IOCDetectionResult Class
**Location:** `veritas/osint/ioc_detector.py`

| Field | Type | Description | Frontend Type |
|-------|------|-------------|---------------|
| `iocs` | IOCIndicator[] | All IOCs found | `IOCIndicator[]` |
| `threat_score` | float | Aggregate threat score | `number` |
| `attack_patterns` | string[] | MITRE ATT&CK techniques | `string[]` |

**WebSocket Event:**
```json
{
  "type": "ioc_detection_complete",
  "result": {
    "iocs": [...],
    "threat_score": 0.75,
    "attack_patterns": ["T1566", "T1059"]
  }
}
```

**Frontend Store:** `iocDetection: IOCDetectionResult | null`

---

## 4. Judge Agent Dual-Verdict Data

### 4.1 VerdictTechnical Class
**Location:** `veritas/agents/judge/verdict/base.py`

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `cwe_entries` | CWEEntry[] | CWE vulnerabilities | `CWEEntry[]` | `verdict_technical` |
| `cvss_metrics` | CVSSMetric[] | CVSS breakdown | `CVSSMetric[]` | `verdict_technical` |
| `cvss_base_score` | number | CVSS base score 0-10 | `number` | `verdict_technical` |
| `cvss_vector` | string | Full CVSS vector string | `string` | `verdict_technical` |
| `iocs` | IOCIndicator[] | IOCs found | `IOCIndicator[]` | `verdict_technical` |
| `threat_indicators` | string[] | Threat indicators | `string[]` | `verdict_technical` |
| `attack_techniques` | string[] | MITRE ATT&CK IDs | `string[]` | `verdict_technical` |
| `exploitability` | string | NONE/LOW/HIGH | `string` | `verdict_technical` |
| `impact` | string | NONE/LOW/HIGH | `string` | `verdict_technical` |

**WebSocket Event:**
```json
{
  "type": "verdict_technical",
  "technical": {
    "cwe_entries": [
      {"cwe_id": "CWE-79", "name": "Cross-site Scripting", "description": "...", "severity": "HIGH"}
    ],
    "cvss_metrics": [
      {"name": "AV", "value": "N", "severity": "HIGH"}
    ],
    "cvss_base_score": 7.5,
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
    "iocs": [...],
    "attack_techniques": ["T1078"],
    "exploitability": "HIGH",
    "impact": "HIGH"
  },
  "trust_score": 45
}
```

---

### 4.2 VerdictNonTechnical Class
**Location:** `veritas/agents/judge/verdict/base.py`

| Field | Type | Description | Frontend Type | Event Type |
|-------|------|-------------|---------------|------------|
| `risk_level` | string | trusted,probably_safe,suspicious,high_risk,likely_fraudulent | `string` | `verdict_nontechnical` |
| `summary` | string | Plain English summary | `string` | `verdict_nontechnical` |
| `key_findings` | string[] | Main findings | `string[]` | `verdict_nontechnical` |
| `recommendations` | string[] | Actionable advice | `string[]` | `verdict_nontechnical` |
| `warnings` | string[] | Warning messages | `string[]` | `verdict_nontechnical` |
| `green_flags` | GreenFlag[] | Positive indicators | `GreenFlag[]` | `verdict_nontechnical` |
| `simple_explanation` | string | Very simple explanation | `string` | `verdict_nontechnical` |
| `what_to_do` | string[] | User actions | `string[]` | `verdict_nontechnical` |

**WebSocket Event:**
```json
{
  "type": "verdict_nontechnical",
  "verdict": {
    "risk_level": "suspicious",
    "summary": "This site shows several concerning patterns...",
    "key_findings": ["Dark pattern countdown", "New domain registration"],
    "recommendations": ["Be cautious with personal data", "Verify business presence"],
    "warnings": ["Site claims trust without verification"],
    "green_flags": [...],
    "simple_explanation": "We found some things that worry us...",
    "what_to_do": ["Don't enter sensitive info", "Research the company first"]
  },
  "trust_score": 45
}
```

---

### 4.3 DualVerdict Class
Combines both technical and non-technical verdicts:

```typescript
interface DualVerdict {
  technical: VerdictTechnical;
  non_technical: VerdictNonTechnical;
  trust_score: number;
  timestamp: string;
}
```

**WebSocket Event:**
```json
{
  "type": "dual_verdict_complete",
  "dual_verdict": {
    "technical": {...},
    "non_technical": {...},
    "trust_score": 45,
    "timestamp": "2026-03-07T10:30:00Z"
  }
}
```

**Frontend Store:** `dualVerdict: DualVerdict | null`

---

## 5. WebSocket Event Flow

### 5.1 Event Sequence During Audit

```
1. phase_start (init)
2. phase_complete (init)
3. phase_start (scout)
4. screenshot (each screenshot)
5. site_type (detected type)
6. phase_complete (scout)
7. phase_start (security)
8. security_result (each module)
9. phase_complete (security)
10. phase_start (vision)
11. vision_pass_start (pass 1)
12. vision_pass_findings (batch)
13. dark_pattern_finding (each)
14. vision_pass_complete (pass 1)
15. vision_pass_start (pass 2)
16. ... (repeat for passes 3-5)
17. temporal_finding (if temporal enabled)
18. phase_complete (vision)
19. phase_start (graph)
20. osint_result (each OSINT source)
21. darknet_threat (if threats found)
22. ioc_indicator (each IOC)
23. ioc_detection_complete (all IOCs)
24. phase_complete (graph)
25. phase_start (judge)
26. verdict_technical (if technical mode)
27. verdict_nontechnical (or default)
28. dual_verdict_complete (if both)
29. phase_complete (judge)
30. audit_complete
```

---

## 6. Frontend Store State Structure

```typescript
interface AuditStore {
  // Basic State
  auditId: string | null;
  url: string | null;
  tier: string;
  status: "idle" | "connecting" | "running" | "complete" | "error";
  currentPhase: Phase | null;
  phases: Record<Phase, PhaseState>;
  pct: number;

  // Basic Data
  findings: Finding[];
  screenshots: Screenshot[];
  stats: AuditStats;
  logs: LogEntry[];
  siteType: string | null;
  siteTypeConfidence: number;
  securityResults: SecurityResultItem[];
  result: AuditResult | null;
  error: string | null;

  // Advanced Vision Data
  darkPatternFindings: DarkPatternFinding[];
  temporalFindings: TemporalFinding[];
  visionPasses: VisionPassSummary[];

  // Advanced OSINT Data
  osintResults: OSINTResult[];
  marketplaceThreats: MarketplaceThreatData[];
  iocIndicators: IOCIndicator[];
  iocDetection: IOCDetectionResult | null;

  // Advanced Judge Data
  dualVerdict: DualVerdict | null;
}
```

---

## 7. File Structure

```
veritas/
├── agents/
│   ├── vision.py              # DarkPatternFinding, TemporalFinding, VisionResult
│   ├── scout.py               # ScoutResult (contains temporal, forms, etc.)
│   ├── graph_investigator.py  # GraphResult (contains OSINT results)
│   └── judge.py               # JudgeDecision (contains dual verdict modules)
├── osint/
│   └── types.py               # OSINTResult, MarketplaceThreatData
├── core/
│   └── types.py               # ScrollResult, ExplorationResult, SecurityFinding
└── analysis/
    └── temporal_analyzer.py   # TemporalFinding generation

backend/
├── services/
│   └── audit_runner.py        # WebSocket event emission (updated with advanced events)

frontend/
├── src/
│   └── lib/
│       ├── types.ts           # All TypeScript type definitions (updated)
│       └── store.ts           # Zustand store with all handlers (updated)
└── ...
```

---

## 8. Integration Checklist

- [x] TypeScript types added for all advanced data structures
- [x] Frontend store updated with new state fields
- [x] Event handlers added for all advanced events
- [x] Backend audit_runner updated to emit advanced events
- [ ] Frontend components created to visualize advanced data
- [ ] Testing on real audit flows

---

## 9. Next Steps

1. **Visual Components**: Create components to display:
   - DarkPatternFindingDetail card
   - TemporalFinding timeline view
   - VisionPassSummary progress indicator
   - OSINTResult list with confidence bars
   - MarketplaceThreatCard for darknet threats
   - IOCIndicator grid
   - Technical Verdict panel (expert mode)
   - Non-Technical Verdict panel (default mode)

2. **Theater Integration**: Add to the Agent Theater:
   - Vision pass progress overlay
   - OSINT intelligence network visualization
   - Dual-verdict toggle switch
   - Darknet threat alerts

3. **Testing**: Test with real URLs to ensure data flows correctly

---

*Document End*
