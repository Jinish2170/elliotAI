# Phase 13 Plan 03: Fix Broken Tests Summary

## One-liner
Fixed 7 onion detector test cases with correct V2/V3 address lengths, updated AUDIT_TIERS count assertion from 3 to 4, and consolidated TORClient with full implementation in core/tor_client.py.

## What was changed

### Task 1: OnionDetector test data in `elliot/tests/unit/test_onion_detector.py`
Fixed all 7 failing tests by using correct address lengths:
- `test_pattern_v3_matches_56_char`: Changed 40-char address to valid 56-char
- `test_validate_onion_v2_valid`: Removed invalid 26-char address from valid_urls list
- `test_validate_onion_v3_valid`: Changed 66-char to 56-char address
- `test_detect_onion_urls_single_v3`: Changed 66-char to 56-char address
- `test_detect_onion_urls_multiple`: Replaced invalid short addresses with 4 valid 16-char v2 addresses
- `test_is_darknet_url_v3`: Changed 66-char to 56-char address
- `test_detect_onion_urls_with_special_chars`: Replaced invalid short addresses with 3 valid 16-char v2 addresses

### Task 2: Fix test_audit_tiers in `elliot/tests/test_elliot.py`
Changed `assert len(settings.AUDIT_TIERS) == 3` to `== 4`

### Task 3: Consolidate TORClient
- Moved full `TORClient` async HTTP client implementation to `elliot/core/tor_client.py` (canonical location)
- `elliot/darknet/tor_client.py` now just re-exports: `from elliot.core.tor_client import TORClient`

## Files Modified
- `elliot/tests/unit/test_onion_detector.py`
- `elliot/tests/test_elliot.py`
- `elliot/core/tor_client.py`
- `elliot/darknet/tor_client.py`

## Commit
`c1f9e9f` - fix(13-03): fix onion detector tests, update audit_tiers count, consolidate TORClient

## Test Results
All 31 tests in test_onion_detector.py pass. TestSettings::test_audit_tiers passes.

## Deviations from Plan
None - plan executed exactly as written.

## Self-Check: PASSED
