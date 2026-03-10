# Phase 13 Plan 05: Darknet Pipeline Wiring Summary

## One-liner
Added `use_tor` parameter to StealthScout with SOCKS5 proxy routing, wired scout_node to read `enable_tor` from tier config, and fixed darknet_correlation handler to use `analyze_with_details()`.

## What was changed

### Task 1: TOR routing in Scout
- Added `use_tor: bool = False` to `StealthScout.__init__()` parameters
- Added SOCKS5 proxy configuration in `__aenter__()` when `use_tor=True`
- Graceful degradation: logs warning on failure, continues without TOR
- Settings reads `TOR_SOCKS_HOST` and `TOR_SOCKS_PORT` from settings

Updated `veritas/core/nodes/scout.py`:
- Reads `enable_tor` from `tier_config` (comes from AUDIT_TIERS)
- Passes `use_tor=use_tor` to `StealthScout()`
- `darknet_investigation` tier now has `enable_tor: True` in AUDIT_TIERS

### Task 2: Darknet Security Modules
Fixed `security_node()` darknet_correlation handler:
- Changed from `analyzer.analyze()` (returns list of findings) to `analyzer.analyze_with_details()` (returns `DarknetAnalysisResult` with `.to_dict()`)
- Properly passes `page_content` from scout results
- Returns proper dict for the security results

## Files Modified
- `veritas/agents/scout.py` (added use_tor parameter + SOCKS5 proxy setup)
- `veritas/core/nodes/scout.py` (added tier_config reading and use_tor passing)
- `veritas/core/nodes/security.py` (fixed darknet_correlation handler)

## Commit
`d7890ab` - feat(13-05): wire darknet pipeline

## Test Results
All 91 tests still pass after changes.

## Deviations from Plan
- [Rule 1 - Bug] Fixed darknet_correlation handler: `analyze()` returns list not dict, so `analyze_with_details()` is the correct method to call for a dict result

## Self-Check: PASSED
