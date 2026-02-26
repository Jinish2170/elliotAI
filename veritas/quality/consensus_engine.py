"""
Consensus Engine for Multi-Source Finding Validation

Implements multi-factor consensus verification across Vision, OSINT, and Security agents:
- Finding status tiers: CONFIRMED (2+ sources), UNCONFIRMED (1 source), CONFLICTED (disagreement), PENDING
- Conflict detection when agents disagree (threat vs safe)
- Confidence scoring with explainable breakdown (source agreement 60%, severity 25%, context 15%)
"""

import logging
from typing import Optional

from veritas.core.types import (
    ConsensusResult,
    FindingSource,
    FindingStatus,
)

logger = logging.getLogger("veritas.quality.consensus_engine")


class ConsensusEngine:
    """
    Multi-source consensus engine for finding verification.

    Aggregates findings from multiple agents (Vision, OSINT, Security) and
    computes consensus-based confidence scores with explainable breakdowns.
    """

    def __init__(self, min_sources: int = 2):
        """
        Initialize the consensus engine.

        Args:
            min_sources: Minimum number of distinct agent sources required for confirmation
        """
        self.min_sources = min_sources
        self.findings: dict[str, ConsensusResult] = {}

    def add_finding(
        self,
        finding_key: str,
        agent_type: str,
        finding_id: str,
        severity: str,
        confidence: float,
        timestamp: Optional[str] = None,
    ) -> FindingStatus:
        """
        Add a finding source and update consensus result.

        Args:
            finding_key: Normalized finding signature
            agent_type: Type of agent (vision, osint, security)
            finding_id: Identifier for the finding within the agent
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
            confidence: Original confidence from source agent (0.0-1.0)
            timestamp: ISO format timestamp (auto-generated if None)

        Returns:
            Updated FindingStatus after adding the source
        """
        # Generate ISO timestamp if not provided
        if timestamp is None:
            from datetime import datetime, timezone

            timestamp = datetime.now(timezone.utc).isoformat()

        # Create FindingSource instance
        source = FindingSource(
            agent_type=agent_type,
            finding_id=finding_id,
            severity=severity,
            confidence=confidence,
            timestamp=timestamp,
        )

        # Get or create ConsensusResult
        result = self.findings.get(finding_key)
        if result is None:
            result = ConsensusResult(finding_key=finding_key)
            self.findings[finding_key] = result

        # Check for conflicts BEFORE adding source
        if self._detect_conflict(result.sources, source):
            result.status = FindingStatus.CONFLICTED
            conflict_note = (
                f"Conflict detected: {source.agent_type} reports {source.severity} "
                f"while existing sources disagree"
            )
            result.conflict_notes.append(conflict_note)
            # Still add the source for tracking, but keep conflicted status
            result.sources.append(source)
            return result.status

        # Add source to result
        result.sources.append(source)

        # Compute unique agent count (distinct agent types)
        unique_agents = {s.agent_type for s in result.sources}

        # Update status based on unique agent count
        if len(unique_agents) >= self.min_sources:
            result.status = FindingStatus.CONFIRMED
            result.aggregated_confidence = self._compute_confidence(result)
        elif len(unique_agents) == 1:
            result.status = FindingStatus.UNCONFIRMED
            # Cap confidence at 49.0 (<50% per CONTEXT.md) for single source
            result.aggregated_confidence = self._compute_confidence(result)
        else:
            result.status = FindingStatus.PENDING
            result.aggregated_confidence = 0.0

        return result.status

    def _detect_conflict(
        self, existing_sources: list[FindingSource], new_source: FindingSource
    ) -> bool:
        """
        Detect if new source conflicts with existing sources.

        A conflict occurs when one source indicates a threat (CRITICAL/HIGH/MEDIUM/LOW)
        and another indicates safe (INFO).

        Args:
            existing_sources: List of existing finding sources
            new_source: New source being added

        Returns:
            True if conflict detected, False otherwise
        """
        # Map severity to boolean: threat=True, safe=False
        def is_threat(severity: str) -> bool:
            if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                return True
            return False  # INFO or unknown = safe

        new_is_threat = is_threat(new_source.severity)

        # Check all existing sources
        for source in existing_sources:
            existing_is_threat = is_threat(source.severity)
            if existing_is_threat != new_is_threat:
                # Found disagreement: one says threat, one says safe
                return True

        return False

    def _compute_confidence(self, result: ConsensusResult) -> float:
        """
        Compute aggregated confidence score with explainable breakdown.

        Weights: source agreement 60%, severity 25%, context 15%.

        Applies CONTEXT.md thresholds:
        - 2+ sources + high severity: 75.0-100.0 range
        - 2+ sources + medium severity: 50.0-75.0 range
        - 1 source + high severity: 40.0-60.0 range
        - 1 source + medium severity: 20.0-40.0 range

        Args:
            result: ConsensusResult with sources

        Returns:
            Aggregated confidence score (0-100)
        """
        # Get unique agents (distinct agent types, not total findings)
        unique_agents = {s.agent_type for s in result.sources}
        source_count = len(unique_agents)

        # Find max severity among sources
        severity_weights = {
            "CRITICAL": 1.0,
            "HIGH": 0.8,
            "MEDIUM": 0.6,
            "LOW": 0.4,
            "INFO": 0.2,
        }

        # Get max severity weight (most severe finding)
        max_severity_weight = max(
            (severity_weights.get(s.severity, 0.5) for s in result.sources), default=0.5
        )

        # Average confidence from all sources
        avg_source_confidence = sum(s.confidence for s in result.sources) / len(
            result.sources
        )

        # Compute weighted score (source agreement 60%, severity 25%, context 15%)
        source_agreement_factor = min(1.0, source_count / self.min_sources)
        severity_factor = max_severity_weight
        context_factor = avg_source_confidence

        # Base score from weighted factors
        base_score = (
            source_agreement_factor * 60.0
            + severity_factor * 25.0
            + context_factor * 15.0
        )

        # Apply CONTEXT.md thresholds
        if source_count >= self.min_sources:
            # Multi-source confirmed
            if max_severity_weight >= 0.8:  # CRITICAL or HIGH
                # 75.0-100.0 range: ensure minimum 75.0
                final_score = max(75.0, base_score)
            else:
                # 50.0-75.0 range for medium severity
                final_score = min(75.0, max(50.0, base_score))
        else:
            # Single source - cap at 49.0 (<50% per CONTEXT.md)
            if max_severity_weight >= 0.8:  # CRITICAL or HIGH
                # 40.0-60.0 range, cap at 49.0
                final_score = min(49.0, max(40.0, base_score))
            else:
                # 20.0-40.0 range
                final_score = min(49.0, max(20.0, base_score))

        # Round to 1 decimal place
        final_score = round(final_score, 1)

        # Populate confidence breakdown for explainability
        result.confidence_breakdown = {
            "source_agreement": round(source_agreement_factor * 100, 1),
            "severity_factor": round(severity_factor * 100, 1),
            "context_confidence": round(context_factor * 100, 1),
            "source_count": source_count,
        }

        return final_score

    def get_result(self, finding_key: str) -> Optional[ConsensusResult]:
        """
        Get the consensus result for a finding key.

        Args:
            finding_key: Normalized finding signature

        Returns:
            ConsensusResult if found, None otherwise
        """
        return self.findings.get(finding_key)

    def get_confirmed_findings(self) -> list[ConsensusResult]:
        """
        Get all findings with CONFIRMED status.

        Returns:
            List of ConsensusResult objects with CONFIRMED status
        """
        return [r for r in self.findings.values() if r.status == FindingStatus.CONFIRMED]

    def get_conflicted_findings(self) -> list[ConsensusResult]:
        """
        Get all findings with CONFLICTED status.

        Returns:
            List of ConsensusResult objects with CONFLICTED status
        """
        return [r for r in self.findings.values() if r.status == FindingStatus.CONFLICTED]
