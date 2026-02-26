---
phase: 07
plan: 03
subsystem: Quality Foundation
tags:
  - quality
  - consensus
  - false-positive-prevention
  - multi-factor-validation
dependency-graph:
  requires:
    - "05-Scout Navigation Foundation"
    - "06-Vision Agent Enhancement"
  provides:
    - "07-04: Confidence Scorer and Validation State Machine"
    - "08-Quality Assurance"
  affects:
    - "VisionAgent"
    - "SecurityAgent"
    - "OSINTAgent"
tech-stack:
  added:
    - "ConsensusEngine: Multi-source finding aggregation"
    - "FindingStatus: Enum for verification states"
    - "FindingSource: Dataclass for agent source tracking"
    - "ConsensusResult: Dataclass for consensus results"
  patterns:
    - "State machine pattern for finding verification"
    - "Conflict detection for inconsistent findings"
    - "Weighted scoring with explainable breakdowns"
key-files:
  created:
    - "veritas/quality/consensus_engine.py: ConsensusEngine class"
    - "veritas/quality/__init__.py: Module exports"
  modified:
    - "veritas/core/types.py: Added FindingStatus, FindingSource, ConsensusResult"
decisions: []
metrics:
  duration: 8 minutes
  tasks: 2
  files: 3
  completed_date: 2026-02-26
---

# Phase 7 Plan 03: Quality Foundation - Consensus Engine Summary

Multi-source consensus engine with conflict detection and explainable confidence scoring for false positive prevention.

## Implementation Summary

Implemented `ConsensusEngine` with multi-factor validation across Vision, OSINT, and Security agents. The system requires 2+ distinct agent types to corroborate findings before confirming them as threats, preventing solo-source false positives. Single-source findings are automatically downgraded to "unconfirmed" status with capped confidence (<50%).

### Core Components

**FindingStatus Enum** (`veritas/core/types.py`):
- `UNCONFIRMED`: Single source, <50% confidence
- `CONFIRMED`: 2+ sources, >=50% confidence
- `CONFLICTED`: Sources disagree (threat vs safe)
- `PENDING`: Insufficient data

**FindingSource Dataclass** (`veritas/core/types.py`):
- Tracks agent_type (vision, osint, security)
- Stores finding_id, severity, confidence (0.0-1.0)
- Auto-generates ISO timestamp with default_factory

**ConsensusResult Dataclass** (`veritas/core/types.py`):
- finding_key: Normalized finding signature
- sources: List of FindingSource objects
- status: Current FindingStatus
- aggregated_confidence: Computed score (0-100)
- conflict_notes: Descriptions of conflicts detected
- confidence_breakdown: Explainable scoring factors

**ConsensusEngine Class** (`veritas/quality/consensus_engine.py`):
- `__init__(min_sources=2)`: Configure consensus threshold
- `add_finding()`: Incrementally add findings and update consensus
- `_detect_conflict()`: Detect threat vs safe disagreements
- `_compute_confidence()`: Weighted scoring (60% agreement, 25% severity, 15% context)
- `get_result()`: Retrieve consensus result by key
- `get_confirmed_findings()`: Filter confirmed findings
- `get_conflicted_findings()`: Filter conflicted findings

### Key Features

**Multi-Factor Validation**:
- Source agreement weight: 60%
- Finding severity weight: 25%
- Contextual confidence weight: 15%

**Conflict Detection**:
- Detects when one agent flags threat while another flags safe
- Sets status to CONFLICTED with descriptive conflict_notes
- Threat severities: CRITICAL, HIGH, MEDIUM, LOW
- Safe severity: INFO

**Threshold Enforcement** (per CONTEXT.md):
- 2+ sources + high severity: 75.0-100.0 range (minimum 75.0)
- 2+ sources + medium severity: 50.0-75.0 range
- 1 source + high severity: 40.0-60.0 range (capped at 49.0)
- 1 source + medium severity: 20.0-40.0 range (capped at 49.0)

**Distinct Agent Counting**:
- Uses set of agent_type for consensus counting
- Multiple findings from same agent do not double-count toward consensus
- Prevents gaming of consensus threshold

**Explainable Confidence**:
- confidence_breakdown dict provides full audit trail
- Shows source_agreement, severity_factor, context_confidence, source_count
- Format: "87.5%: 2 sources agree, high severity (CRITICAL)"

## Deviations from Plan

None - plan executed exactly as written.

## Testing and Verification

All verification criteria met:

- [x] FindingStatus enum exists with all 4 values
- [x] FindingStatus inherits from str (class FindingStatus(str, Enum))
- [x] FindingSource dataclass exists with all 5 fields
- [x] FindingSource.timestamp has default factory generating ISO timestamp
- [x] ConsensusResult dataclass exists with all 6 fields
- [x] List fields use field(default_factory=list)
- [x] Dict field uses field(default_factory=dict)
- [x] ConsensusEngine class exists with all 7 methods
- [x] Conflict detection happens BEFORE source addition
- [x] _detect_conflict() returns True for threat vs safe combinations
- [x] _compute_confidence() calculates weighted score with correct factors
- [x] CONTEXT.md thresholds applied correctly
- [x] confidence_breakdown dict populated with all 4 keys
- [x] get_confirmed_findings() and get_conflicted_findings() filter correctly
- [x] Single-source confidence capped at 49.0 (<50%)

### Test Results

Quick verification test (test_consensus_engine.py) passed all 12 test cases:

- FindingStatus enum: PASS
- FindingSource ISO timestamp: PASS
- ConsensusResult dataclass: PASS
- Single source UNCONFIRMED with 49.0% confidence: PASS
- Multi-source CONFIRMED with 98.1% confidence: PASS
- Conflict detection: PASS
- Distinct agent counting: PASS
- Confidence breakdown populated: PASS
- get_confirmed_findings()/conflicted_findings() filtering: PASS
- 2+ high severity threshold (>=75%): PASS
- 2+ medium severity threshold (50-75%): PASS
- 1 source high severity threshold (40-49%): PASS
- 1 source medium severity threshold (20-49%): PASS

## Quality Assurance

- All data structures properly typed with dataclasses
- Methods have proper type hints and docstrings
- ISO timestamp handling with timezone.utc
- Conflict detection prevents ambiguous findings
- Distinct agent counting enforces true multi-source consensus
- Confidence thresholds match CONTEXT.md specifications exactly
- confidence_breakdown provides full audit trail

## Integration Points

**Dependencies**:
- Requires veritas/core/types.py for base data structures
- ConsensusEngine ready for integration with VisionAgent, SecurityAgent, OSINTAgent

**Provides for Next Phase**:
- 07-04: Confidence Scorer and Validation State Machine will build on this foundation
- ConsensusEngine ready for VisionAgent integration (finding aggregation)

## Files Changed

**Created**:
- `veritas/quality/consensus_engine.py` (282 lines): ConsensusEngine class with all methods
- `veritas/quality/__init__.py` (19 lines): Module exports

**Modified**:
- `veritas/core/types.py` (55 lines added): FindingStatus, FindingSource, ConsensusResult

## Commits

1. `8e52759`: feat(07-03): add quality foundation data structures
2. `7152121`: feat(07-03): implement ConsensusEngine for multi-source finding validation

## Self-Check: PASSED

All claims verified:
- veritas/quality/consensus_engine.py: FOUND
- veritas/quality/__init__.py: FOUND
- 07-03-SUMMARY.md: FOUND
- Commit 8e52759: FOUND
- Commit 7152121: FOUND
