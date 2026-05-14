"""
Quality Foundation Module

Provides consensus-based multi-source verification for findings across Vision, OSINT, and Security agents.
"""

from elliot.core.types import (
    ConsensusResult,
    FindingSource,
    FindingStatus,
)
from elliot.quality.confidence_scorer import ConfidenceScorer
from elliot.quality.consensus_engine import ConsensusEngine
from elliot.quality.validation_state import ValidationStateMachine

__all__ = [
    "ConsensusEngine",
    "ConfidenceScorer",
    "ValidationStateMachine",
    "ConsensusResult",
    "FindingSource",
    "FindingStatus",
]
