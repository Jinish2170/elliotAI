# Phase 13 Plan 07: Integration Tests Summary

## One-liner
Created veritas/tests/integration/ package with tier workflow configuration tests and data flow verification tests covering all 4 audit tiers and the Scout-to-Security data pipeline.

## What was changed

### New files created
- `veritas/tests/integration/__init__.py`: empty package init
- `veritas/tests/integration/conftest.py`: fixtures for `base_audit_state` and `mock_scout_result_dict`
- `veritas/tests/integration/test_tier_workflows.py`: 7 tests verifying AUDIT_TIERS behavioral budgets
- `veritas/tests/integration/test_data_flow.py`: 4 tests verifying Scout data flows correctly

### Test coverage
**test_tier_workflows.py:**
- All tiers have `max_verifications`, `enable_tavily`, `vision_passes`
- `quick_scan`: max_verifications=0, enable_tavily=False, enable_osint=False, vision_passes=1, graph_timeout≤20
- `deep_forensic`: max_verifications≥15, enable_tavily=True, vision_passes=5
- `darknet_investigation`: enable_tor=True, enable_darknet=True
- Parametrized test: darknet_correlation module only in darknet_investigation tier
- Vision passes increase monotonically: quick < standard ≤ deep

**test_data_flow.py:**
- Scout result has real page_content (not fabricated HTML pattern)
- Scout result has real response_headers (not hardcoded stub)
- Security node receives real HTML from Scout state
- All required Scout output fields present in result dict

## Files Created
- `veritas/tests/integration/__init__.py`
- `veritas/tests/integration/conftest.py`
- `veritas/tests/integration/test_tier_workflows.py`
- `veritas/tests/integration/test_data_flow.py`

## Commit
`7d2f2b2` - feat(13-07): add integration tests for tier workflows and data flow

## Test Results
13/13 integration tests pass.
104/104 total tests pass (unit + settings + integration).

## Deviations from Plan
None - plan executed exactly as written.

## Self-Check: PASSED
