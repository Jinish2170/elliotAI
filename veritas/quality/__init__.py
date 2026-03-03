"""
Quality Foundation Module

Provides consensus-based multi-source verification for findings across Vision, OSINT, and Security agents.
"""

from veritas.core.types import (
    ConsensusResult,
    FindingSource,
    FindingStatus,
)
from veritas.quality.confidence_scorer import ConfidenceScorer
from veritas.quality.consensus_engine import ConsensusEngine
from veritas.quality.validation_state import ValidationStateMachine

__all__ = [
    "ConsensusEngine",
    "ConfidenceScorer",
    "ValidationStateMachine",
    "ConsensusResult",
    "FindingSource",
    "FindingStatus",
]
