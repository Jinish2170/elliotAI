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

    def calculate_osint_confidence(
        self,
        consensus_result: dict,
        reputation_manager=None,
    ) -> tuple[float, str]:
        """
        Calculate OSINT-specific confidence score from consensus result.

        Confidence breakdown:
            - Base score: 50
            - Source agreement factor (60%): (agreement_ratio - 0.5) * 60
            - Status boost: confirmed=+20, likely=+10, possible=0, insufficient=-20, conflicted=0
            - Conflict penalty: -10 if has_conflict

        Args:
            consensus_result: Dict from compute_osint_consensus()
            reputation_manager: Optional ReputationManager for source weights (future)

        Returns:
            Tuple of (score, explanation) where score is 0-100 and explanation is formatted
        """
        # Extract values from consensus result
        status = consensus_result.get("consensus_status", "insufficient")
        agreement_count = consensus_result.get("agreement_count", 0)
        total_sources = consensus_result.get("total_sources", 0)
        has_conflict = consensus_result.get("has_conflict", False)

        # Start with base score
        score = 50.0

        # Source agreement factor (60% weight)
        if total_sources > 0:
            agreement_ratio = agreement_count / total_sources
            agreement_factor = (agreement_ratio - 0.5) * 60.0
            score += agreement_factor

        # Status boost
        status_boosts = {
            "confirmed": 20.0,
            "likely": 10.0,
            "possible": 0.0,
            "insufficient": -20.0,
            "conflicted": 0.0,
        }
        score += status_boosts.get(status, 0.0)

        # Conflict penalty
        if has_conflict:
            score -= 10.0

        # Clamp to valid range
        score = max(0.0, min(100.0, score))
        score = round(score, 1)

        # Generate explanation
        explanation = self._generate_osint_explanation(
            score=score,
            status=status,
            agreement=agreement_count,
            total=total_sources,
            has_conflict=has_conflict,
        )

        return (score, explanation)

    def _generate_osint_explanation(
        self,
        score: float,
        status: str,
        agreement: int,
        total: int,
        has_conflict: bool,
    ) -> str:
        """
        Generate human-readable explanation for OSINT confidence.

        Args:
            score: Confidence score (0-100)
            status: Consensus status (confirmed, conflicted, etc.)
            agreement: Number of sources agreeing
            total: Total number of sources
            has_conflict: True if conflict detected

        Returns:
            Formatted string like "87%: high - 3/4 sources agree, multi-source consensus"
        """
        # Calculate source agreement percentage
        agreement_pct = (agreement / total * 100) if total > 0 else 0

        # Build context parts
        parts = []

        # Source agreement percentage
        parts.append(f"{agreement}/{total} sources agree ({agreement_pct:.0f}%)")

        # Status context
        if status == "confirmed":
            parts.append("multi-source consensus")
        elif status == "conflicted":
            parts.append("conflicting evidence")
        elif status == "insufficient":
            parts.append("insufficient sources")

        # Determine confidence tier
        if score >= 80.0:
            tier = "high"
        elif score >= 60.0:
            tier = "moderate"
        elif score >= 40.0:
            tier = "low"
        else:
            tier = "very low"

        # Format: "{score}%: {tier} - {parts}"
        parts_str = ", ".join(parts)
        return f"{int(score)}%: {tier} - {parts_str}"
