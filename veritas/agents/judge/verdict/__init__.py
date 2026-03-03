"""
Dual-tier verdict system for Judge Agent.

Provides technical (CWE/CVSS/IOCs) and non-technical (plain English) verdict tiers.

Usage:
    from veritas.agents.judge.verdict import (
        DualVerdict,
        VerdictTechnical,
        VerdictNonTechnical,
        SeverityLevel,
        RiskLevel,
        IOC,
    )
"""

from veritas.agents.judge.verdict.base import (
    DualVerdict,
    IOC,
    RiskLevel,
    SeverityLevel,
    VerdictNonTechnical,
    VerdictTechnical,
)

__all__ = [
    "IOC",
    "SeverityLevel",
    "RiskLevel",
    "VerdictTechnical",
    "VerdictNonTechnical",
    "DualVerdict",
]
