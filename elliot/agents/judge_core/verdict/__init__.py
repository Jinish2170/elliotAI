"""
Dual-tier verdict system for Judge Agent.

Provides technical (CWE/CVSS/IOCs) and non-technical (plain English) verdict tiers.

Usage:
    from elliot.agents.judge_core.verdict import (
        DualVerdict,
        VerdictTechnical,
        VerdictNonTechnical,
        SeverityLevel,
        RiskLevel,
        IOC,
    )
"""

from elliot.agents.judge_core.verdict.base import (
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
