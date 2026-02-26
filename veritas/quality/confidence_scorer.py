"""
Confidence Scorer for Quality Foundation

Provides human-readable confidence formatting and tier classification
for consensus-based finding verification.
"""

import logging
from typing import Optional

from veritas.core.types import ConsensusResult

logger = logging.getLogger("veritas.quality.confidence_scorer")


class ConfidenceScorer:
    """
    Formats and classifies confidence scores for findings.

    Provides human-readable explanations (e.g., "87%: 3 sources agree, high severity")
    and tier classification (high_confidence, medium_confidence, etc.)
    """

    # Score ranges for tier classification
    SCORE_RANGES = {
        "high_confidence": (75.0, 100.0),      # 2+ sources, high severity
        "medium_confidence": (50.0, 75.0),     # 2+ sources, medium severity
        "unconfirmed_high": (40.0, 60.0),      # 1 source, high severity
        "unconfirmed_medium": (20.0, 40.0),    # 1 source, medium severity
        "low_confidence": (0.0, 20.0),         # Insufficient data
    }

    @classmethod
    def format_confidence(cls, result: ConsensusResult) -> str:
        """
        Format confidence score with human-readable explanation.

        Example outputs:
        - "87%: 3 sources agree, high severity"
        - "42%: 1 source, medium severity"
        - "0%: insufficient data"

        Args:
            result: ConsensusResult with sources and aggregated_confidence

        Returns:
            Formatted string like "XX%: description"
        """
        if result.status.value == "PENDING":
            return "0%: insufficient data"

        score = result.aggregated_confidence
        source_count = len({s.agent_type for s in result.sources})

        # Find max severity
        severity = "unknown"
        if result.sources:
            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
            existing_severities = [s.severity for s in result.sources]
            # Get highest severity (first match in order)
            for sev in severity_order:
                if sev in existing_severities:
                    severity = sev.lower()
                    break

        # Build description
        if source_count == 1:
            description = f"1 source, {severity} severity"
        else:
            source_word = "sources" if source_count > 1 else "source"
            description = f"{source_count} {source_word} agree, {severity} severity"

        return f"{int(score)}%: {description}"

    @classmethod
    def get_confidence_tier(cls, score: float) -> str:
        """
        Classify a confidence score into a tier.

        Tier boundaries:
        - high_confidence: >= 75
        - medium_confidence: >= 50
        - unconfirmed_high: >= 40
        - unconfirmed_medium: >= 20
        - low_confidence: < 20

        Args:
            score: Confidence score (0-100)

        Returns:
            Tier key from SCORE_RANGES
        """
        # Check tiers in order from highest to lowest
        if score >= 75.0:
            return "high_confidence"
        elif score >= 50.0:
            return "medium_confidence"
        elif score >= 40.0:
            return "unconfirmed_high"
        elif score >= 20.0:
            return "unconfirmed_medium"
        else:
            return "low_confidence"
