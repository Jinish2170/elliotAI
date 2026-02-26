"""
Quality Foundation Module

Provides consensus-based multi-source verification for findings across Vision, OSINT, and Security agents.
"""

from veritas.core.types import (
    ConsensusResult,
    FindingSource,
    FindingStatus,
)
from veritas.quality.consensus_engine import ConsensusEngine

__all__ = [
    "ConsensusEngine",
    "ConsensusResult",
    "FindingSource",
    "FindingStatus",
]
