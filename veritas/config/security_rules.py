"""
Security Rules Configuration - CWE Mapping and Severity Rules.

Configuration for security findings, integrating Phase 9 CWE
registry and CVSS calculator for professional vulnerability reporting.

Main Exports:
    - cwemapper: Use map_finding_to_cwe() from veritas.cwe.registry
    - calculate_cvss_for_severity(): Helper function for CVSS scoring
    - CWE_SEVERITY_MAPPING: Default severity mappings by category
    - DEFAULT_CVSS_METRICS: CVSS metrics presets by severity level
"""

from veritas.cwe.cvss_calculator import (
    CVSSMetrics,
    CWMetricStatus,
    PRESET_METRICS,
    cvss_calculate_score,
)
from veritas.cwe.registry import CWE_REGISTRY, map_finding_to_cwe


# ============================================================
# Phase 9 Integration
# ============================================================

# Direct import of CWE registry and CVSS functions
# cwemapper: Use CWE_REGISTRY directly or map_finding_to_cwe() function
# cvss_calculator: Use cvss_calculate_score() function


# ============================================================
# CWE Severity Mapping
# ============================================================

"""
Default severity mappings for security findings by category and pattern type.

Structure:
    {
        "category_id": {
            "pattern_type": "severity_level"
        }
    }

Severity levels: low, medium, high, critical

Note: These are fallback defaults - modules can provide custom severity
based on their analysis logic.
"""

CWE_SEVERITY_MAPPING = {
    # Security Headers
    "security_headers": {
        "missing_hsts": "high",
        "hsts_missing_max_age": "medium",
        "missing_csp": "high",
        "weak_csp": "medium",
        "missing_x_frame_options": "medium",
        "missing_x_content_type_options": "medium",
        "missing_x_xss_protection": "low",
        "missing_referrer_policy": "low",
    },
    # Cookies
    "cookies": {
        "missing_secure": "high",
        "missing_httponly": "medium",
        "missing_samesite": "low",
        "samesite_none_without_secure": "medium",
        "insecure_cookie_flag": "high",
    },
    # Content Security Policy
    "csp": {
        "missing_csp": "high",
        "unsafe_inline": "high",
        "unsafe_eval": "high",
        "overly_permissive": "medium",
        "weak_directives": "medium",
    },
    # TLS/SSL
    "tls_ssl": {
        "missing_https": "critical",
        "weak_cipher": "high",
        "expired_certificate": "critical",
        "self_signed_certificate": "medium",
        "invalid_certificate": "high",
    },
    # OWASP Top 10
    "owasp_a01": {  # Broken Access Control
        "admin_panel_no_auth": "critical",
        "idor": "high",
        "privilege_escalation": "high",
    },
    "owasp_a02": {  # Cryptographic Failures
        "cleartext_transmission": "critical",
        "weak_encryption": "high",
    },
    "owasp_a03": {  # Injection
        "sql_injection": "critical",
        "xss": "high",
        "command_injection": "critical",
    },
    "owasp_a04": {  # Insecure Design
        "broken_authentication": "high",
    },
    "owasp_a05": {  # Security Misconfiguration
        "default_config": "medium",
        "debug_enabled": "low",
    },
}


# ============================================================
# CVSS Metrics Presets
# ============================================================

"""
Default CVSS v4.0 metrics by severity level.

Used by security modules to calculate CVSS scores when specific
metrics aren't available from analysis.

Based on CVSS v4.0 specification.
"""

DEFAULT_CVSS_METRICS = {
    "critical": CVSSMetrics(
        attack_vector=CWMetricStatus.N,  # Network
        attack_complexity=CWMetricStatus.L,  # Low
        privileges_required=CWMetricStatus.N,  # None
        user_interaction=CWMetricStatus.N,  # None
        scope=CWMetricStatus.U,  # Unchanged
        confidentiality=CWMetricStatus.H,  # High impact
        integrity=CWMetricStatus.H,
        availability=CWMetricStatus.H,
    ),
    "high": CVSSMetrics(
        attack_vector=CWMetricStatus.N,
        attack_complexity=CWMetricStatus.L,
        privileges_required=CWMetricStatus.L,  # Low
        user_interaction=CWMetricStatus.N,
        scope=CWMetricStatus.U,
        confidentiality=CWMetricStatus.H,
        integrity=CWMetricStatus.H,
        availability=CWMetricStatus.M,  # Medium impact
    ),
    "medium": CVSSMetrics(
        attack_vector=CWMetricStatus.A,  # Adjacent
        attack_complexity=CWMetricStatus.L,
        privileges_required=CWMetricStatus.L,
        user_interaction=CWMetricStatus.R,  # Required
        scope=CWMetricStatus.U,
        confidentiality=CWMetricStatus.M,
        integrity=CWMetricStatus.M,
        availability=CWMetricStatus.L,  # Low impact
    ),
    "low": CVSSMetrics(
        attack_vector=CWMetricStatus.L,  # Local
        attack_complexity=CWMetricStatus.H,  # High
        privileges_required=CWMetricStatus.H,  # High
        user_interaction=CWMetricStatus.R,
        scope=CWMetricStatus.U,
        confidentiality=CWMetricStatus.L,
        integrity=CWMetricStatus.L,
        availability=CWMetricStatus.L,
    ),
}


# ============================================================
# Helper Functions
# ============================================================

def get_severity_for_finding(
    category_id: str,
    pattern_type: str,
    fallback: str = "medium",
) -> str:
    """
    Get default severity for a finding by category and pattern type.

    Args:
        category_id: Module category (e.g., "security_headers", "cookies")
        pattern_type: Specific pattern (e.g., "missing_hsts", "missing_secure")
        fallback: Default severity if no mapping found (default "medium")

    Returns:
        Severity level string (low, medium, high, critical)
    """
    if category_id in CWE_SEVERITY_MAPPING:
        category_mapping = CWE_SEVERITY_MAPPING[category_id]
        if pattern_type in category_mapping:
            return category_mapping[pattern_type]
    return fallback


def get_cwe_for_finding(
    category_id: str,
    pattern_type: str,
) -> str | None:
    """
    Get CWE ID for a finding using the CWE mapper.

    Args:
        category_id: Module category
        pattern_type: Specific pattern

    Returns:
        CWE ID string (e.g., "CWE-523") or None if no match
    """
    cwe_entry = map_finding_to_cwe(f"{category_id}_{pattern_type}", "high")
    if cwe_entry:
        return cwe_entry.cwe_id
    return None


def calculate_cvss_for_severity(severity: str) -> float:
    """
    Calculate CVSS score for a given severity level.

    Uses the PRESET_METRICS from cvss_calculator or DEFAULT_CVSS_METRICS.

    Args:
        severity: Severity level (critical, high, medium, low)

    Returns:
        CVSS base score (0.0-10.0) or 0.0 if invalid severity
    """
    # Use PRESET_METRICS from cvss_calculator if available
    preset_names = {
        "critical": "critical_web",
        "high": "high_risk",
        "medium": "medium_risk",
        "low": "low_risk",
    }

    # Try to get preset from cvss_calculator
    preset_name = preset_names.get(severity.lower())
    if preset_name and preset_name in PRESET_METRICS:
        # Calculate CVSS score from preset metrics
        metrics = PRESET_METRICS[preset_name]
        return cvss_calculate_score(metrics)

    # Fallback: use severity-based approximation
    severity_scores = {
        "critical": 9.0,
        "high": 7.0,
        "medium": 5.0,
        "low": 2.0,
    }
    return severity_scores.get(severity.lower(), 0.0)


def map_cwe_from_category(category: str) -> str | None:
    """
    Map a security category to a CWE ID.

    Args:
        category: Security category (e.g., "injection", "xss", "crypto")

    Returns:
        CWE ID string or None if no match
    """
    cwe_entry = map_finding_to_cwe(category, "high")
    return cwe_entry.cwe_id if cwe_entry else None


def get_recommended_cvss_metrics(severity: str) -> CVSSMetrics:
    """
    Get recommended CVSS metrics for a given severity.

    Args:
        severity: Severity level (critical, high, medium, low)

    Returns:
        CVSSMetrics object with recommended values
    """
    return DEFAULT_CVSS_METRICS.get(severity.lower(), DEFAULT_CVSS_METRICS["medium"])


# ============================================================
# Rule Validation
# ============================================================

def validate_severity_level(severity: str) -> bool:
    """
    Validate a severity level string.

    Args:
        severity: Severity level to validate

    Returns:
        True if valid severity level
    """
    valid_levels = {"low", "medium", "high", "critical"}
    return severity.lower() in valid_levels


def normalize_severity(severity: str) -> str:
    """
    Normalize severity level string to lowercase.

    Args:
        severity: Severity level string

    Returns:
        Normalized severity string
    """
    return severity.lower() if severity else "medium"
