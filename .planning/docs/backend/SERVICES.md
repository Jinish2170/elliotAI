# VERITAS Backend - Services Reference

**Version:** 2.0.0
**Last Updated:** 2026-03-08

---

## Overview

This document describes the core services in the VERITAS backend and their purposes.

---

## Services Architecture

```
Frontend Request
    ↓
FastAPI Routes Layer
    ↓
AuditRunner Service
    ↓
Veritas Orchestrator (Core Logic)
    ↓
Veritas Analysis Modules
```

---

## 1. AuditRunner Service (`backend/services/audit_runner.py`)

### Purpose
Wraps the VeritasOrchestrator for WebSocket streaming. Captures progress markers and converts them into typed WebSocket events for the frontend.

### Key Responsibilities
- Execute audit in subprocess for Windows compatibility
- Stream progress events via WebSocket callback
- Convert orchestrator output to frontend events
- Handle screenshot encoding and transmission
- Manage audit lifecycle (start, complete, error)

### Class Definition

```python
class AuditRunner:
    def __init__(self, audit_id: str, url: str, tier: str,
                 verdict_mode: str = "expert",
                 security_modules: Optional[list[str]] = None)

    async def run(self, send: Callable) -> None:
        """Execute audit and stream events via send callback"""
```

### IPC Modes

The service supports two IPC (Inter-Process Communication) modes:

1. **Queue Mode** - Uses multiprocessing.Queue for reliable data transfer
2. **Stdout Mode** - Parses ##PROGRESS markers from stdout

Mode is determined automatically based on environment and system capabilities.

### Event Generation Helper Methods

```python
_get_attack_vector_description(finding: dict) -> str
    """Get attack vector description based on finding data"""

_get_exploit_complexity(cvss_score: float) -> str
    """Get exploit complexity rating based on CVSS score"""

_get_impact_description(severity: str) -> str
    """Get impact description based on severity level"""

_get_technique_for_severity(severity: str) -> str
    """Get MITRE ATT&CK technique ID for given severity"""

_get_complexity_rating(cvss_score: float) -> str
    """Get complexity rating based on CVSS score"""
```

### Advanced Event Generation Methods

```python
_get_cve_severity_value(severity: str) -> int
    """Convert severity string to sortable numeric value"""

_generate_exploitation_advisories(findings: list) -> list
    """Generate exploitation advisories from high-severity findings"""

_generate_attack_scenarios(cves: list) -> list
    """Construct attack scenarios from detected CVEs"""

_calculate_agent_performance(result: dict) -> list
    """Calculate per-agent performance metrics from audit results"""

_has_graph_data(result: dict) -> bool
    """Check if graph data is available in results"""

_construct_knowledge_graph(result: dict, trust_score: int) -> dict
    """Build knowledge graph from audit results"""

_calculate_graph_analysis(graph: dict) -> dict
    """Calculate graph analysis metrics"""
```

### Event Emission Map

The service emits the following events:
- Phase lifecycle: `phase_start`, `phase_complete`, `phase_error`, `agent_personality`
- Audit lifecycle: `audit_complete`, `audit_error`, `audit_result`
- Scout events: `screenshot`, `site_type`, `navigation_*`, `scroll_event`, `captcha_result`, `form_detected`
- Vision events: `vision_pass_*`, `dark_pattern_finding`, `temporal_finding`
- Security events: `security_result`, `owasp_module_result`, `cvss_*`, `cve_detected`
- Graph events: `knowledge_graph`, `graph_analysis`, `osint_*`, `ioc_*`, `marketplace_threat`, etc.
- Judge events: `verdict_technical`, `verdict_nontechnical`, `dual_verdict_complete`

---

## 2. Veritas Orchestrator (Core Logic)

### Purpose
The main coordinator that orchestrates all 5 agents and manages the audit lifecycle.

### Key Responsibilities
- Coordinate agent execution sequence
- Collect results from each agent
- Manage shared data structure
- Handle errors and retries
- Calculate final trust score

### Agent Execution Sequence

```
1. Scout Agent (navigation, page analysis)
2. Vision Agent (VLM visual analysis)
3. Security Agent (vulnerability scanning)
4. Graph Investigator (knowledge graph, OSINT)
5. Judge Agent (final verdict synthesis)
```

### Entry Point
Located in `veritas/core/` (implementation varies by project structure).

---

## 3. Screenshot Storage Service (`veritas/screenshots/storage.py`)

### Purpose
Store screenshots to the filesystem and provide metadata access.

### Class Definition

```python
class ScreenshotStorage:
    async def save(self, audit_id: str, index: int,
                   label: str, base64_data: str) -> tuple[str, int]:
        """Save screenshot and return (file_path, file_size)"""
```

### Storage Structure

```
storage/
└── screenshots/
    └── {audit_id}/
        ├── 0_homepage.png
        ├── 1_after_scroll.png
        └── 2_checkout.png
```

---

## 4. Database Service (`veritas/db/`)

### Purpose
Provide persistence for audit records, findings, and screenshots.

### Components

#### Database Config (`veritas/db/config.py`)
- Database URL configuration
- Session management
- Async engine setup

#### Database Models (`veritas/db/models.py`)
Defines SQLAlchemy ORM models:

```python
class Audit(Base):
    id: str
    url: str
    status: AuditStatus
    audit_tier: str
    verdict_mode: str
    trust_score: Optional[int]
    risk_level: Optional[str]
    narrative: Optional[str]
    signal_scores: Optional[dict]
    site_type: Optional[str]
    site_type_confidence: Optional[float]
    security_results: Optional[dict]
    pages_scanned: Optional[int]
    elapsed_seconds: Optional[int]
    created_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    findings: List[AuditFinding]
    screenshots: List[AuditScreenshot]

class AuditFinding(Base):
    id: str
    audit_id: str
    pattern_type: str
    category: str
    severity: str
    confidence: float
    description: str
    plain_english: str
    screenshot_index: int

class AuditScreenshot(Base):
    id: str
    audit_id: str
    file_path: str
    label: str
    index_num: int
    file_size_bytes: int

class AuditStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
```

#### Database Repository (`veritas/db/repositories.py`)
Data access layer:

```python
class AuditRepository:
    async def get_by_id(self, audit_id: str) -> Optional[Audit]
    async def create(self, audit: Audit) -> Audit
    async def update(self, audit: Audit) -> Audit
    async def list_audits(self, limit: int, offset: int,
                         status_filter: Optional[AuditStatus],
                         risk_level_filter: Optional[str]) -> List[Audit]
```

#### Database Initialization (`veritas/db/__init__.py`)

```python
async def init_database() -> None:
    """Initialize SQLite database with WAL mode and create tables"""

async def get_db() -> AsyncSession:
    """Dependency for database session injection"""
```

---

## 5. OSINT Services (`veritas/osint/`)

### Purpose
Provide Open Source Intelligence data from 15+ external sources.

### Components

#### OSINT Orchestrator (`veritas/osint/orchestrator.py`)
Coordinates OSINT queries across multiple sources.

```python
class OSINTOrchestrator:
    async def query_domain(self, domain: str) -> OSINTResult
    async def query_ip(self, ip_address: str) -> OSINTResult
    async def query_url(self, url: str) -> OSINTResult
```

#### IOC Detector (`veritas/osint/ioc_detector.py`)
Detects indicators of compromise:

```python
class IOCDetector:
    def extract_iocs(self, text: str) -> List[IOC]
    def is_malicious_ioc(self, ioc: IOC) -> bool
```

#### Threat Intelligence (`veritas/osint/cti.py`)
Provides cyber threat intelligence:

```python
class CTIService:
    async def get_threat_actors(self) -> List[ThreatActor]
    async def get_apt_groups(self) -> List[APTGroup]
    async def attribute_threat(self, indicators: List) -> ThreatAttribution
```

#### OSINT Sources (`veritas/osint/sources/`)
Individual OSINT data providers:

| Source | File | Purpose |
|--------|------|---------|
| AbuseIPDB | `abuseipdb.py` | IP reputation database |
| URLVoid | `urlvoid.py` | URL reputation service |
| DNS Lookup | `dns_lookup.py` | DNS records (A, MX, NS, TXT) |
| WHOIS Lookup | `whois_lookup.py` | Domain registration data |
| SSL Verify | `ssl_verify.py` | SSL certificate verification |
| Empire Monitor | `darknet_empire.py` | Empire marketplace monitor |
| AlphaBay Monitor | `darknet_alpha.py` | AlphaBay marketplace monitor |
| Dream Monitor | `darknet_dream.py` | Dream marketplace monitor |
| Hansa Monitor | `darknet_hansa.py` | Hansa marketplace monitor |
| WallStreet Monitor | `darknet_wallstreet.py` | WallStreet marketplace |
| Tor2Web Monitor | `darknet_tor2web.py` | Tor2Web gateway detection |

---

## 6. CWE/CVSS Service (`veritas/cwe/`)

### Purpose
Provide CVE/CWE database and CVSS scoring capabilities.

### Components

#### CVSS Calculator (`veritas/cwe/cvss_calculator.py`)
Calculates CVSS v4.0 scores:

```python
class CVSSCalculator:
    def calculate_base_score(self, metrics: dict) -> float
    def calculate_temporal_score(self, base_score: float, metrics: dict) -> float
    def calculate_environmental_score(self, base_score: float, metrics: dict) -> float
    def get_severity(self, score: float) -> str
```

#### CWE Registry (`veritas/cwe/registry.py`)
CVE/CWE database access:

```python
class CWERegistry:
    def get_cve(self, cve_id: str) -> Optional[CVEEntry]
    def search_cves(self, query: str) -> List[CVEEntry]
    def get_cwe(self, cwe_id: str) -> Optional[CWEEntry]
    def find_related_cves(self,finding: dict) -> List[CVEEntry]
```

---

## 7. Analysis Services (`veritas/analysis/`)

### Purpose
Security and behavioral analysis modules.

### Components

#### Dark Pattern Matcher (`veritas/analysis/pattern_matcher.py`)
Detects dark patterns in text and elements:

```python
class PatternMatcher:
    def match_dark_patterns(self, text: str) -> List[DarkPattern]
    def confirmshaming_patterns() -> List[str]
    def countdown_patterns() -> List[str]
```

#### JavaScript Analyzer (`veritas/analysis/js_analyzer.py`)
Analyzes JavaScript code:

```python
class JSAnalyzer:
    def analyze_scripts(self, scripts: list) -> dict
    def detect_beacons(self, js_code: str) -> List[str]
    def detect_tracking(self, js_code: str) -> List[str]
```

#### Phishing Checker (`veritas/analysis/phishing_checker.py`)
Detects phishing indicators:

```python
class PhishingChecker:
    def is_phishing_url(self, url: str) -> tuple[bool, float]
    def check_typosquatting(self, url: str) -> bool
    def check_suspicious_tld(self, url: str) -> bool
```

#### Form Validator (`veritas/analysis/form_validator.py`)
Validates form security:

```python
class FormValidator:
    def validate_form(self, form: dict) -> FormValidationResult
    def check_csrf_protection(self, form: dict) -> bool
    def check_input_validation(self, fields: list) -> bool
```

#### Security Analysis (`veritas/analysis/security/`)
Security-specific analysis modules:

| Module | File | Purpose |
|--------|------|---------|
| Cookies | `cookies.py` | Cookie security analysis |
| CSP | `csp.py` | Content Security Policy analysis |
| Darknet | `darknet.py` | Darknet marketplace analysis |
| GDPR | `gdpr.py` | GDPR compliance check |
| TLS/SSL | `tls_ssl.py` | TLS/SSL validation |

#### OWASP Modules (`veritas/analysis/security/owasp/`)
OWASP Top 10 vulnerability scanners:

| Module | File | OWASP Category |
|--------|------|----------------|
| A01 | `a01_broken_access_control.py` | Broken Access Control |
| A02 | `a02_cryptographic_failures.py` | Cryptographic Failures |
| A03 | `a03_injection.py` | Injection |
| A04 | `a04_insecure_design.py` | Insecure Design |
| A05 | `a05_security_misconfiguration.py` | Security Misconfiguration |
| A06 | `a06_vulnerable_components.py` | Vulnerable Components |
| A07 | `a07_authentication_failures.py` | Authentication Failures |
| A08 | `a08_data_integrity.py` | Software and Data Integrity |
| A09 | `a09_logging_failures.py` | Logging Failures |
| A10 | `a10_ssrf.py` | Server-Side Request Forgery |

#### Exploitation Advisor (`veritas/analysis/exploitation_advisor.py`)
Generates exploitation advisories:

```python
class ExploitationAdvisor:
    def generate_advisories(self, findings: list) -> List[ExploitationAdvisory]
    def assess_exploitability(self, CVE: CVEEntry) -> str
    def get_remediation(self, CVE: CVEEntry) -> dict
```

#### Scenario Generator (`veritas/analysis/scenario_generator.py`)
Constructs attack scenarios:

```python
class ScenarioGenerator:
    def generate_scenarios(self, cves: list) -> List[AttackScenario]
    def chain_exploits(self, cves: list) -> List[AttackScenarioStep]
    def estimate_impact(self, scenario: AttackScenario) -> str
```

---

## 8. Darknet Services (`veritas/darknet/`)

### Purpose
Access and monitor darknet marketplaces.

### Components

#### Onion Detector (`veritas/darknet/onion_detector.py`)
Detects .onion domains:

```python
class OnionDetector:
    def is_onion_url(self, url: str) -> bool
    def detect_tor_exit_node(self, ip_address: str) -> bool
```

#### Tor Client (`veritas/darknet/tor_client.py`)
Tor network client:

```python
class TorClient:
    async def make_tor_request(self, url: str) -> dict
    def set_proxy(self, proxy_address: str) -> None
```

#### Threat Scraper (`veritas/darknet/threat_scraper.py`)
Scrapes darknet threats:

```python
class ThreatScraper:
    def scrape_marketplace(self, marketplace_url: str) -> List[MarketplaceListing]
    def search_threats(self, query: str) -> List[DarknetThreat]
```

---

## 9. Configuration Services (`veritas/config/`)

### Purpose
Provide configuration and rule definitions.

### Components

| File | Purpose |
|------|---------|
| `settings.py` | Application settings and environment variables |
| `security_rules.py` | Security check rules and thresholds |
| `dark_patterns.py` | Dark pattern definitions and templates |
| `site_types.py` | Site type classification rules |
| `trust_weights.py` | Trust scoring weight configuration |
| `darknet_rules.py` | Darknet monitoring rules |

---

## Service Dependencies

```
FastAPI (main.py)
    ↓
Routes (audit.py)
    ↓
AuditRunner (audit_runner.py)
    ↓
Veritas Orchestrator (core logic)
    ├→ Scout Agent
    │   ├→ Scroll Orchestrator
    │   ├→ Lazy Load Detector
    │   └→ Link Explorer
    ├→ Vision Agent
    │   ├→ Temporal Analysis
    │   └→ VLM API
    ├→ Security Agent
    │   ├→ OWASP Modules (A01-A10)
    │   ├→ Cookies, CSP, TLS/SSL
    │   └→ GDPR Checker
    ├→ Graph Investigator
    │   ├→ OSINT Orchestrator
    │   ├→ IOC Detector
    │   ├→ CTI Service
    │   └→ Attack Patterns
    └→ Judge Agent
        ├→ Strategies (11+)
        └→ Dual Verdict System
```

---

**End of Services Reference**
