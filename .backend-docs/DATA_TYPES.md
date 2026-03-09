# VERITAS Backend - Data Types Reference

**Version:** 2.0.0
**Last Updated:** 2026-03-08
**Total Types:** 50+

---

## Overview

This document defines all data types used in the VERITAS backend. These types correspond to Python dataclasses and TypeScript interfaces.

---

## Core Types

### AuditResult

```python
class AuditResult:
    audit_id: str
    url: str
    status: "queued" | "running" | "completed" | "error" | "disconnected"
    trust_score: int  # 0-100
    risk_level: "trusted" | "probably_safe" | "suspicious" | "high_risk" | "likely_fraudulent" | "dangerous"
    narrative: str
    signal_scores: dict[str, float]
    site_type: str
    site_type_confidence: float
    security_results: dict
    pages_scanned: int
    elapsed_seconds: int
    created_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
```

### RiskLevel

```python
type RiskLevel = (
    "trusted"           # Score 80-100
    | "probably_safe"   # Score 60-79
    | "suspicious"      # Score 40-59
    | "high_risk"       # Score 20-39
    | "likely_fraudulent" # Score 1-19
    | "dangerous"       # Score 0
)
```

### SiteType

```python
type SiteType = (
    "ecommerce"
    | "social_media"
    | "news_blog"
    | "saaS_subscription"
    | "gaming"
    | "financial"
    | "healthcare"
    | "government"
    | "education"
    | "company_portfolio"
    | "darknet_suspicious"
)
```

### SecuritySeverity

```python
type SecuritySeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "INFO"
```

---

## Scout Agent Types

### ScoutResult

```python
class ScoutResult:
    url: str
    status: "SUCCESS" | "CAPTCHA_BLOCKED" | "TIMEOUT" | "ERROR"
    screenshots: list[str]  # base64 encoded images
    screenshot_timestamps: list[int]
    screenshot_labels: list[str]
    page_title: str
    page_metadata: PageMetadata
    links: list[str]
    forms_detected: int
    captcha_detected: bool
    redirect_chain: list[str]
    final_url: str
```

### PageMetadata

```python
class PageMetadata:
    url: str
    title: str
    description: Optional[str]
    keywords: Optional[list[str]]
    author: Optional[str]
    robots: Optional[str]
    canonical_url: Optional[str]
    og_title: Optional[str]
    og_description: Optional[str]
    og_image: Optional[str]
    twitter_card: Optional[str]
    viewport: Optional[str]
    charset: Optional[str]
    content_type: Optional[str]
    content_length: int
    language: Optional[str]
    last_modified: Optional[str]
```

### ScrollResult

```python
class ScrollResult:
    url: str
    scroll_position: int
    scroll_percentage: float
    total_height: int
    new_elements_detected: int
    loaded_elements: list[str]  # element IDs or selectors
    lazy_load_trigger: bool
    timestamp: datetime
```

### PageVisit

```python
class PageVisit:
    url: str
    title: str
    visited_at: datetime
    duration_seconds: float
    status: "SUCCESS" | "ERROR" | "TIMEOUT"
    error_message: Optional[str]
    screenshot_count: int
    element_count: int
```

### ExplorationResult

```python
class ExplorationResult:
    start_url: str
    pages_visited: list[PageVisit]
    total_pages: int
    exploration_type: "breadth_first" | "depth_first" | "focused"
    depth_limit: int
    max_pages: int
    duration_seconds: float
    interrupted: bool
```

### LinkInfo

```python
class LinkInfo:
    url: str
    text: str
    href: str
    internal: bool
    nofollow: bool
    screenshot_index: int
    coordinates: Optional[dict]  # x, y, width, height
    target: Optional[str]  # _blank, _self, etc.
    rel: Optional[str]
```

---

## Vision Agent Types

### VisionResult

```python
class VisionResult:
    dark_patterns: list[DarkPatternFinding]
    temporal_findings: list[TemporalFinding]
    visual_score: float  # 0-100
    temporal_score: float  # 0-100
    pass_count: int
    passes_completed: int
    duration_seconds: float
    analyzed_screenshots: list[int]  # indices
```

### DarkPatternFinding

```python
class DarkPatternFinding:
    id: str
    pattern_type: str  # e.g., "confirmshaming", "countdown_timer"
    category: "manipulation" | "pressure" | "obfuscation" | "misinformation"
    severity: "low" | "medium" | "high" | "critical"
    confidence: float  # 0-1
    description: str  # Technical description
    plain_english: str  # User-friendly explanation
    screenshot_index: int
    coordinates: dict  # {x, y, width, height}
    temporal: bool  # whether this is a time-based pattern
    detected_at: datetime
    pass_number: int  # which vision pass detected this
```

### TemporalFinding

```python
class TemporalFinding:
    id: str
    type: "countdown" | "price_change" | "availability_change" | "ui_state_change"
    description: str
    severity: "low" | "medium" | "high"
    confidence: float  # 0-1
    timestamps: list[datetime]
    values: list[dict]  # snapshot of values at each timestamp
    screenshot_indices: list[int]
    pass_number: int
```

### VisionPassSummary

```python
class VisionPassSummary:
    pass_num: int
    pass_name: str  # e.g., "UI Layout Analysis"
    duration_seconds: float
    findings_count: int
    status: "started" | "completed" | "error"
    description: str
```

---

## Graph Agent Types

### GraphResult

```python
class GraphResult:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    claims: list[EntityClaim]
    verifications: list[VerificationResult]
    inconsistencies: list[GraphInconsistency]
    domain_intel: DomainIntel
    analysis: GraphAnalysis
```

### GraphNode

```python
class GraphNode:
    id: str
    type: "domain" | "entity" | "ioc" | "claim" | "scout" | "vision" | "graph" | "security" | "judge"
    label: str
    properties: dict
    confidence: float  # 0-1
    source: str  # where this came from (agent or OSINT)
    created_at: datetime
```

### GraphEdge

```python
class GraphEdge:
    id: str
    source: str  # node ID
    target: str  # node ID
    relationship: str  # "verified_by", "contradicts", "supports", "implies", etc.
    weight: float  # 0-1
    confidence: float  # 0-1
    created_at: datetime
```

### EntityClaim

```python
class EntityClaim:
    id: str
    entity: str  # company name, person name, etc.
    claim_type: "location" | "registration" | "contact" | "ownership" | "domain"
    value: str  # the claimed value
    source: str  # what page/section claimed this
    source_type: "footer" | "about_page" | "contact_page" | "header" | "copyright"
    confidence: float  # 0-1
    extracted_at: datetime
```

### VerificationResult

```python
class VerificationResult:
    claim_id: str
    verified: bool | "partial"
    confidence: float  # 0-1
    sources: list[str]  # OSINT sources that verified/contradicted
    timeline: str  # "verified as of 2024-01-15"
    conflicting_sources: list[str]  # sources that disagree
    verified_at: datetime
    notes: Optional[str]
```

### DomainIntel

```python
class DomainIntel:
    domain: str
    created_date: str
    expiry_date: str
    registrar: str
    registrant: Optional[dict]
    dns_records: dict
    ssl_info: dict
    reputation: dict
    status: "registered" | "expired" | "suspended"
    age_years: int
```

### GraphInconsistency

```python
class GraphInconsistency:
    id: str
    type: "address_mismatch" | "phone_mismatch" | "email_mismatch" | "timing_discrepancy"
    description: str
    severity: "low" | "medium" | "high"
    affected_claims: list[str]  # claim IDs
    evidence: dict
    detected_at: datetime
```

### KnowledgeGraph

```python
class KnowledgeGraph:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metadata: {
        "created_at": datetime,
        "audit_id": str,
        "domain": str,
        "total_nodes": int,
        "total_edges": int
    }
```

### GraphAnalysis

```python
class GraphAnalysis:
    total_nodes: int
    total_edges: int
    graph_sparsity: float  # 0-1, lower = more connected
    avg_clustering: float  # 0-1, community effect
    osint_clusters: int
    centrality_scores: dict  # node_id -> score
    connected_components: int
    diameter: Optional[int]
    path_lengths: dict
```

---

## Security Agent Types

### SecurityResult

```python
class SecurityResult:
    tls_valid: bool
    tls_grade: str  # "A+", "A", "B", "C", "D", "F"
    https: bool
    security_headers: dict[str, bool]  # header_name -> present
    cookies: dict
    csp: dict
    owasp: dict[str, OWASPModuleResult]
    overall_score: int  # 0-100
    critical_findings: int
```

### SecurityFinding

```python
class SecurityFinding:
    id: str
    category: "injection" | "xss" | "csrf" | "ssrf" | "authentication" | "authorization" | "encryption"
    severity: "low" | "medium" | "high" | "critical"
    confidence: float  # 0-1
    description: str
    plain_english: str
    cwe_id: Optional[str]  # e.g., "CWE-79"
    cvss_score: Optional[float]
    remediation: Optional[str]
    source: str  # which module found this
```

### SecurityConfig

```python
class SecurityConfig:
    enable_tls: bool
    enable_cookies: bool
    enable_csp: bool
    enable_owasp: bool
    enable_gdpr: bool
    owasp_modules: list[str]
```

### OWASPModuleResult

```python
class OWASPModuleResult:
    module: str  # e.g., "A01_2021_Broken_Access_Control"
    category: str
    passed: bool
    findings: list[SecurityFinding]
    severity: "low" | "medium" | "high" | "critical"
    confidence: float  # 0-1
    score: int  # 0-100
```

### SecurityFindingDetailed

```python
class SecurityFindingDetailed:
    id: str
    category: str
    subcategory: str
    severity: str
    confidence: float
    title: str
    description: str
    impact: str
    recommendation: str
    references: list[str]
    detected_at: datetime
    evidence: dict
```

---

## Judge Agent Types

### JudgeDecision

```python
class JudgeDecision:
    technical_verdict: VerdictTechnical
    nontechnical_verdict: VerdictNonTechnical
    trust_score: int  # 0-100
    risk_level: RiskLevel
    site_type: SiteType
    confidence: float  # 0-1
    metadata: dict
```

### AuditEvidence

```python
class AuditEvidence:
    findings: list[dict]  # All findings from all agents
    screenshots: list[str]
    osint_matches: list[dict]
    security_vulnerabilities: list[dict]
    entity_claims: list[dict]
    timestamp: datetime
    summary: dict
```

### DualVerdict

```python
class DualVerdict:
    verdict_technical: VerdictTechnical
    verdict_nontechnical: VerdictNonTechnical
    metadata: {
        "timestamp": datetime,
        "audit_id": str,
        "version": str
    }
```

### VerdictTechnical

```python
class VerdictTechnical:
    risk_level: RiskLevel
    trust_score: int
    confidence: float  # 0-1
    signal_scores: dict[str, float]
    summary: str
    findings_analysis: dict
    recommendations: list[str]
    technical_details: dict
    vulnerabilities: list[str]
```

### VerdictNonTechnical

```python
class VerdictNonTechnical:
    risk_level: RiskLevel
    ease_of_understanding: str  # "very_easy" | "easy" | "moderate" | "difficult"
    summary: str
    key_concerns: list[str]
    green_flags: list[str]
    actionable_advice: list[str]
    privacy_implications: str
    transparency_rating: int  # 0-5 stars
```

### CWEEntry

```python
class CWEEntry:
    cwe_id: str  # e.g., "CWE-79"
    name: str
    description: str
    severity: "low" | "medium" | "high" | "critical"
    likelihood: "rare" | "uncommon" | "likely" | "very_likely"
    common_pitfalls: list[str]
    detection_methods: list[str]
    remediation: str
    references: list[str]
```

---

## OSINT/CTI Types

### OSINTResult

```python
class OSINTResult:
    source: str  # "abuseipdb", "urlvoid", "whois", "dns", "ssl_verify", etc.
    data: dict
    timestamp: datetime
    reliability: float  # 0-1
    ttl: int  # time to live in seconds
    cached: bool
```

### DarknetThreatData

```python
class DarknetThreatData:
    marketplace: str  # "Empire", "AlphaBay", "Dream", etc.
    url: str  # .onion URL
    listing_title: str
    listing_price: str
    seller: str
    listing_date: datetime
    match_fields: list[str]  # ["domain", "email", "phone", etc.]
    confidence: float  # 0-1
    threat_type: "credential_leak" | "credit_card_dump" | "phishing_kit" | "identity_theft" | "bank_account" | "crypto_wallet"
```

### IOCIndicator

```python
class IOCIndicator:
    type: str  # "ip_address", "domain", "email", "phone", "crypto_wallet", "file_hash"
    value: str
    detection_count: int
    severity: "low" | "medium" | "high" | "critical"
    confidence: float  # 0-1
    sources: list[str]  # which OSINT sources found this
    first_seen: datetime
    last_seen: datetime
    tags: list[str]
    category: str  # "malware", "phishing", "c2", etc.
```

### ThreatAttribution

```python
class ThreatAttribution:
    threat_actors: list[str]
    apt_groups: list[str]
    confidence: float  # 0-1
    technique_matches: list[str]  # MITRE technique IDs
    indicators: dict
    timeline: dict
    estimated_motivation: str
    estimated_origin: str
```

### APTGroupAttribution

```python
class APTGroupAttribution:
    apt_group: str  # "APT28 (Fancy Bear)", "Lazarus Group", etc.
    aliases: list[str]
    country: str
    motivation: str  # "espionage", "financial", "political", "sabotage"
    techniques_used: list[str]  # MITRE technique IDs
    targets: list[str]
    activity_period: str
    confidence: float  # 0-1
    sources: list[str]
```

---

## CVE/CVSS Types

### CVEEntry

```python
class CVEEntry:
    cve_id: str  # e.g., "CVE-2024-1234"
    description: str
    severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    cvss_score: float  # 0-10
    published_date: str
    modified_date: str
    references: list[str]
    affected_products: list[str]
    exploit_available: bool
    patch_available: bool
    cwe_ids: list[str]
```

### CVSSMetrics

```python
class CVSSMetrics:
    base_score: float  # 0-10
    base_severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    temporal_score: float
    temporal_severity: str
    environmental_score: float
    environmental_severity: str
    vector_string: str  # CVSS vector string
    metrics: list[CVSSMetric]
```

### CVSSMetric

```python
class CVSSMetric:
    metric_name: str  # "AttackVector", "AttackComplexity", etc.
    value: str  # "Network", "Low", etc.
    numeric_value: float  # 0-1, for calculations
    description: str
```

---

## MITRE ATT&CK Types

### MITRETechnique

```python
class MITRETechnique:
    technique_id: str  # "T1566.001"
    technique_name: str  # "Spearphishing Link"
    tactic: str  # "Initial Access"
    tactics: list[str]
    description: str
    detection_count: int
    confidence: float  # 0-1
    platforms: list[str]
    mitigation: str
    references: list[str]
```

### TechniqueMatch

```python
class TechniqueMatch:
    technique_id: str
    technique_name: str
    tactic: str
    detection_count: int
    confidence: float  # 0-1
    matched_findings: list[str]  # finding IDs
    rank: int
```

---

## Exploitation Types

### ExploitationAdvisory

```python
class ExploitationAdvisory:
    cve: str  # CVE ID
    title: str
    severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    priority: str  # "Immediate patching required", "High priority", etc.
    remediation: {
        "description": str,
        "patch_available": bool,
        "patch_version": str,
        "workarounds": list[str],
        "vendor_advisory": str
    }
    exploit_complexity: "LOW" | "MEDIUM" | "HIGH" | "VERY HIGH"
    impact_description: str
    confidence: float  # 0-1
```

### AttackScenario

```python
class AttackScenario:
    id: str
    title: str
    description: str
    steps: list[AttackScenarioStep]
    overall_severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    estimated_impact: str
    likelihood: float  # 0-1
    cve_dependencies: list[str]
    mitre_techniques: list[str]
    preconditions: list[str]
```

### AttackScenarioStep

```python
class AttackScenarioStep:
    step: int
    technique_id: str
    technique_name: str
    description: str
    success_probability: float  # 0-1
    dependencies: list[int]  # step numbers that must complete first
    evidence: str
    mitigation: str
```

---

## Darknet Types

### DarknetAnalysisResult

```python
class DarknetAnalysisResult:
    url: str
    is_onion: bool
    darknet_detected: bool
    marketplaces: list[DarknetMarketplaceDetail]
    tor2web_risk: bool
    detected_gateways: list[str]
    exit_scams: list[dict]
    category: str
    confidence: float  # 0-1
```

### DarknetMarketplaceDetail

```python
class DarknetMarketplaceDetail:
    name: str  # "Empire", "AlphaBay", etc.
    url: str
    status: "active" | "exit_scam" | "taken_down" | "unknown"
    listings: list[MarketplaceListing]
    category: str
    threat_level: "low" | "medium" | "high"
    last_updated: str
```

### MarketplaceListing

```python
class MarketplaceListing:
    title: str
    price: str  # e.g., "0.05 BTC"
    seller: str
    listing_date: datetime
    description: str
    threat_type: str
    match_confidence: float  # 0-1
    verified: bool
```

### Tor2WebThreatData

```python
class Tor2WebThreatData:
    detected_gateway: str  # "onion.to", "onion.link", etc.
    original_onion: str
    risk_level: "low" | "medium" | "high"
    de_anonymization_risk: float  # 0-1
    description: str
    mitigation: str
```

---

## Other Types

### LogEntry

```python
class LogEntry:
    timestamp: str  # "HH:MM:SS"
    agent: str  # "Scout", "Vision", "Security", "Graph", "Judge"
    message: str
    level: "info" | "warning" | "error"
```

### NavigationStartEvent

```python
class NavigationStartEvent:
    url: str
    timestamp: datetime
    page_index: int
```

### NavigationCompleteEvent

```python
class NavigationCompleteEvent:
    url: str
    status: "SUCCESS" | "CAPTCHA_BLOCKED" | "TIMEOUT" | "ERROR"
    timestamp: datetime
    duration_seconds: float
    error: Optional[str]
```

### PageScannedEvent

```python
class PageScannedEvent:
    url: str
    title: str
    timestamp: datetime
    elements_found: dict  # {links: 25, forms: 3, images: 15, videos: 2}
```

### ScrollEvent

```python
class ScrollEvent:
    url: str
    scroll_position: int
    scroll_percentage: float
    timestamp: datetime
    new_elements_detected: int
```

### ExplorationPath

```python
class ExplorationPath:
    path: list[dict]  # step entries
    total_pages: int
    total_links_explored: int
    duration_seconds: float
    strategy: str
```

### CaptchaResult

```python
class CaptchaResult:
    url: str
    captcha_detected: bool
    captcha_type: "reCAPTCHA" | "hCaptcha" | "Cloudflare" | "custom"
    timestamp: datetime
    status: "blocked" | "passed"
    attempt_count: int
```

### FormDetection

```python
class FormDetection:
    id: str
    form_type: "login" | "signup" | "contact" | "checkout" | "search" | "subscription"
    action: str
    method: str  # "POST" | "GET"
    fields: list[dict]  # field definitions
    security_features: dict
    url: str
```

### TrustScoreResult

```python
class TrustScoreResult:
    overall_score: int  # 0-100
    risk_level: RiskLevel
    signal_scores: dict[str, float]
    sub_signals: list[SubSignal]
    weightings: dict
    calculated_at: datetime
```

### SubSignal

```python
class SubSignal:
    name: str
    value: float  # 0-1
    weight: float
    description: str
    source: str
    confidence: float
```

### SiteClassification

```python
class SiteClassification:
    site_type: SiteType
    confidence: float  # 0-1
    evidence: dict
    alternatives: list[tuple[SiteType, float]]  # [(type, confidence), ...]
    classified_at: datetime
```

### BusinessEntity

```python
class BusinessEntity:
    name: str
    registered_address: str
    registration_number: str
    registration_country: str
    registered_date: str
    status: str  # "active", "inactive", "dissolved"
    verified: bool
    sources: list[str]
    confidence: float  # 0-1
    last_verified: datetime
```

### AgentPerformance

```python
class AgentPerformance:
    agent: str  # "scout", "vision", "security", "graph", "judge"
    tasks_completed: int
    tasks_total: int
    duration_seconds: float
    success_rate: float  # 0-1
    resource_usage: dict  # CPU, memory, etc.
    error_count: int
    warnings: list[str]
```

### TaskMetric

```python
class TaskMetric:
    task_name: str
    agent: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    status: "pending" | "in_progress" | "completed" | "failed"
    result: Optional[dict]
    error: Optional[str]
```

### ConsensusResult

```python
class ConsensusResult:
    topic: str
    agent_positions: dict  # {"scout": ..., "vision": ..., etc.}
    consensus_value: str
    consensus_confidence: float
    dissenting_agents: list[str]
    reasoning: str
```

### SecurityModuleResult

```python
class SecurityModuleResult:
    module: str  # "tls_ssl", "cookies", "csp", "gdpr", "owasp:A01", etc.
    category: str
    pass: bool
    findings: list[dict]
    score: int  # 0-100
    severity: str
    description: str
```

### OWASPResult

```python
class OWASPResult:
    module: str  # "A01_2021_Broken_Access_Control", etc.
    category: str
    findings: list[dict]
    severity: str
    confidence: float
    impact: str
    remediation: str
```

---

**End of Data Types Reference**
