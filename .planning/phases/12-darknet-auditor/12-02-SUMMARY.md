---
phase: 12
plan: 02
slug: darknet-onion-detection
title: "Phase 12 Plan 02: Darknet Onion Detection"
subsystem: darknet-auditor
tags: [osint, ioc, onion, threat-intelligence, darknet]
created: 2026-03-01
completed: 2026-03-01
duration_minutes: 64

requires:
  - tor_client.py (from veritas/core/)
provides:
  - veritas/osint/ioc_detector.py (IOC detection with onion support)
  - veritas/agents/scout.py (enhanced with IOC detection)
  - IOC detection tests (32 tests)
  - Scout IOC integration tests (10 tests)

tech-stack:
  added:
    - veritas.osint.ioc_detector module
    - IOCIndicator, IOCDetectionResult dataclasses
    - Onion address regex patterns (V2/V3)
  patterns:
    - Dataclass-based result structures
    - Async content scanning
    - Trust score modifier pattern from scout.py

key-files:
  created:
    - veritas/osint/__init__.py
    - veritas/osint/ioc_detector.py (700 lines)
    - veritas/tests/test_ioc_detector.py (500 lines)
    - veritas/tests/test_scout_ioc_integration.py (250 lines)
  modified:
    - veritas/agents/scout.py (+150 lines)

decisions:
  - Use negative lookahead/lookbehind for onion regex (instead of word boundaries) to match in HTML context
  - Use(parsed.hostname for port handling in onion URL detection)
  - Trust modifier of -0.3 for .onion detection (significant risk signal)
  - Graceful degradation when IOC detector unavailable (backward compatibility)
  - Limit IOC indicators to 20 for main result, 10 for subpage to prevent huge payloads

metrics:
  tests_added: 42 (32 IOC detector + 10 scout integration)
  tests_passing: 42
  code_coverage: IOC detector (100% of public API)
  duration: ~64 minutes
---

# Phase 12 Plan 02: Darknet Onion Detection Summary

Implemented comprehensive Indicators of Compromise (IOC) detection with .onion address support for VERITAS darknet auditing capabilities.

## One-liner
Implemented IOC detection module with onion address identification (V2/V3), IP address detection, and hash detection (MD5/SHA1/SHA256/SHA512), integrated into Scout agent with trust score modifiers for darknet connection signals.

## Tasks Completed

### Task 1: Create IOC Detector Module
- **File:** `veritas/osint/ioc_detector.py`
- **Implementations:**
  - `IOCDetector` class for threat intelligence scanning
  - `IOCIndicator` dataclass (type, value, severity, confidence, context)
  - `IOCDetectionResult` class (found flag, indicators list, severity tracking)
  - `detect_url()` - analyze single URL for IOCs
  - `async detect_content()` - scan page content and links
  - `is_onion_url()` - static convenience check
  - `detect_onion_addresses()` - async convenience for extracting onions
- **IOC Types Supported:**
  - `ONION_ADDRESS` - V3 (56 chars)/V2 (16 chars) addresses
  - `IP_ADDRESS` - IPv4 addresses
  - `HASH` - MD5, SHA1, SHA256, SHA512 file hashes
- **Tests:** 32 unit/integration tests covering all functionality
- **Commit:** `921b1fc`

### Task 2: Integrate IOC Detection into Scout Agent
- **File:** `veritas/agents/scout.py`
- **Changes:**
  - Added IOC fields to `ScoutResult`:
    - `ioc_detected` (bool) - any threat indicators found
    - `ioc_indicators` (list[dict]) - detected IOCs
    - `onion_detected` (bool) - .onion addresses present
    - `onion_addresses` (list[str]) - list of onion addresses
  - Imported and instantiated `IOCDetector` in `StealthScout.__init__()`
  - Added IOC scanning to `investigate()` method (after form validation)
  - Added IOC scanning to `navigate_subpage()` method
  - Trust modifier: -0.3 for onion detection
  - Trust notes: descriptive messages about .onion findings
  - Graceful fallback when IOC detector unavailable
- **Tests:** 10 integration tests
- **Commit:** `8f70689`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed regex word boundary issue for .onion addresses**
- **Found during:** IOC detector testing
- **Issue:** Original pattern `\b[a-z2-7]{56}\.onion\b` failed to match .onion addresses in URLs and HTML attributes due to word boundary conflicts with `http://` and HTML quote characters
- **Fix:** Changed to negative lookahead/lookbehind pattern `(?<![a-zA-Z0-9-])[a-z2-7]{56}\.onion(?![a-zA-Z0-9-])` for robust matching
- **Files modified:** `veritas/osint/ioc_detector.py`
- **Commit:** `921b1fc`

**2. [Rule 1 - Bug] Fixed port handling in onion URL detection**
- **Found during:** `test_detect_onion_with_port` test
- **Issue:** `_is_onion_url()` used `parsed.netloc` which includes port (`domain.onion:8080`), causing `endswith(".onion")` check to fail
- **Fix:** Changed to use `parsed.hostname` which automatically strips the port
- **Files modified:** `veritas/osint/ioc_detector.py`
- **Commit:** `921b1fc`

**3. [Rule 3 - Critical] Fixed import path for IOC detector in scout.py**
- **Found during:** `test_init_creates_ioc_detector` test
- **Issue:** Import `from osint.ioc_detector import IOCDetector` created circular import issues and type mismatch
- **Fix Changed to `from veritas.osint.ioc_detector import IOCDetector` with proper import order
- **Files modified:** `veritas/agents/scout.py`
- **Commit:** `8f70689`

**4. [Rule 3 - Critical] Fixed test onion string lengths**
- **Found during:** Initial test runs
- **Issue:** Test onion strings were 42/47/58 characters instead of required exactly 56 for V3 onions
- **Fix:** Updated all test onions to exactly 56 characters using `a` and `b` repeated patterns
- **Files modified:** `veritas/tests/test_ioc_detector.py`
- **Commit:** `921b1fc`

## Testing Coverage

- **IOC Detector Tests:** 32 tests passing
  - Onion address detection (V2, V3, HTTPS, port handling)
  - In-content detection (HTML, links, multiple onions)
  - IP address detection
  - Hash detection (MD5, SHA1, SHA256, SHA512)
  - Edge cases (empty content, None, malformed URLs, case sensitivity)
  - Integration (full HTML scan, combined detection)

- **Scout IOC Integration Tests:** 10 tests passing
  - ScoutResult field validation (ioc_detected, ioc_indicators, onion_detected, onion_addresses)
  - Serialization compatibility
  - Detector initialization
  - Trust score impact
  - Backward compatibility (old ScoutResult creation still works)

## Key Decisions

1. **Regex Pattern Choice:** Used negative lookahead/lookbehind instead of word boundaries to ensure .onion addresses are detected in URLs and HTML attributes.

2. **Trust Score Impact:** Onion detection triggers -0.3 trust modifier (significant reduction) reflecting darknet connection as high-risk signal.

3. **Graceful Degradation:** IOC detector import failure is caught and logged, allowing scout to continue without threat intelligence features.

4. **Payload Size Limits:** Limited IOC indicators to 20 for main results and 10 for subpages to prevent enormous response payloads.

## Code Quality

- **Documentation:** Comprehensive docstrings for all classes and methods
- **Type Safety:** Full type hints using Python 3.11+ syntax
- **Error Handling:** Try-catch blocks for all IOC detection operations
- **Logging:** Debug and info level logging for detection results
- **Testing:** 100% public API coverage with 42 tests

## Integration

- **Scout Agent:** New IOC fields added with default values for backward compatibility
- **Existing Code:** No breaking changes to existing ScoutResult usage
- **Core Module:** `veritas/core/tor_client.py` exists as stub for future integration

## Next Steps

Potential future enhancements:
- Integrate with existing `veritas/core/tor_client.py` for live .onion browsing
- Add additional IOC types (email addresses, phone numbers, cryptocurrency addresses)
- Implement IOC reputation scoring using threat intelligence feeds
- Add darknet marketplace monitoring features
- Deep web analysis support beyond .onion (i2p, freifunk, etc.)

## Auth Gates

None encountered during implementation. Local testing did not require external services.

---

## Self-Check: PASSED

**Created Files:**
- [x] `veritas/osint/__init__.py` - Module marker and exports
- [x] `veritas/osint/ioc_detector.py` - IOC detection implementation (700 lines)
- [x] `veritas/tests/test_ioc_detector.py` - IOC detector tests (500 lines)
- [x] `veritas/tests/test_scout_ioc_integration.py` - Scout integration tests (250 lines)

**Modified Files:**
- [x] `veritas/agents/scout.py` - Added IOC detection integration (+150 lines)

**Commits Verified:**
- [x] `921b1fc` - IOC detector implementation
- [x] `8f70689` - Scout IOC integration

**Tests Passing:**
- [x] 32 IOC detector tests passing
- [x] 10 Scout IOC integration tests passing
- [x] 20 existing veritas tests still passing

---

**Duration:** ~64 minutes
**Date Completed:** 2026-03-01T07:57:29Z
