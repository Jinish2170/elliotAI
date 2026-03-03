"""
Dual-tier verdict data classes for Judge Agent.

This module provides:
- IOC (Indicators of Compromise) dataclass
- VerdictTechnical: CWE/CVSS/IOCs for security professionals
- VerdictNonTechnical: Plain English for end users
- DualVerdict: Combines both tiers with shared trust score
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SeverityLevel(str, Enum):
    """Severity levels for findings and IOCs."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskLevel(str, Enum):
    """Risk levels derived from trust score."""

    TRUSTED = "trusted"
    PROBABLY_SAFE = "probably_safe"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    DANGEROUS = "dangerous"


@dataclass(frozen=True)
class IOC:
    """
    Indicator of Compromise (IOC).

    Attributes:
        type: IOC type (domain, ip, email, url, hash, etc.)
        value: IOC value
        source: Source that detected this IOC
        severity: Severity level
        timestamp: Detection timestamp (UTC ISO 8601)
    """

    type: str
    value: str
    source: str
    severity: SeverityLevel
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class VerdictTechnical:
    """
    Technical verdict containing CWE/CVSS/IOCs for security professionals.

    Attributes:
        cwe_entries: List of CWE entries matched to findings
        cvss_metrics: CVSS metrics used for scoring
        cvss_score: Calculated CVSS base score (0.0-10.0)
        iocs: List of indicators of compromise
        threat_indicators: Raw threat indicators from OSINT/CTI
        version: Technical tier version (for V1/V2 transitions)
    """

    cwe_entries: list[dict[str, Any]] = field(default_factory=list)
    cvss_metrics: dict[str, Any] | None = None
    cvss_score: float = 0.0
    iocs: list[IOC] = field(default_factory=list)
    threat_indicators: list[dict[str, Any]] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cwe_entries": self.cwe_entries,
            "cvss_metrics": self.cvss_metrics,
            "cvss_score": self.cvss_score,
            "iocs": [{"type": ioc.type, "value": ioc.value, "source": ioc.source,
                     "severity": ioc.severity.value, "timestamp": ioc.timestamp}
                    for ioc in self.iocs],
            "threat_indicators": self.threat_indicators,
            "version": self.version,
        }


@dataclass(frozen=True)
class VerdictNonTechnical:
    """
    Non-technical verdict containing plain English explanations for end users.

    Attributes:
        risk_level: Derived risk level from trust score
        summary: One-sentence summary of the assessment
        key_findings: List of critical and high findings (plain English)
        recommendations: Actionable recommendations
        warnings: Critical warnings for user attention
        green_flags: Positive safety indicators
        simple_explanation: Human-friendly "What this means" section
        version: Technical tier version (for V1/V2 transitions)
    """

    risk_level: RiskLevel = RiskLevel.SUSPICIOUS
    summary: str = "Cannot determine safety - insufficient evidence"
    key_findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    green_flags: list[str] = field(default_factory=list)
    simple_explanation: str = "Unable to provide explanation."
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "risk_level": self.risk_level.value,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "green_flags": self.green_flags,
            "simple_explanation": self.simple_explanation,
            "version": self.version,
        }


@dataclass(frozen=True)
class DualVerdict:
    """
    Dual-tier verdict combining technical and non-technical explanations.

    Attributes:
        trust_score: Shared trust score (0-100)
        risk_level: Derived risk level from trust score
        technical: Technical tier (CWE, CVSS, IOCs)
        non_technical: Non-technical tier (plain English)
        site_type: Detected site type for context
        auditor_version: Veritas version that generated this verdict
        timestamp: Verdict timestamp (UTC ISO 8601)
    """

    trust_score: int
    technical: VerdictTechnical
    non_technical: VerdictNonTechnical
    risk_level: RiskLevel = field(init=False)
    site_type: str | None = None
    auditor_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Derive risk_level from trust_score after initialization."""
        # Set risk_level based on trust_score thresholds
        # Use object.__setattr__ for frozen dataclass
        if self.trust_score >= 90:
            object.__setattr__(self, "risk_level", RiskLevel.TRUSTED)
        elif self.trust_score >= 70:
            object.__setattr__(self, "risk_level", RiskLevel.PROBABLY_SAFE)
        elif self.trust_score >= 40:
            object.__setattr__(self, "risk_level", RiskLevel.SUSPICIOUS)
        elif self.trust_score >= 20:
            object.__setattr__(self, "risk_level", RiskLevel.HIGH_RISK)
        else:
            object.__setattr__(self, "risk_level", RiskLevel.DANGEROUS)

    @property
    def is_safe(self) -> bool:
        """Whether the site is safe (trust_score >= 70)."""
        return self.trust_score >= 70

    @property
    def hasCriticalThreats(self) -> bool:
        """Whether critical threats exist (CVSS >= 9.0 or critical CWE IDs)."""
        if self.technical.cvss_score >= 9.0:
            return True

        # Check for critical CWE IDs (787, 125, 287, etc.)
        critical_cwe_ids = {"CWE-787", "CWE-125", "CWE-287", "CWE-89", "CWE-20"}
        for cwe in self.technical.cwe_entries:
            cwe_id = cwe.get("cwe_id", "")
            if any(crit in cwe_id for crit in critical_cwe_ids):
                return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "trust_score": self.trust_score,
            "risk_level": self.risk_level.value,
            "technical": self.technical.to_dict(),
            "non_technical": self.non_technical.to_dict(),
            "site_type": self.site_type,
            "auditor_version": self.auditor_version,
            "timestamp": self.timestamp,
        }
