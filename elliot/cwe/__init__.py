"""
CWE (Common Weakness Enumeration) and CVSS (Common Vulnerability Scoring System) integration module.

This module provides:
- CWE registry for vulnerability categorization
- CVSS calculator for severity scoring
- Mapping functions for threat findings to CWE identifiers

Usage:
    from elliot.cwe import CWEEntry, find_cwe_by_category, map_finding_to_cwe
    from elliot.cwe.cvss_calculator import CVSSMetrics, calculate_score
"""

from elliot.cwe.registry import (
    CWECategory,
    CWEEntry,
    CWE_REGISTRY,
    find_cwe_by_category,
    map_finding_to_cwe,
)

from elliot.cwe.cvss_calculator import (
    CWMetricStatus,
    CVSSMetrics,
    cvss_calculate_score,
)

__all__ = [
    # Registry
    "CWECategory",
    "CWEEntry",
    "CWE_REGISTRY",
    "find_cwe_by_category",
    "map_finding_to_cwe",
    # CVSS
    "CWMetricStatus",
    "CVSSMetrics",
    "cvss_calculate_score",
]
