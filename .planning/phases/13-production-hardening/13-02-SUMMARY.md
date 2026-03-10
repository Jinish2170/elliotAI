# Phase 13 Plan 02: Tier-Aware Nodes Summary

## One-liner
Added behavioral budgets (vision_passes, graph_timeout_s, enable_tavily, etc.) to all 4 AUDIT_TIERS and made graph_node and vision_node read from tier config instead of hardcoded values.

## What was changed

### Task 1: AUDIT_TIERS in `veritas/config/settings.py`
Added to all tiers:
- `max_verifications`: 0/10/15/20 per tier
- `enable_tavily`: False for quick_scan, True for others
- `enable_osint`: False for quick_scan, True for others
- `graph_timeout_s`: 15/60/90/120 per tier
- `vision_passes`: 1/3/5/5 per tier
- `target_duration_s`: 30/120/300/600 per tier
- `enable_osint_deep` and `enable_tor`/`enable_darknet` for deep/darknet tiers

### Task 2: Tier-aware nodes in `veritas/core/orchestrator.py`
- `vision_node()`: replaced `{"quick_scan": 1, "standard_audit": 3}.get(audit_tier, 5)` with `tier_config.get("vision_passes", 3)`
- `graph_node()`: replaced hardcoded `GRAPH_PHASE_TIMEOUT_S` with `tier_config.get("graph_timeout_s", 90)`
- `graph_node()`: added quick_scan branch that passes empty text/links to skip Tavily

## Files Modified
- `veritas/config/settings.py`
- `veritas/core/orchestrator.py`

## Commit
`36eb65c` - feat(13-02): add tier budgets to AUDIT_TIERS and make nodes tier-aware

## Deviations from Plan
- `judge_node()` tier-awareness skipped because `JudgeAgent.analyze()` doesn't accept `audit_tier` parameter (per plan instructions: "if not, just skip this").

## Self-Check: PASSED
