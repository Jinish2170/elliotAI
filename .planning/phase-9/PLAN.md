# Plan: Phase 9 - Judge System & Orchestrator

**Phase ID:** 9
**Milestone:** v2.0 Masterpiece Features
**Depends on:** Phase 7 (Quality Foundation), Phase 8 (OSINT Integration)
**Status:** pending
**Created:** 2026-02-23

---

## Context

### Current State (Pre-Phase)

**Judge Agent (`veritas/agents/judge.py`):**
- Single-tier verdict (plain English recommendations only)
- Simple trust scoring based on 6 signals (visual, structural, temporal, graph, meta, security)
- No CWE/CVSS technical details
- Single verdict mode (no dual-tier separation for technical vs. non-technical users)
- Site-type basic detection but no scoring strategies
- Trust score: 0-100 with simple weighted average

**Orchestrator (`veritas/core/orchestrator.py`):**
- Sequential node execution (scout → security → vision → graph → judge)
- Manual state management (not using LangGraph ainvoke due to Python 3.14 issue)
- Fixed timeouts per node (30s vision, 10s security, etc.)
- No adaptive time management based on page complexity
- Basic error handling (continue on node failure)
- No estimated completion time or countdown
- No graceful degradation for partial results

**Progress Streaming:**
- Basic phase_start/complete events
- No per-source progress events for long OSINT queries
- No screenshot streaming until after audit completes
- No finding streaming as discovered

**Frontend:**
- Basic Agent Theater with phase status cards
- No progress bars with countdown timers
- No "real-time pattern/discovery notifications"
- No user engagement pacing

### Goal State (Post-Phase)

**Dual-Tier Judge System:**
- Technical tier: CWE IDs, CVSS scores, IOCs for security professionals
- Non-technical tier: Plain English explanations, actionable advice for general users
- DualVerdict dataclass containing both VerdictTechnical and VerdictNonTechnical
- Single trust score calculation shared between tiers
- Versioned verdict data classes (V1 → V2 transition path)

**Site-Type-Specific Scoring:**
- 11 site-type strategies (e-commerce, social media, news, financial, portfolio, blog, forum, directory, landing page, SaaS, corporate)
- Context-aware scoring based on detected site type
- Base strategy class with shared configuration
- Weights adjusted per site type (e.g., social proof weight higher for e-commerce)

**Advanced Orchestrator:**
- Dynamic priority adjustment based on complexity
- Adaptive timeout strategies (adjust based on page size, complexity)
- Parallel execution optimization of independent tasks
- Estimated completion time with countdown for frontend

**Comprehensive Error Handling:**
- Detect agent failures immediately
- Automatic fallback to alternative analysis methods
- Graceful degradation - partial results if agent crashes
- "Show must go on" policy - always return something usable

**Complexity-Aware Orchestration:**
- Detect when processing time is exceeding thresholds
- Simplify analysis if time constraints hit (skip optional passes)
- Prioritize high-value findings over comprehensive coverage
- Progressive refinement - return initial results, improve over time

**Real-Time Progress Updates:**
- Progressive screenshot streaming to frontend
- Real-time pattern/discovery notifications
- User engagement pacing during long audits (keep user informed every 5-10 seconds)

---

## Critical Implementation Risks (Must Address)

### 1. Judge Verdict Complexity Explosion (HIGH)

**Risk:** Dual-tier verdict + 11 site types + technical details = massive complexity

**Current:**
```python
Verdict = {
    "trust_score": 75,
    "risk_level": "medium",
    "narrative": "This site appears...",
    "recommendations": ["Check SSL", "Verify contact info"]
}
```

**New Required:**
```python
DualVerdict = {
    "technical": {
        "trust_score": 75,
        "risk_level": "medium",
        "cwe_ids": ["CWE-311", "CWE-352"],
        "cvss_score": "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:N",  # CVSS 3.1 vector
        "cvss_base_score": 9.1,  # Critical
        "cvss_severity": "critical",
        "iocs": {
            "malicious_domains": ["evil.com"],
            "suspicious_ips": ["192.168.1.1"],
            "threat_indicators": ["phish_tank_match"]
        },
        "findings": [
            {"category": "injection", "cwe": "CWE-89", "cvss": "high", ...}
        ]
    },
    "non_technical": {
        "trust_score": 75,
        "risk_level": "medium",
        "summary": "This website shows...",
        "explanation": "In simple terms...",
        "actionable_advice": ["Do these 3 things..."],
        "green_flags": ["Valid SSL certificate", "Contact info visible"],
        "concerns": ["Detected countdown timer (potential urgency tactic)"]
    }
}
```

**Problem:**
- **CWE Mapping**: Each finding needs correct CWE ID mapping (CWE-89 for SQL injection, etc.)
- **CVSS Scoring**: Requires CVSS 3.1 calculator implementation
- **IOC Extraction**: Need to identify malicous domains, IPs, threat indicators
- **Separate Narratives**: Technical detailed vs. non-technical simple explanations

**Mitigation Strategy:**

**A. CWE Taxonomy Mapping**
```python
# veritas/agents/judge/cwe_mapping.py (new file)
from typing import Dict, List
from enum import Enum

logger = logging.getLogger(__name__)

class CWECategory(Enum):
    """CWE categories mapped to VERITAS finding types."""
    INJECTION = " CWE-89"  # SQL Injection
    XSS = "CWE-79"        # Cross-site Scripting
    CSRF = "CWE-352"      # Cross-Site Request Forgery
    AUTH_BYPASS = "CWE-287"  # Authentication Bypass
    SESSION_MGMT = "CWE-613"  # Insufficient Session Expiration
    DATA_LEAK = "CWE-311"     # Missing Encryption
    INPUT_VALIDATION = "CWE-20"  # Improper Input Validation
    REDIRECT = "CWE-601"       # Open Redirect
    INFO_DISCLOSURE = "CWE-200"  # Information Exposure
    SSRF = "CWE-918"        # Server-Side Request Forgery

class CWEMapper:
    """Maps VERITAS findings to CWE IDs."""

    # Finding category → CWE mapping
    FINDING_CWE_MAP = {
        # SQL Injection
        'sql_injection': CWECategory.INJECTION.value,

        # XSS
        'reflected_xss': CWECategory.XSS.value,
        'stored_xss': CWECategory.XSS.value,
        'dom_xss': CWECategory.XSS.value,

        # CSRF
        'csrf_vulnerability': CWECategory.CSRF.value,

        # Authentication
        'weak_auth': CWECategory.AUTH_BYPASS.value,
        'no_password_policy': CWECategory.AUTH_BYPASS.value,

        # Session
        'insecure_cookies': CWECategory.SESSION_MGMT.value,
        'http_cookies': CWECategory.SESSION_MGMT.value,

        # Encryption
        'no_https': CWECategory.DATA_LEAK.value,
        'weak_ssl': CWECategory.DATA_LEAK.value,
        'expired_ssl': CWECategory.DATA_LEAK.value,

        # Input Validation (for dark patterns that could indicate manipulation)
        'form_action_off_domain': CWECategory.INPUT_VALIDATION.value,
        'redirect_chain': CWECategory.REDIRECT.value,

        # Information Disclosure
        'exposed_config': CWECategory.INFO_DISCLOSURE.value,
        'debug_info': CWECategory.INFO_DISCLOSURE.value,

        # SSRF
        'ssrf_vulnerability': CWECategory.SSRF.value,
    }

    # Dark patterns don't map to CWE (not technical vulnerabilities)
    DARK_PATTERN_NO_CWE = {
        'countdown_timer', 'fake_urgency', 'scarcity_indication',
        'social_proof_faked', 'confirmshaming', 'misdirection',
        'obstruction', 'forced_action'
    }

    def map_finding_to_cwe(self, finding_type: str) -> str:
        """Map VERITAS finding type to CWE ID."""
        # Dark patterns don't have CWE IDs
        if finding_type in self.DARK_PATTERN_NO_CWE:
            return None

        # Security findings map to CWE
        cwe = self.FINDING_CWE_MAP.get(finding_type)
        if cwe:
            return cwe

        # Fallback: try to find partial match
        for pattern, cwe_id in self.FINDING_CWE_MAP.items():
            if pattern in finding_type or finding_type in pattern:
                return cwe_id

        logger.warning(f"No CWE mapping for finding type: {finding_type}")
        return None

    def get_cwe_description(self, cwe_id: str) -> str:
        """Get human-readable CWE description."""
        descriptions = {
            CWECategory.INJECTION.value: "SQL Injection - Malicious code insertion via SQL queries",
            CWECategory.XSS.value: "Cross-Site Scripting - Injection of malicious scripts",
            CWECategory.CSRF.value: "Cross-Site Request Forgery - Unauthorized actions on behalf of authenticated user",
            CWECategory.AUTH_BYPASS.value: "Authentication Bypass - Vulnerability allows unauthorized access",
            CWECategory.SESSION_MGMT.value: "Insufficient Session Expiration - Sessions remain active too long",
            CWECategory.DATA_LEAK.value: "Missing Encryption - Sensitive data transmitted without encryption",
            CWECategory.INPUT_VALIDATION.value: "Improper Input Validation - Lack of input sanitization",
            CWECategory.REDIRECT.value: "Open Redirect - Unvalidated redirect allows phishing attacks",
            CWECategory.INFO_DISCLOSURE.value: "Information Exposure - Sensitive information exposed",
            CWECategory.SSRF.value: "Server-Side Request Forgery - Server forced to make requests",
        }
        return descriptions.get(cwe_id, "No description available")
```

**B. CVSS 3.1 Calculator**
```python
# veritas/agents/judge/cvss_calculator.py (new file)
"""
CVSS 3.1 Calculator Implementation.

Based on NIST CVSS 3.1 specification.
https://www.first.org/cvss/calculator/3.1
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class CVSSAttackVector(Enum):
    NETWORK = "N"  # Attackable over network
    ADJACENT = "A" # Attackable over adjacent network
    LOCAL = "L"    # Attack requires local access
    PHYSICAL = "P" # Attack requires physical access

class CVSSAttackComplexity(Enum):
    LOW = "L"       # Little expertise needed
    HIGH = "H"     # Expertise needed

class CVSSPrivilegesRequired(Enum):
    NONE = "N"     # No privileges
    LOW = "L"      # Some user privileges
    HIGH = "H"     # Administrative privileges

class CVSSUserInteraction(Enum):
    NONE = "N"     # No user action required
    REQUIRED = "R" # User action required

class CVSSScope(Enum):
    UNCHANGED = "U" # Vulnerability doesn't affect other components
    CHANGED = "C"   # Vulnerability affects other components

class CVSSImpact(Enum):
    HIGH = "H"
    LOW = "L"
    NONE = "N"

@dataclass
class CVSSMetrics:
    """CVSS 3.1 metrics."""
    # Base Metrics
    attack_vector: CVSSAttackVector
    attack_complexity: CVSSAttackComplexity
    privileges_required: CVSSPrivilegesRequired
    user_interaction: CVSSUserInteraction
    scope: CVSSScope
    confidentiality_impact: CVSSImpact
    integrity_impact: CVSSImpact
    availability_impact: CVSSImpact

class CVSSCalculator:
    """Calculate CVSS 3.1 scores from metrics."""

    # Impact subscores for C/I/A
    IMPACT_SUBSCORES = {
        CVSSImpact.HIGH: 0.56,
        CVSSImpact.LOW: 0.22,
        CVSSImpact.NONE: 0.0,
    }

    # Exploitability scores
    EXPLOITABILITY_SCORES = {
        (CVSSAttackVector.NETWORK, CVSSAttackComplexity.LOW, CVSSPrivilegesRequired.NONE, CVSSUserInteraction.NONE): 0.85,
        (CVSSAttackVector.NETWORK, CVSSAttackComplexity.LOW, CVSSPrivilegesRequired.LOW, CVSSUserInteraction.NONE): 0.62,
        (CVSSAttackVector.NETWORK, CVSSAttackComplexity.LOW, CVSSPrivilegesRequired.HIGH, CVSSUserInteraction.NONE): 0.68,
        # ... (would expand for all combinations, but for brevity include key ones)
    }

    def calculate_base_score(self, metrics: CVSSMetrics) -> float:
        """Calculate CVSS 3.1 base score (0-10)."""
        # Step 1: Calculate Impact (ISS)
        iss = self._calculate_iss(
            metrics.confidentiality_impact,
            metrics.integrity_impact,
            metrics.availability_impact
        )

        # Step 2: Calculate Impact
        if metrics.scope == CVSSScope.UNCHANGED:
            impact = 6.42 * iss
        else:  # CHANGED
            impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02)**15

        impact = min(10, impact)

        # Step 3: Calculate Exploitability
        exploitability = self._calculate_exploitability(metrics)

        # Step 4: Calculate Base Score
        if impact <= 0:
            return 0.0

        if metrics.scope == CVSSScope.UNCHANGED:
            base = min(10, impact + exploitability)
        else:  # CHANGED
            base = min(10, 1.08 * (impact + exploitability))

        return round(base, 1)

    def _calculate_iss(self, c: CVSSImpact, i: CVSSImpact, a: CVSSImpact) -> float:
        """Calculate Impact Subscore (ISS)."""
        c_val = self.IMPACT_SUBSCORES[c]
        i_val = self.IMPACT_SUBSCORES[i]
        a_val = self.IMPACT_SUBSCORES[a]

        return 1 - (1 - c_val) * (1 - i_val) * (1 - a_val)

    def _calculate_exploitability(self, metrics: CVSSMetrics) -> float:
        """Calculate Exploitability score."""
        # Simplified lookup (full implementation would have all combinations)
        key = (
            metrics.attack_vector,
            metrics.attack_complexity,
            metrics.privileges_required,
            metrics.user_interaction
        )

        return self.EXPLOITABILITY_SCORES.get(key, 0.5)

    def get_severity(self, score: float) -> str:
        """Get severity level from score."""
        if score >= 9.0:
            return "critical"
        elif score >= 7.0:
            return "high"
        elif score >= 4.0:
            return "medium"
        elif score > 0:
            return "low"
        else:
            return "none"

    def generate_cvss_vector(self, metrics: CVSSMetrics) -> str:
        """Generate CVSS 3.1 vector string."""
        return (
            f"CVSS:3.1/"
            f"AV:{metrics.attack_vector.value}/"
            f"AC:{metrics.attack_complexity.value}/"
            f"PR:{metrics.privileges_required.value}/"
            f"UI:{metrics.user_interaction.value}/"
            f"S:{metrics.scope.value}/"
            f"C:{metrics.confidentiality_impact.value}/"
            f"I:{metrics.integrity_impact.value}/"
            f"A:{metrics.availability_impact.value}"
        )

    def estimate_metrics_from_finding(self, finding: dict) -> CVSSMetrics:
        """
        Estimate CVSS metrics from finding attributes.

        This is an estimation - for accurate CVSS, manual scoring is preferred.
        """
        severity = finding.get('severity', 'medium').lower()

        # Map severity to CVSS impact
        if severity in ['critical', 'high']:
            c_i_a = CVSSImpact.HIGH
        elif severity == 'medium':
            c_i_a = CVSSImpact.LOW
        else:
            c_i_a = CVSSImpact.NONE

        # Estimate other metrics (simplified)
        return CVSSMetrics(
            attack_vector=CVSSAttackVector.NETWORK if finding.get('external', False) else CVSSAttackVector.LOCAL,
            attack_complexity=CVSSAttackComplexity.LOW,  # Most web vulnerabilities are easy to exploit
            privileges_required=CVSSPrivilegesRequired.NONE,  # Most web vulnerabilities need no auth
            user_interaction=CVSSUserInteraction.NONE,  # Most web vulnerabilities don't need user action
            scope=CVSSScope.UNCHANGED,  # Default to unchanged
            confidentiality_impact=c_i_a,
            integrity_impact=c_i_a,
            availability_impact=c_i_a
        )
```

**C. IOC (Indicator of Compromise) Extraction**
```python
# veritas/agents/judge/ioc_extractor.py (new file)
"""
Extract Indicators of Compromise (IOCs) from findings.

IOCs include:
- Malicious domains
- Suspicious IPs
- File hashes (SHA-256, MD5)
- URLs
- Email addresses
- Registry keys (less relevant for web)
"""

import re
import logging
from typing import List, Dict, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IOC:
    indicator_type: str  # 'domain', 'ip', 'url', 'email', 'hash'
    value: str
    confidence: float
    source: str  # Which finding agent found this

class IOCExtractor:
    """Extract IOCs from agent findings."""

    # Regex patterns for IOCs
    PATTERNS = {
        'domain': re.compile(r'(?:https?://)?(?:[\w-]+\.)+[\w-]+'),
        'ip': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        'email': re.compile(r'\b[\w.-]+@[\w.-]+\.\w+\b'),
        'url': re.compile(r'https?://(?:[\w-]+\.)+[\w-]+(?:/[\w-./?%&=]*)?'),
        # Hash patterns (MD5: 32 hex, SHA-256: 64 hex)
        'hash_md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
        'hash_sha256': re.compile(r'\b[a-fA-F0-9]{64}\b'),
    }

    def extract_ios(self, findings: List[dict]) -> Dict[str, List[IOC]]:
        """
        Extract IOCs from all findings.

        Returns:
            {'domains': [...], 'ips': [...], 'urls': [...], 'emails': [...]}
        """
        ios = {
            'domains': [],
            'ips': [],
            'urls': [],
            'emails': [],
            'hashes': []
        }

        for finding in findings:
            # Extract from finding description and evidence
            text = finding.get('description', '')
            evidence = str(finding.get('evidence', {}))

            combined = text + ' ' + evidence

            # Extract domains
            domains = self._extract_pattern(combined, 'domain')
            if domains:
                ios['domains'].extend([
                    IOC('domain', d, 0.7, finding.get('category', 'unknown'))
                    for d in domains
                ])

            # Extract IPs
            ips = self._extract_pattern(combined, 'ip')
            if ips:
                ios['ips'].extend([
                    IOC('ip', ip, 0.6, finding.get('category', 'unknown'))
                    for ip in ips
                ])

            # Extract URLs
            urls = self._extract_pattern(combined, 'url')
            if urls:
                ios['urls'].extend([
                    IOC('url', url, 0.7, finding.get('category', 'unknown'))
                    for url in urls
                ])

            # Extract emails from evidence (contact forms, etc.)
            emails = self._extract_pattern(combined, 'email')
            if emails:
                ios['emails'].extend([
                    IOC('email', email, 0.5, finding.get('category', 'unknown'))
                    for email in emails
                ])

            # Extract hashes from security analysis evidence
            hashes_md5 = self._extract_pattern(combined, 'hash_md5')
            hashes_sha256 = self._extract_pattern(combined, 'hash_sha256')
            if hashes_md5:
                ios['hashes'].extend([
                    IOC('hash_md5', h, 0.8, finding.get('category', 'unknown'))
                    for h in hashes_md5
                ])
            if hashes_sha256:
                ios['hashes'].extend([
                    IOC('hash_sha256', h, 0.9, finding.get('category', 'unknown'))
                    for h in hashes_sha256
                ])

        # Deduplicate
        for key in ios:
            seen = set()
            unique = []
            for ioc in ios[key]:
                if ioc.value not in seen:
                    seen.add(ioc.value)
                    unique.append(ioc)
            ios[key] = unique

        return ios

    def _extract_pattern(self, text: str, pattern_key: str) -> List[str]:
        """Extract all matches for a pattern."""
        pattern = self.PATTERNS.get(pattern_key)
        if not pattern:
            return []

        matches = pattern.findall(text)

        # Filter and normalize
        if pattern_key == 'domain':
            # Remove common false positives
            filtered = [m for m in matches if not m.startswith(('example', 'test', 'localhost'))]
            return filtered
        elif pattern_key == 'ip':
            # Remove private IP ranges
            public_ips = []
            for ip in matches:
                octets = list(map(int, ip.split('.')))
                if not (octets[0] in [10] or
                       (octets[0] == 192 and octets[1] == 168) or
                       (octets[0] == 172 and 16 <= octets[1] <= 31)):
                    public_ips.append(ip)
            return public_ips
        else:
            return matches

    def detect_malicious_ios(self, ios: Dict[str, List[IOC]], osint_results: Dict) -> Dict:
        """
        Cross-reference IOCs with OSINT results to detect malicious indicators.

        Uses results from Phase 8 OSINT analysis.
        """
        malicious_ios = {
            'malicious_domains': [],
            'suspicious_ips': [],
            'threat_indicators': []
        }

        # Check domains against OSINT
        for ioc in ios.get('domains', []):
            domain = ioc.value
            if osint_results.get('virustotal', {}).get('malicious', False):
                malicious_ios['malicious_domains'].append({
                    'domain': domain,
                    'source': 'virustotal',
                    'confidence': osint_results.get('virustotal', {}).get('confidence', 0)
                })
            if domain in osint_results.get('offline_feeds', {}).get('findings', []):
                malicious_ios['threat_indicators'].append({
                    'type': 'domain',
                    'value': domain,
                    'source': 'offline_threat_feed',
                    'details': 'Domain in threat database'
                })

        # Check IPs against OSINT
        for ioc in ios.get('ips', []):
            ip = ioc.value
            if osint_results.get('abuseipdb', {}).get('is_malicious', False):
                malicious_ios['suspicious_ips'].append({
                    'ip': ip,
                    'source': 'abuseipdb',
                    'abuse_confidence': osint_results.get('abuseipdb', {}).get('abuse_confidence_score', 0)
                })

        return malicious_ios
```

**D. DualVerdict Dataclass**
```python
# veritas/agents/judge/dual_verdict.py (new file)
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRUSTED = "trusted"

@dataclass
class VerdictTechnical:
    """Technical verdict for security professionals."""
    trust_score: float  # 0-100
    risk_level: RiskLevel
    cwe_ids: List[str] = field(default_factory=list)
    cvss_score: Optional[str] = None
    cvss_base_score: Optional[float] = None
    cvss_severity: Optional[str] = None
    iocs: Dict[str, List[dict]] = field(default_factory=dict)
    findings: List[dict] = field(default_factory=list)
    security_findings: List[dict] = field(default_factory=list)
    osint_intel: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'trust_score': self.trust_score,
            'risk_level': self.risk_level.value,
            'cwe_ids': self.cwe_ids,
            'cvss': {
                'vector': self.cvss_score,
                'base_score': self.cvss_base_score,
                'severity': self.cvss_severity
            },
            'iocs': self.iocs,
            'findings': self.findings,
            'security_findings': self.security_findings,
            'osint_intel': self.osint_intel
        }

@dataclass
class VerdictNonTechnical:
    """Non-technical verdict for general users."""
    trust_score: float  # 0-100
    risk_level: RiskLevel
    summary: str  # One-sentence summary
    explanation: str  # Plain English explanation
    actionable_advice: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    emoji_rating: str = "🤔"  # Emoji for quick visual assessment

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'trust_score': self.trust_score,
            'risk_level': self.risk_level.value,
            'summary': self.summary,
            'explanation': self.explanation,
            'actionable_advice': self.actionable_advice,
            'green_flags': self.green_flags,
            'concerns': self.concerns,
            'emoji_rating': self.emoji_rating
        }

@dataclass
class DualVerdict:
    """Dual-tier verdict combining technical and non-technical views."""
    technical: VerdictTechnical
    non_technical: VerdictNonTechnical
    version: str = "2.0"
    timestamp: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'technical': self.technical.to_dict(),
            'non_technical': self.non_technical.to_dict(),
            'version': self.version,
            'timestamp': self.timestamp
        }
```

---

### 2. Site-Type Strategy Weight Explosion (MEDIUM)

**Risk:** 11 site types × 6 signals × customizable weights = 66 weights to maintain

**Problem:**
- Current trust_weights.py has static weights
- Need 11 sets of weights
- Hard to tune and debug
- Performance impact

**Solution:**
```python
# veritas/agents/judge/site_type_strategies.py (new file)
from dataclasses import dataclass
from typing import Dict
from enum import Enum

logger = logging.getLogger(__name__)

class SiteType(Enum):
    """Website types with different scoring priorities."""
    E_COMMERCE = "ecommerce"       # Online stores
    FINANCIAL = "financial"        # Banking, investing
    PORTFOLIO = "portfolio"        # Personal websites
    SOCIAL_MEDIA = "social"        # Social networks
    NEWS = "news"                  # News sites
    BLOG = "blog"                  # Personal blogs
    FORUM = "forum"                # Discussion forums
    DIRECTORY = "directory"        # Link directories
    LANDING_PAGE = "landing"       # Single-page marketing
    SAAS = "saas"                  # Software as a Service
    CORPORATE = "corporate"        # Company websites

@dataclass
class SignalWeights:
    """Base configuration for signal weights."""
    visual: float     # Vision Agent findings
    structural: float # DOM structure analysis
    temporal: float   # Temporal dynamics
    graph: float      # Entity verification
    meta: float       # SEO/meta analysis
    security: float   # Security module findings

    def to_dict(self) -> Dict[str, float]:
        return {
            'visual': self.visual,
            'structural': self.structural,
            'temporal': self.temporal,
            'graph': self.graph,
            'meta': self.meta,
            'security': self.security
        }

class SiteTypeStrategy:
    """Base strategy for site-type-specific scoring."""

    def __init__(self, site_type: SiteType):
        self.site_type = site_type
        self.weights = self._get_weights()
        self.thresholds = self._get_thresholds()

    def _get_weights(self) -> SignalWeights:
        """Get signal weights for this site type."""
        return SIGNAL_WEIGHTS_DEFAULT  # Default

    def _get_thresholds(self) -> Dict[RiskLevel, Tuple[float, float]]:
        """Get trust score thresholds for risk levels."""
        return RISK_THRESHOLDS_DEFAULT

# Default weights (used as fallback)
SIGNAL_WEIGHTS_DEFAULT = SignalWeights(
    visual=0.2,
    structural=0.15,
    temporal=0.1,
    graph=0.2,
    meta=0.15,
    security=0.2
)

# Default risk thresholds [(low_bound, high_bound)]
RISK_THRESHOLDS_DEFAULT = {
    RiskLevel.TRUSTED: (85, 100),
    RiskLevel.LOW: (70, 85),
    RiskLevel.MEDIUM: (40, 70),
    RiskLevel.HIGH: (20, 40),
    RiskLevel.CRITICAL: (0, 20)
}

# Site-type strategies
SITE_TYPE_STRATEGIES = {
    # E-commerce: Social proof and security most important
    SiteType.E_COMMERCE: ECommerceStrategy,

    # Financial: Security critical
    SiteType.FINANCIAL: FinancialStrategy,

    # Portfolio: Lower standards
    SiteType.PORTFOLIO: PortfolioStrategy,

    # News: Content quality matters
    SiteType.NEWS: NewsStrategy,

    # ... (other strategies omitted for brevity)
}

class ECommerceStrategy(SiteTypeStrategy):
    """E-commerce site scoring strategy."""

    def _get_weights(self) -> SignalWeights:
        return SignalWeights(
            visual=0.2,      # Dark patterns common in e-commerce
            structural=0.15,
            temporal=0.1,
            graph=0.2,      # Entity verification important
            meta=0.1,
            security=0.25   # Security critical for payments
        )

    def _get_thresholds(self) -> Dict[RiskLevel, Tuple[float, float]]:
        # Stricter thresholds for e-commerce (users enter payment info)
        return {
            RiskLevel.TRUSTED: (90, 100),
            RiskLevel.LOW: (80, 90),
            RiskLevel.MEDIUM: (50, 80),
            RiskLevel.HIGH: (30, 50),
            RiskLevel.CRITICAL: (0, 30)
        }

class FinancialStrategy(SiteTypeStrategy):
    """Financial site scoring strategy."""

    def _get_weights(self) -> SignalWeights:
        return SignalWeights(
            visual=0.1,      # Less important
            structural=0.1,
            temporal=0.1,
            graph=0.3,      # Entity verification critical
            meta=0.1,
            security=0.3     # Security critical
        )

    def _get_thresholds(self) -> Dict[RiskLevel, Tuple[float, float]]:
        # Very strict thresholds for financial sites
        return {
            RiskLevel.TRUSTED: (95, 100),
            RiskLevel.LOW: (85, 95),
            RiskLevel.MEDIUM: (60, 85),
            RiskLevel.HIGH: (40, 60),
            RiskLevel.CRITICAL: (0, 40)
        }

class PortfolioStrategy(SiteTypeStrategy):
    """Personal portfolio website strategy."""

    def _get_weights(self) -> SignalWeights:
        return SignalWeights(
            visual=0.25,     # Aesthetics more important
            structural=0.2,
            temporal=0.05,
            graph=0.15,
            meta=0.2,
            security=0.15    # Less critical (no payment processing)
        )

    def _get_thresholds(self) -> Dict[RiskLevel, Tuple[float, float]]:
        # More lenient thresholds for portfolios
        return {
            RiskLevel.TRUSTED: (80, 100),
            RiskLevel.LOW: (65, 80),
            RiskLevel.MEDIUM: (40, 65),
            RiskLevel.HIGH: (20, 40),
            RiskLevel.CRITICAL: (0, 20)
        }

class NewsStrategy(SiteTypeStrategy):
    """News website strategy."""

    def _get_weights(self) -> SignalWeights:
        return SignalWeights(
            visual=0.15,
            structural=0.2,
            temporal=0.15,   # Content freshness
            graph=0.25,      # Source verification critical
            meta=0.15,       # SEO, source attribution
            security=0.1     # Less critical
        )

    def _get_thresholds(self) -> Dict[RiskLevel, Tuple[float, float]]:
        return {
            RiskLevel.TRUSTED: (85, 100),
            RiskLevel.LOW: (70, 85),
            RiskLevel.MEDIUM: (50, 70),
            RiskLevel.HIGH: (30, 50),
            RiskLevel.CRITICAL: (0, 30)
        }
```

---

### 3. Orchestrator Time Management Complexity (MEDIUM)

**Risk:** Adaptive timeouts and estimated completion time with parallel execution adds unpredictability

**Problem:**
- Current: Fixed 30s timeout per agent
- New: "Adaptive timeout strategies (adjust based on page size, complexity)"
- How to estimate page complexity ahead of time?
- How to provide accurate countdown when variable execution times?

**Solution:**
```python
# veritas/core/orchestrator/complexity_estimator.py (new file)
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PageComplexity(Enum):
    TRIVIAL = "trivial"     # <10KB HTML, few scripts
    SIMPLE = "simple"       # 10-100KB, moderate scripts
    MODERATE = "moderate"   # 100-500KB, many scripts
    COMPLEX = "complex"     # 500KB-2MB, heavy frameworks
    VERY_COMPLEX = "very_complex"  # >2MB, SPA, infinite scroll

@dataclass
class ComplexityEstimate:
    """Estimated complexity of a web page."""
    complexity: PageComplexity
    estimated_vision_time: float  # seconds
    estimated_security_time: float
    estimated_osint_time: float
    total_estimated_time: float
    confidence: float  # 0-1, how confident in estimate

class ComplexityEstimator:
    """Estimate page complexity from Scout metadata."""

    def __init__(self):
        self.base_times = {
            PageComplexity.TRIVIAL: {'vision': 5, 'security': 2, 'osint': 5},
            PageComplexity.SIMPLE: {'vision': 10, 'security': 5, 'osint': 10},
            PageComplexity.MODERATE: {'vision': 20, 'security': 10, 'osint': 15},
            PageComplexity.COMPLEX: {'vision': 30, 'security': 15, 'osint': 20},
            PageComplexity.VERY_COMPLEX: {'vision': 45, 'security': 20, 'osint': 30},
        }

    def estimate(self, scout_result: dict) -> ComplexityEstimate:
        """Estimate complexity from Scout result metadata."""
        dom_meta = scout_result.get('dom_metadata', {})
        page_height = scout_result.get('lazy_loading', {}).get('final_height', 0)

        # Estimate DOM size
        dom_size = dom_meta.get('element_count', 0)
        script_count = dom_meta.get('script_count', 0)
        image_count = dom_meta.get('image_count', 0)

        # Determine complexity
        complexity = self._determine_complexity(dom_size, script_count, image_count, page_height)

        # Get base times
        base_times = self.base_times[complexity]

        # Adjust for multi-page
        page_count = scout_result.get('depth', 0) + 1
        vision_time = base_times['vision'] * page_count
        security_time = base_times['security'] * page_count
        osint_time = base_times['osint']  # OSINT doesn't scale linearly with pages (cached)
        total = vision_time + security_time + osint_time

        # Confidence (higher if more metadata available)
        confidence = min(1.0, dom_size / 1000 + script_count / 50 + image_count / 20)

        return ComplexityEstimate(
            complexity=complexity,
            estimated_vision_time=vision_time,
            estimated_security_time=security_time,
            estimated_osint_time=osint_time,
            total_estimated_time=total,
            confidence=confidence
        )

    def _determine_complexity(self, dom_size: int, script_count: int, image_count: int, page_height: int) -> PageComplexity:
        """Determine complexity level."""
        # Very complex: SPA detection + large DOM
        if dom_size > 5000 or script_count > 50 or page_height > 10000:
            return PageComplexity.VERY_COMPLEX

        # Complex: Moderate size
        if dom_size > 1000 or script_count > 20 or image_count > 50:
            return PageComplexity.COMPLEX

        # Moderate
        if dom_size > 200 or script_count > 5 or image_count > 10:
            return PageComplexity.MODERATE

        # Simple
        if dom_size > 50:
            return PageComplexity.SIMPLE

        # Trivial
        return PageComplexity.TRIVIAL


# veritas/core/orchestrator/adaptive_orchestrator.py (new file)
class AdaptiveOrchestrator:
    """Orchestrator with adaptive timeout and progress tracking."""

    def __init__(self):
        self.complexity_estimator = ComplexityEstimator()
        self.progress_tracker = ProgressTracker()

    async def execute_adaptive_audit(self, url: str, audit_tier: str = "standard") -> dict:
        """Execute audit with adaptive timeouts and progress tracking."""

        # Step 1: Scout (first pass to estimate complexity)
        scout_start = time.time()
        scout_result = await self._execute_scout(url)
        scout_time = time.time() - scout_start

        # Step 2: Estimate complexity
        complexity = self.complexity_estimator.estimate(scout_result)

        # Emit estimated completion time
        await self.progress_tracker.emit_estimate(complexity.total_estimated_time)

        # Step 3: Execute other agents with adaptive timeouts
        vision_result = await self._execute_vision(
            scout_result,
            timeout=self._calc_timeout(complexity, 'vision')
        )

        security_result = await self._execute_security(
            scout_result,
            timeout=self._calc_timeout(complexity, 'security')
        )

        osint_result = await self._execute_osint(
            url,
            timeout=self._calc_timeout(complexity, 'osint')
        )

        # Step 4: Judge with multi-source validation results
        judge_result = await self._execute_judge({
            'scout': scout_result,
            'vision': vision_result,
            'security': security_result,
            'osint': osint_result
        })

        return {
            'scout': scout_result,
            'vision': vision_result,
            'security': security_result,
            'osint': osint_result,
            'judge': judge_result,
            'complexity_estimate': complexity,
            'actual_time': time.time() - scout_start
        }

    def _calc_timeout(self, complexity: ComplexityEstimate, phase: str) -> float:
        """Calculate adaptive timeout based on complexity and phase."""
        base_time = {
            'vision': complexity.estimated_vision_time,
            'security': complexity.estimated_security_time,
            'osint': complexity.estimated_osint_time
        }[phase]

        # Add 2x safety margin
        return base_time * 2.0

class ProgressTracker:
    """Track progress and estimate completion time."""

    def __init__(self):
        self.start_time = None
        self.estimated_total = None
        self.last_progress_update = 0

    async def emit_estimate(self, estimated_seconds: float):
        """Emit estimated completion time."""
        self.start_time = time.time()
        self.estimated_total = estimated_seconds

        await self._emit({
            "type": "audit_established",
            "estimated_duration_seconds": estimated_seconds,
            "estimated_completion_time": self.start_time + estimated_seconds
        })

    async def update_progress(self, phase: str, progress_pct: float):
        """Update progress and emit countdown."""
        if not self.start_time or not self.estimated_total:
            return

        elapsed = time.time() - self.start_time
        remaining = max(0, self.estimated_total - elapsed)

        await self._emit({
            "type": "progress_update",
            "phase": phase,
            "progress_pct": progress_pct,
            "elapsed_seconds": elapsed,
            "estimated_remaining_seconds": remaining
        })

    async def _emit(self, event: dict):
        """Emit progress event."""
        print(f"##PROGRESS:{json.dumps(event)}", flush=True)
```

---

## Dependencies (What Must Complete First)

### Internal (Within Phase 9)
1. **CWE Mapping → CVSS Calculator**: Map findings to CWE first, then calculate CVSS
2. **IOC Extraction → Malicious IOCs**: Extract IOCs, then cross-reference with OSINT
3. **SiteType Strategy → Judge Result**: Determine site type first, then apply strategy
4. **Complexity Estimator → Adaptive Timeout**: Estimate complexity before setting timeouts

### External (From Previous Phases)
1. **Phase 7 (Quality Foundation)**: Multi-source validated findings feed into Judge
2. **Phase 8 (OSINT Integration)**: OSINT results used for IOC verification and trust scoring
3. **Phase 1-5 (v1.0 Core)**: ✅ DONE

### Blocks for Future Phases
1. **Phase 10 (Cybersecurity)**: Security findings feed into technical verdict (CWE/CVSS)
2. **Phase 11 (Showcase)**: Dual-tier verdict enables appropriate front-end display selection

---

## Task Breakdown (With File Locations)

### 9.1 Implement CWEMapper and CVE Mapping

**Files:**
- `veritas/agents/judge/cwe_mapping.py` (new file)

**Tasks:**
- Map finding categories to CWE IDs
- Implement CWE description lookup
- Handle dark patterns (no CWE mapping)
- Handle unknown finding types gracefully

---

### 9.2 Implement CVSSCalculator

**Files:**
- `veritas/agents/judge/cvss_calculator.py` (new file)

**Tasks:**
- Implement CVSS 3.1 base score calculation
- Implement CVSS vector string generation
- Map finding severity to CVSS metrics (estimation)
- Calculate severity level from score

---

### 9.3 Implement IOCExtractor

**Files:**
- `veritas/agents/judge/ioc_extractor.py` (new file)

**Tasks:**
- Extract domains, IPs, URLs, emails, hashes
- Cross-reference IOCs with OSINT results
- Detect malicious IOCs
- Format IOCs for technical verdict

---

### 9.4 Implement SiteTypeStrategy Classes

**Files:**
- `veritas/agents/judge/site_type_strategies.py` (new file)

**Tasks:**
- Define 11 site types
- Create base strategy class
- Implement ECommerce, Financial, Portfolio, News strategies
- Create weight configurations per site type

---

### 9.5 Implement DualVerdict Dataclasses

**Files:**
- `veritas/agents/judge/dual_verdict.py` (new file)

**Tasks:**
- Define VerdictTechnical dataclass
- Define VerdictNonTechnical dataclass
- Define DualVerdict container
- Implement to_dict() methods

---

### 9.6 Implement ComplexityEstimator

**Files:**
- `veritas/core/orchestrator/complexity_estimator.py` (new file)

**Tasks:**
- Analyze DOM metadata for complexity metrics
- Determine complexity level (trivial → very_complex)
- Estimate time per phase
- Calculate total estimated time

---

### 9.7 Implement AdaptiveOrchestrator

**Files:**
- `veritas/core/orchestrator/adaptive_orchestrator.py` (new file)

**Tasks:**
- Execute Scout first to estimate
- Calculate adaptive timeouts per phase
- Track real progress
- Emit countdown for frontend

---

## Test Strategy

### Unit Tests

**Test: CWE Mapping**
```python
def test_map_sql_injection_to_cwe():
    mapper = CWEMapper()
    cwe = mapper.map_finding_to_cwe('sql_injection')
    assert cwe == 'CWE-89'

def test_map_dark_pattern_no_cwe():
    mapper = CWEMapper()
    cwe = mapper.map_finding_to_cwe('countdown_timer')
    assert cwe is None
```

**Test: CVSS Calculation**
```python
def test_cvss_calculation_high_severity():
    metrics = CVSSMetrics(
        attack_vector=CVSSAttackVector.NETWORK,
        attack_complexity=CVSSAttackComplexity.LOW,
        privileges_required=CVSSPrivilegesRequired.NONE,
        user_interaction=CVSSUserInteraction.NONE,
        scope=CVSSScope.UNCHANGED,
        confidentiality_impact=CVSSImpact.HIGH,
        integrity_impact=CVSSImpact.HIGH,
        availability_impact=CVSSImpact.HIGH
    )

    score = CVSSCalculator().calculate_base_score(metrics)

    assert score >= 9.0  # Critical
```

**Test: SiteTypeStrategy eCommerce**
```python
def test_ecommerce_weights_security_heavier():
    strategy = ECommerceStrategy(SiteType.E_COMMERCE)
    weights = strategy.weights

    assert weights.security > weights.visual
    assert weights.security == 0.25
```

**Test: ConflictResolver weighted aggregation**
```python
def test_conflict_resolver_trust_weighted():
    resolver = ConflictResolver()

    # Conflicting results from different sources
    results = {
        'high_trust': {'trust_score': 0.95, 'findings': ['critical_vuln']},
        'low_trust': {'trust_score': 0.60, 'findings': ['no_vuln']}
    }

    resolved = resolver.resolve(results)

    # High-trust source should dominate
    assert 'critical_vuln' in resolved['findings']
    assert resolved['weighted_confidence'] > 0.8
```

**Test: ConflictResolver WEIGHTING logic - high-trust overrides lower-trust**
```python
def test_conflict_resolver_high_trust_overrides_low_trust():
    """Verify high-trust sources correctly override lower-trust sources."""
    resolver = ConflictResolver()

    # Scenario: VirusTotal (HIGH trust) vs URLVoid (MEDIUM trust)
    vt_result = {'malicious': True, 'confidence': 0.7}
    urlvoid_result = {'malicious': False, 'confidence': 0.8}

    # Give URLVoid lower trust weight
    SOURCE_WEIGHTS = {
        'virustotal': SourceTrustWeight('virustotal', SourceTrustLevel.HIGH, 0.9, 1.2),
        'urlvoid': SourceTrustWeight('urlvoid', SourceTrustLevel.MEDIUM, 0.6, 1.0),
    }

    results = {
        'virustotal': vt_result,
        'urlvoid': urlvoid_result
    }

    resolution = resolver.resolve(results)

    # HIGH trust malicious should override MEDIUM trust clean
    assert resolution['malicious'] == True
    assert resolution['confidence'] > 60  # Higher due to trust weight bias

    # Verify trust breakdown prioritizes high-trust source
    assert resolution['trust_breakdown']['weighted_malicious_score'] > resolution['trust_breakdown']['weighted_clean_score']

    # Verify resolution notes explain the decision
    notes = '\n'.join(resolution['resolution_notes'])
    assert 'virustotal' in notes.lower()
```

**Test: SiteTypeStrategy thresholds verify scoring adjustments**
```python
def test_site_type_strategy_thresholds_scoring_adjustments():
    """Verify scoring adjustments based on detected site type."""
    from veritas.agests.judge.site_type_strategies import (
        ECommerceStrategy, FinancialStrategy, PortfolioStrategy, SiteType, RiskLevel
    )

    # Test E-commerce stricter thresholds
    ecommerce = ECommerceStrategy(SiteType.E_COMMERCE)
    ecommerce_weights = ecommerce.weights
    ecommerce_thresholds = ecommerce._get_thresholds()

    # E-commerce should weight security heavier (0.25) than others
    assert ecommerce_weights.security == 0.25
    assert ecommerce_weights.visual == 0.2

    # E-commerce TRUSTED threshold should be 90 (stricter than default 85)
    trusted_threshold = ecommerce_thresholds[RiskLevel.TRUSTED]
    assert trusted_threshold[0] == 90  # Minimum TRUSTED score

    # Test Financial very strict thresholds
    financial = FinancialStrategy(SiteType.FINANCIAL)
    financial_thresholds = financial._get_thresholds()

    # Financial TRUSTED should be 95 (very strict)
    financial_trusted = financial_thresholds[RiskLevel.TRUSTED]
    assert financial_trusted[0] == 95

    # Financial should weight graph and security equally high (0.30 each)
    financial_weights = financial.weights
    assert financial_weights.graph == 0.30
    assert financial_weights.security == 0.30

    # Test Portfolio lenient thresholds
    portfolio = PortfolioStrategy(SiteType.PORTFOLIO)
    portfolio_thresholds = portfolio._get_thresholds()

    # Portfolio should have lower TRUSTED threshold (80)
    portfolio_trusted = portfolio_thresholds[RiskLevel.TRUSTED]
    assert portfolio_trusted[0] == 80  # More lenient

    # Portfolio should weight visual heavier (0.25) since aesthetics matter
    portfolio_weights = portfolio.weights
    assert portfolio_weights.visual == 0.25
    assert portfolio_weights.security == 0.15  # Less critical than e-commerce
```

**Test: Complexity estimation accuracy vs actual execution time**
```python
def test_complexity_estimation_accuracy():
    """Validate estimator predictions align with actual execution times."""
    estimator = ComplexityEstimator()

    # Create test cases with known durations (from historical data)
    test_cases = [
        # (scout_result_metadata, actual_duration_seconds, tolerance_pct)
        (
            {'dom_metadata': {'element_count': 50, 'script_count': 1, 'image_count': 2},
             'lazy_loading': {'final_height': 800}},
            10.0,  # Actual took 10s
            50     # 50% tolerance for estimation
        ),
        (
            {'dom_metadata': {'element_count': 500, 'script_count': 10, 'image_count': 15},
             'lazy_loading': {'final_height': 2500}},
            25.0,  # Actual took 25s
            50
        ),
        (
            {'dom_metadata': {'element_count': 5000, 'script_count': 50, 'image_count': 80},
             'lazy_loading': {'final_height': 8000}},
            60.0,  # Actual took 60s
            50
        ),
    ]

    for metadata, actual_duration, tolerance_pct in test_cases:
        estimate = estimator.estimate(metadata)

        # Check that estimated time is within tolerance of actual
        lower_bound = actual_duration * (1 - tolerance_pct / 100)
        upper_bound = actual_duration * (1 + tolerance_pct / 100)

        assert lower_bound <= estimate.total_estimated_time <= upper_bound, (
            f"Estimate {estimate.total_estimated_time}s outside tolerance for actual {actual_duration}s.\n"
            f"Range [{lower_bound:.1f}s, {upper_bound:.1f}s], confidence: {estimate.confidence}"
        )

    # Verify confidence correlates with metadata availability
    # More metadata = higher confidence
    complex_estimate = estimator.estimate({
        'dom_metadata': {'element_count': 10000, 'script_count': 100, 'image_count': 150},
        'lazy_loading': {'final_height': 10000}
    })
    trivial_estimate = estimator.estimate({
        'dom_metadata': {'element_count': 10, 'script_count': 0, 'image_count': 1},
        'lazy_loading': {'final_height': 500}
    })

    # Complex pages have more data for estimation, so higher confidence
    assert complex_estimate.confidence > trivial_estimate.confidence
```

**Test: IOC Extraction**
```python
def test_ioc_extraction_multiple_types():
    extractor = IOCExtractor()
    text = "Contact support@malicious.com or visit http://phishing-site.com"

    io_s = extractor.extract(text)

    assert 'support@malicious.com' in io_s['emails']
    assert 'http://phishing-site.com' in io_s['urls']
```

---

### Integration Tests

**Test: Judge Agent produces dual-tier verdict**
```python
@pytest.mark.asyncio
async def test_judge_produces_dual_verdict():
    judge = JudgeAgent()

    # Input with Vision, Security, OSINT, Graph findings
    findings = {
        'vision': [EnhancedFinding(category='dark_pattern')],
        'security': [EnhancedFinding(category='sql_injection')],
        'graph': [GraphResult(is_suspicious=True)],
        'osint': {'domain_verified': True, 'ssl_valid': False}
    }

    verdict = await judge.judge(findings)

    assert isinstance(verdict, DualVerdict)
    assert verdict.technical.cwe_ids
    assert verdict.nonTechnical.explanation
```

**Test: Adaptive timeout based on complexity**
```python
@pytest.mark.asyncio
async def test_adaptive_timeout_complex_page():
    orchestrator = AdaptiveOrchestrator()

    # Simulate complex page (large DOM, many scripts)
    page_metadata = {'dom_size': 150000, 'scripts': 45}

    estimated = orchestrator.estimate_complexity(page_metadata)

    # Complex pages should get longer timeouts
    assert estimated.complexity == 'very_complex'
    assert estimated.timeout_vision > 60  # More than base timeout
```

---

### Performance Tests

**Test: CVSS calculator performance - verify scoring completes within time limits**
```python
import pytest
import time
import psutil
import gc

def generate_cvss_metrics():
    """Generate random CVSS metrics for testing."""
    import random
    return CVSSMetrics(
        attack_vector=random.choice(list(CVSSAttackVector)),
        attack_complexity=random.choice(list(CVSSAttackComplexity)),
        privileges_required=random.choice(list(CVSSPrivilegesRequired)),
        user_interaction=random.choice(list(CVSSUserInteraction)),
        scope=random.choice(list(CVSSScope)),
        confidentiality_impact=random.choice(list(CVSSImpact)),
        integrity_impact=random.choice(list(CVSSImpact)),
        availability_impact=random.choice(list(CVSSImpact))
    )

@pytest.mark.parametrize("metric_count", [10, 50, 100, 500, 1000])
def test_cvss_calculator_performance(metric_count):
    """Verify CVSS scoring completes within time limits for batch calculations."""
    calculator = CVSSCalculator()

    metrics = [generate_cvss_metrics() for _ in range(metric_count)]

    start = time.time()
    results = [calculator.calculate_base_score(m) for m in metrics]
    elapsed = time.time() - start

    # Performance criteria based on metric count
    if metric_count == 10:
        assert elapsed < 0.05, f"10 CVSS calculations took {elapsed*1000:.1f}ms, expected < 50ms"
    elif metric_count == 50:
        assert elapsed < 0.1, f"50 CVSS calculations took {elapsed*1000:.1f}ms, expected < 100ms"
    elif metric_count == 100:
        assert elapsed < 0.2, f"100 CVSS calculations took {elapsed*1000:.1f}ms, expected < 200ms"
    elif metric_count == 500:
        assert elapsed < 0.5, f"500 CVSS calculations took {elapsed:.2f}s, expected < 0.5s"
    else:  # 1000
        assert elapsed < 1.0, f"1000 CVSS calculations took {elapsed:.2f}s, expected < 1s"

    # Verify all scores are valid (0-10 range)
    for score in results:
        assert 0.0 <= score <= 10.0, f"Invalid CVSS score: {score}"
```

**Test: Memory management under load - no memory leaks in orchestrator during long audits**
```python
@pytest.mark.asyncio
async def test_orchestrator_memory_management_no_leaks():
    """Validate no memory leaks in orchestrator during long audits."""
    import gc
    import psutil
    import os

    orchestrator = AdaptiveOrchestrator()
    process = psutil.Process(os.getpid())

    # Get initial memory usage
    gc.collect()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Simulate 20 consecutive audits
    for i in range(20):
        url = f'http://test-site-{i}.com'

        # Execute audit (using mock agents to avoid network calls)
        result = await orchestrator.execute_audit_mock(url)

        # Force garbage collection after each audit
        gc.collect()

    # Get final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # Memory increase should be reasonable (< 100MB for 20 audits)
    # This allows for some accumulation but prevents leaks
    assert memory_increase < 100, (
        f"Memory increased by {memory_increase:.1f}MB after 20 audits. "
        f"Possible memory leak detected.\n"
        f"Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB"
    )

    # Additional check: per-audit average should be < 5MB
    avg_per_audit = memory_increase / 20
    assert avg_per_audit < 5, (
        f"Average memory increase per audit: {avg_per_audit:.2f}MB, expected < 5MB"
    )


@pytest.mark.asyncio
async def test_orchestrator_state_cleanup():
    """Verify orchestrator properly cleans up state between audits."""
    orchestrator = AdaptiveOrchestrator()

    # Execute first audit
    result1 = await orchestrator.execute_audit_mock('http://test1.com')

    # Verify state is tracked
    assert len(orchestrator.active_audits) > 0 if hasattr(orchestrator, 'active_audits') else True

    # Execute second audit (should reuse or clean up from first)
    result2 = await orchestrator.execute_audit_mock('http://test2.com')

    # Verify no accumulation of stale state
    if hasattr(orchestrator, 'audit_history'):
        # History should be limited (e.g., last 10 audits)
        assert len(orchestrator.audit_history) <= 10

    # Verify results are independent (no cross-contamination)
    assert result1['url'] != result2['url']
```

**Test: Complexity estimation accuracy - cross-reference estimated vs actual completion times**
```python
@pytest.mark.asyncio
async def test_complexity_estimation_accuracy_vs_actual():
    """Cross-reference estimated vs actual completion times."""
    orchestrator = AdaptiveOrchestrator()
    estimator = orchestrator.complexity_estimator

    # Collect historical data points (mock historical audits)
    # In production, this would query the AuditRepository for past audits
    historical_data = [
        # (metadata, actual_duration_seconds)
        (
            {'dom_metadata': {'element_count': 80, 'script_count': 2, 'image_count': 5}, 'lazy_loading': {'final_height': 1200}},
            12.5
        ),
        (
            {'dom_metadata': {'element_count': 350, 'script_count': 12, 'image_count': 25}, 'lazy_loading': {'final_height': 3200}},
            28.3
        ),
        (
            {'dom_metadata': {'element_count': 2500, 'script_count': 35, 'image_count': 60}, 'lazy_loading': {'final_height': 6500}},
            52.7
        ),
        (
            {'dom_metadata': {'element_count': 8000, 'script_count': 85, 'image_count': 120}, 'lazy_loading': {'final_height': 12000}},
            78.2
        ),
    ]

    accuracy_errors = []
    for metadata, actual_duration in historical_data:
        estimate = estimator.estimate(metadata)
        estimated = estimate.total_estimated_time

        # Calculate percent error
        error_pct = abs(estimated - actual_duration) / actual_duration * 100
        accuracy_errors.append(error_pct)

        # Each individual estimate should be within 50% of actual
        assert error_pct < 50, (
            f"Estimate {estimated:.1f}s has {error_pct:.1f}% error vs actual {actual_duration:.1f}s. "
            f"Expected < 50% error."
        )

    # Calculate overall accuracy metrics
    mean_error = sum(accuracy_errors) / len(accuracy_errors)
    max_error = max(accuracy_errors)

    # Mean error should be reasonable (< 30%)
    assert mean_error < 30, (
        f"Mean estimation error {mean_error:.1f}% too high. Expected < 30%."
    )

    # No single estimate should be wildly off (> 75%)
    assert max_error < 75, (
        f"Maximum estimation error {max_error:.1f}% too high. Expected < 75%."
    )

    # Verify complexity levels are correctly identified
    trivial = estimator.estimate({'dom_metadata': {'element_count': 30, 'script_count': 1}, 'lazy_loading': {'final_height': 600}})
    assert trivial.complexity == PageComplexity.TRIVIAL or trivial.complexity == PageComplexity.SIMPLE

    complex = estimator.estimate({'dom_metadata': {'element_count': 6000, 'script_count': 60}, 'lazy_loading': {'final_height': 9000}})
    assert complex.complexity == PageComplexity.VERY_COMPLEX or complex.complexity == PageComplexity.COMPLEX
```

**Test: Conflict resolver handles 100+ concurrent findings**
```python
def test_conflict_resolver_scalability():
    resolver = ConflictResolver()

    # Simulate 100 conflicting findings from 10 agents
    results = {
        f'agent_{i}': {
            'trust_score': 0.5 + (i * 0.05),
            'findings': [f'finding_{i}_{j}' for j in range(10)]
        }
        for i in range(10)
    }

    start = time.time()
    resolved = resolver.resolve(results)
    elapsed = time.time() - start

    # Should resolve 1000 findings quickly
    assert len(resolved['findings']) > 0
    assert elapsed < 2.0
```

---

## Success Criteria (When Phase 9 Is Done)

### Must Have
1. ✅ DualVerdict contains both technical and non-technical tiers
2. ✅ Technical verdict includes CWE IDs and CVSS scores
3. ✅ IOCs extracted and cross-referenced with OSINT
4. ✅ Site types detected and appropriate strategies applied
5. ✅ Adaptive timeouts set based on page complexity
6. ✅ Estimated completion time emitted countdown

### Should Have
1. ✅ CWE mapping covers all security finding types
2. ✅ CVSS calculator handles full metric range
3. ✅ 11 site-type strategies implemented
4. ✅ Graceful degradation for partial results
5. ✅ Progress updates every 5-10 seconds

### Nice to Have
1. ✅ Mitre ATT&CK framework integration
2. ✅ Real-time pattern notifications
3. ✅ Automatic fallback methods for failed agents
4. ✅ Progressive refinement (show results, improve over time)

---

## Requirements Covered

| Requirement | Status | Notes |
|-------------|--------|-------|
| JUDGE-01 | 📝 Covered | DualVerdict dataclasses |
| JUDGE-02 | 📝 Covered | 11 site-type strategies |
| JUDGE-03 | 📝 Covered | JudgeAgent with dual-tier |
| ORCH-01 | 📝 Covered | Adaptive timeouts + complexity estimation |
| ORCH-02 | 📝 Covered | Error handling + graceful degradation |
| ORCH-03 | 📝 Covered | Complexity-aware orchestration |
| PROG-01 | 📝 Covered | Progressive screenshot streaming |
| PROG-02 | 📝 Covered | Real-time pattern notifications |
| PROG-03 | 📝 Covered | User engagement pacing (countdown) |

---

*Plan created: 2026-02-23*
*Next phase: Phase 10 (Cybersecurity Deep Dive)*
