"""
Tests for ConsensusEngine and Quality Foundation

Comprehensive test coverage for multi-source finding validation,
confidence scoring, and state machine transitions.
"""

import pytest

from veritas.core.types import FindingStatus, FindingSource
from veritas.quality import ConfidenceScorer, ConsensusEngine, ValidationStateMachine


class TestFindingStatusAndSourceDataclasses:
    """Verify enum values and dataclass instantiation."""

    def test_finding_status_enum_values(self):
        """Verify FindingStatus has correct enum values."""
        assert hasattr(FindingStatus, "UNCONFIRMED")
        assert hasattr(FindingStatus, "CONFIRMED")
        assert hasattr(FindingStatus, "CONFLICTED")
        assert hasattr(FindingStatus, "PENDING")

    def test_finding_source_dataclass(self):
        """Verify FindingSource creates correctly."""
        source = FindingSource(
            agent_type="vision",
            finding_id="v-001",
            severity="HIGH",
            confidence=0.8,
            timestamp="2026-02-26T10:00:00Z"
        )
        assert source.agent_type == "vision"
        assert source.finding_id == "v-001"
        assert source.severity == "HIGH"
        assert source.confidence == 0.8
        assert source.timestamp == "2026-02-26T10:00:00Z"


class TestTwoSourcesConfirmFinding:
    """Verify 2+ distinct agent types produce CONFIRMED status."""

    def test_two_distinct_agents_confirm_finding(self):
        """Add 2 distinct agent types with HIGH severity verify CONFIRMED status."""
        engine = ConsensusEngine(min_sources=2)

        # Add first source (vision)
        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)

        # Add second source (osint)
        engine.add_finding("test-1", "osint", "o-001", "HIGH", 0.9)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.status == FindingStatus.CONFIRMED
        assert result.aggregated_confidence >= 75.0

    def test_two_distinct_agents_medium_severity(self):
        """Add 2 distinct agent types with MEDIUM severity verify CONFIRMED status."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "MEDIUM", 0.7)
        engine.add_finding("test-1", "osint", "o-001", "MEDIUM", 0.75)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.status == FindingStatus.CONFIRMED
        assert 50.0 <= result.aggregated_confidence <= 75.0


class TestThreeSourcesHighConfidence:
    """Verify 3+ sources produce CONFIRMED status with high confidence."""

    def test_three_distinct_agents_high_confidence(self):
        """Add 3 distinct agents with CRITICAL severity verify high confidence."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "CRITICAL", 0.95)
        engine.add_finding("test-1", "osint", "o-001", "CRITICAL", 0.9)
        engine.add_finding("test-1", "security", "s-001", "CRITICAL", 0.85)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.status == FindingStatus.CONFIRMED
        assert 75.0 <= result.aggregated_confidence <= 100.0

    def test_unique_agent_count_three(self):
        """Verify 3 distinct agents counted correctly."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("test-1", "osint", "o-001", "HIGH", 0.85)
        engine.add_finding("test-1", "security", "s-001", "HIGH", 0.9)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.status == FindingStatus.CONFIRMED
        assert len(result.sources) == 3


class TestSingleSourceUnconfirmed:
    """Verify single source findings remain UNCONFIRMED with <50% confidence."""

    def test_single_source_unconfirmed_status(self):
        """Add single source with HIGH severity verify UNCONFIRMED status."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.status == FindingStatus.UNCONFIRMED
        assert result.aggregated_confidence < 50.0

    def test_single_source_source_count(self):
        """Verify single source has source_count of 1."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.confidence_breakdown.get("source_count") == 1


class TestSingleSourceMediumSeverityUnconfirmed:
    """Verify single source with MEDIUM severity has lower confidence."""

    def test_single_source_medium_severity_confidence(self):
        """Add single source with MEDIUM severity verify confidence in 20-40% range."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "MEDIUM", 0.7)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.status == FindingStatus.UNCONFIRMED
        assert 20.0 <= result.aggregated_confidence < 50.0

    def test_single_source_medium_severity_format(self):
        """Verify format_confidence for medium severity single source."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "MEDIUM", 0.7)

        result = engine.get_result("test-1")
        formatted = ConfidenceScorer.format_confidence(result)
        assert "%" in formatted
        assert "1 source" in formatted
        assert "medium" in formatted.lower()


class TestConflictingSourcesConflicted:
    """Verify conflict detection when agents disagree (threat vs safe)."""

    def test_threat_vs_safe_conflict(self):
        """Add HIGH severity (threat) and INFO severity (safe) verify CONFLICTED."""
        engine = ConsensusEngine(min_sources=2)

        # Add vision source with HIGH severity (threat)
        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)

        # Add osint source with INFO severity (safe)
        engine.add_finding("test-1", "osint", "o-001", "INFO", 0.9)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.status == FindingStatus.CONFLICTED
        assert len(result.conflict_notes) > 0

    def test_conflict_notes_populated(self):
        """Verify conflict_notes are populated when conflict detected."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("test-1", "osint", "o-001", "INFO", 0.9)

        result = engine.get_result("test-1")
        assert result is not None
        assert len(result.conflict_notes) > 0
        assert "Conflict detected" in result.conflict_notes[0]


class TestConfidenceBreakdownExplainable:
    """Verify confidence breakdown provides explainable factors."""

    def test_confidence_breakdown_keys(self):
        """Verify confidence_breakdown has all required keys."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("test-1", "osint", "o-001", "HIGH", 0.9)

        result = engine.get_result("test-1")
        assert result is not None

        breakdown = result.confidence_breakdown
        assert "source_agreement" in breakdown
        assert "severity_factor" in breakdown
        assert "context_confidence" in breakdown
        assert "source_count" in breakdown

    def test_format_confidence_human_readable(self):
        """Verify format_confidence returns human-readable format."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("test-1", "osint", "o-001", "HIGH", 0.9)

        result = engine.get_result("test-1")
        formatted = ConfidenceScorer.format_confidence(result)

        # Format should be like "XX%: description"
        assert "%" in formatted
        assert ":" in formatted
        assert "sources" in formatted.lower() or "source" in formatted.lower()


class TestSameAgentTypeDoesNotIncreaseCount:
    """Verify distinct agent counting (same agent_type doesn't double-count)."""

    def test_same_agent_type_single_count(self):
        """Add 2 findings from same agent_type verify single unique agent."""
        engine = ConsensusEngine(min_sources=2)

        # Add two findings from vision agent
        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("test-1", "vision", "v-002", "HIGH", 0.85)

        result = engine.get_result("test-1")
        assert result is not None

        # Should remain UNCONFIRMED since only 1 unique agent type
        assert result.status == FindingStatus.UNCONFIRMED
        assert result.aggregated_confidence < 50.0

    def test_same_agent_type_source_count(self):
        """Verify source_count is 1 despite 2 findings from same agent."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "vision-001", "HIGH", 0.8)
        engine.add_finding("test-1", "vision", "vision-002", "HIGH", 0.85)

        result = engine.get_result("test-1")
        assert result is not None
        assert result.confidence_breakdown.get("source_count") == 1


class TestConfidenceTierClassification:
    """Verify ConfidenceScorer.get_confidence_tier returns correct tier."""

    def test_high_confidence_tier(self):
        """Verify scores >=75 return high_confidence."""
        assert ConfidenceScorer.get_confidence_tier(75.0) == "high_confidence"
        assert ConfidenceScorer.get_confidence_tier(87.5) == "high_confidence"
        assert ConfidenceScorer.get_confidence_tier(100.0) == "high_confidence"

    def test_medium_confidence_tier(self):
        """Verify scores >=50 return medium_confidence."""
        assert ConfidenceScorer.get_confidence_tier(50.0) == "medium_confidence"
        assert ConfidenceScorer.get_confidence_tier(62.5) == "medium_confidence"
        assert ConfidenceScorer.get_confidence_tier(74.9) == "medium_confidence"

    def test_unconfirmed_high_tier(self):
        """Verify scores >=40 return unconfirmed_high."""
        assert ConfidenceScorer.get_confidence_tier(40.0) == "unconfirmed_high"
        assert ConfidenceScorer.get_confidence_tier(49.9) == "unconfirmed_high"

    def test_unconfirmed_medium_tier(self):
        """Verify scores >=20 return unconfirmed_medium."""
        assert ConfidenceScorer.get_confidence_tier(20.0) == "unconfirmed_medium"
        assert ConfidenceScorer.get_confidence_tier(39.9) == "unconfirmed_medium"

    def test_low_confidence_tier(self):
        """Verify scores <20 return low_confidence."""
        assert ConfidenceScorer.get_confidence_tier(0.0) == "low_confidence"
        assert ConfidenceScorer.get_confidence_tier(10.0) == "low_confidence"
        assert ConfidenceScorer.get_confidence_tier(19.9) == "low_confidence"

    def test_all_tier_boundaries(self):
        """Verify all 5 tier boundaries work correctly."""
        test_cases = [
            (100.0, "high_confidence"),
            (75.0, "high_confidence"),
            (74.9, "medium_confidence"),
            (50.0, "medium_confidence"),
            (49.9, "unconfirmed_high"),
            (40.0, "unconfirmed_high"),
            (39.9, "unconfirmed_medium"),
            (20.0, "unconfirmed_medium"),
            (19.9, "low_confidence"),
            (0.0, "low_confidence"),
        ]

        for score, expected_tier in test_cases:
            actual_tier = ConfidenceScorer.get_confidence_tier(score)
            assert actual_tier == expected_tier, f"Score {score}: expected {expected_tier}, got {actual_tier}"


class TestValidationStateTransitions:
    """Verify ValidationStateMachine transition() and is_valid_transition()."""

    def test_transition_pending_to_unconfirmed(self):
        """Verify PENDING -> UNCONFIRMED is valid."""
        engine = ConsensusEngine(min_sources=2)

        status = engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        assert status == FindingStatus.UNCONFIRMED
        assert ValidationStateMachine.is_valid_transition(
            FindingStatus.PENDING, FindingStatus.UNCONFIRMED
        )

    def test_transition_unconfirmed_to_confirmed(self):
        """Verify UNCONFIRMED -> CONFIRMED is valid."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        status = engine.add_finding("test-1", "osint", "o-001", "HIGH", 0.9)
        assert status == FindingStatus.CONFIRMED
        assert ValidationStateMachine.is_valid_transition(
            FindingStatus.UNCONFIRMED, FindingStatus.CONFIRMED
        )

    def test_transition_to_conflicted(self):
        """Verify transitions to CONFLICTED are valid."""
        engine = ConsensusEngine(min_sources=2)

        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        status = engine.add_finding("test-1", "osint", "o-001", "INFO", 0.9)
        assert status == FindingStatus.CONFLICTED
        assert ValidationStateMachine.is_valid_transition(
            FindingStatus.UNCONFIRMED, FindingStatus.CONFLICTED
        )

        # Test from CONFIRMED to CONFLICTED
        engine2 = ConsensusEngine(min_sources=2)
        engine2.add_finding("test-2", "vision", "v-001", "HIGH", 0.8)
        engine2.add_finding("test-2", "osint", "o-001", "HIGH", 0.9)
        status = engine2.add_finding("test-2", "security", "s-001", "INFO", 0.7)
        assert status == FindingStatus.CONFLICTED
        assert ValidationStateMachine.is_valid_transition(
            FindingStatus.CONFIRMED, FindingStatus.CONFLICTED
        )

    def test_conflicted_is_terminal(self):
        """Verify CONFLICTED state has no valid outgoing transitions."""
        assert len(ValidationStateMachine.VALID_TRANSITIONS[FindingStatus.CONFLICTED]) == 0
        assert not ValidationStateMachine.is_valid_transition(
            FindingStatus.CONFLICTED, FindingStatus.CONFIRMED
        )
        assert not ValidationStateMachine.is_valid_transition(
            FindingStatus.CONFLICTED, FindingStatus.UNCONFIRMED
        )

    def test_invalid_transitions_rejected(self):
        """Verify invalid transitions return False."""
        # Can't go from UNCONFIRMED back to PENDING
        assert not ValidationStateMachine.is_valid_transition(
            FindingStatus.UNCONFIRMED, FindingStatus.PENDING
        )

        # Can't go from CONFIRMED back to UNCONFIRMED
        assert not ValidationStateMachine.is_valid_transition(
            FindingStatus.CONFIRMED, FindingStatus.UNCONFIRMED
        )


class TestGetConfirmedAndConflictedFindings:
    """Verify filtering methods for different finding statuses."""

    def test_get_confirmed_findings(self):
        """Verify get_confirmed_findings() returns only CONFIRMED."""
        engine = ConsensusEngine(min_sources=2)

        # Add findings with different statuses
        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("test-1", "osint", "o-001", "HIGH", 0.9)  # CONFIRMED

        engine.add_finding("test-2", "vision", "v-002", "MEDIUM", 0.7)  # UNCONFIRMED

        engine.add_finding("test-3", "vision", "v-003", "HIGH", 0.8)
        engine.add_finding("test-3", "osint", "o-003", "INFO", 0.9)  # CONFLICTED

        confirmed = engine.get_confirmed_findings()
        assert len(confirmed) == 1
        assert confirmed[0].finding_key == "test-1"
        assert confirmed[0].status == FindingStatus.CONFIRMED

    def test_get_conflicted_findings(self):
        """Verify get_conflicted_findings() returns only CONFLICTED."""
        engine = ConsensusEngine(min_sources=2)

        # Add findings with different statuses
        engine.add_finding("test-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("test-1", "osint", "o-001", "HIGH", 0.9)  # CONFIRMED

        engine.add_finding("test-2", "vision", "v-002", "MEDIUM", 0.7)  # UNCONFIRMED

        engine.add_finding("test-3", "vision", "v-003", "HIGH", 0.8)
        engine.add_finding("test-3", "osint", "o-003", "INFO", 0.9)  # CONFLICTED

        conflicted = engine.get_conflicted_findings()
        assert len(conflicted) == 1
        assert conflicted[0].finding_key == "test-3"
        assert conflicted[0].status == FindingStatus.CONFLICTED

    def test_mixed_findings_filtering(self):
        """Verify filtering works correctly with multiple finding types."""
        engine = ConsensusEngine(min_sources=2)

        # CONFIRMED
        engine.add_finding("confirmed-1", "vision", "v-001", "HIGH", 0.8)
        engine.add_finding("confirmed-1", "osint", "o-001", "HIGH", 0.9)

        # UNCONFIRMED (2 separate finding)
        engine.add_finding("unconf-1", "vision", "v-002", "MEDIUM", 0.7)
        engine.add_finding("unconf-2", "vision", "v-003", "HIGH", 0.8)

        # CONFLICTED
        engine.add_finding("conflict-1", "vision", "v-004", "HIGH", 0.8)
        engine.add_finding("conflict-1", "osint", "o-004", "INFO", 0.9)

        confirmed = engine.get_confirmed_findings()
        conflicted = engine.get_conflicted_findings()

        assert len(confirmed) == 1
        assert len(conflicted) == 1
        assert confirmed[0].finding_key == "confirmed-1"
        assert conflicted[0].finding_key == "conflict-1"

    def test_can_confirm_helper(self):
        """Verify can_confirm() method returns correct values."""
        assert ValidationStateMachine.can_confirm(FindingStatus.CONFIRMED)
        assert ValidationStateMachine.can_confirm(FindingStatus.UNCONFIRMED)
        assert not ValidationStateMachine.can_confirm(FindingStatus.CONFLICTED)
        assert not ValidationStateMachine.can_confirm(FindingStatus.PENDING)

    def test_requires_review_helper(self):
        """Verify requires_review() method returns correct values."""
        assert ValidationStateMachine.requires_review(FindingStatus.CONFLICTED)
        assert not ValidationStateMachine.requires_review(FindingStatus.CONFIRMED)
        assert not ValidationStateMachine.requires_review(FindingStatus.UNCONFIRMED)
        assert not ValidationStateMachine.requires_review(FindingStatus.PENDING)
