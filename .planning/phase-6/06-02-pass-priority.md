---
id: 06-02
phase: 6
wave: 2
autonomous: true

objective: Implement pass priority logic to skip unnecessary VLM passes based on findings and cost/benefit analysis.

files_modified:
  - veritas/agents/vision.py

tasks:
  - Define VisionPassPriority enum (CRITICAL, CONDITIONAL, EXPENSIVE)
  - Implement should_run_pass() logic for each pass
  - Test pass skipping behavior with mock prior findings

has_summary: false
gap_closure: false
---

# Plan 06-02: Pass Priority Logic

**Goal:** Skip expensive VLM passes when safe - reducing GPU costs by 3-5x through intelligent pass prioritization.

## Context

Not all 5 passes need to run on every page. Pass priority logic enables conditional execution:
- **CRITICAL:** Always run (Pass 1: quick threat, Pass 5: synthesis)
- **CONDITIONAL:** Run only if prior findings exist (Pass 2: dark patterns, Pass 4: cross-reference)
- **EXPENSIVE:** Run only if temporal changes detected (Pass 3: temporal dynamics)

## Implementation

### Task 1: Define pass priority enum

**File:** `veritas/agents/vision.py`

```python
class VisionPassPriority(enum.Enum):
    CRITICAL = 1      # Always run: Pass 1 (quick threat), Pass 5 (final synthesis)
    CONDITIONAL = 2   # Run if prior findings: Pass 2 (dark patterns), Pass 4 (cross-reference)
    EXPENSIVE = 3     # Run only if temporal changes: Pass 3 (temporal dynamics)
```

### Task 2: Implement pass skipping logic

**File:** `veritas/agents/vision.py`

```python
def should_run_pass(pass_num: int, prior_findings: List[Finding], has_temporal_changes: bool) -> bool:
    """Determine if pass should execute based on cost/benefit."""
    pass_priority = {
        1: VisionPassPriority.CRITICAL,
        2: VisionPassPriority.CONDITIONAL,
        3: VisionPassPriority.EXPENSIVE,
        4: VisionPassPriority.CONDITIONAL,
        5: VisionPassPriority.CRITICAL
    }[pass_num]

    if pass_priority == VisionPassPriority.CRITICAL:
        return True
    elif pass_priority == VisionPassPriority.CONDITIONAL:
        return len(prior_findings) > 0
    elif pass_priority == VisionPassPriority.EXPENSIVE:
        return has_temporal_changes
    return True
```

## Success Criteria

1. ✅ Pass 1 and 5 always execute
2. ✅ Pass 2 and 4 skip when no prior findings
3. ✅ Pass 3 skips when no temporal changes
4. ✅ Unit tests verify pass skipping behavior

## Dependencies

- Requires: 06-01 (VLM Caching) - cache key must exist for skipping to work
