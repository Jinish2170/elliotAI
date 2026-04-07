# VERITAS Advanced Data Types - Complete Reference

**Documentation Date:** 2026-03-07
**Project:** VERITAS v2.0 Masterpiece Upgrade
**Status:** Advanced Type System Complete, Integration In Progress

---

## Executive Summary

This document provides a comprehensive reference for all advanced data types in the VERITAS system. The system implements a sophisticated forensic web auditing platform with 5 specialized AI agents (Scout, Security, Vision, Graph, Judge) and supports deep threat intelligence including darknet marketplace monitoring, CVE/CVSS scoring, MITRE ATT&CK framework mapping, and knowledge graph construction.

---

## Table of Contents

1. [Vision Agent Types](#vision-agent-types)
2. [Scout Agent Types](#scout-agent-types)
3. [OSINT / Graph Investigator Types](#osint--graph-investigator-types)
4. [Premium Darknet Feature Types](#premium-darknet-feature-types)
5. [CVE / CVSS Types](#cve--cvss-types)
6. [MITRE ATT&CK Framework Types](#mitre-attack-framework-types)
7. [Exploitation & Scenario Types](#exploitation--scenario-types)
8. [Security Module Result Types](#security-module-result-types)
9. [Agent Performance Types](#agent-performance-types)
10. [Knowledge Graph Types](#knowledge-graph-types)
11. [Judge Dual-Verdict Types](#judge-dual-verdict-types)
12. [Site Classification Types](#site-classification-types)
13. [WebSocket Event Mapping](#websocket-event-mapping)
14. [Integration Status](#integration-status)

---

## Vision Agent Types

### DarkPatternFinding

Advanced dark pattern detection with full model metadata and confidence scoring.

```typescript
interface DarkPatternFinding {
  category_id: string;         // e.g., "visual_interference", "false_urgency"
  pattern_type: string;        // e.g., "misdirected_click", "fake_countdown"
  confidence: number;          // 0.0 to 1.0 - AI detection confidence
  severity: "low" | "medium" | "high" | "critical";
  evidence: string;            // Description of what was found
  screenshot_path: string;     // Which screenshot contains the finding
  raw_vlm_response?: string;   // Full VLM response for audit trail
  model_used?: string;         // Which AI model produced this finding
  fallback_mode?: boolean;     // True if using fallback AI instead of primary NIM VLM
}
```

**Category IDs Supported:**
- `visual_interference` - Button manipulation, hidden elements, misleading proximity
- `false_urgency` - Fake timers, artificial scarcity, countdown fraud
- `obstruction` - Hard to cancel, difficult navigation, forced flows
- `sneak_into_cart` - Pre-selected purchases, hidden add-ons
- `misdirection` - Visual flow manipulation, attention hijacking
- `social_proof` - Fake reviews, manufactured testimonials

---

### TemporalFinding

Time-based deception detection comparing screenshots at different time intervals.

```typescript
interface TemporalFinding {
  finding_type: string;        // "fake_countdown", "fake_scarcity", "consistent"
  value_at_t0: string;         // Timer/counter value at first capture
  value_at_t_delay: string;    // Timer/counter value at second capture
  delta_seconds: number;       // Time between captures
  is_suspicious: boolean;      // True if deception detected
  explanation: string;         // Human-readable explanation of findings
  confidence: number;          // 0.0 to 1.0
}
```

**Detection Methods:**
- SSIM (Structural Similarity Index) comparison
- Optical flow analysis for element movement
- OCR text extraction for timer values
- Temporal consistency verification

---

### VisionPassSummary

Multi-pass vision analysis tracking with individual pass metrics.

```typescript
interface VisionPassSummary {
  pass_num: number;
  pass_name: string;           // One of the 5 passes below
  findings_count: number;
  confidence: number;          // Overall confidence for this pass
  prompt_used?: string;        // VLM prompt used for this pass
  model_used?: string;         // AI model used (NIM/fallback)
}
```

**Vision Pass Pipeline (5-Pass Analysis):**
1. **full_page_scan** - Complete visual overview, layout analysis
2. **element_interaction** - Button/form manipulation detection
3. **deceptive_patterns** - Dark pattern specific analysis
4. **content_analysis** - Trustworthiness signals, legitimacy cues
5. **screenshot_temporal** - Before/after comparison, time-based deception

---

## Scout Agent Types

### ScrollState

Intelligent scrolling state with lazy-load detection.

```typescript
interface ScrollState {
  cycle: number;               // Current scroll cycle
  has_lazy_load: boolean;      // Lazy loading detected
  last_scroll_y: number;       // Last Y position scrolled
  last_scroll_height: number;  // Page height before scroll
  cycles_without_content: number;
  stabilized: boolean;         // No more content loaded
}
```

### ScrollResult

Complete scrolling results for a page.

```typescript
interface ScrollResult {
  total_cycles: number;
  stabilized: boolean;
  lazy_load_detected: boolean;
  screenshots_captured: number;
  scroll_states: ScrollState[]; // Full scroll history
}
```

### PageVisit

Individual page visit with navigation metrics.

```typescript
interface PageVisit {
  url: string;
  status: "SUCCESS" | "TIMEOUT" | "ERROR";
  screenshot_path?: string;
  page_title: string;
  navigation_time_ms: number;
  scroll_result?: ScrollResult;
}
```

### ExplorationResult

Multi-page exploration summary with breadcrumbs.

```typescript
interface ExplorationResult {
  base_url: string;
  total_pages: number;
  total_time_ms: number;
  breadcrumbs: string[];       // Navigation path
  pages_visited: PageVisit[];
  links_discovered: LinkInfo[];
}
```

### LinkInfo

Discovered link metadata with priority ranking.

```typescript
interface LinkInfo {
  url: string;
  text: string;
  location: "nav" | "footer" | "content";
  priority: number;            // Lower = higher priority
  depth: number;               // Navigation depth
}
```

---

## OSINT / Graph Investigator Types

### OSINTCategory

Open Source Intelligence query categories.

```typescript
type OSINTCategory =
  | "dns"                      // Domain Name System lookups
  | "whois"                    // Domain registration data
  | "ssl"                      // SSL/TLS certificate analysis
  | "threat_intel"             // Threat intelligence feeds
  | "reputation"               // Reputation scoring
  | "social";                  // Social media presence
```

### OSINTResult

Individual OSINT query result with full metadata.

```typescript
interface OSINTResult {
  source: string;              // e.g., "virus_total", "whois", "phishtank"
  category: OSINTCategory;
  query_type: string;          // Type of query made
  query_value: string;         // Value queried
  status: "success" | "error" | "timeout" | "rate_limited";
  data?: Record<string, unknown>;  // Query response data
  confidence_score: number;    // 0.0 to 1.0
  cached_at?: string;          // ISO datetime of cache
  error_message?: string;      // Error details if failed
}
```

**Supported OSINT Sources:**
- **DNS:** Cloudflare, Google DNS
- **WHOIS:** WHOIS.com, DomainTools
- **SSL:** crt.sh, SSL Labs
- **Threat Intel:** VirusTotal, Phishtank, URLhaus, Abuse.ch, Cymon
- **Reputation:** Web of Trust, Scamadviser
- **Social:** LinkedIn, Twitter, Facebook

---

### ExitRiskLevel

Darknet exit node risk classification.

```typescript
type ExitRiskLevel =
  | "none"                     // No risk detected
  | "low"                      // Minimal exposure
  | "medium"                   // Moderate risk
  | "high"                     // High risk
  | "critical";                // Severe threat
```

### DarknetMarketplaceType

Types of darknet marketplaces monitored.

```typescript
type DarknetMarketplaceType =
  | "marketplace"              // General marketplace
  | "forum"                    // Discussion forum
  | "exchange"                 // Currency exchange
  | "hacking"                  // Hacking tools/services
  | "carding"                  // Credit card fraud
  | "drugs"                    // Drug trade
  | "weapons"                  // Weapons trade
  | "unknown";                 // Unclassified
```

### MarketplaceThreatData

Darknet marketplace threat intelligence.

```typescript
interface MarketplaceThreatData {
  marketplace_name: string;    // e.g., "Empire", "AlphaBay"
  marketplace_type: DarknetMarketplaceType;
  onion_address: string;       // .onion address
  threat_level: ExitRiskLevel;
  confidence: number;
  description: string;
  indicators: string[];        // specific threat indicators
  source: string;

  // Premium fields
  product_categories?: string[];
  risk_factors?: string[];
  shutdown_date?: string;      // For exit scams
  exit_scam_status?: boolean;
  anonymity_breach?: string;    // "high", "medium", "low"
}
```

**Monitored Darknet Markets:**
1. AlphaBay (revival)
2. Empire
3. Dream
4. Hansa
5. WallStreet
6. Alpha2

---

### DarknetAnalysisResult

Complete darknet analysis result.

```typescript
interface DarknetAnalysisResult {
  has_onion_references: boolean;
  onion_urls_detected: string[];
  marketplace_threats: MarketplaceThreatData[];
  tor2web_exposure: boolean;    // Exposed through Tor2Web
  darknet_risk_score: number;   // 0.0 to 1.0
  recommendations: string[];
  threat_level?: ExitRiskLevel;

  // Premium intelligence
  onion_validated?: boolean;
  marketplace_verified?: boolean;
  attack_patterns?: string[];   // MITRE techniques
  cve_associated?: string[];    // CVE IDs
}
```

---

### Tor2WebThreatData

Tor2Web gateway de-anonymization risk assessment.

```typescript
interface Tor2WebThreatData {
  gateway_domains: string[];    // Tor2Web domains detected
  de_anon_risk: ExitRiskLevel;
  referrer_leaks?: boolean;     // Referrer header exposes .onion
  recommendation: string;
  anonymity_breach?: string;
}
```

---

### IOCType

Indicator of Compromise types.

```typescript
type IOCType =
  | "url"
  | "domain"
  | "ipv4"
  | "ipv6"
  | "email"
  | "md5"
  | "sha1"
  | "sha256"
  | "filename"
  | "onion";                   // Dark web address
```

### IOCIndicator

Individual IOC with confidence and source.

```typescript
interface IOCIndicator {
  type: IOCType;
  value: string;               // The actual indicator value
  confidence: number;          // 0.0 to 1.0
  source: string;              // Source of detection
  context?: string;            // Additional context
  detection_count?: number;    // Number of sources confirming
}
```

### IOCDetectionResult

Aggregate IOC detection results.

```typescript
interface IOCDetectionResult {
  iocs: IOCIndicator[];
  threat_score: number;        // 0.0 to 1.0
  attack_patterns?: string[];   // MITRE techniques mapped
  attribution?: ThreatAttribution;
}
```

---

### ThreatAttribution

Threat actor attribution with MITRE framework mapping.

```typescript
interface ThreatAttribution {
  threat_actor: string;        // e.g., "APT29", "FIN7"
  attack_pattern: string;      // Attack pattern name
  attack_tactic: string;       // MITRE tactic (e.g., "INITIAL_ACCESS")
  technique_id?: string;       // e.g., "T1566.001"
  confidence: number;
  explanation: string;
  all_techniques?: TechniqueMatch[];
}
```

---

## Premium Darknet Feature Types

### DarknetMarketplaceDetail

Detailed marketplace information including exit scams.

```typescript
interface DarknetMarketplaceDetail {
  marketplace_name: string;
  marketplace_short_name: string;  // e.g., "Empire", "Alpha"
  status: "active" | "exit_scam" | "shutdown" | "unknown";
  exit_scam_date?: string;
  shutdown_date?: string;
  threat_score: number;           // 0.0-1.0
  active_since?: string;
  vendor_affected_count?: number;
  funds_stolen_estimate?: string;  // "millions in BTC"
}
```

### MarketplaceListing

Individual darknet marketplace listing.

```typescript
interface MarketplaceListing {
  listing_id: string;
  marketplace: string;
  threat_type:
    | "phishing_kit"
    | "credential_database"
    | "credit_card_dumps"
    | "identity_theft"
    | "bank_account"
    | "crypto_wallet";
  title: string;
  price?: string;
  price_crypto?: string;
  seller_reputation?: number;
  date_posted?: string;
  description?: string;
  evidence_tokens?: string[];    // Matching tokens
  confidence: number;
}
```

---

## CVE / CVSS Types

### CWMetricStatus

CVSS metric status values.

```typescript
type CWMetricStatus =
  | "X"   // Not Defined
  | "N"   // Network / None
  | "A"   // Adjacent
  | "L"   // Local / Low (context-dependent)
  | "P"   // Physical
  | "H"   // High
  | "M"   // Medium
  | "R"   // Required
  | "C"   // Changed
  | "U"   // Unchanged;
```

### CVSSMetrics

Complete CVSS metric breakdown.

```typescript
interface CVSSMetrics {
  attack_vector: CWMetricStatus;       // A
  attack_complexity: CWMetricStatus;   // AC
  privileges_required: CWMetricStatus; // PR
  user_interaction: CWMetricStatus;    // UI
  scope: CWMetricStatus;               // S
  confidentiality: CWMetricStatus;     // C
  integrity: CWMetricStatus;           // I
  availability: CWMetricStatus;        // A
}
```

### CVEEntry

Complete CVE entry with full technical details.

```typescript
interface CVEEntry {
  cve_id: string;            // e.g., "CVE-2024-34351"
  name: string;              // CVE title
  description: string;       // Full description
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  cwe_id?: string;           // CWE identifier (e.g., "CWE-79")
  cvss_score?: number;       // 0.0-10.0 base score
  cvss_vector?: string;      // e.g., "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"
  attack_vector?: "N" | "A" | "L" | "P";
  exploitability?: "NONE" | "LOW" | "HIGH";
  impact?: string;           // Plain text impact description
  patch_available?: boolean;
  technical_notes?: string[];
  affected_components?: string[];
  references?: string[];
}
```

---

## MITRE ATT&CK Framework Types

### MITRETactic

MITRE ATT&CK tactics.

```typescript
type MITRETactic =
  | "initial_access"
  | "execution"
  | "persistence"
  | "privilege_escalation"
  | "defense_evasion"
  | "credential_access"
  | "discovery"
  | "lateral_movement"
  | "collection"
  | "exfiltration"
  | "command_and_control"
  | "impact";
```

### MITRETechnique

Complete MITRE ATT&CK technique.

```typescript
interface MITRETechnique {
  technique_id: string;      // e.g., "T1566.001"
  technique_name: string;
  tactic: MITRETactic;
  description: string;
  detection_markers: string[];    // Keywords/patterns
  matched_markers?: string[];     // Which markers matched
  confidence?: number;            // 0.0 to 1.0
}
```

**Common Mapped Techniques:**
- T1566: Phishing Spearphishing Link
- T1056: Input Capture Keylogging
- T1204: User Execution Malicious File
- T1059: Command and Scripting Interpreter
- T1106: Native API Scheduled Task
- T1190: Exploit Public-Facing Application

---

### TechniqueMatch

Simplified technique match for frontend display.

```typescript
interface TechniqueMatch {
  technique_id: string;
  technique_name: string;
  tactic: string;
  confidence: number;          // 0.0 to 1.0
  matched_markers: string[];
}
```

---

## Exploitation & Scenario Types

### ExploitationAdvisory

Advisory for exploitation risk based on severity.

```typescript
interface ExploitationAdvisory {
  cve: string;                // CVE or CWE reference
  title: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  priority: "IMMEDIATE" | "URGENT" | "SCHEDULED";
  remediation: string;
  advisory_note: string;
  affected_components?: string[];
  attack_vector_description?: string;
  exploit_complexity?: string;
}
```

### AttackScenarioStep

Individual step in attack scenario.

```typescript
interface AttackScenarioStep {
  step_number: number;
  description: string;
  technique_used?: string;    // MITRE technique ID
  expected_outcome: string;
  prerequisites?: string[];
  tools_required?: string[];
}
```

### AttackScenario

Complete attack scenario with multi-step flow.

```typescript
interface AttackScenario {
  cve?: string;
  title: string;
  attack_flow: AttackScenarioStep[];
  potential_impact: string;
  technique_id?: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  estimated_complexity?: "LOW" | "MEDIUM" | "HIGH";
  actor_groups?: string[];     // Threat actors using this
  required_privileges?: string[];
}
```

**Common Attack Scenarios:**
- SSRF (Server-Side Request Forgery)
- Cache Poisoning
- XSS (Cross-Site Scripting)
- SQL Injection
- CSRF (Cross-Site Request Forgery)

---

## Security Module Result Types

### OWASPModuleResult

OWASP Top 10 category results.

```typescript
interface OWASPModuleResult {
  owasp_id: string;           // e.g., "A01", "A02"
  owasp_name: string;         // e.g., "Broken Access Control"
  cwe_id?: string;            // Associated CWE
  findings_count: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  details: Record<string, unknown>;
  remediation?: string;
}
```

### SecurityModuleResult

Individual security module execution result.

```typescript
interface SecurityModuleResult {
  module_name: string;        // e.g., "security_headers", "tls_ssl_analysis"
  category: string;           // "owasp", "gdpr", "pci_dss", "darknet"
  findings_count: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  composite_score: number;    // Weighted score
  execution_time_ms: number;
  findings: SecurityFinding[];
  details: Record<string, unknown>;
  recommendations?: string[];
}
```

**Security Module Categories:**
- `owasp` - OWASP Top 10 vulnerabilities
- `gdpr` - GDPR compliance
- `pci_dss` - PCI DSS compliance
- `darknet` - Darknet exposure
- `headers` - Security header analysis
- `tls` - TLS/SSL configuration
- `csp` - Content Security Policy
- `cookies` - Cookie security

---

## Agent Performance Types

### AgentPerformance

Individual agent performance metrics.

```typescript
interface AgentPerformance {
  agent: Phase;                // "scout", "security", "vision", "graph", "judge"
  tasks_completed: number;
  tasks_total: number;
  accuracy: number;            // 0-100%
  processing_time_ms: number;
  finding_rate: number;        // findings per second
  memory_usage_mb?: number;
  cache_hit_rate?: number;     // For NIM cache
  ai_calls_made?: number;      // NIM call count
  fallback_used?: boolean;     // Used fallback AI
}
```

### TaskMetric

Individual task execution metric.

```typescript
interface TaskMetric {
  task_id: string;
  task_name: string;
  agent: Phase;
  start_time: string;          // ISO datetime
  end_time: string;            // ISO datetime
  duration_ms: number;
  success: boolean;
  error_message?: string;
  resources_used?: string[];   // "NIM", "cache", "fallback"
  confidence?: number;
}
```

---

## Knowledge Graph Types

### KnowledgeGraphNode

Node in the knowledge graph.

```typescript
interface KnowledgeGraphNode {
  id: string;
  node_type:
    | "domain"
    | "entity"
    | "osint_source"
    | "darknet_threat"
    | "ioc"
    | "attribute";
  attributes: Record<string, unknown>;
}
```

### GraphEdge

Edge in the knowledge graph.

```typescript
interface GraphEdge {
  source: string;
  target: string;
  relationship_type: string;
  weight: number;              // Edge weight for importance
  confidence: number;          // 0.0-1.0
  timestamp?: string;
}
```

### KnowledgeGraph

Complete knowledge graph structure.

```typescript
interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: GraphEdge[];
  node_count: number;
  edge_count: number;
  graph_density: number;       // Sparsity metric (0.0-1.0)
  avg_clustering: number;      // Community clustering
  largest_component_size: number;
  isolated_nodes: number;
}
```

### GraphAnalysis

Graph analysis results.

```typescript
interface GraphAnalysis {
  graph_sparsity: number;
  avg_clustering: number;
  strongly_connected: boolean;
  shortest_path_to_darknet?: number;
  osint_clusters: OSINTCluster[];
  centrality_scores?: NodeCentrality[];
}
```

### OSINTCluster

OSINT source cluster.

```typescript
interface OSINTCluster {
  source: string;
  connected_entities: string[];
  cluster_strength: number;
  confidence?: number;
}
```

### NodeCentrality

Node centrality metrics.

```typescript
interface NodeCentrality {
  node_id: string;
  degree_centrality: number;
  eigenvector_centrality: number;
  betweenness_centrality: number;
  page_rank?: number;
}
```

---

## Judge Dual-Verdict Types

### CWEEntry

Common Weakness Enumeration entry.

```typescript
interface CWEEntry {
  cwe_id: string;            // e.g., "CWE-79"
  name: string;
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}
```

### CVSSMetric

Individual CVSS metric.

```typescript
interface CVSSMetric {
  name: string;
  value: string;
  severity: "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}
```

### VerdictTechnical

Expert technical verdict for security professionals.

```typescript
interface VerdictTechnical {
  cwe_entries: CWEEntry[];                 // Associated CWEs
  cvss_metrics: CVSSMetric[];              // CVSS breakdown
  cvss_base_score: number;                 // Base score 0-10
  cvss_vector: string;                     // CVSS vector string
  iocs: IOCIndicator[];                    // Indicators of compromise
  threat_indicators: string[];             // General threat indicators
  attack_techniques: string[];             // MITRE ATT&CK techniques
  exploitability: "NONE" | "LOW" | "HIGH";
  impact: "NONE" | "LOW" | "HIGH";
}
```

### VerdictNonTechnical

User-friendly verdict for general users.

```typescript
interface VerdictNonTechnical {
  risk_level:
    | "trusted"
    | "probably_safe"
    | "suspicious"
    | "high_risk"
    | "likely_fraudulent";
  summary: string;                         // Plain English summary
  key_findings: string[];                  // Bullet point findings
  recommendations: string[];               // Actionable steps
  warnings: string[];                      // Important warnings
  green_flags: GreenFlag[];                // Positive indicators
  simple_explanation: string;              // Extra simple explanation
  what_to_do: string[];                    // What user should do
}
```

### DualVerdict

Combined technical and non-technical verdicts.

```typescript
interface DualVerdict {
  technical: VerdictTechnical;
  non_technical: VerdictNonTechnical;
  trust_score: number;                     // 0-100
  timestamp: string;                       // ISO datetime
}
```

---

## Site Classification Types

### SiteClassification

Website classification with signals.

```typescript
interface SiteClassification {
  site_type: string;                       // e.g., "ecommerce", "news", "gaming"
  site_type_confidence: number;            // 0.0-1.0
  primary_signals: Record<string, number>; // Weighted signal scores
  additional_signals: string[];
  content_categories: string[];
  detected_technologies: string[];
  risk_indicators: string[];
  green_flags: string[];
}
```

### BusinessEntity

Business entity verification.

```typescript
interface BusinessEntity {
  entity_id: string;
  entity_name: string;
  entity_type: "company" | "organization" | "brand" | "individual";
  verification_status: "verified" | "unverified" | "conflicted";
  confidence: number;
  sources_supporting: string[];
  verification_links: string[];
  registration_info?: {
    business_number?: string;
    incorporation_date?: string;
    jurisdiction?: string;
  };
  contact_info?: {
    phone?: string;
    email?: string;
    address?: string;
    social_profiles?: string[];
  };
}
```

---

## WebSocket Event Mapping

### Backend → Frontend Events

| Event Type | Handler | Data Structure | Description |
|------------|---------|----------------|-------------|
| `phase_start` | store.ts | Phase data | Phase execution started |
| `phase_complete` | store.ts | Phase data + summary | Phase execution complete |
| `phase_error` | store.ts | Phase data + error | Phase execution failed |
| `finding` | store.ts | `Finding` | Security finding detected |
| `screenshot` | store.ts | `Screenshot` | Screenshot captured |
| `stats_update` | store.ts | `AuditStats` | Statistics updated |
| `log_entry` | store.ts | `LogEntry` | Agent log message |
| `site_type` | store.ts | site_type + confidence | Site classification detected |
| `security_result` | store.ts | `SecurityResultItem` | Security module result |
| `audit_result` | store.ts | `AuditResult` | Final audit result |
| `green_flags` | store.ts | `GreenFlag[]` | Positive indicators |
| `audit_complete` | store.ts | - | Audit finished |
| `audit_error` | store.ts | error message | Audit failed |

### Advanced Data Events

| Event Type | Handler | Data Structure | Status |
|------------|---------|----------------|--------|
| `dark_pattern_finding` | store.ts | `DarkPatternFinding` | ✅ Integrated |
| `temporal_finding` | store.ts | `TemporalFinding` | ✅ Integrated |
| `vision_pass_start` | store.ts | Pass data | ✅ Integrated |
| `vision_pass_findings` | store.ts | Findings batch | ✅ Integrated |
| `vision_pass_complete` | store.ts | `VisionPassSummary` | ✅ Integrated |
| `osint_result` | store.ts | `OSINTResult` | ✅ Integrated |
| `darknet_threat` | store.ts | `MarketplaceThreatData` | ✅ Integrated |
| `ioc_indicator` | store.ts | `IOCIndicator` | ✅ Integrated |
| `ioc_detection_complete` | store.ts | `IOCDetectionResult` | ✅ Integrated |
| `verdict_technical` | store.ts | Technical verdict | ✅ Integrated |
| `verdict_nontechnical` | store.ts | Non-technical verdict | ✅ Integrated |
| `dual_verdict_complete` | store.ts | `DualVerdict` | ✅ Integrated |
| `darknet_analysis_result` | store_patch.ts | `DarknetAnalysisResult` | ⚠️ Patch file |
| `marketplace_threat` | store_patch.ts | `MarketplaceThreatData` | ⚠️ Patch file |
| `tor2web_anonymous_breach` | store_patch.ts | Tor2Web threat | ⚠️ Patch file |
| `exit_scam_detected` | store_patch.ts | Exit scam data | ⚠️ Patch file |
| `cvss_metrics` | store_patch.ts | `CVSSMetric[]` | ⚠️ Patch file |
| `cve_detected` | store_patch.ts | `CVEEntry` | ⚠️ Patch file |
| `mitre_technique_mapped` | store_patch.ts | `MITRETechnique` | ⚠️ Patch file |
| `threat_attribution` | store_patch.ts | `ThreatAttribution` | ⚠️ Patch file |
| `attack_pattern_detected` | store_patch.ts | Pattern string | ⚠️ Patch file |
| `exploitation_advisory` | store_patch.ts | `ExploitationAdvisory` | ⚠️ Patch file |
| `attack_scenario` | store_patch.ts | `AttackScenario` | ⚠️ Patch file |
| `security_module_result` | store_patch.ts | `SecurityModuleResult` | ⚠️ Patch file |
| `knowledge_graph` | store_patch.ts | `KnowledgeGraph` | ⚠️ Patch file |
| `site_classification` | store_patch.ts | `SiteClassification` | ⚠️ Patch file |

---

## Integration Status

### Completed ✅

| Component | Status | Notes |
|-----------|--------|-------|
| TypeScript Types Definitions | ✅ Complete | All advanced types defined in types.ts |
| Frontend Store (Basic) | ✅ Complete | Dark pattern, temporal, vision, OSINT, judge events |
| Backend Vision Events | ✅ Complete | 5-pass pipeline, temporal findings |
| Backend OSINT Events | ✅ Complete | 15+ sources, IOC indicators |
| Backend Judge Events | ✅ Complete | Dual verdict, technical/non-technical |
| Backend Security Events | ✅ Complete | CVE detection, CVSS calculation |
| Premium Category System | ✅ Complete | 6 categories with pricing |

### In Progress ⚠️

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend Store (Advanced) | ⚠️ Patch file | Events in store_patch.ts need integration |
| Backend Mitre Events | ⚠️ Partial | Technique mapping implemented in runner |
| Backend Darknet Premium Events | ⚠️ Partial | Basic emission in runner, needs testing |
| Agent Performance Metrics | ⚠️ Not started | Placeholder in types, no backend emission |
| Knowledge Graph Events | ⚠️ Not started | Placeholder in store_patch.ts |

### Pending 📋

| Component | Status | Notes |
|-----------|--------|-------|
| store_patch.ts Merging | 📋 Pending | Merge into store.ts main file |
| Helper Methods | 📋 Pending | `_generate_exploitation_advisories()` etc. |
| E2E Testing | 📋 Pending | Complete data flow verification |
| Theater Components | 📋 Pending | UI components to display data |

---

## Backend Event Emissions Summary

### Location: `backend/services/audit_runner.py`

The following advanced events are emitted in the `_handle_result()` method around lines 700-1100:

**Darknet Analysis Events:**
```python
await send({"type": "darknet_analysis_result", "result": darknet_result})
await send({"type": "marketplace_threat", "threat": threat})
await send({"type": "tor2web_anonymous_breach", "threat": threat})
await send({"type": "exit_scam_detected", "marketplace": market, ...})
```

**CVSS/CVE Events:**
```python
await send({"type": "cvss_metrics", "metrics": metrics})
await send({"type": "cve_detected", "cve": cve_entry})
```

**MITRE ATT&CK Events:**
```python
await send({"type": "mitre_technique_mapped", "technique": technique})
await send({"type": "threat_attribution", "attribution": attribution})
await send({"type": "apt_group_attribution", ...})
```

**Exploitation Events:**
```python
await send({"type": "exploitation_advisory", "advisory": advisory})
```

**OSINT Events:**
```python
await send({"type": "osint_result", "result": osint})
await send({"type": "darknet_threat", "threat": threat})
await send({"type": "ioc_indicator", "ioc": ioc})
await send({"type": "ioc_detection_complete", "result": ioc_detection})
```

**Judge Events:**
```python
await send({"type": "verdict_technical", "technical": verdict})
await send({"type": "verdict_nontechnical", "verdict": verdict})
await send({"type": "dual_verdict_complete", "dual_verdict": dual})
```

---

## Premium Darknet Categories

### Category Configuration

| ID | Name | Tier | Price | Features |
|----|------|------|-------|----------|
| `onion_detection` | Onion Address Detection | Standard | Free | Pattern detection, validation |
| `marketplace_monitoring` | Darknet Marketplace Monitoring | Premium | $99 | 6 markets monitored |
| `credential_leak_check` | Credential Leak DB Check | Premium | $149 | Breach compilation, search |
| `phishing_kit_detection` | Phishing Kit Database | Darknet Premium | $499 | TOR access, operator tracking |
| `exit_scam_tracking` | Exit Scam Database | Darknet Premium | $599 | Real-time alerts, tracking |
| `attribution_engine` | Threat Attribution Engine | Darknet Premium | $999 | APT mapping, technique correlation |

---

## Key Architecture Decisions

1. **Type System First:** Complete TypeScript type definitions created before implementing event handlers
2. **Dual-Verdict System:** Separate technical/non-technical verdicts for different user personas
3. **Multi-Pass Vision:** 5-pass pipeline for comprehensive visual analysis with temporal comparison
4. **Event-Driven Streaming:** WebSocket-based real-time event streaming from backend to frontend
5. **Zustand Store:** Centralized state management with event sequencer for ordering
6. **Fallback System:** NIM VLM with fallback to alternative models for reliability

---

## Next Steps

1. **Merge store_patch.ts:** Integrate remaining event handlers into main store.ts
2. **Complete Helper Methods:** Implement `_generate_exploitation_advisories()`, `_construct_knowledge_graph()`, etc.
3. **E2E Testing:** Verify complete data flow from backend through WebSocket to frontend
4. **Theater Components:** Create UI components to display all advanced data in Agent Theater
5. **Documentation:** Update ADVANCED_INTEGRATION_SUMMARY.md with completion status

---

*Document Version: 1.0*
*Last Updated: 2026-03-07*
