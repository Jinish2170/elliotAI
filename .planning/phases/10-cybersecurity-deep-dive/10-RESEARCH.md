# Phase 10: Cybersecurity Deep Dive - Research

**Researched:** 2026-02-28
**Domain:** Web application security, compliance checking, vulnerability scanning
**Confidence:** MEDIUM
**Note:** No CONTEXT.md file exists for this phase - all decisions are within planning discretion.

## Summary

Phase 10 requires implementing 25+ enterprise-grade security modules covering OWASP Top 10, PCI DSS, and GDPR compliance checks. The implementation must integrate with existing Phase 9 components (CVSSCalculator, CWEMapper) and use the SecurityAgent pattern for consistency. Modules should be grouped into three execution tiers (fast <5s, medium <15s, deep <30s) for efficient sequential analysis.

The primary technical challenge is designing a flexible, extensible security module architecture that can:
1. Check compliance across multiple standards (OWASP, PCI, GDPR)
2. Map findings to CWE IDs and calculate CVSS scores
3. Correlate with darknet threat intelligence from Phase 8
4. Execute in grouped tiers for performance optimization

Key implementation risks include:
- OWASP Top 10 detection requires complex DOM analysis and behavioral testing
- PCI DSS compliance may need enterprise-level infrastructure checks beyond public URL analysis
- GDPR compliance is context-dependent and may require manual review
- CVSS calculation needs accurate severity classification

**Primary recommendation:** Implement a SecurityModule base class with tier classification, use async/await for all I/O operations, leverage existing httpx and Playwright infrastructure, and focus on publicly-accessible security checks rather than deep infrastructure penetration.

## Standard Stack

### Core Security Libraries
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **httpx** | >=0.25.0 | Async HTTP client for security header checks | Async-first, HTTP/2 support, session pooling (part of existing stack) |
| **requests** | - | HTTP client with TLS verification (already installed) | Browser-style TLS verification, SSL context control |
| **Playwright** | >=1.40.0 | DOM analysis, JavaScript execution, shadow DOM | Existing browser automation, can pierce shadow DOM, captures live snapshots |
| **BeautifulSoup4** | - | HTML/DOM parsing for vulnerability detection | Already in stack for DOMAnalyzer, handles malformed HTML |

### Supporting Security Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **cryptography/pyca** | >=0.3.0 | TLS certificate validation, cryptographic primitives | Recommended over pyOpenSSL for certificate analysis |
| **validators** | ^0.22.0 | Input validation (URL, email, domain) | Quick validation before deep analysis |
| **tldextract** | ^5.0.0 | Domain/subdomain extraction for security decisions | Accurate domain parsing for cross-origin checks |
| **hashlib** | (stdlib) | Hashing for content integrity, cache keys | Already in stack for cache key generation |
| **ssl** | (stdlib) | SSL/TLS context configuration and verification | Direct access to OpenSSL features |

### Alternative Libraries (Consider but not preferred)
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom SSL checks | **pyOpenSSL** | pyOpenSSL is being phased out in favor of cryptography; use only if cryptography lacks specific feature |
| Manual XSS detection | **Bandit** | Bandit is for Python static analysis, not web app scanning - different domain |
| Manual header parsing | **OWASP ZAP** | ZAP is a full scanner, too heavy for modular integration; use manual checks for specific headers |

### Already Available (Reuse from Existing Stack)
| Component | Location | Purpose for Phase 10 |
|-----------|----------|---------------------|
| **CVSSCalculator** | From Phase 9 | Calculate CVSS base scores for security findings |
| **CWEMapper** | From Phase 9 | Map security findings to CWE IDs |
| **SecurityHeaderAnalyzer** | `veritas/analysis/` | Existing security header checking (extend/enhance) |
| **PhishingChecker** | `veritas/analysis/` | Existing URL reputation checks (extend/enhance) |
| **DOMAnalyzer** | `veritas/analysis/` | DOM parsing infrastructure (reuse for OWASP checks) |
| **httpx** | Backend requirements | Async HTTP requests for header/SSL checks |

**Installation (if needed beyond existing stack):**
```bash
# These may already be installed based on existing requirements
pip install validators tldextract cryptography

# If adding new security-specific libraries
pip install pyjwt  # For JWT validation in security checks
```

## Architecture Patterns

### Recommended Project Structure
```
veritas/
├── analysis/
│   ├── security/                    # NEW: Security module organization
│   │   ├── __init__.py
│   │   ├── base.py                  # SecurityModule base class
│   │   ├── owasp/                   # OWASP Top 10 modules
│   │   │   ├── __init__.py
│   │   │   ├── a01_broken_access_control.py
│   │   │   ├── a02_cryptographic_failures.py
│   │   │   ├── a03_injection.py
│   │   │   ├── a04_insecure_design.py
│   │   │   ├── a05_security_misconfiguration.py
│   │   │   ├── a06_vulnerable_components.py
│   │   │   ├── a07_authentication_failures.py
│   │   │   ├── a08_data_integrity.py
│   │   │   ├── a09_logging_failures.py
│   │   │   └── a10_ssrf.py
│   │   ├── pci_dss.py               # PCI DSS compliance modules
│   │   ├── gdpr.py                  # GDPR compliance modules
│   │   ├── tls_ssl.py               # TLS/SSL analysis
│   │   ├── cookies.py               # Cookie security analysis
│   │   ├── csp.py                   # Content Security Policy analysis
│   │   └── utils.py                 # Shared security utilities
│   └── [existing analysis modules] # DOMAnalyzer, PhishingChecker, etc.
├── agents/
│   ├── security_agent.py            # REWRITE: Replace empty SecurityAgent
│   └── [other agents]
├── config/
│   ├── security_rules.py            # NEW: CWE mappings, severity rules
│   └── [existing config]
└── tests/
    └── test_security/               # NEW: Security module tests
        ├── __init__.py
        ├── conftest.py
        ├── test_owasp_modules.py
        ├── test_pci_gdpr.py
        └── test_security_agent.py
```

### Pattern 1: SecurityModule Base Class with Tiers
**What:** Abstract base class for all security modules with tier classification and async analysis interface
**When to use:** All security modules must extend this base class for consistent behavior
**Example:**
```python
# veritas/analysis/security/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class SecurityTier(str, Enum):
    """Execution tier for performance optimization."""
    FAST = "fast"      # <5s: headers, basic TLS
    MEDIUM = "medium"  # <15s: CSP, cookies
    DEEP = "deep"      # <30s: full DOM analysis, compliance

@dataclass
class SecurityFinding:
    """Standardized security finding structure."""
    category_id: str          # e.g., "owasp_a01", "pci_ssl", "gdpr_cookies"
    pattern_type: str         # Specific vulnerability type
    severity: str             # "low", "medium", "high", "critical"
    confidence: float         # 0.0-1.0
    description: str          # Technical description
    evidence: str             # Detail on what was found
    cwe_id: Optional[str]     # CWE identifier (e.g., "CWE-79")
    cvss_score: Optional[float] = None  # 0.0-10.0
    recommendation: str = ""  # Remediation guidance
    url_finding: bool = False  # If URL-specific finding

class SecurityModule(ABC):
    """Base class for all security analysis modules."""

    def __init__(self):
        self.timeout: int = 10
        self.tier: SecurityTier = SecurityTier.MEDIUM

    @property
    @abstractmethod
    def category_id(self) -> str:
        """Module identifier (e.g., 'owasp_a01')."""
        pass

    @abstractmethod
    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None
    ) -> list[SecurityFinding]:
        """
        Analyze URL/page for security issues.

        Args:
            url: Target URL
            page_content: HTML content (if available)
            headers: HTTP response headers
            dom_meta: DOM metadata from Scout

        Returns:
            List of security findings (empty if no issues)
        """
        pass

    def to_dict(self) -> dict:
        """Serialize module info for progress streaming."""
        return {
            "category_id": self.category_id,
            "tier": self.tier.value,
            "timeout": self.timeout
        }
```
**Source:** Based on existing dataclass patterns in ScoutResult, VisionResult from codebase

### Pattern 2: Tier-Grouped Parallel Execution
**What:** Execute modules in tier groups for performance optimization (fast→medium→deep)
**When to use:** SecurityAgent needs to execute 25+ modules efficiently
**Example:**
```python
# veritas/agents/security_agent.py (rewrite)
import asyncio
from typing import Dict, List
from analysis.security.base import SecurityModule, SecurityTier, SecurityFinding
from analysis.security.utils import get_all_security_modules

class SecurityAgent:
    """Orchestrates tier-based security analysis."""

    # Auto-discover all modules and group by tier
    _modules_by_tier: Dict[SecurityTier, List[type[SecurityModule]]] = {}

    @classmethod
    def _load_modules(cls):
        """Load and group security modules by tier."""
        if not cls._modules_by_tier:
            modules = get_all_security_modules()
            for module_class in modules:
                tier = module_class().tier
                cls._modules_by_tier.setdefault(tier, []).append(module_class)

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
        enable_cvss: bool = True,
        enable_darknet_correlation: bool = True
    ) -> "SecurityResult":
        """
        Run full security analysis with tier execution.

        Returns:
            SecurityResult with findings, CVSS scores, darknet exposure
        """
        self._load_modules()

        all_findings: List[SecurityFinding] = []

        # FAST TIER: Execute all fast modules in parallel
        if SecurityTier.FAST in self._modules_by_tier:
            fast_tasks = [
                mod().analyze(url, page_content, headers, dom_meta)
                for mod in self._modules_by_tier[SecurityTier.FAST]
            ]
            fast_results = await asyncio.gather(*fast_tasks, return_exceptions=True)
            for result in fast_results:
                if isinstance(result, list):
                    all_findings.extend(result)

        # MEDIUM TIER: Execute all medium modules in parallel
        if SecurityTier.MEDIUM in self._modules_by_tier:
            medium_tasks = [
                mod().analyze(url, page_content, headers, dom_meta)
                for mod in self._modules_by_tier[SecurityTier.MEDIUM]
            ]
            medium_results = await asyncio.gather(*medium_tasks, return_exceptions=True)
            for result in medium_results:
                if isinstance(result, list):
                    all_findings.extend(result)

        # DEEP TIER: Execute sequentially (resource-intensive)
        if SecurityTier.DEEP in self._modules_by_tier:
            for mod_class in self._modules_by_tier[SecurityTier.DEEP]:
                try:
                    deep_findings = await mod_class().analyze(
                        url, page_content, headers, dom_meta
                    )
                    all_findings.extend(deep_findings)
                except TimeoutError:
                    logger.warning(f"Deep module {mod_class.__name__} timed out")
                except Exception as e:
                    logger.error(f"Deep module {mod_class.__name__} failed: {e}")

        # CVSS Integration (from Phase 9)
        if enable_cvss:
            all_findings = await self._calculate_cvss_scores(all_findings)

        # Darknet Correlation (from Phase 8)
        if enable_darknet_correlation:
            all_findings = await self._correlate_darknet_threats(url, all_findings)

        return SecurityResult(findings=all_findings)

    async def _calculate_cvss_scores(self, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """Calculate CVSS scores using Phase 9 CVSSCalculator."""
        from config.security_rules import cwemapper, cvss_calculator

        for finding in findings:
            # Map to CWE
            finding.cwe_id = cwemapper.map_finding_to_cwe(
                finding.category_id,
                finding.pattern_type
            )

            # Calculate CVSS
            if finding.cwe_id:
                finding.cvss_score = cvss_calculator.calculate_base_score_from_finding(finding)

        return findings

    async def _correlate_darknet_threats(self, url: str, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """Correlate findings with darknet threat intel from Phase 8."""
        from agents.graph_investigator import DarknetThreatIntel

        darknet_intel = DarknetThreatIntel(offline_feeds=True)
        exposure = darknet_intel.analyze_exposure(url)

        for finding in findings:
            if finding.category_id in ["owasp_a03", "owasp_a07", "owasp_a10"]:
                # Elevate severity if darknet exposure detected
                if exposure.get("has_exposure"):
                    finding.confidence = min(finding.confidence * 1.5, 1.0)
                    if finding.severity == "medium":
                        finding.severity = "high"
                    finding.evidence += " | [DARKNET CORRELATION: Elevated due to threat feed exposure]"

        return findings


@dataclass
class SecurityResult:
    """Container for security analysis results."""
    findings: List[SecurityFinding]
    execution_time_ms: int = 0
    modules_executed: int = 0
    modules_failed: int = 0
```
**Source:** Adapted from Async patterns in `veritas/core/orchestrator.py`, ScoutAgent patterns

### Pattern 3: OWASP-A01 Broken Access Control Detection
**What:** Detect administrative panels exposed without proper authentication
**When to use:** Checking for unrestricted admin access, path traversal, IDOR
**Example:**
```python
# veritas/analysis/security/owasp/a01_broken_access_control.py
import asyncio
from analysis.security.base import SecurityModule, SecurityTier, SecurityFinding

class BrokenAccessControlModule(SecurityModule):
    """OWASP A01: Broken Access Control detection."""

    def __init__(self):
        super().__init__()
        self.tier = SecurityTier.DEEP
        self.timeout = 20

    @property
    def category_id(self) -> str:
        return "owasp_a01"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None
    ) -> list[SecurityFinding]:
        findings = []

        if not dom_meta:
            return findings

        # Check 1: Admin panel without role requirements
        admin_panel = dom_meta.get("admin_panel")
        if admin_panel and admin_panel.get("exists"):
            if not admin_panel.get("requires_role"):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="admin_panel_no_auth",
                    severity="critical",
                    confidence=0.85,
                    description="Admin panel accessible without authentication",
                    evidence=f"Admin panel at {admin_panel.get('path')} does not require role verification",
                    cwe_id="CWE-285",  # Improper Authorization
                    recommendation="Implement role-based access control (RBAC) for admin endpoints"
                ))

        # Check 2: Insecure direct object references (IDOR)
        idor_patterns = dom_meta.get("idor_patterns", [])
        for pattern in idor_patterns:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="insecure_direct_object_reference",
                severity="high",
                confidence=0.70,
                description="Potential IDOR vulnerability detected",
                evidence=f"Sequential IDs exposed: {pattern}",
                cwe_id="CWE-639",
                recommendation="Use UUID or randomized IDs, verify object ownership on access"
            ))

        return findings
```
**Source:** Based on CWE-285, CWE-639 from MITRE CWE documentation

### Pattern 4: Security Header Checking (Existing Infrastructure Extended)
**What:** Check presence and correctness of security headers
**When to use:** All URL scans - part of FAST tier
**Example:**
```python
# veritas/analysis/security/tls_ssl.py (extend existing SecurityHeaderAnalyzer)
from analysis.security.base import SecurityModule, SecurityTier, SecurityFinding

class SecurityHeaderAnalyzerEnhanced(SecurityModule):
    """Enhanced security header analysis with OWASP recommendations."""

    def __init__(self):
        super().__init__()
        self.tier = SecurityTier.FAST
        self.timeout = 5

    # Critical headers to check
    REQUIRED_HEADERS = {
        "Strict-Transport-Security": {"cwe": "CWE-523", "sev": "high"},
        "Content-Security-Policy": {"cwe": "CWE-693", "sev": "high"},
        "X-Frame-Options": {"cwe": "CWE-1021", "sev": "medium"},
        "X-Content-Type-Options": {"cwe": "CWE-693", "sev": "medium"},
    }

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None
    ) -> list[SecurityFinding]:
        findings = []

        if not headers:
            return findings

        # Check each required header
        for header_name, header_info in self.REQUIRED_HEADERS.items():
            if header_name not in headers:
                findings.append(SecurityFinding(
                    category_id="security_headers",
                    pattern_type=f"missing_{header_name.lower().replace('-', '_')}",
                    severity=header_info["sev"],
                    confidence=0.95,
                    description=f"Missing security header: {header_name}",
                    evidence=f"Response headers do not include {header_name}",
                    cwe_id=header_info["cwe"],
                    recommendation=f"Add {header_name} header per OWASP recommendations"
                ))

        # Check HSTS configuration if present
        if "Strict-Transport-Security" in headers:
            hsts_value = headers["Strict-Transport-Security"]
            if "max-age=" not in hsts_value:
                findings.append(SecurityFinding(
                    category_id="security_headers",
                    pattern_type="hsts_misconfigured",
                    severity="medium",
                    confidence=0.80,
                    description="HSTS header present but missing max-age",
                    evidence=f"HSTS value: {hsts_value}",
                    cwe_id="CWE-523",
                    recommendation="Include max-age (e.g., 'max-age=31536000' for 1 year)"
                ))

        return findings
```
**Source:** Based on owasp.org Secure Headers Project documentation

### Pattern 5: GDPR Cookie Consent Detection
**What:** Check for GDPR-compliant cookie consent banners and mechanisms
**When to use:** All URL scans - part of MEDIUM tier
**Example:**
```python
# veritas/analysis/security/gdpr.py
from analysis.security.base import SecurityModule, SecurityTier, SecurityFinding

class GDPRComplianceModule(SecurityModule):
    """GDPR compliance checks (cookie consent, privacy policy)."""

    def __init__(self):
        super().__init__()
        self.tier = SecurityTier.MEDIUM
        self.timeout = 15

    @property
    def category_id(self) -> str:
        return "gdpr_compliance"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None
    ) -> list[SecurityFinding]:
        findings = []

        if not dom_meta:
            return findings

        # Check 1: Cookie consent banner
        cookies = dom_meta.get("cookies", [])
        consent_banner = dom_meta.get("consent_banner", {})

        # Analyze cookies for consent requirements
        analytics_cookies = [c for c in cookies if "analytics" in c.get("name", "").lower()]

        if analytics_cookies and not consent_banner.get("present"):
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_consent_banner",
                severity="medium",
                confidence=0.75,
                description="Analytics cookies detected without consent banner",
                evidence=f"Found {len(analytics_cookies)} analytics cookies: " +
                        ", ".join([c['name'] for c in analytics_cookies[:3]]),
                cwe_id=None,  # Regulatory, not vulnerability
                recommendation="Implement GDPR-compliant cookie consent banner with granular consent options"
            ))

        # Check 2: Privacy policy link
        has_privacy_link = dom_meta.get("has_privacy_policy_link", False)
        if not has_privacy_link:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_privacy_policy",
                severity="low",
                confidence=0.80,
                description="No privacy policy link detected",
                evidence="Privacy policy link not found in header/footer",
                cwe_id=None,
                recommendation="Add privacy policy link complying with GDPR Article 12-14 requirements"
            ))

        # Check 3: Secure cookie attributes
        insecure_cookies = [
            c for c in cookies
            if not c.get("secure", False) and c.get("httpOnly", False)
        ]
        if insecure_cookies:
            findings.append(SecurityFinding(
                category_id="gdpr_compliance",
                pattern_type="insecure_cookie_attributes",
                severity="medium",
                confidence=0.70,
                description="HttpOnly cookies without Secure flag",
                evidence=f"{len(insecure_cookies)} cookies: " +
                        ", ".join([c['name'] for c in insecure_cookies[:3]]),
                cwe_id="CWE-614",  # Sensitive Cookie in HTTPS Session Without 'Secure' Attribute
                recommendation="Add Secure flag to all cookies for HTTPS sites"
            ))

        return findings
```
**Source:** Based on GDPR Article 4-11 requirements for consent and transparency

### Anti-Patterns to Avoid
- **Don't block execution on single module failure:** Use return_exceptions=True in asyncio.gather, log failures but continue with other modules
- **Don't hardcode severity:** Use severity based on CWE mapping and confidence, not arbitrary thresholds
- **Don't mix tiers incorrectly:** FAST tier modules must complete in <5s, MEDIUM in <15s, DEEP in <30s
- **Don't skip CWE mapping:** All security findings should reference relevant CWE IDs for proper scoring
- **Don't ignore async context:** All I/O operations (HTTP requests, Playwright page access) must use async/await

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| URL validation | Manual regex parsing | `validators.url()` + `tldextract` | Handles edge cases, uses Public Suffix List |
| HTTP requests | `urllib.request` | `httpx` (already in stack) | Async, HTTP/2 support, connection pooling |
| HTML parsing | Manual regex | `BeautifulSoup4` (already in stack) | Handles malformed HTML, CSS selectors |
| SSL/TLS verification | Manual socket SSL context | `ssl` module + `requests` built-in verification | Proper certificate chain validation |
| Hash functions | Custom implementation | `hashlib` (stdlib) | Secure, crypto-grade algorithms |
| JWT validation | Manual parsing | `PyJWT` if needed | Proper signature verification |
| XSS detection | Manual regex + heuristics | Playwright + DOM inspection (already in stack) | Can execute JS, detect reflected XSS through browser context |
| OWASP scanning rules | Manual vulnerability patterns | CWE mappings + CVSSCalculator (from Phase 9) | Standardized industry classification |
| CSRF detection | Manual token checking | Check for CSRF tokens + SameSite cookies (use httpx/Playwright) | Relies on proper browser behavior testing |

**Key insight:** Security scanning is an adversarial domain - custom implementations miss edge cases and bypass techniques. Leverage existing infrastructure (httpx, Playwright, BeautifulSoup, Phase 9 components) and standard references (CWE, CVSS) rather than building from scratch.

## Common Pitfalls

### Pitfall 1: False Positives in Security Scanning
**What goes wrong:** Security modules flag legitimate functionality as vulnerabilities (e.g., admin pages in public documentation, intentional use of older TLS)
**Why it happens:** Binary checks (header present/absent) without context validation
**How to avoid:**
- Use multi-factor validation (2+ sources must agree)
- Check for legitimate use cases (e.g., documentation pages can have admin URLs)
- Use confidence scores and tier-based severity elevation
- Implement "requires_review" category for ambiguous findings
**Warning signs:** High finding count on known-safe sites (google.com, github.com), inconsistent results between runs

### Pitfall 2: Broken Tier Execution Timing
**What goes wrong:** FAST tier takes >5s, causing timeouts or cascading delays
**Why it happens:** No enforcement of timeout per tier, or modules misclassified
**How to avoid:**
- Use `asyncio.timeout()` around each module execution: `async with asyncio.timeout(module.timeout):`
- Time modules during testing and adjust tier classification accordingly
- Log actual execution time for monitoring
- Use `return_exceptions=True` in asyncio.gather to prevent cascading failures
**Warning signs:** Security module phase consistently exceeds expected duration (FAST > 5s, MEDIUM > 15s)

### Pitfall 3: CWE/CVSS Mapping Inaccuracies
**What goes wrong:** Wrong CWE ID assigned, or CVSS score doesn't match severity
**Why it happens:** Manual mapping tables become outdated, or CVSS base metrics misconfigured
**How to avoid:**
- Use CWEMapper from Phase 9 (if it exists) or build based on official CWE documentation
- CVSSCalculator calculates based on Attack Vector, Complexity, CIA impact - verify metric assignments
- Test against known vulnerabilities (CVE database) to validate mappings
- Document mapping decisions with source URLs to official CWE entries
**Warning signs:** Critical findings have CVSS < 8.0, or non-critical findings have CVSS >= 8.0

### Pitfall 4: Darknet Correlation False Elevations
**What goes wrong:** Safe sites elevated to high risk due to benign darknet mentions
**Why it happens:** Correlating based on keyword matches without context
**How to avoid:**
- Validate darknet threat intel before correlating (use IOCs from Phase 8)
- Only correlate specific vulnerability types (injection, XSS, CSRF)
- Require multiple darknet sources to agree before elevation
- Add "darknet_correlation" metadata field indicating this was a correlation decision, not a direct finding
**Warning signs:** Inconsistent severity between runs, or known-safe sites showing "DARKNET CORRELATION" findings

### Pitfall 5: SSL Certificate Verification Issues
**What goes wrong:** Certificate errors reported as security issues for legitimate expired certificates (e.g., staging/testing)
**Why it happens:** Binary check (cert valid/invalid) without context about environment
**How to avoid:**
- Distinguish between expired, self-signed, and weak cipher issues
- Check for staging/test environment indicators (e.g., "staging" in domain)
- Use severity classification: expired (low), self-signed (medium), weak cipher (high)
- Log certificate details for context (issuer, validity period)
**Warning signs:** Self-signed staging sites flagged as critical, or legitimate sites in error states

## Code Examples

Verified patterns from official/authoritative sources:

### Multi-Tier Execution with Timeout Enforcement
```python
# Source: AsyncIO timeout patterns (Python 3.11+ docs)
import asyncio
from analysis.security.base import SecurityModule, SecurityTier

async def execute_tier(
    modules: list[type[SecurityModule]],
    url: str,
    page_content: str,
    headers: dict,
    dom_meta: dict
) -> list:
    """Execute all modules in a tier with timeout enforcement."""
    tasks = [
        self._execute_with_timeout(mod, url, page_content, headers, dom_meta)
        for mod in modules
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_findings = []
    for result in results:
        if isinstance(result, list):
            all_findings.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f"Module execution failed: {result}")

    return all_findings

async def _execute_with_timeout(
    mod_class: type[SecurityModule],
    url: str,
    page_content: str,
    headers: dict,
    dom_meta: dict
) -> list:
    """Execute single module with per-module timeout."""
    module = mod_class()

    try:
        async with asyncio.timeout(module.timeout):
            return await module.analyze(url, page_content, headers, dom_meta)
    except TimeoutError:
        logger.warning(f"Module {module.category_id} timed out after {module.timeout}s")
        return []
    except Exception as e:
        logger.error(f"Module {module.category_id} failed: {e}")
        return []
```

### CWE Mapping Table (Simplified Example)
```python
# Source: cwe.mitre.org - Common Weakness Enumeration
# veritas/config/security_rules.py

CWE_MAPPINGS = {
    # OWASP A01: Broken Access Control
    "owasp_a01": {
        "admin_panel_no_auth": "CWE-285",   # Improper Authorization
        "idor": "CWE-639",                   # Authorization Bypass Through User-Controlled Key
        "path_traversal": "CWE-22",          # Path Traversal
    },
    # OWASP A02: Cryptographic Failures
    "owasp_a02": {
        "weak_ssl_cipher": "CWE-327",        # Use of a Broken or Risky Cryptographic Algorithm
        "plaintext_passwords": "CWE-256",    # Unprotected Storage of Credentials
    },
    # OWASP A03: Injection
    "owasp_a03": {
        "sql_injection": "CWE-89",           # SQL Injection
        "xss": "CWE-79",                     # Cross-site Scripting
        "csrf": "CWE-352",                   # Cross-Site Request Forgery
    },
    # Security Headers
    "security_headers": {
        "missing_hsts": "CWE-523",           # Unprotected Transport of Credentials
        "missing_csp": "CWE-693",            # Protection Mechanism Failure
        "missing_x_frame_options": "CWE-1021", # Frame Restriction Bypass
    },
    # GDPR (regulatory, not CWE - mapped to closest)
    "gdpr_compliance": {
        "insecure_cookie_attributes": "CWE-614",  # Sensitive Cookie Without 'Secure'
    }
}

CWEMapper:
    @staticmethod
    def map_finding_to_cwe(category_id: str, pattern_type: str) -> Optional[str]:
        category_map = CWE_MAPPINGS.get(category_id, {})
        return category_map.get(pattern_type)
```

### CVSS Base Score Calculation (Simplified - uses Phase 9 calculator)
```python
# Source: FIRST.org CVSS specification
# veritas/config/security_rules.py

# This integrates with CVSSCalculator from Phase 9
# Example usage (assuming Phase 9 CVSSCalculator exists):

# from phase 9
# cvss_calculator = CVSSCalculator()

# For each finding:
# cvss_score = cvss_calculator.calculate_base_score_from_finding(
#     attack_vector="NETWORK",        # Based on finding type
#     attack_complexity="LOW",        # Based on exploit difficulty
#     privileges_required="NONE",     # Based on authentication required
#     user_interaction="REQUIRED",    # Based on whether user must interact
#     scope="UNCHANGED",              # Whether scope changes
#     confidentiality="HIGH",         # CIA impact
#     integrity="HIGH",               # CIA impact
#     availability="NONE"             # CIA impact
# )
# # Result: 8.1 (High severity)

# Severity mapping based on CVSS:
# 0.0-3.9: Low severity (LOW)
# 4.0-6.9: Medium severity (MEDIUM)
# 7.0-8.9: High severity (HIGH)
# 9.0-10.0: Critical severity (CRITICAL)
```

### X-Frame-Options Header Validation
```python
# Source: OWASP Secure Headers - https://owasp.org/www-project-secure-headers/
async def check_x_frame_options(headers: dict) -> Optional[SecurityFinding]:
    """Validate X-Frame-Options header configuration."""
    xfo = headers.get("X-Frame-Options", "")

    if not xfo:
        return SecurityFinding(
            category_id="security_headers",
            pattern_type="missing_x_frame_options",
            severity="medium",
            confidence=0.95,
            description="Missing X-Frame-Options header",
            evidence="Response headers do not include X-Frame-Options",
            cwe_id="CWE-1021",
            recommendation="Add X-Frame-Options: DENY or SAMEORIGIN"
        )

    valid_values = ["DENY", "SAMEORIGIN"]
    if xfo.upper() not in valid_values:
        return SecurityFinding(
            category_id="security_headers",
            pattern_type="x_frame_options_misconfigured",
            severity="medium",
            confidence=0.80,
            description=f"X-Frame-Options has invalid value: {xfo}",
            evidence=f"Valid values are: {valid_values}",
            cwe_id="CWE-1021",
            recommendation="Use DENY or SAMEORIGIN for X-Frame-Options"
        )

    return None  # Header is valid
```

### Content Security Policy Parsing
```python
# Source: MDN Content Security Policy - https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
async def check_csp(headers: dict, page_url: str) -> list[SecurityFinding]:
    """Analyze Content Security Policy for common issues."""
    findings = []
    csp = headers.get("Content-Security-Policy", "")

    if not csp:
        findings.append(SecurityFinding(
            category_id="security_headers",
            pattern_type="missing_csp",
            severity="high",
            confidence=0.95,
            description="Missing Content-Security-Policy header",
            evidence="Response headers do not include Content-Security-Policy",
            cwe_id="CWE-693",
            recommendation="Implement restrictive CSP to prevent XSS attacks"
        ))
        return findings

    # Parse CSP directives
    directives = parse_csp_directives(csp)

    # Check for unsafe-eval (high risk)
    if "script-src" in directives and "'unsafe-eval'" in directives["script-src"]:
        findings.append(SecurityFinding(
            category_id="security_headers",
            pattern_type="csp_unsafe_eval",
            severity="high",
            confidence=0.85,
            description="CSP allows 'unsafe-eval' in script-src",
            evidence=f"script-src directive includes 'unsafe-eval'",
            cwe_id="CWE-942",
            recommendation="Remove 'unsafe-eval' from CSP script-src directive"
        ))

    # Check for default-src weak configuration
    if "default-src" in directives and "*" in directives["default-src"]:
        findings.append(SecurityFinding(
            category_id="security_headers",
            pattern_type="csp_wildcard_default_src",
            severity="medium",
            confidence=0.75,
            description="CSP default-src allows wildcard (*)",
            evidence="default-src: *",
            cwe_id="CWE-693",
            recommendation="Replace wildcard with specific origins"
        ))

    return findings

def parse_csp_directives(csp: str) -> dict:
    """Parse CSP header into directive dictionary."""
    directives = {}
    for directive_part in csp.split(";"):
        if not directive_part.strip():
            continue

        parts = directive_part.strip().split()
        directive_name = parts[0]
        directive_values = parts[1:] if len(parts) > 1 else []

        directives[directive_name] = directive_values

    return directives
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| OWASP Top 10 2017 | OWASP Top 10 2021 | 2021 | New categories A04 Insecure Design, A08 Data Integrity Failures; SSL/TLS removed as separate category |
| CVSS v3.0 | CVSS v3.1 | 2019 | Minor metric clarifications, more consistent scoring |
| CVSS v3.1 | CVSS v4.0 | 2023 | Major overhaul - new Base Score formula, new Environmental and Supplemental metrics | **Phase 10 should use v3.1 for compatibility with existing tools; v4.0 is newer but less widely adopted** |
| Manual CSS inspection | CSP Analysis with directive parsing | Ongoing | Automated CSP parsing reduces false positives, detects nuanced misconfigurations |
| Basic header checks | Tier-based header analysis with CVSS scoring | Phase 10 design | Enables severity-based prioritization based on CVE impact |

**Deprecated/outdated:**
- **MD5/SHA1 for security**: Use SHA-256+ (from hashlib documentation - these have known collision vulnerabilities)
- **pyOpenSSL**: Python Cryptographic Authority recommends migrating to `cryptography` library for new implementations
- **Security header binary checks**: Current trend is directive-level CSP parsing, not just header presence/absence
- **Manual XSS detection**: Playwright with JS execution for reflected XSS detection is now standard
- **PCI DSS 3.x**: PCI DSS 4.0 is current standard (released 2022, effective March 2024)

## Open Questions

1. **PCI DSS Scope for Public URL Analysis**
   - What we know: Phase 10 scope includes PCI DSS compliance checks
   - What's unclear: Many PCI DSS requirements (network segmentation, encryption at rest, access logging) cannot be assessed from public URL scanning alone
   - Recommendation: Focus on publicly-verifiable PCI DSS checks (SSL/TLS compliance, secure cookies, data in transit, weak cipher detection). Mark infrastructure-only requirements as "requires internal assessment" or skip with documentation

2. **CVSS Scoring for Regulatory Violations (GDPR)**
   - What we know: CVSS is for technical vulnerabilities, GDPR is regulatory
   - What's unclear: How to assign CVSS scores to GDPR compliance findings
   - Recommendation: Map GDPR violations to closest technical CWE (e.g., insecure cookies -> CWE-614). For pure regulatory violations (missing consent banner), use CVSS 0.0 and rely on separate severity classification based on regulatory impact

3. **Darknet Threat Feed Integration**
   - What we know: Phase 8 has DarknetThreatIntel component with offline feeds
   - What's unclear: What threat intelligence sources are available and how to correlate with security findings without false elevations
   - Recommendation: Use only high-confidence threat indicators (IOCs, confirmed malicious domains) for correlation. Require multiple threat feed sources to agree before elevating severity

4. **Performance Testing Baseline for Tiers**
   - What we know: FAST <5s, MEDIUM <15s, DEEP <30s
   - What's unclear: Actual module performance on real-world sites and which modules may need tier reclassification
   - Recommendation: Implement profiling in each module execution, log actual execution times, and adjust tier classifications after Phase 10 testing on diverse sites

5. **CVSS v3.1 vs v4.0 Integration**
   - What we know: Phase 9 CVSSCalculator exists, unknown if v3.1 or v4.0
   - What's unclear: Which CVSS version the CVSSCalculator implements
   - Recommendation: Check Phase 9 CVSSCalculator implementation during Phase 10 implementation. If v4.0, use it (forward-looking). If v3.1, document and consider upgrade path.

## Validation Architecture

*Note: Based on config.json, workflow.nyquist_validation is not set. Including Validation Architecture section because Phase 10 has security validation requirements that benefit from test coverage.*

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.4.0 |
| Config file | Not found - using default pytest configuration |
| Async support | pytest-asyncio >=0.23.0 (auto-detection without explicit config) |
| Quick run command | `cd veritas && python -m pytest tests/test_security/ -v -k "test_fast_tier" --tb=short` |
| Full suite command | `cd veritas && python -m pytest tests/test_security/ -v --tb=short` |

### Phase Requirements → Test Map

**SEC-01:** Implement 25+ enterprise security modules (OWASP Top 10, PCI DSS, GDPR compliance)

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SEC-01 | OWASP Top 10 A01-A10 modules exist and execute | unit | `pytest tests/test_security/ -v -k "test_owasp"` | ❌ Wave 0: Create test_security/test_owasp_modules.py |
| SEC-01 | PCI DSS modules detect SSL/TLS issues | unit | `pytest tests/test_security/ -v -k "test_pci_"` | ❌ Wave 0: Create test_security/test_pci_gdpr.py |
| SEC-01 | GDPR modules detect cookie consent issues | unit | `pytest tests/test_security/ -v -k "test_gdpr_"` | ❌ Wave 0: Create test_security/test_pci_gdpr.py |
| SEC-01 | Security headers module checks all required headers | unit | `pytest tests/test_security/ -v -k "test_headers_"` | ✅ May exist in existing tests - check SECURITY_HEADER_ANALYZER tests |
| SEC-01 | Module tier classification is accurate (FAST/MEDIUM/DEEP) | unit | `pytest tests/test_security/ -v -k "test_tier_"` | ❌ Wave 0: Create test_security/test_tier_classification.py |
| SEC-01 | Total modules >= 25 | integration | `pytest tests/test_security/ -v -k "test_module_count"` | ❌ Wave 0: Create in conftest.py as module discovery test |

**SEC-02:** Darknet-level threat detection with CVSS scoring

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SEC-02 | Security findings have CWE IDs from Phase 9 mapper | unit | `pytest tests/test_security/ -v -k "test_cwe_mapping"` | ❌ Wave 0: Create test_security/test_cwe_mapping.py |
| SEC-02 | Security findings have CVSS scores from Phase 9 calculator | unit | `pytest tests/test_security/ -v -k "test_cvss_scoring"` | ❌ Wave 0: Requires Phase 9 CVSSCalculator verification - check if exists |
| SEC-02 | Darknet threat correlation elevates severity appropriately | unit | `pytest tests/test_security/ -v -k "test_darknet_"` | ❌ Wave 0: Requires Phase 8 DarknetThreatIntel - verify exists |
| SEC-02 | Calibration - known-safe sites have low CVSS scores | integration | `pytest tests/test_security/ -v -k "test_calibration_"` | ❌ Wave 0: Create test_security/test_calibration.py (needs live network - may run in CI only) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_security/ -v -k "test_[module_name]" --tb=short` (module-specific tests only)
- **Per wave merge:** `python -m pytest tests/test_security/ -v --tb=short` (full security test suite)
- **Phase gate:** Full suite green + calibration test against known-safe sites before `/gsd:verify-work`

### Wave 0 Gaps

**Test Files to Create:**
- [ ] `veritas/tests/test_security/__init__.py` - Test directory initialization
- [ ] `veritas/tests/test_security/conftest.py` - Shared fixtures for security testing:
  - `mock_scout_result` fixture (ScoutResult with dom_metadata)
  - `mock_headers` fixture (dict with various security header combinations)
  - `mock_page_content` fixture (sample HTML for OWASP analysis)
  - `mock_security_modules` fixture (list of available security module classes)
- [ ] `veritas/tests/test_security/test_owasp_modules.py` - OWASP A01-A10 module tests with sample findings
- [ ] `veritas/tests/test_security/test_pci_gdpr.py` - PCI DSS and GDPR compliance module tests
- [ ] `veritas/tests/test_security/test_tier_classification.py` - Tier timeout and classification tests
- [ ] `veritas/tests/test_security/test_cwe_mapping.py` - CWE mapping verification against CWE_MAPPINGS table
- [ ] `veritas/tests/test_security/test_cvss_scoring.py` - CVSS scoring integration with Phase 9 calculator
- [ ] `veritas/tests/test_security/test_calibration.py` - Baseline testing against known-safe sites (google.com, github.com)

**Framework Dependencies:**
- pytest >=7.4.0: Already in `veritas/requirements.txt`
- pytest-asyncio >=0.23.0: Already in `veritas/requirements.txt`
- httpx: Already in stack for HTTP client mocking

**Phase 9 Component Integration Check (Required for SEC-02):**
- [ ] **CVSSCalculator**: Check if exists in Phase 9 codebase (likely in `veritas/config/judge/` or `veritas/config/security_rules.py`)
- [ ] **CWEMapper**: Check if exists for CWE ID mapping (likely in `veritas/config/security_rules.py`)
- [ ] **DarknetThreatIntel**: Check if exists in Phase 8 (`veritas/agents/graph_investigator.py`)

*(If any Phase 9/Phase 8 components are missing or differ from assumed interface, update Wave 0 gaps accordingly)*

## Sources

### Primary (HIGH confidence)
- **OWASP Secure Headers Project** - https://owasp.org/www-project-secure-headers/
  - Verified: Critical security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options), CORS headers, permissions policies
- **CWE (Common Weakness Enumeration)** - https://cwe.mitre.org/
  - Verified: CWE system as standardized taxonomy, Base level for vulnerability mapping, CWE-79 (XSS) as example with Observed Examples
- **Python hashlib (stdlib)** - https://docs.python.org/3/library/hashlib.html
  - Verified: Guaranteed algorithms (SHA-2, SHA-3, BLAKE2), PBKDF2-HMAC/scrypt for key derivation, keyed hashing for HMAC, MD5/SHA1 marked as insecure
- **Python ssl (stdlib)** - https://docs.python.org/3/library/ssl.html
  - Verified: SSL context configuration, certificate verification interfaces (referenced - content not fully fetched)
- **requests library (PyPI)** - https://pypi.org/project/requests/
  - Verified: Browser-style TLS/SSL Verification feature (basic documentation only)
- **httpx library (official site)** - https://www.python-httpx.org/
  - Verified: Full HTTP client for Python 3, sync/async APIs, HTTP/1.1 and HTTP/2 support, requests-compatible API, sessions with cookie persistence
- **BeautifulSoup4 (official docs)** - https://www.crummy.com/software/BeautifulSoup/bs4/doc/
  - Verified: Tree-based HTML parsing, navigation methods (down/up/sideways), find/find_all search methods, CSS selectors, handles malformed HTML
- **Playwright (official docs)** - https://playwright.dev/python/
  - Verified: End-to-end testing framework, browser isolation, shadow DOM piercing, inspector tool, trace viewer with DOM snapshots
- **validators (PyPI)** - https://pypi.org/project/validators/
  - Verified: validators.email() function example, validation without schema
- **tldextract (PyPI)** - https://pypi.org/project/tldextract/
  - Verified: Domain parsing (subdomain, domain, suffix), handles multi-level domains (e.g., bbc.co.uk), uses Public Suffix List, ExtractResult attributes
- **cryptography (PyPI)** - https://pypi.org/project/cryptography/
  - Verified: Recommendation over pyOpenSSL (referenced - content not fully fetched)

### Secondary (MEDIUM confidence)
- **OWASP ZAP (official site)** - https://www.zaproxy.org/
  - Verified: World's most widely used web app scanner, free/open source, marketplace for add-ons, automation capabilities
- **CVSS v4.0 Specification (FIRST.org)** - https://www.first.org/cvss/specification-document
  - Verified: Current CVSS version is 4.0 (released 2023), v3.1 is older, v4.0 is backward compatible for severity score boundaries, introduces Base/Exploitability/Impact/Environmental/Supplemental metrics

### Tertiary (LOW confidence - marked for validation)
- **OWASP Top 10 2021 Categories** - https://owasp.org/Top10/
  - Status: REDIRECT_ONLY - page only shows redirect notice to 2025 version
  - Need validation: 2021 category list (A01-A10) from OWASP Wikipedia or archived documentation
  - Alternative: Use OWASP Top 10 Cheat Sheet (attempted but got 404)
- **PCI DSS Security Standards** - https://www.pcisecuritystandards.org/pci_security/
  - Status: FAILED (404)
  - Need validation: PCI DSS 4.0 requirements relevant to web application security
  - Alternative: Download PCI DSS v4.0 PDF directly or search for summary documentation
- **GDPR Compliance Summary** - https://gdpr.eu/summary/
  - Status: FAILED (web_fetch error)
  - Need validation: GDPR cookie consent requirements, Article 4-11 transparency obligations
  - Alternative: Use official GDPR text or compliance guides
- **CVSS v3.1 Calculator** - https://www.first.org/cvss/calculator/3.1
  - Status: FAILED (web_fetch error)
  - Need validation: CVSS v3.1 base metric scoring formula, severity ranges
  - Alternative: Use CVSS v3.1 specification PDF (if accessible)
- **PyJWT Documentation** - https://pyjwt.readthedocs.io/en/stable/
  - Status: FAILED (web_fetch error)
  - Need validation: JWT decoding/validation functions for security checks
  - Alternative: PyPI page or GitHub README

### Project Context (HIGH confidence - from direct file reads)
- **REQUIREMENTS.md** - C:/files/coding dev era/elliot/elliotAI/.planning/REQUIREMENTS.md
  - SEC-01, SEC-02 requirement definitions, phase mapping
- **PLAN.md (Phase 10)** - C:/files/coding dev era/elliot/elliotAI/.planning/phase-10/PLAN.md
  - Detailed implementation strategy, success criteria
- **STACK.md** - C:/files/coding dev era/elliot/elliotAI/.planning/codebase/STACK.md
  - Python 3.10+, FastAPI, LangChain, Playwright, httpx, BeautifulSoup4 already in stack
- **ARCHITECTURE.md** - C:/files/coding dev era/elliot/elliotAI/.planning/codebase/ARCHITECTURE.md
  - Agent patterns, dataclass patterns, async/await patterns, LangGraph orchestration
- **CONVENTIONS.md** - C:/files/coding dev era/elliot/elliotAI/.planning/codebase/CONVENTIONS.md
  - Naming conventions, dataclass usage, async patterns, error handling
- **TESTING.md** - C:/files/coding dev era/elliot/elliotAI/.planning/codebase/TESTING.md
  - pytest framework, pytest-asyncio, test organization, mocking patterns
- **STATE.md** - C:/files/coding dev era/elliot/elliotAI/.planning/STATE.md
  - Phase 9 completion status (CVSSCalculator, CWEMapper should exist)

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - httpx, Playwright, BeautifulSoup4 verified from official docs; OWASP/PCI/GDPR requirements LOW (web_fetch issues, need validation)
- Architecture: HIGH - Based on existing project patterns (dataclasses, async/await, LangGraph), verified from ARCHITECTURE.md, CONVENTIONS.md
- Pitfalls: MEDIUM - Based on common security scanning anti-patterns referenced in industry literature; specific domain experience limited
- CVSS/CVWE: MEDIUM - CWE system verified from official docs; CVSS v3.1 details LOW (web_fetch error), v4.0 verified but not standard yet

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (30 days for OWASP/PCI/GDPR - stable standards), **2026-02-29 (1 day for CVSS v3.1 vs v4.0 decision)** - urgent: verify which CVSS version Phase 9 implements

**Critical Action Items Before Planning:**
1. **Verify Phase 9 CVSSCalculator**: Check if it implements v3.1 or v4.0. This affects all SEC-02 CVSS scoring tests.
2. **Verify Phase 8 DarknetThreatIntel**: Check interface for `analyze_exposure()` method for darknet correlation.
3. **Complete LOW-confidence sources**: Manually verify OWASP Top 10 2021 categories (A01-A10) and get PCI DSS 4.0 summary from alternative sources.
4. **Create Wave 0 test infrastructure**: Generate `tests/test_security/` directory with fixtures before implementation starts.
