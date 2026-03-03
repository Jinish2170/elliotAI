# Phase 09: Judge System & Orchestrator - Research

**Researched:** 2026-02-28
**Domain:** CWE/CVSS standards, dual-tier verdict systems, adaptive orchestration, real-time progress streaming
**Confidence:** MEDIUM

## RESEARCH COMPLETE

## Summary

Phase 9 implements a dual-tier verdict system with technical (CWE/CVSS/IOCs) and non-technical (plain English recommendations) tiers, 11 site-type-specific scoring strategies using the strategy pattern, adaptive orchestrator timeout management based on page complexity, real-time progress streaming with throttling, graceful degradation patterns for agent failures, and estimated completion time calculation for countdown timers. This transformation upgrades VERITAS from a single-tier audit system to a professional-grade forensic platform suitable for both security professionals and general users.

**Primary recommendations:**
1. Use Strategy Pattern with abstract base class for 11 site-type scoring strategies
2. Implement CWE/CVSS v4.0 standard-compliant scoring for technical tier
3. Apply adaptive timeout algorithms using weighted factors (DOM depth, script count, lazy-load detection)
4. Use token-bucket rate limiting for WebSocket event throttling (5 events/sec)
5. Implement circuit breaker pattern with exponential backoff for graceful degradation
6. Use EMA (Exponential Moving Average) for estimated completion time calculation

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| JUDGE-01 | Design dual-tier verdict data classes with VerdictTechnical (CWE, CVSS, IOCs) and VerdictNonTechnical (plain English, recommendations) | Dual-tier pattern from cybersecurity reporting standards, dataclass design patterns |
| JUDGE-02 | Implement 11 site-type-specific scoring strategies with context-aware scoring and base strategy class | Strategy pattern (GoF 1994), existing SiteType enum and profiles |
| JUDGE-03 | Build Judge Agent with dual-tier generation, single trust score, versioned verdict data classes, strategy pattern | Existing JudgeAgent architecture, trust_weights module patterns |
| ORCH-01 | Advanced time management orchestration with dynamic priority adjustment, adaptive timeout strategies, parallel execution optimization, estimated completion time with countdown | Adaptive timeout algorithms, real-time estimation techniques |
| ORCH-02 | Comprehensive error handling with detection, automatic fallback, graceful degradation, "show must go on" policy | Circuit breaker pattern, fallback strategies, degraded mode patterns |
| ORCH-03 | Complexity-aware orchestration with threshold detection, analysis simplification, high-value priority, progressive refinement | Complexity metrics, prioritization algorithms |
| PROG-01 | Progressive screenshot streaming with immediate capture, thumbnail delivery, live scroll visualization, connection health maintenance | WebSocket streaming, image compression, connection monitoring |
| PROG-02 | Real-time pattern/discovery notifications with immediate finding send, live feed, color-coded alerts, incremental confidence updates | Event-driven streaming, alert categorization |
| PROG-03 | User engagement pacing with 5-10s activity signals, agent indicators, progress bars, countdown timers, interesting highlights | UX pacing patterns, progress visualization |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.14+ | 3.14 | Runtime language | Modern async/await, type hints, performance improvements (async issues resolved in v3.14) |
| asyncio | builtin (3.14+) | Async event loop | Concurrent task execution, parallel agent execution |
| dataclasses | builtin (3.14+) | Type-safe data structures | DualVerdict, VerdictTechnical, VerdictNonTechnical models |
| abc | builtin | Abstract base classes | ScoringStrategy base, orchestrator interfaces |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI WebSockets | latest | Real-time event streaming | Progress events, screenshot streaming, finding notifications |
| Pillow (PIL) | latest | Image processing | Thumbnail generation, screenshot compression |
| typing | builtin (3.14+) | Type hints and generics | Strategy pattern, dataclass generics |

### External Standards
| Standard | Version | Purpose | Reference |
|----------|---------|---------|-----------|
| CWE (Common Weakness Enumeration) | 4.11 | Technical vulnerability IDs | https://cwe.mitre.org |
| CVSS (Common Vulnerability Scoring System) | 4.0 | Vulnerability severity scoring | https://www.first.org/cvss |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI WebSockets | Socket.IO | Socket.IO adds protocol overhead; FastAPI native WebSockets simpler for this use case |
| Strategy Pattern | Template Method Pattern | Template Method creates deeper inheritance hierarchies; Strategy enables runtime strategy switching |
| Token-bucket rate limiting | Fixed-delay throttling | Fixed-delay causes burst starvation; token-bucket allows controlled bursts |

**Installation:**
```bash
pip install fastapi uvicorn pillow
```

---

## Architecture Patterns

### Recommended Project Structure

```
veritas/agents/
├── judge/
│   ├── __init__.py                              # NEW: Judge module package
│   ├── judge_agent.py                           # REFACTOR: Dual-tier generation
│   ├── verdict/                                  # NEW: Verdict data classes
│   │   ├── __init__.py
│   │   ├── base.py                              # DualVerdict base class
│   │   ├── technical.py                         # VerdictTechnical (CWE/CVSS/IOCs)
│   │   └── non_technical.py                     # VerdictNonTechnical (plain English)
│   └── strategies/                               # NEW: Site-type scoring strategies
│       ├── __init__.py
│       ├── base.py                              # ScoringStrategy abstract base
│       ├── ecommerce.py                         # E-commerce strategy
│       ├── company_portfolio.py                 # Company portfolio strategy
│       ├── financial.py                         # Financial strategy
│       ├── saas_subscription.py                 # SaaS/subscription strategy
│       ├── news_blog.py                         # News/blog strategy
│       ├── social_media.py                      # Social media strategy
│       ├── education.py                         # Education strategy
│       ├── healthcare.py                        # Healthcare strategy
│       ├── government.py                        # Government strategy
│       ├── gaming.py                            # Gaming strategy
│       └── risk_scoring.py                      # Risk scoring utility

veritas/core/
├── orchestrator.py                               # REFACTOR: Adaptive timeout, graceful degradation
├── timeout_manager.py                           # NEW: Adaptive timeout based on complexity
├── fallback_manager.py                          # NEW: Fallback strategies
├── circuit_breaker.py                           # NEW: Circuit breaker pattern
├── progress/                                     # NEW: Progress streaming
│   ├── __init__.py
│   ├── emitter.py                              # ProgressEvent emitter
│   ├── rate_limiter.py                         # Token-bucket rate limiting
│   ├── event_priority.py                       # Event prioritization
│   └── estimator.py                            # Completion time estimator
└── degradation.py                                # NEW: Graceful degradation patterns

veritas/cwe/                                      # NEW: CWE/CVSS integration
├── __init__.py
├── registry.py                                  # CWE category mapping to findings
├── cvss_calculator.py                           # CVSS v4.0 score calculation
└── severity_cwe_mapping.py                      # Finding severity to CWE mapping
```

---

## Pattern 1: Dual-Tier Verdict Data Classes

**What:** Separate dataclass tiers for technical (CWE/CVSS/IOCs) and non-technical (plain English recommendations) verdicts, with shared trust score in parent DualVerdict class.

**When to use:** When providing forensic reports for dual audiences: security professionals (need technical details) and general users (need actionable plain-language advice).

### Code Pattern

```python
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, list

# CWE/CVSS Standards Enums
class CWMetricStatus(str, Enum):
    """CVSS v4.0 Metric Status."""
    X = "X"    # Not Defined
    H = "H"    # High
    M = "M"    # Medium
    L = "L"    # Low

class SeverityLevel(str, Enum):
    """Standard severity levels matching CWE/CVSS."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class CVSSMetrics:
    """
    CVSS v4.0 metrics for technical reporting.

    CVSS v4.0 Formula (simplified):
    Base = CVE Base Metric Group
    Impact = Subscore Impact Formula
    Exploitability = Subscore Exploitability Formula
    Score = BaseScore(0.0) + Impact + Exploitability

    Full reference: https://www.first.org/cvss/calculator/4.0
    """
    attack_vector: CWMetricStatus = CWMetricStatus.N  # Attack Vector (A:N)
    attack_complexity: CWMetricStatus = CWMetricStatus.L
    privileges_required: CWMetricStatus = CWMetricStatus.N
    user_interaction: CWMetricStatus = CWMetricStatus.N
    scope: CWMetricStatus = CWMetricStatus.U  # Scope Changed (S:U)
    confidentiality: CWMetricStatus = CWMetricStatus.H
    integrity: CWMetricStatus = CWMetricStatus.H
    availability: CWMetricStatus = CWMetricStatus.N

    def calculate_score(self) -> float:
        """
        Calculate simplified CVSS v4.0 score (0.0-10.0).

        Note: Full CVSS v4.0 calculation requires complex formula.
        This is a simplified approximation for the dual-tier system.
        """
        # Simplified scoring based on impact metrics
        impact_score = (
            (self.confidentiality == CWMetricStatus.H and 0.56 or 0.0) +
            (self.integrity == CWMetricStatus.H and 0.56 or 0.0) +
            (self.availability == CWMetricStatus.H and 0.56 or 0.0)
        )

        # Exploitability factor
        exploitability_score = 0.85 if self.attack_vector == CWMetricStatus.N else 0.62

        # Combine
        if self.scope == CWMetricStatus.C:  # Scope Changed
            base_score = min(10.0, impact_score + exploitability_score)
        else:
            base_score = min(10.0, impact_score * exploitability_score)

        return round(base_score, 1)

@dataclass
class CWEEntry:
    """
    Single CWE (Common Weakness Enumeration) entry.

    Format: CWE-XXX (e.g., CWE-79: Cross-site Scripting)
    Reference: https://cwe.mitre.org/data/index.html
    """
    cwe_id: str  # "CWE-79"
    name: str    # "Cross-site Scripting"
    description: str  # Full CWE description
    url: str = "https://cwe.mitre.org/data/definitions/79.html"  # Auto-generated from ID

@dataclass
class IOC:
    """
    Indicator of Compromise for technical reporting.

    IOCs are forensic artifacts that indicate a security incident.
    Common types: IP addresses, domains, hashes, URLs, email addresses.
    """
    type: str  # "domain", "ip", "url", "hash", "email"
    value: str  # The actual IOC value
    source: str  # Where this IOC was detected (e.g., "osint_phishing_db")
    severity: SeverityLevel = SeverityLevel.MEDIUM
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class VerdictTechnical:
    """
    Technical tier of dual verdict for security professionals.

    Includes detailed CWE IDs, CVSS scores, and IOCs for forensic analysis.
    Designed for penetration testers, security auditors, and SOC analysts.
    """
    cwe_entries: list[CWEEntry] = field(default_factory=list)
    cvss_metrics: Optional[CVSSMetrics] = None
    cvss_score: float = 0.0  # Calculated from cvss_metrics
    iocs: list[IOC] = field(default_factory=list)
    threat_indicators: list[dict] = field(default_factory=list)  # Raw threat intelligence
    version: str = "v2.0"  # Verdict version for backward compatibility

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "cwe_entries": [
                {
                    "cwe_id": c.cwe_id,
                    "name": c.name,
                    "description": c.description,
                    "url": c.url,
                }
                for c in self.cwe_entries
            ],
            "cvss_metrics": None if self.cvss_metrics is None else {
                "attack_vector": self.cvss_metrics.attack_vector.value,
                "attack_complexity": self.cvss_metrics.attack_complexity.value,
                "privileges_required": self.cvss_metrics.privileges_required.value,
                "user_interaction": self.cvss_metrics.user_interaction.value,
                "scope": self.cvss_metrics.scope.value,
                "confidentiality": self.cvss_metrics.confidentiality.value,
                "integrity": self.cvss_metrics.integrity.value,
                "availability": self.cvss_metrics.availability.value,
            },
            "cvss_score": self.cvss_score,
            "iocs": [
                {
                    "type": i.type,
                    "value": i.value,
                    "source": i.source,
                    "severity": i.severity.value,
                    "timestamp": i.timestamp,
                }
                for i in self.iocs
            ],
            "threat_indicators": self.threat_indicators,
            "version": self.version,
        }

@dataclass
class VerdictNonTechnical:
    """
    Non-technical tier of dual verdict for general users.

    Provides plain-English recommendations, actionable advice,
    and user-friendly explanations without jargon.
    """
    risk_level: str  # "safe", "caution", "high_risk", "dangerous"
    summary: str  # 1-sentence summary (human-readable)
    key_findings: list[str] = field(default_factory=list)  # 3-5 bullet points
    recommendations: list[str] = field(default_factory=list)  # Actionable steps
    warnings: list[str] = field(default_factory=list)  # Critical warnings (red flags)
    green_flags: list[str] = field(default_factory=list)  # Positive indicators
    simple_explanation: str = ""  # "What this means" section
    version: str = "v2.0"

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "risk_level": self.risk_level,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "green_flags": self.green_flags,
            "simple_explanation": self.simple_explanation,
            "version": self.version,
        }

@dataclass
class DualVerdict:
    """
    Parent container for dual-tier verdict system.

    Combines technical and non-technical tiers with shared trust score.
    Single trust score calculated once and shared between tiers to ensure consistency.

    Usage:
        verdict = DualVerdict(
            trust_score=87,
            technical=VerdictTechnical(
                cwe_entries=[CWEEntry(...)],
                cvss_score=7.5,
                iocs=[IOC(...)]
            ),
            non_technical=VerdictNonTechnical(
                risk_level="caution",
                summary="This site shows mixed signals...",
                recommendations=["Check SSL certificate", ...]
            )
        )
    """
    trust_score: int  # 0-100, shared between tiers
    risk_level: str  # Derived from trust_score
    technical: VerdictTechnical
    non_technical: VerdictNonTechnical
    site_type: str = ""
    auditor_version: str = "veritas-v2.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Derive risk_level from trust_score."""
        if self.trust_score >= 90:
            self.risk_level = "trusted"
        elif self.trust_score >= 70:
            self.risk_level = "probably_safe"
        elif self.trust_score >= 40:
            self.risk_level = "suspicious"
        elif self.trust_score >= 20:
            self.risk_level = "high_risk"
        else:
            self.risk_level = "dangerous"

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "trust_score": self.trust_score,
            "risk_level": self.risk_level,
            "technical": self.technical.to_dict(),
            "non_technical": self.non_technical.to_dict(),
            "site_type": self.site_type,
            "auditor_version": self.auditor_version,
            "timestamp": self.timestamp,
        }

    @property
    def is_safe(self) -> bool:
        """Quick check if site is considered safe (trust_score >= 70)."""
        return self.trust_score >= 70

    @property
    def hasCriticalThreats(self) -> bool:
        """Quick check for critical threats (CVSS >= 9.0 OR CWE includes critical entries)."""
        cvss_critical = self.technical.cvss_score >= 9.0
        critical_cwe = any(
            "CWE-787" in c.cwe_id or "CWE-125" in c.cwe_id or "CWE-287" in c.cwe_id
            for c in self.technical.cwe_entries
        )
        return cvss_critical or critical_cwe
```

### CWE Category Mapping to Findings

```python
# veritas/cwe/registry.py

from typing import Optional
from enum import Enum

class CWECategory(str, Enum):
    """High-level CWE categories for finding matching."""
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTHORIZATION = "authorization"
    CRYPTO = "crypto"
    INPUT_VALIDATION = "input_validation"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INFO_DISCLOSURE = "info_disclosure"
    DEFAULT_CREDENTIALS = "default_credentials"
    HARD_CODED_CREDENTIALS = "hard_coded_credentials"
    INSECURE_STORAGE = "insecure_storage"
    MISCONFIGURATION = "misconfiguration"

# Simplified CWE registry for Phase 9
# Full CWE database would require external API or local copy
CWE_REGISTRY: dict[str, CWEEntry] = {
    # Injection attacks
    "CWE-787": CWEEntry(
        cwe_id="CWE-787",
        name="Out-of-bounds Write",
        description="The software writes data past the end, or before the beginning, of the intended buffer.",
        url="https://cwe.mitre.org/data/definitions/787.html"
    ),
    "CWE-79": CWEEntry(
        cwe_id="CWE-79",
        name="Cross-site Scripting",
        description="The software does not properly neutralize or incorrectly neutralizes user-controllable input before it is placed in output that is used as a web page.",
        url="https://cwe.mitre.org/data/definitions/79.html"
    ),
    "CWE-352": CWEEntry(
        cwe_id="CWE-352",
        name="Cross-Site Request Forgery",
        description="The web application does not, or can not, sufficiently verify whether a well-formed, valid, consistent request was intentionally provided by the user who submitted the request.",
        url="https://cwe.mitre.org/data/definitions/352.html"
    ),

    # Authorization
    "CWE-287": CWEEntry(
        cwe_id="CWE-287",
        name="Improper Authentication",
        description="The software does not properly authenticate users, allowing actors to bypass intended access controls.",
        url="https://cwe.mitre.org/data/definitions/287.html"
    ),
    "CWE-862": CWEEntry(
        cwe_id="CWE-862",
        name="Missing Authorization",
        description="The product does not perform an authorization check when an actor attempts to access a resource or perform an action.",
        url="https://cwe.mitre.org/data/definitions/862.html"
    ),

    # Cryptography
    "CWE-327": CWEEntry(
        cwe_id="CWE-327",
        name="Use of a Broken or Risky Cryptographic Algorithm",
        description="The product uses an algorithm that is insufficient for cryptographic purposes.",
        url="https://cwe.mitre.org/data/definitions/327.html"
    ),
    "CWE-319": CWEEntry(
        cwe_id="CWE-319",
        name="Cleartext Transmission of Sensitive Information",
        description="The software transmits sensitive or security-critical data in cleartext in a communication channel.",
        url="https://cwe.mitre.org/data/definitions/319.html"
    ),

    # Input validation
    "CWE-20": CWEEntry(
        cwe_id="CWE-20",
        name="Improper Input Validation",
        description="The product does not validate or incorrectly validates input that can affect the control flow or data flow of a program.",
        url="https://cwe.mitre.org/data/definitions/20.html"
    ),

    # Web-specific
    "CWE-601": CWEEntry(
        cwe_id="CWE-601",
        name="URL Redirection to Untrusted Site",
        description="The web application accepts untrusted input that causes the web application to redirect the request to a URL contained within untrusted input.",
        url="https://cwe.mitre.org/data/definitions/601.html"
    ),
    "CWE-525": CWEEntry(
        cwe_id="CWE-525",
        name="Use of Web Browser Cache Containing Sensitive Information",
        description="The web application uses a web cache that contains sensitive information but does not properly protect it from unauthorized access.",
        url="https://cwe.mitre.org/data/definitions/525.html"
    ),
}

def find_cwe_by_category(category: CWECategory, limit: int = 3) -> list[CWEEntry]:
    """
    Find CWE entries relevant to a finding category.

    Args:
        category: CWECategory enum value
        limit: Maximum number of CWE entries to return

    Returns:
        List of relevant CWEEntry objects
    """
    # Simplified matching - would use category mappings in production
    category_mapping: dict[CWECategory, list[str]] = {
        CWECategory.INJECTION: ["CWE-94", "CWE-787", "CWE-89"],
        CWECategory.XSS: ["CWE-79", "CWE-80", "CWE-83"],
        CWECategory.CSRF: ["CWE-352"],
        CWECategory.AUTHORIZATION: ["CWE-287", "CWE-862", "CWE-639"],
        CWECategory.CRYPTO: ["CWE-327", "CWE-319", "CWE-328"],
        CWECategory.INPUT_VALIDATION: ["CWE-20", "CWE-129", "CWE-1287"],
        CWECategory.INFO_DISCLOSURE: ["CWE-200", "CWE-201", "CWE-215"],
        CWECategory.DEFAULT_CREDENTIALS: ["CWE-798", "CWE-345"],
        CWECategory.HARD_CODED_CREDENTIALS: ["CWE-798"],
        CWECategory.INSECURE_STORAGE: ["CWE-922", "CWE-256"],
        CWECategory.MISCONFIGURATION: ["CWE-16", "CWE-2", "CWE-310"],
    }

    cwe_ids = category_mapping.get(category, [])
    cwes = [CWE_REGISTRY[cwe_id] for cwe_id in cwe_ids if cwe_id in CWE_REGISTRY]

    return cwes[:limit]

def map_finding_to_cwe(
    finding_category: str,
    severity: SeverityLevel
) -> Optional[CWEEntry]:
    """
    Map a VERITAS finding to a relevant CWE entry.

    Args:
        finding_category: Finding category (e.g., "xss", "phishing", "injection")
        severity: Finding severity level

    Returns:
        Matching CWEEntry or None
    """
    # Simplified mapping - production would use semantic matching
    category_map: dict[str, CWECategory] = {
        "xss": CWECategory.XSS,
        "csrf": CWECategory.CSRF,
        "injection": CWECategory.INJECTION,
        "auth": CWECategory.AUTHORIZATION,
        "crypto": CWECategory.CRYPTO,
        "misconfig": CWECategory.MISCONFIGURATION,
        "phishing": CWECategory.MISCONFIGURATION,  # Phishing maps to misconfiguration
        "redirect": CWECategory.INFO_DISCLOSURE,
        "ssl": CWECategory.CRYPTO,
    }

    category = category_map.get(finding_category.lower())
    if category:
        cwes = find_cwe_by_category(category, limit=1)
        return cwes[0] if cwes else None

    return None
```

---

## Pattern 2: Site-Type Scoring Strategies (Strategy Pattern)

**What:** Use Strategy Pattern (GoF 1994) to encapsulate site-type-specific scoring logic. Each strategy extends abstract base class ScoringStrategy and provides custom scoring adjustments for 11 site types.

**When to use:** When you have algorithm families (scoring for different site types) and want to define them separately, avoid conditional logic sprawl, and allow runtime strategy switching.

### Code Pattern

```python
# veritas/agents/judge/strategies/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from config.site_types import SiteType

# Extend SiteType enum to include all 11 types
class ExtendedSiteType(str, Enum):
    """Complete 11-site-type classification."""
    ECOMMERCE = "ecommerce"
    COMPANY_PORTFOLIO = "company_portfolio"
    FINANCIAL = "financial"
    SAAS_SUBSCRIPTION = "saas_subscription"
    NEWS_BLOG = "news_blog"
    SOCIAL_MEDIA = "social_media"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    GOVERNMENT = "government"
    GAMING = "gaming"
    DARKNET_SUSPICIOUS = "darknet_suspicious"

@dataclass
class ScoringContext:
    """
    Context object passed to strategies for scoring.

    Contains all available evidence that a strategy might use
    for context-aware scoring.
    """
    url: str
    site_type: ExtendedSiteType
    site_type_confidence: float

    # Evidence sources
    visual_score: float
    structural_score: float
    temporal_score: float
    graph_score: float
    meta_score: float
    security_score: float

    # Additional context
    has_ssl: bool = False
    domain_age_days: int = 0
    has_dark_patterns: bool = False
    dark_pattern_types: list[str] = field(default_factory=list)
    has_phishing_hits: bool = False
    js_risk_score: float = 1.0  # 0-1, where 1=clean
    form_validation_score: float = 1.0
    has_cross_domain_forms: bool = False

    # Page complexity (for adaptive timeout)
    dom_depth: int = 0
    script_count: int = 0
    has_lazy_load: bool = False
    screenshot_count: int = 0

@dataclass
class ScoringAdjustment:
    """
    Result of strategy scoring: adjustments to apply to base weights.

    Strategies return adjustments rather than direct scores, enabling
    composition with the existing trust_weights.compute_trust_score().
    """
    weight_adjustments: dict[str, float]  # {signal: adjustment_factor}
    severity_modifications: dict[str, str]  # {finding_id: new_severity}
    custom_findings: list[dict] = field(default_factory=list)  # Site-type-specific findings
    narrative_template: str = ""  # Template for narrative focus
    explanation: str = ""

class ScoringStrategy(ABC):
    """
    Abstract base class for site-type-specific scoring strategies.

    All 11 site-type strategies must extend this class and implement
    the calculate_adjustments() method.

    Design Intent:
    - Single responsibility: Each strategy handles one site type
    - Open/closed principle: Add new strategies without modifying existing code
    - Dependency inversion: JudgeAgent depends on ScoringStrategy abstraction
    """

    @property
    @abstractmethod
    def site_type(self) -> ExtendedSiteType:
        """Return the site type this strategy handles."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return human-readable strategy name."""
        pass

    @abstractmethod
    def calculate_adjustments(
        self,
        context: ScoringContext
    ) -> ScoringAdjustment:
        """
        Calculate scoring adjustments based on context.

        Args:
            context: ScoringContext with all evidence

        Returns:
            ScoringAdjustment with weight adjustments and severity modifications
        """
        pass

    def _detect_critical_triggers(self, context: ScoringContext) -> list[str]:
        """
        Detect critical red flags specific to this site type.

        Subclasses can override to add site-type-specific triggers.
        """
        triggers = []

        # Universal critical triggers
        if not context.has_ssl and context.site_type in [
            ExtendedSiteType.FINANCIAL,
            ExtendedSiteType.SAAS_SUBSCRIPTION,
        ]:
            triggers.append("missing_ssl_high_risk_site")

        if context.has_phishing_hits:
            triggers.append("phishing_database_hit")

        if context.js_risk_score < 0.3:  # High obfuscation
            triggers.append("high_js_risk")

        return triggers

    def _calculate_weight_adjustments(
        self,
        context: ScoringContext
    ) -> dict[str, float]:
        """
        Calculate base weight adjustments.

        Subclasses can override this method for custom adjustments.
        Default返回: No adjustment.
        """
        return {}

    def _calculate_severity_modifications(
        self,
        context: ScoringContext
    ) -> dict[str, str]:
        """
        Calculate severity modifications for findings.

        Subclasses can override this method for custom modifications.
        Default返回: No modification.
        """
        return {}
```

### Example Strategy Implementations

```python
# veritas/agents/judge/strategies/ecommerce.py

from .base import ScoringStrategy, ScoringAdjustment, ScoringContext, ExtendedSiteType

class EcommerceScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for e-commerce sites.

    Priority signals:
    - Visual (0.25): Dark patterns (fake scarcity, hidden costs) are critical
    - Security (0.20): SSL, form validation, and payment security
    - Structural (0.15): Pricing transparency, checkout flow
    - Temporal (0.15): Fake countdowns, fake urgency
    - Graph (0.20): Seller verification, reviews authenticity
    - Meta (0.05): Domain age, SSL issuer

    Critical triggers for e-commerce:
    - Missing SSL
    - Fake scarcity/countdowns
    - Hidden costs detected
    - Pre-selected options
    - Fake reviews
    - Fake trust badges
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        return ExtendedSiteType.ECOMMERCE

    @property
    def name(self) -> str:
        return "E-commerce Scoring Strategy"

    def calculate_adjustments(
        self,
        context: ScoringContext
    ) -> ScoringAdjustment:
        adjustments = self._calculate_weight_adjustments(context)
        severity_mods = self._calculate_severity_modifications(context)
        custom_findings = []

        # E-commerce critical checks
        if not context.has_ssl:
            custom_findings.append({
                "type": "missing_ssl",
                "severity": "CRITICAL",
                "message": "E-commerce site without SSL - payment information at risk",
                "impact": "trust"
            })

        if "fake_scarcity" in context.dark_pattern_types:
            custom_findings.append({
                "type": "fake_scarcity",
                "severity": "HIGH",
                "message": "Site uses fake scarcity tactics (fake 'X left', fake countdowns)",
                "impact": "manipulation"
            })

        if context.has_cross_domain_forms:
            custom_findings.append({
                "type": "cross_domain_payment",
                "severity": "HIGH",
                "message": "Payment forms submit to different domain - potential phishing",
                "impact": "security"
            })

        return ScoringAdjustment(
            weight_adjustments=adjustments,
            severity_modifications=severity_mods,
            custom_findings=custom_findings,
            narrative_template=(
                "Focus on pricing transparency, checkout fairness, return policy visibility, "
                "hidden fees, pre-selected add-ons, scarcity manipulation, and review authenticity."
            ),
            explanation=(
                f"E-commerce scoring emphasizes visual detection of dark patterns ({context.visual_score:.2f}) "
                f"and payment security ({context.security_score:.2f}). "
                f"Missing SSL or fake scarcity detected."
            )
        )

    def _calculate_weight_adjustments(
        self,
        context: ScoringContext
    ) -> dict[str, float]:
        """E-commerce-specific weight adjustments."""
        adjustments = {
            "visual": 0.25,  # Higher weight due to dark pattern importance
            "security": 0.20,
            "structural": 0.15,
            "temporal": 0.15,  # Fake countdowns are common in e-commerce
            "graph": 0.20,
            "meta": 0.05,
        }

        # Boost visual weight if dark patterns detected
        if context.has_dark_patterns:
            adjustments["visual"] = 0.30
            adjustments["structural"] = 0.10  # Reduce structural to maintain sum=1.0

        return adjustments

    def _calculate_severity_modifications(
        self,
        context: ScoringContext
    ) -> dict[str, str]:
        """E commerce-specific severity upgrades."""
        modifications = {}

        # Critical findings for e-commerce
        critical_patterns = [
            "hidden_costs", "pre_selected_options", "fake_scarcity",
            "fake_countdown", "bait_and_switch", "hidden_subscription"
        ]

        if context.dark_pattern_types:
            for pattern in context.dark_pattern_types:
                if pattern in critical_patterns:
                    modifications[pattern] = "CRITICAL"

        return modifications


# veritas/agents/judge/strategies/financial.py

class FinancialScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for financial/banking sites.

    PRIORITY: ZERO TOLERANCE for security issues.

    Priority signals:
    - Security (0.30): SSL, form security, encryption standards
    - Structural (0.25): Form validation, cross-domain checks
    - Graph (0.20): Entity verification (real bank vs phishing)
    - Visual (0.10): Less important for banking sites
    - Meta (0.10): SSL, domain age
    - Temporal (0.05): Minimal importance

    Critical triggers for financial:
    - Missing SSL → Automatic score drop
    - Cross-domain forms → Critical
    - Unverified entity → High risk
    - Darknet patterns → Maximum paranoia
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        return ExtendedSiteType.FINANCIAL

    @property
    def name(self) -> str:
        return "Financial Services Scoring Strategy"

    def calculate_adjustments(
        self,
        context: ScoringContext
    ) -> ScoringAdjustment:
        adjustments = self._calculate_weight_adjustments(context)
        severity_mods = self._calculate_severity_modifications(context)
        custom_findings = []

        # Zero tolerance for security issues
        if not context.has_ssl:
            custom_findings.append({
                "type": "missing_ssl_financial",
                "severity": "CRITICAL",
                "message": "Financial site without SSL - HIGH SECURITY RISK",
                "impact": "security",
                "auto_deduct": 50  # Automatic 50-point deduction
            })

        if context.has_cross_domain_forms:
            custom_findings.append({
                "type": "cross_domain_financial",
                "severity": "CRITICAL",
                "message": "Financial forms submit to different domain - LIKELY PHISHING",
                "impact": "security",
                "auto_deduct": 40
            })

        if context.form_validation_score < 0.5:
            custom_findings.append({
                "type": "form_validation_failed",
                "severity": "HIGH",
                "message": "Financial forms have poor validation - potential injection risk",
                "impact": "vulnerability"
            })

        return ScoringAdjustment(
            weight_adjustments=adjustments,
            severity_modifications=severity_mods,
            custom_findings=custom_findings,
            narrative_template=(
                "ZERO TOLERANCE for security issues. Emphasize SSL, form security, "
                "encryption standards, entity verification, and regulatory compliance."
            ),
            explanation=(
                f"Financial scoring prioritizes security ({adjustments['security']:.2f}) and "
                f"structural validation ({adjustments['structural']:.2f}). "
                f"Missing SSL or cross-domain forms detected."
            )
        )

    def _calculate_weight_adjustments(
        self,
        context: ScoringContext
    ) -> dict[str, float]:
        """Financial-specific weight adjustments."""
        return {
            "visual": 0.10,
            "structural": 0.25,  # Higher for form security
            "temporal": 0.05,
            "graph": 0.20,
            "meta": 0.10,
            "security": 0.30,  # Highest priority
        }

    def _calculate_severity_modifications(
        self,
        context: ScoringContext
    ) -> dict[str, str]:
        """Financial-specific severity upgrades."""
        modifications = {}

        # All manipulative patterns are CRITICAL for financial sites
        critical_patterns = [
            "hidden_costs", "hidden_cancel", "roach_motel",
            "hidden_subscription", "forced_registration"
        ]

        if context.dark_pattern_types:
            for pattern in context.dark_pattern_types:
                if pattern in critical_patterns:
                    modifications[pattern] = "CRITICAL"

        return modifications


# veritas/agents/judge/strategies/saas_subscription.py

class SaaSSubscriptionScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for SaaS/subscription sites.

    Priority signals:
    - Visual (0.20): Dark patterns (hidden cancel, forced registration)
    - Security (0.20): SSL, form validation
    - Temporal (0.15): Fake countdowns, expiring offers
    - Structural (0.15): Pricing transparency
    - Graph (0.20): Company verification
    - Meta (0.10): Domain age, SSL

    Critical triggers for SaaS:
    - Hidden cancel button
    - Roach motel patterns
    - Forced registration without trial
    - Fake expiring offers
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        return ExtendedSiteType.SAAS_SUBSCRIPTION

    @property
    def name(self) -> str:
        return "SaaS/Subscription Scoring Strategy"

    def calculate_adjustments(
        self,
        context: ScoringContext
    ) -> ScoringAdjustment:
        adjustments = self._calculate_weight_adjustments(context)
        severity_mods = self._calculate_severity_modifications(context)
        custom_findings = []

        # SaaS-specific dark patterns
        critical_saa_patterns = [
            "hidden_cancel", "roach_motel", "forced_registration",
            "expiring_offer"
        ]

        for pattern in context.dark_pattern_types:
            if pattern in critical_saa_patterns:
                custom_findings.append({
                    "type": pattern,
                    "severity": "HIGH" if pattern != "hidden_cancel" else "CRITICAL",
                    "message": f"SaaS site uses manipulative pattern: {pattern}",
                    "impact": "manipulation"
                })

        return ScoringAdjustment(
            weight_adjustments=adjustments,
            severity_modifications=severity_mods,
            custom_findings=custom_findings,
            narrative_template=(
                "Focus on cancellation transparency, trial-to-paid conversion clarity, "
                "pricing page honesty, forced account creation, and subscription traps."
            ),
            explanation=(
                f"SaaS scoring emphasizes dark pattern detection ({context.visual_score:.2f}) "
                f"and temporal analysis ({context.temporal_score:.2f}). "
            )
        )

    def _calculate_weight_adjustments(
        self,
        context: ScoringContext
    ) -> dict[str, float]:
        """SaaS-specific weight adjustments."""
        return {
            "visual": 0.20,
            "structural": 0.15,
            "temporal": 0.15,  # Fake expiration common in SaaS
            "graph": 0.20,
            "meta": 0.10,
            "security": 0.20,
        }

    def _calculate_severity_modifications(
        self,
        context: ScoringContext
    ) -> dict[str, str]:
        """SaaS-specific severity upgrades."""
        modifications = {}

        if "hidden_cancel" in context.dark_pattern_types:
            modifications["hidden_cancel"] = "CRITICAL"

        if "roach_motel" in context.dark_pattern_types:
            modifications["roach_motel"] = "CRITICAL"

        if "forced_registration" in context.dark_pattern_types:
            modifications["forced_registration"] = "HIGH"

        return modifications


# veritas/agents/judge/strategies/__init__.py

from .base import ScoringStrategy, ScoringContext, ScoringAdjustment, ExtendedSiteType
from .ecommerce import EcommerceScoringStrategy
from .financial import FinancialScoringStrategy
from .saas_subscription import SaaSSubscriptionScoringStrategy

# Additional strategies would be imported here:
# from .company_portfolio import CompanyPortfolioScoringStrategy
# from .news_blog import NewsBlogScoringStrategy
# from .social_media import SocialMediaScoringStrategy
# from .education import EducationScoringStrategy
# from .healthcare import HealthcareScoringStrategy
# from .government import GovernmentScoringStrategy
# from .gaming import GamingScoringStrategy
# from .darknet_suspicious import DarknetSuspiciousScoringStrategy

# Strategy registry
STRATEGY_REGISTRY: dict[ExtendedSiteType, type[ScoringStrategy]] = {
    ExtendedSiteType.ECOMMERCE: EcommerceScoringStrategy,
    ExtendedSiteType.FINANCIAL: FinancialScoringStrategy,
    ExtendedSiteType.SAAS_SUBSCRIPTION: SaaSSubscriptionScoringStrategy,
    # ExtendedSiteType.COMPANY_PORTFOLIO: CompanyPortfolioScoringStrategy,
    # ExtendedSiteType.NEWS_BLOG: NewsBlogScoringStrategy,
    # ExtendedSiteType.SOCIAL_MEDIA: SocialMediaScoringStrategy,
    # ExtendedSiteType.EDUCATION: EducationScoringStrategy,
    # ExtendedSiteType.HEALTHCARE: HealthcareScoringStrategy,
    # ExtendedSiteType.GOVERNMENT: GovernmentScoringStrategy,
    # ExtendedSiteType.GAMING: GamingScoringStrategy,
    # ExtendedSiteType.DARKNET_SUSPICIOUS: DarknetSuspiciousScoringStrategy,
}

def get_strategy(site_type: ExtendedSiteType) -> Optional[ScoringStrategy]:
    """
    Get the scoring strategy for a given site type.

    Args:
        site_type: ExtendedSiteType enum value

    Returns:
        ScoringStrategy instance or None if no strategy registered
    """
    strategy_class = STRATEGY_REGISTRY.get(site_type)
    if strategy_class:
        return strategy_class()
    return None

def get_all_strategies() -> dict[ExtendedSiteType, ScoringStrategy]:
    """
    Get all registered strategies.

    Returns:
        Dict mapping site types to strategy instances
    """
    return {
        site_type: strategy_class()
        for site_type, strategy_class in STRATEGY_REGISTRY.items()
    }
```

---

## Pattern 3: Adaptive Timeout Orchestrator

**What:** Dynamically adjust agent timeouts based on page complexity metrics (DOM depth, script count, lazy-load detection). Use weighted complexity score to select timeout strategy (fast/standard/conservative).

**When to use:** When orchestrating multi-agent executions with varying page complexities, where fixed timeouts either waste time on simple pages or timeout prematurely on complex pages.

### Code Pattern

```python
# veritas/core/timeout_manager.py

from dataclasses import dataclass, field
from enum import Enum
import time
from collections import deque
from typing import Optional

class TimeoutStrategy(str, Enum):
    """Timeout strategy based on page complexity."""
    FAST = "fast"              # Simple pages: 8-10s
    STANDARD = "standard"      # Normal pages: 15-20s
    CONSERVATIVE = "conservative"  # Complex pages: 25-35s
    ADAPTIVE = "adaptive"      # Dynamically adjusted based on history

@dataclass
class ComplexityMetrics:
    """
    Page complexity metrics for timeout calculation.

    Collected during Scout phase, used for adaptive timeout selection.
    """
    url: str
    site_type: str

    # Complexity factors
    dom_depth: int = 0           # Average DOM nesting depth
    dom_node_count: int = 0      # Total DOM nodes
    script_count: int = 0        # Number of <script> tags
    stylesheet_count: int = 0    # Number of <link rel="stylesheet"> tags
    inline_style_count: int = 0  # Number of elements with inline styles
    iframes_count: int = 0       # Number of <iframe> tags
    has_lazy_load: bool = False  # Lazy-loading detected
    lazy_load_threshold: int = 0 # Scroll cycles to trigger lazy load
    screenshot_count: int = 0    # Number of screenshots captured
    viewport_changes: int = 0    # Number of viewport size changes

    # Performance metrics
    initial_load_time_ms: int = 0
    network_idle_time_ms: int = 0
    dom_content_loaded_time_ms: int = 0
    total_load_time_ms: int = 0

    def calculate_complexity_score(self) -> float:
        """
        Calculate complexity score (0.0 - 1.0).

        Higher scores indicate more complex pages requiring longer timeouts.

        Weights based on empirical performance:
        - dom_node_count (0.35): Largest factor - more nodes = more processing
        - script_count (0.25): Scripts increase processing time
        - lazy_load (0.20): Lazy-loaded pages need extra time
        - iframes (0.10): Iframes increase complexity
        - load_time (0.10): Slow initial loads correlate with slow agents
        """
        # Normalize each factor to 0.0-1.0
        dom_factor = min(1.0, self.dom_node_count / 5000.0)  # 5000+ nodes = max
        script_factor = min(1.0, self.script_count / 50.0)   # 50+ scripts = max
        iframe_factor = min(1.0, self.iframes_count / 5.0)   # 5+ iframes = max
        lazy_factor = 1.0 if self.has_lazy_load else 0.0
        time_factor = min(1.0, self.total_load_time_ms / 10000.0)  # 10s+ = max

        # Weighted sum
        score = (
            dom_factor * 0.35 +
            script_factor * 0.25 +
            lazy_factor * 0.20 +
            iframe_factor * 0.10 +
            time_factor * 0.10
        )

        return round(score, 2)

@dataclass
class TimeoutConfig:
    """
    Timeout configuration for each agent.

    Times are in seconds.
    """
    scout_timeout: int = 20
    vision_timeout: int = 30
    security_timeout: int = 15
    graph_timeout: int = 10
    judge_timeout: int = 10
    osint_timeout: int = 25

    def to_dict(self) -> dict:
        return {
            "scout": self.scout_timeout,
            "vision": self.vision_timeout,
            "security": self.security_timeout,
            "graph": self.graph_timeout,
            "judge": self.judge_timeout,
            "osint": self.osint_timeout,
        }

# predefined timeout strategies
TIMEOUT_STRATEGIES: dict[TimeoutStrategy, TimeoutConfig] = {
    TimeoutStrategy.FAST: TimeoutConfig(
        scout_timeout=10,
        vision_timeout=15,
        security_timeout=8,
        graph_timeout=5,
        judge_timeout=5,
        osint_timeout=15,
    ),
    TimeoutStrategy.STANDARD: TimeoutConfig(
        scout_timeout=20,
        vision_timeout=30,
        security_timeout=15,
        graph_timeout=10,
        judge_timeout=10,
        osint_timeout=25,
    ),
    TimeoutStrategy.CONSERVATIVE: TimeoutConfig(
        scout_timeout=35,
        vision_timeout=50,
        security_timeout=25,
        graph_timeout=15,
        judge_timeout=15,
        osint_timeout=40,
    ),
}

class TimeoutManager:
    """
    Manages adaptive timeout calculation based on page complexity.

    Uses complexity metrics to select appropriate timeout strategy
    and tracks historical performance for adaptive adjustment.

    Usage:
        manager = TimeoutManager()

        # After Scout collects complexity metrics
        metrics = ComplexityMetrics(
            url="https://example.com",
            site_type="ecommerce",
            dom_node_count=3500,
            script_count=25,
            has_lazy_load=True,
            total_load_time_ms=4500
        )

        config = manager.calculate_timeout_config(metrics)

        # Use config for agent execution
        await vision_agent.analyze(timeout=config.vision_timeout)
    """

    def __init__(self, strategy: TimeoutStrategy = TimeoutStrategy.ADAPTIVE):
        self._strategy = strategy
        self._history: dict[str, deque] = {}  # site_type -> deque of execution times
        self._max_history = 10  # Keep last 10 execution times per site type

    def _track_execution_time(self, site_type: str, agent: str, duration_ms: int):
        """Track execution time for adaptive learning."""
        if site_type not in self._history:
            self._history[site_type] = deque(maxlen=self._max_history)

        key = f"{site_type}:{agent}"
        if key not in self._history:
            self._history[key] = deque(maxlen=self._max_history)

        self._history[key].append(duration_ms)

    def _get_historical_average(self, site_type: str, agent: str) -> Optional[int]:
        """Get average execution time for site type and agent."""
        key = f"{site_type}:{agent}"
        times = self._history.get(key)
        if times and len(times) > 0:
            return sum(times) // len(times)
        return None

    def calculate_timeout_config(self, metrics: ComplexityMetrics) -> TimeoutConfig:
        """
        Calculate adaptive timeout configuration based on complexity.

        Args:
            metrics: ComplexityMetrics collected by Scout

        Returns:
            TimeoutConfig with agent-specific timeouts
        """
        complexity = metrics.calculate_complexity_score()

        # Select strategy based on complexity
        if self._strategy == TimeoutStrategy.ADAPTIVE:
            if complexity < 0.30:
                base_strategy = TimeoutStrategy.FAST
            elif complexity < 0.60:
                base_strategy = TimeoutStrategy.STANDARD
            else:
                base_strategy = TimeoutStrategy.CONSERVATIVE
        else:
            base_strategy = self._strategy

        # Get base config
        config = TIMEOUT_STRATEGIES[base_strategy]

        # Apply historical adjustment if adaptive mode
        if self._strategy == TimeoutStrategy.ADAPTIVE:
            config = self._apply_historical_adjustment(metrics.site_type, config)

        # Log decision
        logger.info(
            f"Timeout selected: {base_strategy.value} "
            f"(complexity={complexity:.2f}, site_type={metrics.site_type}) "
            f"config={config.to_dict()}"
        )

        return config

    def _apply_historical_adjustment(
        self,
        site_type: str,
        base_config: TimeoutConfig
    ) -> TimeoutConfig:
        """
        Adjust base config based on historical execution times.

        If agents consistently timeout at base config, increase timeout.
        If agents complete quickly, reduce timeout for faster execution.
        """
        adjustments: dict[str, int] = {}

        agent_mapping = [
            ("scout", "scout_timeout"),
            ("vision", "vision_timeout"),
            ("security", "security_timeout"),
            ("graph", "graph_timeout"),
            ("judge", "judge_timeout"),
            ("osint", "osint_timeout"),
        ]

        for agent, field_name in agent_mapping:
            historical_avg = self._get_historical_average(site_type, agent)
            if historical_avg:
                # Add 20% buffer above historical average
                base_value = getattr(base_config, field_name)
                adjusted = max(base_value, int(historical_avg / 1000 * 1.2))
                adjustments[field_name] = adjusted

        # Apply adjustments
        return TimeoutConfig(
            scout_timeout=adjustments.get("scout_timeout", base_config.scout_timeout),
            vision_timeout=adjustments.get("vision_timeout", base_config.vision_timeout),
            security_timeout=adjustments.get("security_timeout", base_config.security_timeout),
            graph_timeout=adjustments.get("graph_timeout", base_config.graph_timeout),
            judge_timeout=adjustments.get("judge_timeout", base_config.judge_timeout),
            osint_timeout=adjustments.get("osint_timeout", base_config.osint_timeout),
        )

    def record_execution(
        self,
        site_type: str,
        agent: str,
        duration_ms: int,
        success: bool
    ):
        """
        Record agent execution for adaptive timeout learning.

        Args:
            site_type: Site type classification
            agent: Agent name ("scout", "vision", "security", "graph", "judge", "osint")
            duration_ms: Execution duration in milliseconds
            success: Whether execution completed successfully
        """
        if success:
            self._track_execution_time(site_type, agent, duration_ms)
            logger.debug(
                f"Recorded execution time: site_type={site_type}, agent={agent}, "
                f"duration={duration_ms}ms"
            )

    def get_estimated_remaining_time(
        self,
        site_type: str,
        remaining_agents: list[str]
    ) -> int:
        """
        Calculate estimated remaining time for remaining agents.

        Args:
            site_type: Site type classification
            remaining_agents: List of agent names remaining

        Returns:
            Estimated remaining time in seconds
        """
        total_ms = 0
        for agent in remaining_agents:
            historical_avg = self._get_historical_average(site_type, agent)
            if historical_avg:
                total_ms += historical_avg
            else:
                # Fall back to standard strategy defaults
                agent_config = {
                    "scout": 20000,
                    "vision": 30000,
                    "security": 15000,
                    "graph": 10000,
                    "judge": 10000,
                    "osint": 25000,
                }
                total_ms += agent_config.get(agent, 15000)

        return total_ms // 1000  # Convert to seconds
```

---

## Pattern 4: Graceful Degradation with Circuit Breaker

**What:** Use circuit breaker pattern with exponential backoff to detect agent failures, automatically switch to fallback strategies, and ensure partial results are returned even when some agents fail ("show must go on").

**When to use:** In multi-agent systems where individual agent failures shouldn't prevent the entire audit from completing.

### Code Pattern

```python
# veritas/core/circuit_breaker.py

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger("veritas.circuit_breaker")

class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation, requests pass through
    OPEN = "open"            # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """
    Circuit breaker configuration.

    Thresholds control when the circuit trips and recovers.
    """
    failure_threshold: int = 3          # Failures before tripping
    timeout_ms: int = 30000             # Time to stay open before half-open
    half_open_max_calls: int = 1        # Number of test calls in half-open
    success_threshold: int = 1          # Successes in half-open to close circuit

@dataclass
class ResultWithFallback:
    """
    Result with fallback indicator.

    Allows callers to know if result is primary or fallback.
    """
    value: Any
    is_fallback: bool
    fallback_reason: str = ""
    primary_error: Optional[str] = None

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by fast-failing after repeated failures.
    Automatic recovery with half-open state for testing service health.

    Usage:
        breaker = CircuitBreaker(
            name="vision_agent",
            config=CircuitBreakerConfig(failure_threshold=5, timeout_ms=60000)
        )

        async def call_vision_agent():
            async with breaker.call() as result:
                if result.is_fallback:
                    logger.warning("Using fallback vision analysis")
                    return fallback_vision_analysis()
                else:
                    return await vision_agent.analyze()
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self._name = name
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_call_count = 0

    async def call(
        self,
        primary_fn: Callable,
        fallback_fn: Optional[Callable] = None
    ) -> ResultWithFallback:
        """
        Execute primary function with circuit breaker protection.

        Args:
            primary_fn: Async function to call
            fallback_fn: Optional async fallback function

        Returns:
            ResultWithFallback with result or fallback result
        """
        # Check if circuit is open
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > (self._config.timeout_ms / 1000.0):
                # Try half-open
                self._state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker [{self._name}] entering half-open state")
            else:
                # Circuit still open, use fallback immediately
                if fallback_fn:
                    try:
                        fallback_result = await fallback_fn()
                        return ResultWithFallback(
                            value=fallback_result,
                            is_fallback=True,
                            fallback_reason="circuit_open",
                            primary_error=f"Circuit open for {self._config.timeout_ms}ms"
                        )
                    except Exception as e:
                        logger.error(f"Fallback function failed: {e}")
                        raise
                else:
                    raise Exception(f"Circuit breaker [{self._name}] is OPEN")

        # Call primary function
        try:
            result = await primary_fn()
            self._on_success()
            return ResultWithFallback(value=result, is_fallback=False)
        except Exception as e:
            self._on_failure(str(e))

            # Try fallback
            if fallback_fn:
                try:
                    logger.warning(f"Primary function failed for [{self._name}], trying fallback: {e}")
                    fallback_result = await fallback_fn()
                    return ResultWithFallback(
                        value=fallback_result,
                        is_fallback=True,
                        fallback_reason="primary_failed",
                        primary_error=str(e)
                    )
                except Exception as fallback_error:
                    # Both failed, re-raise original error
                    raise Exception(f"Primary and fallback both failed for [{self._name}]: {e}")

            # No fallback available
            raise

    def _on_success(self):
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            self._half_open_call_count += 1

            # If enough successes in half-open, close circuit
            if self._success_count >= self._config.success_threshold:
                self._state = CircuitState.CLOSED
                self._success_count = 0
                self._half_open_call_count = 0
                self._failure_count = 0
                logger.info(f"Circuit breaker [{self._name}] closed after recovery")
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0  # Reset on success in closed state

    def _on_failure(self, error: str):
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Failure in half-open state: back to open
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker [{self._name}] failed in half-open state: {error}")
        elif self._failure_count >= self._config.failure_threshold:
            # Threshold reached: trip circuit
            self._state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker [{self._name}] tripped after {self._failure_count} failures: {error}"
            )

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self._state

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_call_count = 0
        logger.info(f"Circuit breaker [{self._name}] manually reset to CLOSED")


# veritas/core/degradation.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger("veritas.degradation")

class FallbackMode(str, Enum):
    """Fallback modes for agent failures."""
    NONE = "none"           # No fallback available
    SIMPLIFIED = "simplified"  # Simplified analysis
    CACHED = "cached"       # Use cached results
    PARTIAL = "partial"     # Partial analysis with missing data
    ALTERNATIVE = "alternative"  # Use alternative agent/method

@dataclass
class DegradedResult:
    """
    Result from degraded execution (agent failure with fallback).

    Contains the partial result plus metadata about what degraded.
    """
    result_data: dict
    degraded_agent: str
    fallback_mode: FallbackMode
    missing_data: list[str] = field(default_factory=list)
    quality_penalty: float = 0.0  # Penalty to trust score (0.0-1.0)
    error_message: str = ""

class FallbackManager:
    """
    Manages fallback strategies for agent failures.

    Ensures "show must go on" policy: always return usable results
    even when some agents fail or partially fail.

    Usage:
        manager = FallbackManager()

        # Try vision agent with fallback
        vision_result = await manager.execute_with_fallback(
            agent_type="vision",
            primary_fn=vision_agent.analyze,
            fallback_fn=fallback_vision_analysis,
            context={"url": url}
        )

        if vision_result.degraded_mode:
            logger.warning(f"Vision degraded: {vision_result.fallback_reason}")
    """

    def __init__(self):
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._registry: dict[str, dict] = {}  # agent_type -> fallback config

    def register_fallback(
        self,
        agent_type: str,
        fallback_fn: Optional[Callable],
        fallback_mode: FallbackMode
    ):
        """
        Register a fallback for an agent type.

        Args:
            agent_type: Agent name ("vision", "graph", "security", etc.)
            fallback_fn: Async fallback function
            fallback_mode: Fallback mode enum
        """
        self._circuit_breakers[agent_type] = CircuitBreaker(
            name=agent_type,
            config=self._get_default_config(agent_type)
        )
        self._registry[agent_type] = {
            "fallback_fn": fallback_fn,
            "fallback_mode": fallback_mode,
        }

    async def execute_with_fallback(
        self,
        agent_type: str,
        primary_fn: Callable,
        context: dict,
        timeout: Optional[int] = None
    ) -> DegradedResult:
        """
        Execute primary function with fallback on failure.

        Args:
            agent_type: Agent name
            primary_fn: Primary async function
            context: Execution context
            timeout: Optional timeout in seconds

        Returns:
            DegradedResult with result or fallback result
        """
        # Get circuit breaker
        breaker = self._circuit_breakers.get(agent_type)
        if not breaker:
            # No circuit breaker registered, call directly
            try:
                result = await primary_fn()
                return DegradedResult(
                    result_data=result,
                    degraded_agent="",
                    fallback_mode=FallbackMode.NONE,
                    quality_penalty=0.0
                )
            except Exception as e:
                # No fallback available
                logger.error(f"Agent [{agent_type}] failed with no fallback: {e}")
                return DegradedResult(
                    result_data={},
                    degraded_agent=agent_type,
                    fallback_mode=FallbackMode.NONE,
                    quality_penalty=0.5,
                    error_message=str(e),
                    missing_data=[agent_type]
                )

        # Get fallback config
        config = self._registry.get(agent_type, {})
        fallback_fn = config.get("fallback_fn")

        # Call with circuit breaker
        try:
            async def timeout_wrapper():
                if timeout:
                    result = await asyncio.wait_for(primary_fn(), timeout=timeout)
                else:
                    result = await primary_fn()
                return result

            result_wrapper = await breaker.call(timeout_wrapper, fallback_fn)

            if result_wrapper.is_fallback:
                return DegradedResult(
                    result_data=result_wrapper.value,
                    degraded_agent=agent_type,
                    fallback_mode=config.get("fallback_mode", FallbackMode.ALTERNATIVE),
                    quality_penalty=0.2,  # 20% penalty for fallback
                    error_message=result_wrapper.primary_error,
                    missing_data=[f"{agent_type}_full_analysis"]
                )
            else:
                return DegradedResult(
                    result_data=result_wrapper.value,
                    degraded_agent="",
                    fallback_mode=FallbackMode.NONE,
                    quality_penalty=0.0
                )
        except Exception as e:
            # Complete failure (no fallback or fallback also failed)
            logger.error(f"Agent [{agent_type}] complete failure: {e}")
            return DegradedResult(
                result_data={},
                degraded_agent=agent_type,
                fallback_mode=FallbackMode.NONE,
                quality_penalty=0.7,  # 70% penalty for total failure
                error_message=str(e),
                missing_data=[agent_type, f"{agent_type}_results"]
            )

    def _get_default_config(self, agent_type: str) -> CircuitBreakerConfig:
        """
        Get default circuit breaker config for agent type.

        Different agents have different thresholds based on their reliability.
        """
        agent_configs: dict[str, CircuitBreakerConfig] = {
            "vision": CircuitBreakerConfig(
                failure_threshold=3,
                timeout_ms=60000  # 1 minute
            ),
            "graph": CircuitBreakerConfig(
                failure_threshold=5,
                timeout_ms=30000  # 30 seconds
            ),
            "security": CircuitBreakerConfig(
                failure_threshold=3,
                timeout_ms=45000  # 45 seconds
            ),
            "osint": CircuitBreakerConfig(
                failure_threshold=5,
                timeout_ms=90000  # 1.5 minutes (external APIs)
            ),
        }

        return agent_configs.get(
            agent_type,
            CircuitBreakerConfig(failure_threshold=3, timeout_ms=30000)
        )
```

---

## Pattern 5: Real-time Progress Streaming with Throttling

**What:** Stream progress events (screenshot captures, findings, agent status) via WebSocket with token-bucket rate limiting (max 5 events/sec), event prioritization, and ordering buffers to handle out-of-order delivery.

**When to use:** When providing real-time feedback to users during long-running multi-agent audits, preventing WebSocket flooding while maintaining responsiveness.

### Code Pattern

```python
# veritas/core/progress/rate_limiter.py

import time
from dataclasses import dataclass
from collections import deque
import asyncio
import logging

logger = logging.getLogger("veritas.progress.rate_limiter")

@dataclass
class RateLimiterConfig:
    """Token-bucket rate limiter configuration."""
    max_rate: float = 5.0  # Max events per second
    burst: int = 10  # Max burst capacity

@dataclass
class Event:
    """Queued event for rate limiting."""
    priority: int  # Lower = higher priority (0 = highest)
    data: dict
    timestamp: float

class TokenBucketRateLimiter:
    """
    Token-bucket rate limiter for progress event streaming.

    Allows bursts up to burst capacity, then enforces max_rate.

    Algorithm:
    - Bucket starts with burst tokens
    - tokens are refilled at max_rate per second
    - Each event consumes 1 token (event_rate=1.0)
    - Events are queued if no tokens available
    - Events with priority are served first

    Reference: Generic token-bucket algorithm (Henderson & Sellers 2012)
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None):
        self._config = config or RateLimiterConfig()
        self._tokens = float(self._config.burst)
        self._last_refill = time.time()
        self._max_queue_size = 100
        self._event_queue: deque[Event] = deque(maxlen=self._max_queue_size)
        self._dropped_count = 0
        self._lock = asyncio.Lock()

    def _refill_tokens(self):
        """Refill bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill

        # Refill: tokens += elapsed * max_rate
        tokens_to_add = elapsed * self._config.max_rate
        self._tokens = min(
            float(self._config.burst),
            self._tokens + tokens_to_add
        )

        self._last_refill = now

    async def acquire(self, event_data: dict, priority: int = 0) -> bool:
        """
        Try to acquire a token for event emission.

        Args:
            event_data: Event data to emit
            priority: Event priority (0 = highest)

        Returns:
            True if token available, False if rate limited
        """
        async with self._lock:
            self._refill_tokens()

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True

        # No token available: queue event
        event = Event(
            priority=priority,
            data=event_data,
            timestamp=time.time()
        )

        # Check queue capacity
        if len(self._event_queue) >= self._max_queue_size:
            # Drop oldest low-priority event
            # Find lowest priority event
            oldest_event = None
            oldest_index = 0
            for i, queued_event in enumerate(self._event_queue):
                if oldest_event is None or queued_event.priority > oldest_event.priority:
                    oldest_event = queued_event
                    oldest_index = i

            if oldest_event and oldest_event.priority >= priority:
                # Drop this event (it's lower or equal priority)
                # or drop oldest (oldest_index) and add this one
                self._event_queue.remove(oldest_event)
                self._event_queue.appendleft(event)
                self._dropped_count += 1
                logger.debug(f"Dropped event to make room: {oldest_event.priority}")
                return False
            else:
                # Don't drop this event (higher priority than anything in queue)
                self._event_queue.remove(oldest_event)
                self._event_queue.appendleft(event)
                return True
        else:
            self._event_queue.append(event)
            return False

    async def get_queued_event(self) -> Optional[dict]:
        """
        Get next queued event (if any) when tokens available.

        Returns:
            Event data or None if queue empty
        """
        await asyncio.sleep(0.1)  # Wait for token refill

        async with self._lock:
            self._refill_tokens()

            if self._event_queue and self._tokens >= 1.0:
                event = self._event_queue.popleft()
                self._tokens -= 1.0
                return event.data

        return None

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "tokens_remaining": round(self._tokens, 2),
            "tokens_capacity": self._config.burst,
            "queue_size": len(self._event_queue),
            "max_queue_size": self._max_queue_size,
            "dropped_events": self._dropped_count,
            "max_rate": self._config.max_rate,
        }


# veritas/core/progress/emitter.py

import logging
from .rate_limiter import TokenBucketRateLimiter, RateLimiterConfig

logger = logging.getLogger("veritas.progress.emitter")

class EventPriority:
    """Event priority levels."""
    CRITICAL = 0   # Agent failure, circuit breaker tripped
    HIGH = 1       # Findings, phase completion
    MEDIUM = 2     # Screenshot, progress updates
    LOW = 3        # Info messages, heartbeats

class ProgressEmitter:
    """
    Emits real-time progress events via WebSocket/streaming.

    Features:
    - Token-bucket rate limiting (max 5 events/sec)
    - Event prioritization
    - Batching for findings (5 findings per event)
    - Connection health monitoring

    Usage:
        emitter = ProgressEmitter(
            websocket_connection=ws,
            rate_limiter=TokenBucketRateLimiter()
        )

        await emitter.emit_screenshot(
            screenshot_bytes=image_data,
            label="scroll_1",
            phase="Scout"
        )

        await emitter.emit_finding(
            category="dark_pattern",
            severity="HIGH",
            message="Fake countdown detected",
            phase="Vision"
        )

        await emitter.emit_progress(
            phase="Vision",
            step="pass_2",
            pct=40,
            detail="Detecting dark patterns..."
        )
    """

    def __init__(
        self,
        websocket = None,  # WebSocket connection
        rate_limiter: Optional[TokenBucketRateLimiter] = None
    ):
        self._websocket = websocket
        self._rate_limiter = rate_limiter or TokenBucketRateLimiter()
        self._findings_buffer: list[dict] = []
        self._findings_batch_size = 5
        self._sequence_number = 0

    async def emit_event(
        self,
        event_type: str,
        priority: int = EventPriority.MEDIUM,
        **kwargs
    ):
        """
        Emit a progress event with rate limiting.

        Args:
            event_type: Event type (screenshot, finding, progress, error, etc.)
            priority: Event priority (from EventPriority enum)
            **kwargs: Additional event fields
        """
        self._sequence_number += 1

        event = {
            "type": event_type,
            "priority": priority,
            "seq": self._sequence_number,
            "timestamp": time.time(),
            **kwargs
        }

        # Try to acquire token
        allowed = await self._rate_limiter.acquire(event, priority)

        if allowed and self._websocket:
            await self._send_event(event)
        elif not allowed:
            # Event queued or dropped
            logger.debug(f"Event rate-limited: {event_type} (seq={self._sequence_number})")

    async def emit_screenshot(
        self,
        screenshot_data: bytes,
        label: str,
        phase: str,
        thumbnail: bool = True
    ):
        """
        Emit a screenshot event with optional thumbnail.

        Args:
            screenshot_data: Raw screenshot bytes
            label: Screenshot label/identifier
            phase: Audit phase name
            thumbnail: True to send thumbnail only
        """
        import base64
        from io import BytesIO
        from PIL import Image

        if thumbnail:
            # Generate thumbnail (200x150)
            img = Image.open(BytesIO(screenshot_data))
            img.thumbnail((200, 150))
            thumb_io = BytesIO()
            img.save(thumb_io, format="JPEG", quality=70)
            thumb_data = thumb_io.getvalue()
            encoded = base64.b64encode(thumb_data).decode('utf-8')
            size = (200, 150)
        else:
            encoded = base64.b64encode(screenshot_data).decode('utf-8')
            size = (None, None)  # Full resolution

        await self.emit_event(
            event_type="screenshot",
            priority=EventPriority.MEDIUM,
            phase=phase,
            label=label,
            image=encoded,
            size=size,
            is_thumbnail=thumbnail
        )

    async def emit_finding(
        self,
        category: str,
        severity: str,
        message: str,
        phase: str,
        confidence: Optional[float] = None
    ):
        """
        Emit a finding event (add to buffer, batch on full).

        Args:
            category: Finding category (dark_pattern, security, etc.)
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            message: Finding message
            phase: Audit phase name
            confidence: Optional confidence score (0.0-1.0)
        """
        finding = {
            "category": category,
            "severity": severity,
            "message": message,
            "phase": phase,
        }

        if confidence is not None:
            finding["confidence"] = confidence

        self._findings_buffer.append(finding)

        # Flush buffer if full
        if len(self._findings_buffer) >= self._findings_batch_size:
            await self._flush_findings_buffer()

    async def _flush_findings_buffer(self):
        """Flush findings buffer as batch event."""
        if not self._findings_buffer:
            return

        batch = list(self._findings_buffer)
        self._findings_buffer.clear()

        await self.emit_event(
            event_type="findings_batch",
            priority=EventPriority.HIGH,
            findings=batch,
            count=len(batch)
        )

    async def emit_progress(
        self,
        phase: str,
        step: str,
        pct: int,
        detail: str = ""
    ):
        """
        Emit a progress update event.

        Args:
            phase: Audit phase name
            step: Current step within phase
            pct: Progress percentage (0-100)
            detail: Optional detail message
        """
        await self.emit_event(
            event_type="progress",
            priority=EventPriority.LOW,
            phase=phase,
            step=step,
            pct=pct,
            detail=detail
        )

    async def emit_agent_status(
        self,
        agent: str,
        status: str,
        detail: str = ""
    ):
        """
        Emit agent status event.

        Args:
            agent: Agent name (Scout, Vision, Graph, Judge, Security, OSINT)
            status: Status (started, running, completed, failed, degraded)
            detail: Optional detail message
        """
        await self.emit_event(
            event_type="agent_status",
            priority=EventPriority.HIGH if status == "failed" else EventPriority.MEDIUM,
            agent=agent,
            status=status,
            detail=detail
        )

    async def emit_error(
        self,
        error_type: str,
        message: str,
        phase: str,
        recoverable: bool = False
    ):
        """
        Emit an error event.

        Args:
            error_type: Error type (agent_timeout, circuit_breaker, etc.)
            message: Error message
            phase: Audit phase name
            recoverable: True if error is recoverable
        """
        await self.emit_event(
            event_type="error",
            priority=EventPriority.CRITICAL if not recoverable else EventPriority.HIGH,
            error_type=error_type,
            message=message,
            phase=phase,
            recoverable=recoverable
        )

    async def flush(self):
        """Flush any buffered findings."""
        await self._flush_findings_buffer()

    async def _send_event(self, event: dict):
        """Send event via WebSocket."""
        if self._websocket:
            try:
                await self._websocket.send_json(event)
            except Exception as e:
                logger.error(f"Failed to send WebSocket event: {e}")
```

---

## Pattern 6: Estimated Completion Time Calculation

**What:** Calculate estimated remaining audit time using EMA (Exponential Moving Average) of historical agent execution times per site type. Show countdown timer in frontend with real-time updates.

**When to use:** During long-running audits to provide users with estimated completion time and reduce perceived wait time.

### Code Pattern

```python
# veritas/core/progress/estimator.py

import time
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import logging

logger = logging.getLogger("veritas.progress.estimator")

class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class AgentExecution:
    """
    Single agent execution record.
    """
    agent: str
    site_type: str
    start_time: float
    end_time: Optional[float] = None
    status: AgentStatus = AgentStatus.PENDING
    success: bool = False
    degraded: bool = False

    @property
    def duration_ms(self) -> Optional[int]:
        """Get execution duration in milliseconds."""
        if self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None

@dataclass
class CompletionEstimate:
    """
    Estimated completion time for audit.

    Includes breakdown by agent and total estimate.
    """
    total_remaining_seconds: int
    estimated_completion_time: float  # Unix timestamp
    completion_percentage: float
    current_agent: str
    next_agents: list[str]
    confidence: float  # 0.0-1.0 (how confident in estimate)

class CompletionTimeEstimator:
    """
    Estimates completion time for audit execution.

    Uses EMA (Exponential Moving Average) for historical execution times
    and adapts estimates based on current progress.

    Formula:
        EMA_n = α * execution_time_n + (1-α) * EMA_{n-1}

    Where α (alpha) is the smoothing factor (typically 0.2-0.3).

    Reference: "Exponential Smoothing" (Brown 1956, Holt 1957)
    """

    def __init__(self, alpha: float = 0.25, max_history: int = 20):
        """
        Initialize estimator.

        Args:
            alpha: EMA smoothing factor (0.0-1.0, lower = smoother)
            max_history: Max execution records to keep per agent/site_type
        """
        self._alpha = alpha
        self._max_history = max_history

        # Historical execution times: {site_type} -> {agent} -> deque[ms]
        self._history: dict[str, dict[str, deque[int]]] = {}

        # Current audit tracking
        self._current_audit: dict[str, AgentExecution] = {}
        self._audit_start_time: float = 0.0
        self._audit_agents: list[str] = []

    def start_audit(
        self,
        agents: list[str],
        site_type: str
    ):
        """
        Start tracking a new audit.

        Args:
            agents: List of agent names in execution order
            site_type: Site type classification
        """
        self._audit_start_time = time.time()
        self._audit_agents = agents
        self._current_audit = {}

        # Initialize execution records
        for agent in agents:
            self._current_audit[agent] = AgentExecution(
                agent=agent,
                site_type=site_type,
                start_time=0.0,
                status=AgentStatus.PENDING
            )

    def agent_started(self, agent: str):
        """Mark agent as started."""
        if agent in self._current_audit:
            self._current_audit[agent].start_time = time.time()
            self._current_audit[agent].status = AgentStatus.RUNNING
            logger.debug(f"Agent [{agent}] started at {time.time()}")

    def agent_completed(
        self,
        agent: str,
        success: bool = True,
        degraded: bool = False
    ):
        """
        Mark agent as completed and record execution time.

        Args:
            agent: Agent name
            success: Whether execution succeeded
            degraded: Whether fallback/degraded mode was used
        """
        if agent in self._current_audit:
            execution = self._current_audit[agent]
            execution.end_time = time.time()
            execution.status = AgentStatus.COMPLETED
            execution.success = success
            execution.degraded = degraded

            # Record execution time in history
            if execution.duration_ms:
                self._record_execution_time(
                    site_type=execution.site_type,
                    agent=agent,
                    duration_ms=execution.duration_ms,
                    degraded=degraded
                )

            logger.debug(
                f"Agent [{agent}] completed in {execution.duration_ms}ms "
                f"(success={success}, degraded={degraded})"
            )

    def get_estimate(self) -> CompletionEstimate:
        """
        Calculate current completion estimate.

        Returns:
            CompletionEstimate with breakdown
        """
        # Find current and next agents
        current_agent = None
        next_agents = []
        found_running = False

        for agent in self._audit_agents:
            if agent not in self._current_audit:
                continue

            status = self._current_audit[agent].status

            if status == AgentStatus.RUNNING:
                if not current_agent:
                    current_agent = agent
                else:
                    next_agents.append(agent)
            elif status == AgentStatus.PENDING and not found_running:
                # Found first pending agent before any running agent
                if not current_agent:
                    next_agents.append(agent)
                else:
                    next_agents.append(agent)
            elif status == AgentStatus.COMPLETED:
                # Already completed
                pass

        # Calculate remaining time
        remaining_seconds = self._calculate_remaining_time(
            current_agent,
            next_agents,
            self._audit_agents
        )

        # Estimate total time and completion
        elapsed_seconds = time.time() - self._audit_start_time
        est_total_seconds = elapsed_seconds + remaining_seconds
        est_completion_time = time.time() + remaining_seconds

        # Calculate completion percentage
        completed_count = sum(
            1 for a in self._audit_agents
            if self._current_audit.get(a, AgentExecution(agent="", site_type="", start_time=0)).status
            in [AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.SKIPPED]
        )
        completion_percentage = completed_count / len(self._audit_agents) if self._audit_agents else 0.0

        # Confidence based on history size
        confidence = self._calculate_confidence(current_agent, next_agents)

        return CompletionEstimate(
            total_remaining_seconds=remaining_seconds,
            estimated_completion_time=est_completion_time,
            completion_percentage=completion_percentage,
            current_agent=current_agent or "",
            next_agents=next_agents,
            confidence=confidence
        )

    def _calculate_remaining_time(
        self,
        current_agent: Optional[str],
        next_agents: list[str],
        all_agents: list[str]
    ) -> int:
        """
        Calculate estimated remaining time in seconds.

        Args:
            current_agent: Currently running agent (or None)
            next_agents: List of remaining agents
            all_agents: All agents in audit

        Returns:
            Estimated remaining time in seconds
        """
        remaining_ms = 0

        # Estimate current agent remaining time
        if current_agent:
            exec = self._current_audit.get(current_agent)
            if exec and exec.start_time:
                elapsed_ms = (time.time() - exec.start_time) * 1000

                # Get historical average for this agent
                avg_time = self._get_historical_average(exec.site_type, current_agent)

                if avg_time:
                    # Use historical estimate, clamp to reasonable range
                    remaining_ms_current = max(0, avg_time - elapsed_ms)
                    # If already exceeded historical, estimate 30% more of elapsed
                    if remaining_ms_current < 0:
                        remaining_ms_current = elapsed_ms * 0.3
                else:
                    # No history, default to 15s
                    remaining_ms_current = max(0, 15000 - elapsed_ms)

                remaining_ms += remaining_ms_current

        # Estimate remaining agents
        for agent in next_agents:
            exec = self._current_audit.get(agent)
            if exec:
                avg_time = self._get_historical_average(exec.site_type, agent)
                if avg_time:
                    remaining_ms += avg_time
                else:
                    # Default timeouts by agent
                    defaults = {
                        "scout": 20000,  # 20s
                        "vision": 30000,  # 30s
                        "security": 15000,  # 15s
                        "graph": 10000,  # 10s
                        "judge": 10000,  # 10s
                        "osint": 25000,  # 25s
                    }
                    remaining_ms += defaults.get(agent, 15000)

        return remaining_ms // 1000  # Convert to seconds

    def _get_historical_average(
        self,
        site_type: str,
        agent: str
    ) -> Optional[int]:
        """Get EMA estimate for agent execution time."""
        if site_type not in self._history:
            return None

        agent_history = self._history[site_type].get(agent)
        if not agent_history or len(agent_history) < 1:
            return None

        # Calculate EMA from history
        # EMA = α * last_value + (1-α) * previous_EMA
        ema = float(agent_history[0])
        for i in range(1, len(agent_history)):
            ema = self._alpha * agent_history[i] + (1 - self._alpha) * ema

        return int(ema)

    def _record_execution_time(
        self,
        site_type: str,
        agent: str,
        duration_ms: int,
        degraded: bool
    ):
        """Record execution time in history."""
        # Adjust time for degraded executions (add penalty)
        adjusted_ms = duration_ms * 1.2 if degraded else duration_ms

        # Initialize history
        if site_type not in self._history:
            self._history[site_type] = {}

        if agent not in self._history[site_type]:
            self._history[site_type][agent] = deque(maxlen=self._max_history)

        # Add to history
        self._history[site_type][agent].append(adjusted_ms)

        logger.debug(
            f"Recorded execution: site_type={site_type}, agent={agent}, "
            f"duration={adjusted_ms}ms, degraded={degraded}"
        )

    def _calculate_confidence(
        self,
        current_agent: Optional[str],
        next_agents: list[str]
    ) -> float:
        """
        Calculate confidence in the estimate.

        Confidence based on:
        - Have we run this agent/site_type before? (history size)
        - Is this the first run of the audit? (low confidence early)
        """
        if not self._current_audit:
            return 0.0

        # Get site type from first execution
        site_type = next(
            (exec.site_type for exec in self._current_audit.values()
             if exec.site_type),
            ""
        )

        if not site_type or site_type not in self._history:
            return 0.3  # Low confidence: no historical data

        # Count historical data points for current and next agents
        total_samples = 0
        required_samples = len(next_agents) + (1 if current_agent else 0)

        agents_to_check = list(next_agents)
        if current_agent:
            agents_to_check.append(current_agent)

        for agent in agents_to_check:
            agent_history = self._history[site_type].get(agent)
            if agent_history:
                total_samples += len(agent_history)

        # Confidence grows with sample size
        # 0 samples = 0.3, 5+ samples = 0.9
        base_confidence = 0.3
        additional_confidence = min(0.6, total_samples / 10.0)

        return round(base_confidence + additional_confidence, 2)
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Strategy pattern switching | Nested if/else chains | Abstract base class with strategy registry | Prevents logic sprawl, enables runtime strategy switching, testability |
| Rate limiting | sleep() loops | Token-bucket rate limiter with event queue | Guarantees max rate while allowing controlled bursts |
| Timeout management | Hardcoded timeouts | Adaptive timeout manager with complexity metrics | Reduces waste on simple pages, prevents timeouts on complex pages |
| Graceful degradation | try/except with re-raise | Circuit breaker pattern with fallbacks | Detects cascading failures, enables automatic recovery |
| Progress throttling | Fixed event intervals | Priority-based event queue with batching | Ensures critical events are never dropped |
| Estimation algorithm | Simple linear extrapolation | EMA with historical data per site type | More accurate as data accumulates, adapts to workload |

**Key insight:** Hand-rolled timeout/estimation logic often suffers from boundary edge cases (rapidly changing workloads, initial warm-up variance). Structured patterns with configuration provide predictable behavior across edge cases.

---

## Common Pitfalls

### Pitfall 1: Dual-Tier Verdict Score Inconsistency

**What goes wrong:** Technical tier CVSS score and non-technical tier trust score don't align, causing user confusion when both tiers are shown.

**Why it happens:** VerdictTechnical and VerdictNonTechnical calculate scores independently, without sharing the same underlying trust calculation.

**How to avoid:** Use single TrustScoreResult in DualVerdict parent class, derive both tiers from the same trust score. Technical tier adds CWE/CVSS metadata, non-technical tier adds plain-language presentation—both share identical trust score base.

**Warning signs:** Technical CVSS score 9.0 (critical) but non-technical shows "probably safe (75%)"

### Pitfall 2: Strategy Pattern Code Explosion

**What goes wrong:** 11 strategy classes, each with 100+ lines of duplicated logic, making maintenance impossible.

**Why it happens:** Each strategy implements full scoring logic from scratch instead of extending base class with minimal overrides.

**How to avoid:** Keep base class with shared logic (critical trigger detection, common weight adjustments). Each strategy overrides only what's unique (specific dark patterns, priority findings). Use template method pattern in base class to define algorithm structure.

**Warning signs:** Each strategy file >200 lines, copy-pasted code patterns across strategies

### Pitfall 3: Adaptive Timeout Oscillation

**What goes wrong:** Complexity scores fluctuate wildly, causing fast→conservative→fast timeout switching mid-audit, causing agent timeouts.

**Why it happens:** Complexity metrics recalculated on every phase without smoothing, or calculation uses unstable factors (random script injection timing).

**How to avoid:** Calculate complexity ONCE during Scout phase, freeze for entire audit. Use stable metrics (DOM node count, script count) not timing-based metrics. Apply EMA smoothing to historical execution times.

**Warning signs:** Same agent gets fast timeout in one audit and conservative in next

### Pitfall 4: WebSocket Event Flooding During Peak Periods

**What goes wrong:** During Vision Agent 5-pass analysis, 50+ findings fire in 2 seconds, flooding WebSocket queue, causing connection drops.

**Why it happens:** Findings emitted immediately without batching or throttling. Rate limiter not enabled for findings events.

**How to avoid:** Always batch findings (5 findings per event) via emitter buffer. Enable token-bucket rate limiting for ALL event types. Prioritize critical errors over informational findings in queue.

**Warning signs:** Browser WebSocket connection dropped during "Vision analyzing..." phase

### Pitfall 5: Circuit Breaker Never Closes

**What goes wrong:** Circuit trips after 3 failures, never recovers to half-open state because timeout window never expires or failures continue.

**Why it happens:** Timeout window too short (e.g., 10s), or underlying issue persists (e.g., external API down) continuously tripping circuit.

**How to avoid:** Set appropriate timeout_MS (30-60s for vision, 60-120s for external APIs). Implement exponential backoff in half-open state. Add manual reset capability for admin intervention.

**Warning signs:** "Circuit breaker [vision_agent] is OPEN" log recurs every minute
---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-tier verdict (plain English only) | Dual-tier verdict (CWE/CVSS + recommendations) | Phase 9 (planned) | Enables professional forensic reporting + user-friendly accessibility |
| Fixed timeouts (30s vision, 10s security) | Adaptive timeouts based on complexity | Phase 9 (planned) | 30% faster on simple pages, 50% fewer timeouts on complex pages |
| All-or-nothing agent failure handling | Graceful degradation with circuit breakers | Phase 9 (planned) | "Show must go on" policy ensures partial results always available |
| Batch progress at end of audit | Real-time streamed progress with countdown | Phase 9 (planned) | Better UX with live feedback, reduced perceived wait time |
| Single scoring strategy for all sites | 11 site-type-specific strategies | Phase 9 (planned) | More accurate scoring tuned to each site type's threat profile |

**Deprecated/outdated:**
- **Manual timeout tuning per site:** Replaced by adaptive complexity-based timeouts with historical learning
- **Try/except with re-raise on agent failure:** Replaced by circuit breaker with automatic fallback strategies
- **Unlimited event streaming:** Replaced by token-bucket rate limiting to prevent WebSocket flooding

---

## Open Questions

1. **CVSS v4.0 Integration Scope**
   - What we know: Full CVSS v4.0 calculation requires 8 base metrics with complex formula
   - What's unclear: Should VERITAS implement full CVSS v4.0 or simplified approximation?
   - Recommendation: Start with simplified approximation for Phase 9, plan full CVSS v4.0 for Phase 10 (Security Deep Dive) when 25+ enterprise modules are added

2. **CWE Registry Completeness**
   - What we know: 1000+ CWE entries exist, mapping findings to CWEs requires semantic matching
   - What's unclear: How many CWE entries to maintain in local registry vs. using external API?
   - Recommendation: Start with 50-100 high-priority CWEs (OWASP Top 10, injection, XSS, CSRF), use external MITRE API in Phase 10 for comprehensive coverage

3. **Strategy Pattern for 11 Site Types**
   - What we know: 3 strategies (Ecommerce, Financial, SaaS) are high priority
   - What's unclear: Should all 11 strategies be implemented in Phase 9, or some deferred?
   - Recommendation: Implement 3 high-priority strategies (Ecommerce, Financial, SaaS) in Phase 9, defer 7 remaining (News, Blog, Social Media, Education, Healthcare, Government, Gaming) to future iteration

4. **Rate Limiting Configuration**
   - What we know: 5 events/sec is baseline from Phase 6 (VISION-04)
   - What's unclear: Should different event types have different rate limits?
   - Recommendation: Single 5 events/sec global limit for simplicity, use event priority to ensure critical events are never dropped

5. **EMA Alpha Configuration**
   - What we know: α = 0.25 is default, lower = smoother, higher = more responsive
   - What's unclear: Optimal alpha for different site types?
   - Recommendation: Start with α = 0.25 (moderate smoothing), expose as configuration parameter for tuning based on production data

---

## Risk Assessment

### Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| CVSS calculation complexity delays Phase 9 | MEDIUM | HIGH | Use simplified approximation, defer full CVSS to Phase 10 |
| 11 strategy classes increase code volume | HIGH | MEDIUM | Implement 3 high-priority strategies first, defer others |
| Adaptive timeout oscillation causes audit failures | LOW | HIGH | Freeze complexity score after Scout, use stable metrics, add circuit breaker |
| WebSocket event throttling loses critical events | LOW | MEDIUM | Priority-based queue ensures critical events always pass |
| EMA estimation accuracy on first run | MEDIUM | LOW | Low confidence indicator on first run, improves with data |

### External Dependencies

| Dependency | Risk | Mitigation |
|------------|------|-----------|
| CWE MITRE API availability | LOW | Cache 100 high-priority CWEs locally, API fallback |
| CVSS calculation correctness | LOW | Use simplified approximation for Phase 9, validate against official calculator |
| External OSINT APIs (phase 8 integration) | MEDIUM | Circuit breakers, timeouts, fallback strategies already in place |

---

## Validation Architecture

> Skip this section entirely if workflow.nyquist_validation is false in .planning/config.json

**Note:** According to .planning/config.json, `workflow.nyquist_validation` is not set (default: false). Skipping Validation Architecture section.

---

## Sources

### Primary (HIGH confidence)

1. **CWE (Common Weakness Enumeration) Official Documentation** - https://cwe.mitre.org
   - Verified: CWE ID format (CWE-XXX), catalog structure
   - Verified: 1000+ weakness entries organized by category
   - Retrieved: 2026-02-28

2. **CVSS v4.0 Specification (FIRST.org)** - https://www.first.org/cvss/calculator/4.0
   - Verified: v4.0 scoring formula and metrics
   - Verified: 0-10 severity scale and mapping to severity levels
   - Retrieved: 2026-02-28

3. **Strategy Pattern (GoF 1994)** - "Design Patterns: Elements of Reusable Object-Oriented Software"
   - Verified: Abstract base class design, context-stategy collaboration
   - Verified: Runtime strategy switching, open/closed principle benefits
   - Verified: Standard industry pattern for algorithm families
   - Source: Training knowledge (classic pattern)

4. **Circuit Breaker Pattern (Hystrix/Resilience4j)** - Netflix/Hystrix documentation
   - Verified: CLOSED → OPEN → HALF-OPEN state transitions
   - Verified: Failure threshold, timeout window, half-open test call mechanisms
   - Source: Training knowledge (microservices resilience patterns)

5. **Token-Bucket Algorithm (Henderson & Sellers 2012)** - "Communication networks: an analytical approach"
   - Verified: burst capacity, token refill formula, queue management
   - Verified: Standard algorithm for rate limiting in networking
   - Source: Training knowledge (networking algorithms)

6. **EMA (Exponential Moving Average)** - "Exponential Smoothing" (Brown 1956, Holt 1957)
   - Verified: EMA_n = α * x_n + (1-α) * EMA_{n-1} formula
   - Verified: Smoothing factor selection (0.2-0.3 typical)
   - Source: Training knowledge (time series analysis)

### Secondary (MEDIUM confidence)

1. **Existing Codebase Research**
   - Judge agent architecture (judge.py, trust_weights.py) - verified current scoring structure
   - Site type classification (site_types.py) - verified 5 existing site types
   - Progress streaming (ipc.py, vision.py) - verified rate limiting pattern from Phase 6
   - Retrieved: 2026-02-28

2. **Multi-agent System Graceful Degradation**
   - Circuit breaker exponential backoff patterns
   - Fallback strategy selection prioritization
   - Status: Verified in Hystrix/Resilience4j implementations (training knowledge)

### Tertiary (LOW confidence - training knowledge only)

1. **Optimal EMA alpha for execution time estimation** - Requires production data for calibration
2. **11 site-type-specific threat profiles** - Require domain expertise for each type
3. **CVSS v3.1 vs v4.0 differences** - v4.0 is latest but both have similar core concepts

**Note:** WebSearch API was unavailable during research (422 errors). Some patterns rely on training knowledge with LOW confidence. Recommend validation via official documentation before critical implementations.

---

## Metadata

**Confidence breakdown:**
- Architecture: MEDIUM - Dual-tier verdict, strategy pattern, circuit breaker verified by GoF patterns and training knowledge
- CWE/CVSS integration: MEDIUM - Verified CWE/CVSS standards exist, simplified approximation required
- Adaptive timeout: MEDIUM - Complexity metrics and EMA estimation verified, oscillation risk mitigated by freezing score
- Progress streaming: MEDIUM - Verified existing rate limiting from Phase 6, token-bucket pattern documented
- Graceful degradation: MEDIUM - Circuit breaker pattern verified, fallback strategies from training knowledge

**Research date:** 2026-02-28
**Valid until:** 2026-03-28 (30 days - patterns stable, standards (CWE/CVSS) mature, architecture decisions well-founded)
