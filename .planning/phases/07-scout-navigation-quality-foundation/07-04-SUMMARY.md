---
phase: "07"
plan: "04"
subsystem: "Quality Foundation"
tags:
  - quality
  - consensus
  - confidence-scoring
  - validation-state-machine
dependency_graph:
  requires:
    - "07-03: Quality Foundation - Consensus Engine"
  provides:
    - "ConsensusResult with explainable confidence breakdowns"
    - "ConfidenceScorer for human-readable confidence formatting"
    - "ValidationStateMachine for state transition enforcement"
  affects:
    - "vision, osint, security agent consensus aggregation"
tech-stack:
  added:
    - "ConfidenceScorer class in veritas/quality/confidence_scorer.py"
    - "ValidationStateMachine class in veritas/quality/validation_state.py"
  patterns:
    - "State machine pattern for finding status transitions"
    - "Tier classification using boundary-based scoring"
key-files:
  created:
    - "veritas/quality/confidence_scorer.py"
    - "veritas/quality/validation_state.py"
    - "tests/test_consensus_engine.py"
  modified:
    - "veritas/quality/__init__.py"
decisions:
  - "SCORE_RANGES constant with 5 tiers for explainable confidence classification"
  - "format_confidence() returns human-readable format like '87%: 3 sources agree, high severity'"
  - "get_confidence_tier() uses boundary-based classification (>=75, >=50, >=40, >=20, <20)"
  - "ValidationStateMachine.transition() checks conflicts before counting agents"
  - "is_valid_transition() enforces correct state graph (PENDING->{UNCONFIRMED}, UNCONFIRMED->{CONFIRMED,CONFLICTED}, CONFIRMED->{CONFLICTED})"
  - "can_confirm() returns True for CONFIRMED and UNCONFIRMED statuses"
  - "requires_review() returns True for CONFLICTED only"
metrics:
  duration_minutes: 11
  started: "2026-02-26T10:55:04Z"
  completed: "2026-02-26T11:06:03Z"
---

# Phase 07 Plan 04: Quality Foundation - Confidence Scoring & Validation Summary

Confidence scoring tier classification with human-readable formatting and state machine enforcement for finding status transitions.

## Deviations from Plan

None - plan executed exactly as written.

## Tasks Completed

### Task 1: Create ValidationStateMachine and ConfidenceScorer classes
**Commit:** `4a37b19`

Created two new classes to complete the quality foundation:

1. **ConfidenceScorer** (`veritas/quality/confidence_scorer.py`):
   - SCORE_RANGES constant with 5 tiers (high_confidence, medium_confidence, unconfirmed_high, unconfirmed_medium, low_confidence)
   - format_confidence() returns human-readable format like "87%: 3 sources agree, high severity"
   - get_confidence_tier() returns tier key based on score boundaries (>=75, >=50, >=40, >=20, <20)

2. **ValidationStateMachine** (`veritas/quality/validation_state.py`):
   - transition() method checks conflicts (threat vs safe) before counting agents
   - Transition logic: CONFLICTED if threat+safe, CONFIRMED if >=min_sources, UNCONFIRMED if >=1
   - can_confirm() returns True for CONFIRMED and UNCONFIRMED
   - requires_review() returns True for CONFLICTED only
   - is_valid_transition() enforces correct state transition graph:
     - PENDING -> {UNCONFIRMED}
     - UNCONFIRMED -> {CONFIRMED, CONFLICTED}
     - CONFIRMED -> {CONFLICTED}
     - CONFLICTED -> {} (terminal)

3. **Export updates** (`veritas/quality/__init__.py`):
   - Added ConfidenceScorer and ValidationStateMachine to public API

### Task 2: Create tests for consensus engine and quality foundation
**Commit:** `bf2ed3d`

Created comprehensive test suite with 32 test functions covering:

- FindingStatus enum and FindingSource dataclass verification
- Two-source confirmation (CONFIRMED status with >=75% confidence)
- Three-source high confidence verification
- Single-source UNCONFIRMED status (<50% confidence)
- Single-source medium severity confidence (20%-50% range)
- Conflict detection (threat vs safe -> CONFLICTED)
- Confidence breakdown explainability (source_agreement, severity_factor, context_confidence, source_count)
- Distinct agent counting (same agent_type doesn't double-count)
- Confidence tier classification (5 tiers with correct boundaries)
- Validation state transitions (PENDING->UNCONFIRMED->CONFIRMED/CONFLICTED)
- Filtering methods (get_confirmed_findings, get_conflicted_findings)
- Helper methods (can_confirm, requires_review, is_valid_transition)

All 32 tests pass.

### Task 3: Update main phase plan to include Plan 07-04
**Commit:** N/A (no changes needed - PLAN.md was already correctly set up)

PLAN.md already contained:
- Plan 07-04 in Wave 2
- Dependencies correctly set (07-04 depends on 07-03)
- All requirements covered (QUAL-01, QUAL-02, QUAL-03 mapped to 7.3 and 7.4)
- Plan count of 4

## Files Modified

### Created
- `veritas/quality/confidence_scorer.py` (84 lines)
- `veritas/quality/validation_state.py` (134 lines)
- `tests/test_consensus_engine.py` (447 lines)

### Modified
- `veritas/quality/__init__.py` (added ConfidenceScorer, ValidationStateMachine exports)

## Quality Gate Results

- [x] All tests in test_consensus_engine.py pass (32/32)
- [x] ConsensusEngine produces correct FindingStatus for all input scenarios
- [x] ConfidenceScorer produces explainable breakdowns
- [x] ValidationStateMachine enforces correct state transitions
- [x] Conflict detection works correctly (threat vs safe)
- [x] Distinct agent counting works correctly (same agent doesn't double-count)
- [x] Confidence thresholds match CONTEXT.md specifications
- [x] Package exports work correctly from veritas.quality namespace

## Requirements Satisfied

- **QUAL-01**: False positive detection criteria with multi-factor validation (2+ sources for CONFIRMED)
  - ValidationStateMachine.transition() ensures 2+ distinct sources before CONFIRMED
  - Conflict detection prevents false positives from disagreeing agents

- **QUAL-02**: Deep statistics and confidence scoring with explainable factors
  - ConfidenceScorer.format_confidence() provides human-readable format
  - Confidence breakdown includes: source_agreement (60%), severity_factor (25%), context_confidence (15%), source_count

- **QUAL-03**: Incremental verification and refinement with state transitions
  - ValidationStateMachine manages PENDING -> UNCONFIRMED -> CONFIRMED progression
  - is_valid_transition() enforces legal state changes
  - can_confirm() and requires_review() identify actionable states

## Key Decisions

1. **Boundary-based tier classification**: get_confidence_tier() uses >= boundaries (>=75, >=50, >=40, >=20, <20) for clear, unambiguous classification

2. **Human-readable format**: format_confidence() combines percentage with description like "87%: 3 sources agree, high severity" for explainability

3. **Conflict-first transition**: ValidationStateMachine.transition() checks conflicts BEFORE counting agents, preventing misleading CONFIRMED status when agents disagree

4. **Terminal CONFLICTED state**: No valid transitions from CONFLICTED, ensuring manual review is required for conflicted findings

5. **Can-confirm semantics**: can_confirm() returns True for both CONFIRMED and UNCONFIRMED, allowing display of findings that have some source support even if below threshold

## Next Steps

Phase 7 quality foundation is complete. The system now has:
- Multi-source consensus validation (Plan 07-03)
- Explainable confidence scoring (Plan 07-04)
- State machine enforcement for finding status (Plan 07-04)

Remaining Phase 7 work:
- Plan 07-01: Intelligent Scrolling with Lazy-Load Detection (pending)
- Plan 07-02: Multi-Page Exploration (pending)
- Review and finalize Phase 7 implementation
- Prepare for Phase 8 (next phase in roadmap)
