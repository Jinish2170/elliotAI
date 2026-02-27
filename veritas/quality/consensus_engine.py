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
from veritas.osint.types import OSINTResult, SourceStatus

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

    def compute_osint_consensus(
        self,
        results: dict[str, OSINTResult],
        min_sources: int = 3,
        exception_high_trust: bool = True,
    ) -> dict:
        """
        Compute multi-source consensus from OSINT results.

        Aggregates findings from OSINT sources and determines threat status
        through consensus. Preserves conflicts with detailed reasoning.

        Args:
            results: Dict mapping source names to OSINTResult instances
            min_sources: Minimum sources for confirmed status (default: 3)
            exception_high_trust: Allow 2-source confirmation for high-trust sources

        Returns:
            Dict with:
                - consensus_status: Status (confirmed, conflicted, likely, possible, insufficient)
                - verdict: Dominant verdict (malicious, safe, suspicious, unknown)
                - agreement_count: Number of sources agreeing with verdict
                - total_sources: Total number of sources with SUCCESS status
                - conflicting_sources: List of sources with conflicting verdicts
                - has_conflict: True if conflict detected
                - reasoning: Human-readable explanation
        """
        # Filter to only successful results
        valid_results = {
            source: result
            for source, result in results.items()
            if result.status == SourceStatus.SUCCESS
        }

        if not valid_results:
            return {
                "consensus_status": "insufficient",
                "verdict": "unknown",
                "agreement_count": 0,
                "total_sources": 0,
                "conflicting_sources": [],
                "has_conflict": False,
                "reasoning": "No successful OSINT results",
            }

        # Convert each result to verdict
        verdicts: dict[str, str] = {}
        for source, result in valid_results.items():
            verdicts[source] = self._osint_result_to_verdict(result)

        # Count agreement for each verdict
        verdict_counts: dict[str, list[str]] = {}
        for source, verdict in verdicts.items():
            if verdict not in verdict_counts:
                verdict_counts[verdict] = []
            verdict_counts[verdict].append(source)

        # Find dominant verdict (most sources)
        dominant_verdict = max(verdict_counts.keys(), key=lambda k: len(verdict_counts[k]))
        agreement_count = len(verdict_counts[dominant_verdict])
        total_sources = len(valid_results)

        # Check for conflict: both malicious and safe sources present
        has_conflict = ("malicious" in verdict_counts) and ("safe" in verdict_counts)

        conflicting_sources = []
        if has_conflict:
            # List sources that conflict with dominant verdict
            conflicting_sources = verdict_counts.get("safe" if dominant_verdict == "malicious" else "malicious", [])

        # Determine consensus status
        consensus_status = self._determine_osint_status(
            agreement_count=agreement_count,
            total_sources=total_sources,
            has_conflict=has_conflict,
            min_sources=min_sources,
            exception_high_trust=exception_high_trust,
        )

        # Generate human-readable reasoning
        malicious_size = len(verdict_counts.get("malicious", []))
        safe_size = len(verdict_counts.get("safe", []))
        suspicious_size = len(verdict_counts.get("suspicious", []))
        unknown_size = len(verdict_counts.get("unknown", []))

        reasoning = self._generate_osint_reasoning(
            status=consensus_status,
            verdict=dominant_verdict,
            agreement=agreement_count,
            total=total_sources,
            has_conflict=has_conflict,
            malicious_size=malicious_size,
            safe_size=safe_size,
            malicious_sources=verdict_counts.get("malicious", []),
            safe_sources=verdict_counts.get("safe", []),
        )

        return {
            "consensus_status": consensus_status,
            "verdict": dominant_verdict,
            "agreement_count": agreement_count,
            "total_sources": total_sources,
            "conflicting_sources": conflicting_sources,
            "has_conflict": has_conflict,
            "reasoning": reasoning,
        }

    def _osint_result_to_verdict(self, result: OSINTResult) -> str:
        """
        Convert OSINT result to verdict string.

        Args:
            result: OSINTResult with threat intelligence data

        Returns:
            Verdict string: "malicious", "safe", "suspicious", or "unknown"
        """
        data = result.data or {}

        # Handle THREAT_INTEL sources (abuseipdb, urlvoid)
        if result.category.value == "threat_intel":
            abuse_confidence = data.get("abuse_confidence", 0)
            reports_count = data.get("reports", 0)

            if abuse_confidence > 50 or reports_count > 5:
                return "malicious"
            elif abuse_confidence > 20 or reports_count > 2:
                return "suspicious"
            else:
                return "safe"

        # Handle REPUTATION sources
        elif result.category.value == "reputation":
            detections = data.get("detections", 0)
            risk_level = data.get("risk", "").lower()

            if detections > 3 or risk_level == "high":
                return "malicious"
            elif detections > 0 or risk_level in ("low", "medium"):
                return "suspicious"
            else:
                return "safe"

        # Handle WHOIS and SSL sources
        elif result.category.value in ("whois", "ssl"):
            age_days = data.get("age_days", 999)
            is_valid = data.get("is_valid", True)

            if age_days < 30 or not is_valid:
                return "suspicious"
            else:
                return "safe"

        # DNS and other sources default to unknown
        return "unknown"

    def _determine_osint_status(
        self,
        agreement_count: int,
        total_sources: int,
        has_conflict: bool,
        min_sources: int = 3,
        exception_high_trust: bool = True,
    ) -> str:
        """
        Determine consensus status from OSINT results.

        Args:
            agreement_count: Number of sources agreeing with dominant verdict
            total_sources: Total number of successful sources
            has_conflict: True if conflict detected
            min_sources: Minimum sources for confirmed status
            exception_high_trust: Allow 2-source confirmation exception

        Returns:
            Status string: "confirmed", "conflicted", "likely", "possible", "insufficient"
        """
        # Conflict takes precedence - preserve it
        if has_conflict:
            return "conflicted"

        # Check for confirmation
        if agreement_count >= min_sources:
            return "confirmed"

        # High-trust 2-source exception
        if exception_high_trust and agreement_count >= 2:
            return "confirmed"

        # Determine tier based on ratios
        agreement_ratio = agreement_count / total_sources

        if agreement_ratio >= 0.5 and total_sources >= 2:
            return "likely"
        elif agreement_ratio >= 0.33 and total_sources >= 2:
            return "possible"
        else:
            return "insufficient"

    def _generate_osint_reasoning(
        self,
        status: str,
        verdict: str,
        agreement: int,
        total: int,
        has_conflict: bool,
        malicious_size: int,
        safe_size: int,
        malicious_sources: list[str],
        safe_sources: list[str],
    ) -> str:
        """
        Generate human-readable explanation for OSINT consensus.

        Args:
            status: Consensus status
            verdict: Dominant verdict
            agreement: Number of sources agreeing
            total: Total number of sources
            has_conflict: True if conflict detected
            malicious_size: Count of malicious verdicts
            safe_size: Count of safe verdicts
            malicious_sources: List of sources with malicious verdicts
            safe_sources: List of sources with safe verdicts

        Returns:
            Human-readable explanation string
        """
        if has_conflict:
            # Detailed conflict reporting - list conflicting sources explicitly
            malicious_names = ", ".join(malicious_sources[:3])
            safe_names = ", ".join(safe_sources[:3])

            conflicts = []
            for m in malicious_sources:
                conflicts.append(f"{m}: malicious")
            for s in safe_sources:
                conflicts.append(f"{s}: safe")

            conflict_list = ", ".join(conflicts[:5])
            if len(conflicts) > 5:
                conflict_list += f", +{len(conflicts) - 5} more"

            return (
                f"CONFLICTED: {malicious_size} malicious vs {safe_size} safe sources. "
                f"Conflicting evidence from: {conflict_list}. "
                f"Manual review required. "
            )

        # Non-conflicting statuses
        agreement_pct = (agreement / total) * 100 if total > 0 else 0

        if status == "confirmed":
            return (
                f"CONFIRMED {verdict}: {agreement}/{total} sources agree ({agreement_pct:.0f}%) "
                f"- meets {agreement}+ source consensus threshold. "
            )
        elif status == "likely":
            return (
                f"LIKELY {verdict}: {agreement}/{total} sources agree ({agreement_pct:.0f}%) "
                f"- majority but below confirmation threshold. "
            )
        elif status == "possible":
            return (
                f"POSSIBLE {verdict}: {agreement}/{total} sources suggest threat ({agreement_pct:.0f}%) "
                f"- needs additional verification. "
            )
        else:  # insufficient
            return (
                f"INSUFFICIENT: Only {agreement}/{total} sources ({agreement_pct:.0f}%) "
                f"- cannot establish reliable consensus. "
            )
