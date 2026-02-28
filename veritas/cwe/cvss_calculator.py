"""
CVSS (Common Vulnerability Scoring System) v4.0 simplified calculator.

Provides severity scoring for technical vulnerability assessment.
Based on CVSS v4.0 specification: https://www.first.org/cvss/specification-document

Note: This is a simplified implementation suitable for web threat analysis.
For official CVSS calculations, use the CVSS Calculator from FIRST.org.
"""

from dataclasses import dataclass
from enum import Enum


class CWMetricStatus(str, Enum):
    """
    CVSS v4.0 metric status values.

    Values:
        X: Not Defined
        N: Network / None (context-dependent)
        A: Adjacent
        L: Local / Low (context-dependent)
        P: Physical
        H: High
        M: Medium
        R: Required
        C: Changed
        U: Unchanged
    """

    X = "X"
    N = "N"
    A = "A"
    L = "L"
    P = "P"
    H = "H"
    M = "M"
    R = "R"
    C = "C"
    U = "U"


@dataclass(frozen=True)
class CVSSMetrics:
    """
    CVSS v4.0 metrics for vulnerability scoring.

    Attributes:
        attack_vector: Network, Adjacent, Local, Physical (A/N/L/P)
        attack_complexity: High, Low (H/L)
        privileges_required: High, Low, None (H/L/N)
        user_interaction: None, Required (N/R)
        scope: Changed, Unchanged (C/U)
        confidentiality: High, Low, None (H/L/N)
        integrity: High, Low, None (H/L/N)
        availability: High, Low, None (H/L/N)
    """

    attack_vector: CWMetricStatus
    attack_complexity: CWMetricStatus
    privileges_required: CWMetricStatus
    user_interaction: CWMetricStatus
    scope: CWMetricStatus
    confidentiality: CWMetricStatus
    integrity: CWMetricStatus
    availability: CWMetricStatus


# Simplified CVSS v4.0 base score lookup matrix
# Based on attack vector, complexity, and privileges
# Values represent base severity scores (0.0-10.0)
_BASE_SCORE_MATRIX = {
    # Network attacks (worst)
    ("N", "L", "L"): 9.8,
    ("N", "L", "M"): 8.8,
    ("N", "L", "N"): 10.0,
    ("N", "H", "L"): 9.0,
    ("N", "H", "M"): 8.1,
    ("N", "H", "N"): 9.1,
    # Adjacent network attacks
    ("A", "L", "L"): 8.8,
    ("A", "L", "M"): 7.8,
    ("A", "L", "N"): 9.3,
    ("A", "H", "L"): 6.7,
    ("A", "H", "M"): 6.2,
    ("A", "H", "N"): 8.8,
    # Local attacks
    ("L", "L", "L"): 7.8,
    ("L", "L", "M"): 6.8,
    ("L", "L", "N"): 8.6,
    ("L", "H", "L"): 5.3,
    ("L", "H", "M"): 5.5,
    ("L", "H", "N"): 8.1,
    # Physical attacks
    ("P", "L", "L"): 5.5,
    ("P", "L", "M"): 4.6,
    ("P", "L", "N"): 7.5,
    ("P", "H", "L"): 3.8,
    ("P", "H", "M"): 3.6,
    ("P", "H", "N"): 5.6,
}


# Impact scoring multipliers based on CIA triad
_IMPACT_MULTIPLIERS = {
    ("H", "H", "H"): 1.0,  # High impact on all
    ("H", "H", "M"): 0.9,
    ("H", "H", "N"): 0.8,
    ("H", "M", "M"): 0.85,
    ("H", "M", "N"): 0.75,
    ("H", "N", "N"): 0.65,
    ("M", "M", "M"): 0.7,
    ("M", "M", "N"): 0.6,
    ("M", "N", "N"): 0.5,
    ("N", "N", "N"): 0.3,
}


def cvss_calculate_score(metrics: CVSSMetrics) -> float:
    """
    Calculate CVSS v4.0 base score from metrics (simplified).

    Args:
        metrics: CVSSMetrics with all 8 metric fields

    Returns:
        CVSS base score as float between 0.0 and 10.0

    Note:
        This is a simplified calculation. For production use, use the official
        CVSS v4.0 calculator from FIRST.org.
    """
    # Get key metric values
    av_key = _get_metric_char(metrics.attack_vector)
    ac_key = _get_metric_char(metrics.attack_complexity)
    pr_key = _get_metric_char(metrics.privileges_required)

    # Look up base score from matrix (default to medium severity)
    matrix_key = (av_key, ac_key, pr_key)
    base_score = _BASE_SCORE_MATRIX.get(matrix_key, 6.5)

    # Apply impact modifiers based on CIA triad
    cia_key = (
        _get_metric_char(metrics.confidentiality),
        _get_metric_char(metrics.integrity),
        _get_metric_char(metrics.availability),
    )
    impact_multiplier = _IMPACT_MULTIPLIERS.get(cia_key, 0.65)

    # Apply scope change modifier
    scope_modifier = 1.1 if metrics.scope in (CWMetricStatus.C, "C") else 1.0

    # Calculate final score
    final_score = base_score * impact_multiplier * scope_modifier

    # Clamp to CVSS range 0.0-10.0
    return max(0.0, min(10.0, round(final_score, 1)))


def _get_metric_char(status: CWMetricStatus | str) -> str:
    """Extract the character from a CWMetricStatus enum or string."""
    if isinstance(status, CWMetricStatus):
        return status.value
    return str(status).upper()


# Convenience presets for common web vulnerability scenarios
PRESET_METRICS = {
    "critical_web": CVSSMetrics(
        attack_vector=CWMetricStatus.N,
        attack_complexity=CWMetricStatus.L,
        privileges_required=CWMetricStatus.N,
        user_interaction=CWMetricStatus.N,
        scope=CWMetricStatus.X,
        confidentiality=CWMetricStatus.H,
        integrity=CWMetricStatus.H,
        availability=CWMetricStatus.H,
    ),
    "high_risk": CVSSMetrics(
        attack_vector=CWMetricStatus.N,
        attack_complexity=CWMetricStatus.L,
        privileges_required=CWMetricStatus.L,
        user_interaction=CWMetricStatus.N,
        scope=CWMetricStatus.X,
        confidentiality=CWMetricStatus.H,
        integrity=CWMetricStatus.H,
        availability=CWMetricStatus.M,
    ),
    "medium_risk": CVSSMetrics(
        attack_vector=CWMetricStatus.N,
        attack_complexity=CWMetricStatus.L,
        privileges_required=CWMetricStatus.M,
        user_interaction=CWMetricStatus.R,
        scope=CWMetricStatus.X,
        confidentiality=CWMetricStatus.M,
        integrity=CWMetricStatus.M,
        availability=CWMetricStatus.N,
    ),
    "low_risk": CVSSMetrics(
        attack_vector=CWMetricStatus.L,
        attack_complexity=CWMetricStatus.H,
        privileges_required=CWMetricStatus.H,
        user_interaction=CWMetricStatus.R,
        scope=CWMetricStatus.X,
        confidentiality=CWMetricStatus.L,
        integrity=CWMetricStatus.L,
        availability=CWMetricStatus.N,
    ),
}
