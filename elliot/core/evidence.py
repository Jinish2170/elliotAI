"""
ELLIOT V3 — Unified Evidence Schema

Single dataclass that ALL agents, modules, and OSINT sources output.
Replaces fragmented dict formats across ScoutResult, VisionResult,
SecurityResult, GraphResult, OSINTResult, etc.

Design principles:
- Judge-centric: everything aggregates as Evidence
- Traceable: unique IDs, timestamps, source attribution
- Actionable: severity, CWE/CVSS, MITRE ATT&CK, remediation
- Typed: no more dict serialization hell
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional


class EvidenceSeverity:
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceCategory:
    OSINT = "osint"              # External intelligence (WHOIS, DNS, VT, etc.)
    SECURITY = "security"        # Passive checks (headers, forms, redirects)
    VISION = "vision"            # VLM screenshot analysis
    DARK_PATTERN = "dark_pattern" # UX manipulation patterns
    ACTIVE_SCAN = "active_scan"   # Non-destructive active probes (Deep tier)
    THREAT_INTEL = "threat_intel" # VirusTotal, URLhaus, SafeBrowsing
    DOMAIN = "domain"            # WHOIS, DNS, SSL certificate
    NETWORK = "network"          # IP reputation, port exposure (Shodan)
    DARKNET = "darknet"          # Marketplace mentions, TOR exposure


class EvidenceType:
    FINDING = "finding"       # Something was discovered
    INDICATOR = "indicator"   # Supporting evidence / flag
    METRIC = "metric"         # Quantitative measurement
    RECOMMENDATION = "recommendation"  # Actionable fix


@dataclass
class Evidence:
    """
    Unified evidence item — all modules output this format.

    Usage:
        evidence = Evidence(
            category="osint",
            severity="warning",
            title="Domain registered 2 days ago",
            detail="Newly registered domains are statistically ...",
            raw_data={"age_days": 2},
        )
    """
    category: str = EvidenceCategory.SECURITY
    e_type: str = EvidenceType.FINDING
    severity: str = EvidenceSeverity.INFO
    title: str = ""
    detail: str = ""
    raw_data: dict = field(default_factory=dict)
    confidence: float = 0.5      # 0.0 - 1.0, how certain we are

    # Standardized threat mapping (populated by security modules)
    cwe_id: str = ""             # CWE-79, CWE-20, etc.
    cvss_score: float = 0.0      # 0.0 - 10.0
    mitre_technique: str = ""    # "T1190", "T1059", etc.

    # Actionable output
    remediation: str = ""        # What to do about it
    actionable: bool = False     # True if requires user action

    # Tracking
    source: str = ""             # Which module produced this
    id: str = ""                 # Auto-generated UUID
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.id:
            self.id = f"ev-{uuid.uuid4().hex[:8]}"

    @property
    def is_actionable(self) -> bool:
        return self.actionable and self.severity in (
            EvidenceSeverity.HIGH, EvidenceSeverity.CRITICAL
        )

    def to_dict(self) -> dict:
        """Serialize to dict for JSON / downstream agents."""
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "e_type": self.e_type,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "raw_data": self.raw_data,
            "confidence": self.confidence,
            "cwe_id": self.cwe_id,
            "cvss_score": self.cvss_score,
            "mitre_technique": self.mitre_technique,
            "remediation": self.remediation,
            "actionable": self.actionable,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Evidence":
        """Reconstruct from dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================
# Convenience factories for common evidence types
# ============================================================

def osint_finding(
    source: str,
    title: str,
    detail: str,
    severity: str = EvidenceSeverity.INFO,
    raw_data: Optional[dict] = None,
    confidence: float = 0.8,
    remediation: str = "",
) -> Evidence:
    """OSINT-sourced evidence (WHOIS, DNS, SSL, threat intel)."""
    return Evidence(
        category=EvidenceCategory.OSINT,
        e_type=EvidenceType.FINDING,
        severity=severity,
        title=title,
        detail=detail,
        raw_data=raw_data or {},
        confidence=confidence,
        remediation=remediation,
        source=source,
        actionable=severity in (EvidenceSeverity.WARNING, EvidenceSeverity.HIGH, EvidenceSeverity.CRITICAL),
    )


def security_finding(
    source: str,
    title: str,
    detail: str,
    severity: str = EvidenceSeverity.WARNING,
    cwe_id: str = "",
    cvss_score: float = 0.0,
    mitre_technique: str = "",
    remediation: str = "",
    confidence: float = 0.7,
) -> Evidence:
    """Security module finding (headers, OWASP, phishing, etc.)."""
    return Evidence(
        category=EvidenceCategory.SECURITY,
        e_type=EvidenceType.FINDING,
        severity=severity,
        title=title,
        detail=detail,
        confidence=confidence,
        cwe_id=cwe_id,
        cvss_score=cvss_score,
        mitre_technique=mitre_technique,
        remediation=remediation,
        source=source,
        actionable=True,
    )


def dark_pattern_finding(
    source: str,
    title: str,
    detail: str,
    severity: str = EvidenceSeverity.WARNING,
    raw_data: Optional[dict] = None,
    confidence: float = 0.6,
) -> Evidence:
    """Dark pattern detected via VLM or heuristic analysis."""
    return Evidence(
        category=EvidenceCategory.DARK_PATTERN,
        e_type=EvidenceType.FINDING,
        severity=severity,
        title=title,
        detail=detail,
        raw_data=raw_data or {},
        confidence=confidence,
        source=source,
        actionable=True,
    )
