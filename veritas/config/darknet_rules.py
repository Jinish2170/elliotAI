"""
Darknet Security Rules and CVSS Scoring Presets

CVSS 3.1 scoring presets for darknet threat patterns based on
common vulnerability assessment practices for hidden services.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CVSSMetric:
    """CVSS 3.1 metric data."""
    base_score: float
    impact_subscore: float
    exploitability_subscore: float
    severity: str  # NONE, LOW, MEDIUM, HIGH, CRITICAL

    def to_dict(self):
        return {
            "base_score": self.base_score,
            "impact": self.impact_subscore,
            "exploitability": self.exploitability_subscore,
            "severity": self.severity,
        }


# Darknet threat CVSS scoring presets
# Based on OWASP Threat Modeling and NIST CVSS 3.1 guidelines

DARKNET_CVSS_PRESETS = {
    "exit_scam": CVSSMetric(
        base_score=8.5,
        impact_subscore=5.9,
        exploitability_subscore=3.5,
        severity="HIGH",
    ),
    "marketplace_ref": CVSSMetric(
        base_score=6.5,
        impact_subscore=3.6,
        exploitability_subscore=2.8,
        severity="MEDIUM",
    ),
    "tor2web_exposure": CVSSMetric(
        base_score=7.5,
        impact_subscore=4.7,
        exploitability_subscore=3.1,
        severity="HIGH",
    ),
    "onion_reference": CVSSMetric(
        base_score=4.3,
        impact_subscore=1.4,
        exploitability_subscore=2.8,
        severity="MEDIUM",
    ),
    "vendor_compromise": CVSSMetric(
        base_score=9.0,
        impact_subscore=5.9,
        exploitability_subscore=3.4,
        severity="HIGH",
    ),
}


def get_darknet_cvss_score(analysis_result) -> float:
    """
    Calculate CVSS score based on darknet analysis result.

    Args:
        analysis_result: DarknetAnalysisResult from darknet analyzer

    Returns:
        CVSS base score (0.0 - 10.0)
    """
    from analysis.security.darknet import DarknetAnalysisResult

    score = 0.0

    if not isinstance(analysis_result, DarknetAnalysisResult):
        return 0.0

    # Tor2Web exposure is significant (anonymity breach)
    if analysis_result.tor2web_exposure:
        score += DARKNET_CVSS_PRESETS["tor2web_exposure"].base_score * 0.4

    # Marketplace threats (exit scams are severe)
    for threat in analysis_result.marketplace_threats:
        status = threat.get("status", "")
        confidence = threat.get("confidence", 0.5)

        if status == "exit_scam":
            score += (
                DARKNET_CVSS_PRESETS["exit_scam"].base_score * confidence * 0.3
            )
        elif status == "shutdown":
            score += (
                DARKNET_CVSS_PRESETS["marketplace_ref"].base_score * confidence * 0.2
            )

    # .onion references (general concern)
    if analysis_result.has_onion_references:
        score += DARKNET_CVSS_PRESETS["onion_reference"].base_score * 0.1

    return min(score, 10.0)


def get_cvss_metric(threat_type: str) -> Optional[CVSSMetric]:
    """
    Get CVSS metric for a specific darknet threat type.

    Args:
        threat_type: Type of darknet threat (exit_scam, tor2web_exposure, etc.)

    Returns:
        CVSSMetric or None if threat type unknown
    """
    return DARKNET_CVSS_PRESETS.get(threat_type)


# Darknet vulnerability patterns for SecurityFinding generation

DARKNET_PATTERNS = {
    "exit_scam": {
        "cve_id": None,  # Marketplace exit scams not CVE-assigned
        "cwe_id": "CWE-200",  # Exposure of Sensitive Information
        "title": "Darknet Marketplace Exit Scam Reference",
        "description": (
            "This site references a darknet marketplace that executed an exit scam. "
            "Marketplace shutdown after stealing vendor escrow and funds. References "
            "to such markets may indicate fraudulent association or security testing "
            "without authorization."
        ),
    },
    "tor2web": {
        "cve_id": None,
        "cwe_id": "CWE-359",  # Exposure of Private Personal Information
        "title": "Tor2Web Gateway Exposure Detected",
        "description": (
            "Site uses Tor2Web gateway URLs which compromise TOR anonymity by "
            "resolving DNS on the gateway server. This exposes user browsing activity "
            "to the gateway operator and defeats the privacy protections of TOR."
        ),
    },
    "marketplace": {
        "cve_id": None,
        "cwe_id": "CWE-200",
        "title": "Darknet Marketplace Reference",
        "description": (
            "This site references known darknet marketplaces. While not inherently "
            "malicious, such references should be scrutinized for context - legitimate "
            "security research vs. attempts to associate with illicit markets."
        ),
    },
}


def get_pattern_info(threat_type: str) -> Optional[dict]:
    """
    Get pattern information for a darknet threat type.

    Args:
        threat_type: Type of darknet threat

    Returns:
        Pattern dict with cwe_id, title, description or None
    """
    return DARKNET_PATTERNS.get(threat_type)
