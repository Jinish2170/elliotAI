"""
Source Reputation Tracking System for OSINT Sources.

Tracks source accuracy over time, dynamically adjusts weights based on
performance, and provides weighted consensus scoring for multi-source
verification.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger("veritas.osint.reputation")


class VerdictType(str, Enum):
    """Verdict type for OSINT threat classification."""
    MALICIOUS = "malicious"
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    UNKNOWN = "unknown"


@dataclass
class SourcePrediction:
    """Record of a threat prediction made by a source.

    Attributes:
        source: Name of the OSINT source
        verdict: Predicted verdict type
        confidence: Confidence level (0.0-1.0)
        actual_verdict: Actual verified verdict (if known)
        timestamp: When the prediction was made
    """
    source: str
    verdict: VerdictType
    confidence: float
    actual_verdict: Optional[VerdictType] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def was_correct(self) -> bool:
        """Check if prediction matched actual verdict.

        Special case: SUSPICIOUS matching EITHER MALICIOUS or SAFE
        is considered partially correct for reputation purposes.
        """
        if self.actual_verdict is None:
            return False

        # Exact match
        if self.verdict == self.actual_verdict:
            return True

        # SUSPICIOUS matches MALICIOUS or SAFE (partial credit)
        if self.verdict == VerdictType.SUSPICIOUS:
            if self.actual_verdict in (VerdictType.MALICIOUS, VerdictType.SAFE):
                return True

        return False


@dataclass
class SourceReputation:
    """Reputation tracking for an OSINT source.

    Tracks accuracy, false positives, false negatives, and computes
    weighted reputation scores for consensus calculation.

    Attributes:
        source: Name of the OSINT source
        total_predictions: Total number of predictions made
        correct_predictions: Number of correct predictions
        false_positives: Predicted MALICIOUS, actually SAFE
        false_negatives: Predicted SAFE, actually MALICIOUS
        recent_predictions: Last N predictions for recent accuracy
    """
    source: str
    total_predictions: int = 0
    correct_predictions: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    recent_predictions: list[SourcePrediction] = field(default_factory=list)

    @property
    def accuracy_score(self) -> float:
        """Calculate base accuracy score (correct/total).

        Returns 0.5 (neutral) when no predictions exist.
        """
        if self.total_predictions == 0:
            return 0.5
        return self.correct_predictions / self.total_predictions

    def recent_accuracy(self, days: int = 30) -> float:
        """Calculate accuracy from recent predictions.

        Args:
            days: Number of days to look back

        Returns:
            Accuracy score for recent predictions (0.5 default)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = [p for p in self.recent_predictions if p.timestamp > cutoff]

        if not recent:
            return self.accuracy_score  # Fall back to overall accuracy

        correct = sum(1 for p in recent if p.was_correct)
        return correct / len(recent)

    @property
    def false_negative_rate(self) -> float:
        """Calculate false negative rate (FN/total).

        Returns 0.0 when no predictions exist.
        """
        if self.total_predictions == 0:
            return 0.0
        return self.false_negatives / self.total_predictions

    @property
    def false_positive_rate(self) -> float:
        """Calculate false positive rate (FP/total).

        Returns 0.0 when no predictions exist.
        """
        if self.total_predictions == 0:
            return 0.0
        return self.false_positives / self.total_predictions

    @property
    def weighted_reputation(self) -> float:
        """Calculate weighted reputation score.

        Formula:
            (base_accuracy * 0.6) + (recent_factor * 0.2) + (fn_penalty * 0.2)

        Where:
            recent_factor = min(1.0, recent_accuracy / (base_accuracy + 0.01))
            fn_penalty = 1.0 - min(1.0, false_negative_rate * 3)

        Returns:
            Weighted score between 0.0 and 1.0
        """
        base_accuracy = self.accuracy_score
        recent_acc = self.recent_accuracy(days=30)
        fn_rate = self.false_negative_rate

        # Recent factor: reward sources maintaining or improving accuracy
        recent_factor = min(1.0, recent_acc / (base_accuracy + 0.01))

        # FN penalty: significantly penalize false negatives (missed threats)
        fn_penalty = 1.0 - min(1.0, fn_rate * 3)

        # Weighted combination
        weighted = (
            (base_accuracy * 0.6) +
            (recent_factor * 0.2) +
            (fn_penalty * 0.2)
        )

        # Clamp to valid range
        return max(0.0, min(1.0, weighted))


class ReputationManager:
    """Manages reputation tracking for multiple OSINT sources.

    Provides methods to record predictions, actual outcomes, and
    calculate consensus weights based on source reputation.
    """

    def __init__(self):
        """Initialize the reputation manager with core sources."""
        self.sources: dict[str, SourceReputation] = {}
        self._init_core_sources()

    def _init_core_sources(self):
        """Initialize core OSINT sources with neutral reputation."""
        core_sources = [
            "dns",
            "whois",
            "ssl",
            "urlvoid",
            "abuseipdb",
        ]
        for source in core_sources:
            self.sources[source] = SourceReputation(source=source)

    def _get_or_create(self, source_name: str) -> SourceReputation:
        """Get existing source or create new one with neutral reputation.

        Args:
            source_name: Name of the OSINT source

        Returns:
            SourceReputation instance
        """
        if source_name not in self.sources:
            self.sources[source_name] = SourceReputation(source=source_name)
        return self.sources[source_name]

    def record_prediction(
        self,
        source: str,
        verdict: VerdictType,
        confidence: float = 0.8
    ) -> SourcePrediction:
        """Record a threat prediction from a source.

        Args:
            source: Name of the OSINT source
            verdict: Predicted verdict type
            confidence: Confidence level (0.0-1.0)

        Returns:
            Created SourcePrediction instance
        """
        rep = self._get_or_create(source)
        prediction = SourcePrediction(
            source=source,
            verdict=verdict,
            confidence=confidence
        )

        rep.total_predictions += 1
        rep.recent_predictions.append(prediction)

        # Keep recent predictions limited to prevent memory growth
        max_recent = 100
        if len(rep.recent_predictions) > max_recent:
            rep.recent_predictions = rep.recent_predictions[-max_recent:]

        logger.debug(
            f"Recorded prediction from {source}: {verdict.value} "
            f"(confidence: {confidence:.2f})"
        )

        return prediction

    def record_actual(
        self,
        source: str,
        prediction_index: int,
        actual: VerdictType
    ) -> bool:
        """Record the actual verified verdict for a prediction.

        Updates reputation counters based on prediction accuracy.

        Args:
            source: Name of the OSINT source
            prediction_index: Index of the prediction (for future reference)
            actual: Actual verified verdict type

        Returns:
            True if prediction was correct, False otherwise
        """
        rep = self._get_or_create(source)

        # Find prediction (using recent_predictions list)
        if prediction_index < 0 or prediction_index >= len(rep.recent_predictions):
            logger.warning(
                f"Invalid prediction_index {prediction_index} for source {source}"
            )
            return False

        prediction = rep.recent_predictions[prediction_index]
        prediction.actual_verdict = actual

        # Update counters
        if prediction.was_correct:
            rep.correct_predictions += 1
        else:
            # Classify error type
            if prediction.verdict == VerdictType.MALICIOUS and actual == VerdictType.SAFE:
                rep.false_positives += 1
            elif prediction.verdict == VerdictType.SAFE and actual == VerdictType.MALICIOUS:
                rep.false_negatives += 1

        logger.info(
            f"Recorded actual for {source}: {actual.value} "
            f"(correct: {prediction.was_correct}, "
            f"reputation: {rep.weighted_reputation:.2f})"
        )

        return prediction.was_correct

    def calculate_consensus_weight(self, source_name: str) -> float:
        """Calculate consensus weight for a source based on reputation.

        Higher reputation sources get higher weight in consensus.
        Also applies volume bonus for sources with more predictions.

        Args:
            source_name: Name of the OSINT source

        Returns:
            Consensus weight (0.0 to 2.0+)
        """
        rep = self._get_or_create(source_name)

        # Base weight from reputation
        base_weight = rep.weighted_reputation

        # Volume bonus: sources with more history get slight boost
        volume_bonus = 1.0
        if rep.total_predictions >= 100:
            volume_bonus = 1.2
        elif rep.total_predictions >= 50:
            volume_bonus = 1.1
        elif rep.total_predictions >= 20:
            volume_bonus = 1.05

        return base_weight * volume_bonus

    def get_confidence_thresholds(self) -> dict[str, float]:
        """Get minimum confidence thresholds per source.

        Higher reputation sources have lower thresholds (more trusted).

        Returns:
            Dict mapping source name to minimum confidence threshold (0.0-1.0)
        """
        thresholds = {}

        for source, rep in self.sources.items():
            # Base threshold is 0.5 (50%)
            # Reduce for high-reputation sources
            reputation = rep.weighted_reputation

            if reputation >= 0.8:
                threshold = 0.3  # Very trusted
            elif reputation >= 0.6:
                threshold = 0.4  # Trusted
            elif reputation >= 0.4:
                threshold = 0.5  # Neutral
            else:
                threshold = 0.7  # Skeptical

            thresholds[source] = threshold

        return thresholds

    def get_source_reputation(self, source_name: str) -> Optional[SourceReputation]:
        """Get reputation data for a source.

        Args:
            source_name: Name of the OSINT source

        Returns:
            SourceReputation if found, None otherwise
        """
        return self.sources.get(source_name)

    def get_all_sources(self) -> list[str]:
        """Get list of all tracked sources.

        Returns:
            List of source names
        """
        return list(self.sources.keys())
