"""
Validation State Machine for Quality Foundation

Manages finding status transitions and enforces state machine rules
for incremental verification and refinement.
"""

import logging
from typing import Optional

from veritas.core.types import FindingSource, FindingStatus

logger = logging.getLogger("veritas.quality.validation_state")


class ValidationStateMachine:
    """
    State machine for finding validation status transitions.

    Enforces legal status changes and provides helper methods
    for checking finding confirmability and review requirements.
    """

    # Valid state transitions (from_status -> {to_statuses})
    VALID_TRANSITIONS = {
        FindingStatus.PENDING: {FindingStatus.UNCONFIRMED},
        FindingStatus.UNCONFIRMED: {FindingStatus.CONFIRMED, FindingStatus.CONFLICTED},
        FindingStatus.CONFIRMED: {FindingStatus.CONFLICTED},
        FindingStatus.CONFLICTED: set(),  # Terminal state
    }

    @classmethod
    def transition(
        cls,
        current_status: FindingStatus,
        new_source: FindingSource,
        existing_sources: list[FindingSource],
        min_sources: int = 2,
    ) -> FindingStatus:
        """
        Compute the new status after adding a source.

        Transition logic:
        1. Check for conflict (threat vs safe) -> returns CONFLICTED
        2. Check unique agent count -> CONFIRMED if >=min_sources, UNCONFIRMED if >=1, PENDING if 0

        Args:
            current_status: Current finding status
            new_source: Source being added (for conflict check)
            existing_sources: Existing sources (for counting)
            min_sources: Minimum distinct agents required for confirmation

        Returns:
            New FindingStatus after transition
        """
        # Combine existing + new sources
        all_sources = existing_sources + [new_source]

        # Check for conflict BEFORE anything else
        if cls._detect_conflict(all_sources):
            return FindingStatus.CONFLICTED

        # Count unique agent types
        unique_agents = {s.agent_type for s in all_sources}

        # Determine status based on unique agent count
        if len(unique_agents) >= min_sources:
            return FindingStatus.CONFIRMED
        elif len(unique_agents) >= 1:
            return FindingStatus.UNCONFIRMED
        else:
            return FindingStatus.PENDING

    @classmethod
    def can_confirm(cls, status: FindingStatus) -> bool:
        """
        Check if a finding status can be considered "confirmed"
        for display purposes.

        Args:
            status: FindingStatus to check

        Returns:
            True for CONFIRMED and UNCONFIRMED, False otherwise
        """
        return status in (FindingStatus.CONFIRMED, FindingStatus.UNCONFIRMED)

    @classmethod
    def requires_review(cls, status: FindingStatus) -> bool:
        """
        Check if a finding requires manual review.

        Args:
            status: FindingStatus to check

        Returns:
            True for CONFLICTED only
        """
        return status == FindingStatus.CONFLICTED

    @classmethod
    def is_valid_transition(
        cls, from_status: FindingStatus, to_status: FindingStatus
    ) -> bool:
        """
        Check if a state transition is valid.

        Valid transitions:
        - PENDING -> UNCONFIRMED
        - UNCONFIRMED -> CONFIRMED, CONFLICTED
        - CONFIRMED -> CONFLICTED
        - CONFLICTED -> {} (terminal, always false)

        Args:
            from_status: Starting status
            to_status: Target status

        Returns:
            True if transition is valid, False otherwise
        """
        valid_targets = cls.VALID_TRANSITIONS.get(from_status, set())
        return to_status in valid_targets

    @staticmethod
    def _detect_conflict(sources: list[FindingSource]) -> bool:
        """
        Detect if sources conflict (threat vs safe disagreement).

        A conflict occurs when one source indicates a threat
        (CRITICAL/HIGH/MEDIUM/LOW) and another indicates safe (INFO).

        Args:
            sources: List of finding sources to check

        Returns:
            True if conflict detected, False otherwise
        """
        # Map severity to boolean: threat=True, safe=False
        def is_threat(severity: str) -> bool:
            if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                return True
            return False  # INFO or unknown = safe

        # Check all pairs for disagreement
        has_threat = False
        has_safe = False

        for source in sources:
            if is_threat(source.severity):
                has_threat = True
            else:
                has_safe = True

        # Conflict if we have both opinions
        return has_threat and has_safe
