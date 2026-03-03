---
phase: 7
plan: 1
subsystem: Scout Navigation
tags: [scroll-orchestration, lazy-load-detection, mutation-observer]
dependency_requires:
  - []
dependency_provides:
  - [02-multi-page-exploration]
  - [03-quality-foundation]
dependency_affects:
  - [vision-agent-analysis]
tech_stack:
  added:
    - "playwright.async_api (existing)"
    - "LazyLoadDetector"
    - "ScrollOrchestrator"
    - "ScrollState/ScrollResult dataclasses"
  patterns:
    - "MutationObserver for DOM change tracking"
    - "Incremental scroll with stabilization detection"
    - "Screenshot capture at scroll intervals"
key_files:
  created:
    - veritas/agents/scout_nav/lazy_load_detector.py
    - veritas/agents/scout_nav/scroll_orchestrator.py
    - veritas/agents/scout_nav/__init__.py
    - tests/test_scroll_orchestrator.py
    - tests/__init__.py
  modified:
    - veritas/core/types.py
    - veritas/agents/scout.py
decisions:
  - "07-01 Scrolled Screenshot Naming (2026-02-26): Used cycle-based naming {audit_id}_scroll_{cycle:02d}.jpg"
  - "07-01 Scroll Termination Logic (2026-02-26): Stop when 2 consecutive cycles have no new content OR max 15 cycles"
  - "07-01 Detection Signal Priority (2026-02-26): Use bothSignals (mutations AND scroll height change) for strongest lazy-load signal"
  - "07-01 Module Directory Naming (2026-02-26): Renamed scout/ to scout_nav/ to avoid conflict with existing scout.py module"
metrics:
  duration: 8 minutes
  completed_date: 2026-02-26T08:16:00Z
---

# Phase 7 Plan 1: Intelligent Scrolling with Lazy-Load Detection Summary

## One-Liner
Incremental scroll orchestration with MutationObserver-based lazy-load detection, capturing screenshots at scroll intervals for complete temporal page capture.

## Overview

Implemented intelligent scrolling capability for Scout agent to capture lazy-loaded content. The ScrollOrchestrator performs incremental scrolling (page height/2 per chunk) with configurable 400ms wait times, monitoring DOM changes via MutationObserver to detect new content and determine when pages have stabilized.

## Implementation Details

### 1. Scroll State Tracking (Task 1)

Created data structures for scroll state management:

**ScrollState:** Tracks per-cycle scroll metrics
- cycle: Current cycle number (0-indexed)
- has_lazy_load: Whether new content was detected
- last_scroll_y/last_scroll_height: Scroll position and page height
- cycles_without_content: Consecutive cycles without new content
- stabilized: Whether page has reached stable state

**ScrollResult:** Aggregates complete scroll session data
- total_cycles: Number of scroll cycles completed
- stabilized: Whether termination was due to stabilization
- lazy_load_detected: Whether lazy-loading was ever detected
- screenshots_captured: Number of screenshots taken
- scroll_states: Full history of ScrollState objects

### 2. LazyLoadDetector (Task 1)

MutationObserver-based DOM change tracking with three detection signals:
- hasMutations: True if DOM additions occurred
- scrollHeightChanged: True if document.scrollHeight changed
- bothSignals: True if BOTH mutations AND scroll height change (strongest indicator)

JavaScript injection creates `window.__lazyLoadDetector` object with:
- bufferMutations(): Accumulates MutationObserver records
- reset(): Clears mutation buffer and updates scroll height baseline
- hasNewContent(): Returns all three detection signals

### 3. ScrollOrchestrator (Task 2)

Intelligent scroll orchestration with configurable parameters:
- MAX_SCROLL_CYCLES: 15 (prevents infinite loops)
- STABILIZATION_THRESHOLD: 2 (consecutive cycles without new content)
- SCROLL_CHUNK_RATIO: 0.5 (scroll by half viewport height per cycle)
- SCROLL_WAIT_MS: 400 (wait time for lazy loading)

Scroll loop:
1. Scroll by `window.innerHeight * 0.5`
2. Sleep 400ms for lazy content to load
3. Check for new content via LazyLoadDetector
4. Track consecutive cycles without content
5. Capture screenshot if cycle matches interval or is final
6. Stop when stabilized OR max cycles reached

Screenshot capture uses format: `{audit_id}_scroll_{cycle:02d}.jpg`

### 4. Scout Integration (Task 3)

Extended Scout.investigate() method with:
- enable_scrolling: bool = True parameter (default enabled)
- Optional import of ScrollOrchestrator/LazyLoadDetector
- Scroll orchestration between form validation and result assembly
- scroll_result field added to ScoutResult dataclass

Maintains backward compatibility - existing investigate() calls work unchanged.

### 5. Module Naming Resolution (Deviations)

Issue: Created `veritas/agents/scout/` directory conflicting with existing `veritas/agents/scout.py` file.

Fix: Renamed to `veritas/agents/scout_nav/` to avoid module name shadowing.

Files updated:
- veritas/agents/scout_nav/lazy_load_detector.py
- veritas/agents/scout_nav/scroll_orchestrator.py
- veritas/agents/scout.py (imports updated)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Dependency] Installed pytest-mock**
- **Found during:** Task 4 (tests creation)
- **Issue:** Plan specified pytest-mock for mocking page.evaluate() but package not installed
- **Fix:** Installed pytest-mock via pip
- **Files modified:** None (package-level dependency)
- **Commit:** N/A (dependency installation, tracked in Task 4 commit)

**2. [Rule 1 - Bug] Module name conflict with scout/ directory**
- **Found during:** Task 3 (verification)
- **Issue:** Created `veritas/agents/scout/` directory which shadowed existing `veritas/agents/scout.py` file, causing `ScoutResult` import to fail
- **Fix:** Renamed directory to `veritas/agents/scout_nav/` to avoid module name conflict
- **Files modified:** veritas/agents/scout.py (import paths updated), veritas/agents/scout_nav/* (directory renamed)
- **Commit:** b8e0e99

**3. [Rule 1 - Bug] Mock matching issue in test_scrolling_with_lazy_loaded_content**
- **Found during:** Task 4 (test execution)
- **Issue:** Mock used `"hasNewContent" in code` which matched both the inject script AND the actual hasNewContent() call, causing early stabilization
- **Fix:** Changed match pattern to `"hasNewContent()" in code and "(" in code and ")" in code` to match only the actual function call
- **Files modified:** tests/test_scroll_orchestrator.py
- **Commit:** 4aa34f9 (fix included in Task 4 commit)

### Auth Gates

None encountered.

## Requirements Traceability

| Requirement ID | Description | Success Criteria |
|----------------|-------------|------------------|
| SCROLL-01 | Scout/Vision Agent can scroll pages and capture full screenshot series | Screenshots captured at scroll intervals with cycle-based naming |
| SCROLL-03 | Lazy loading detection and handling for complete capture | MutationObserver tracks DOM changes, stops after 2 stable cycles |

All requirements satisfied.

## Verification Results

### Test Results
```
tests/test_scroll_orchestrator.py::test_scroll_state_and_result_dataclasses PASSED
tests/test_scroll_orchestrator.py::test_lazy_load_detector_injection_and_detection PASSED
tests/test_scroll_orchestrator.py::test_scrolling_with_lazy_loaded_content PASSED
tests/test_scroll_orchestrator.py::test_scrolling_stabilizes_early_on_static_page PASSED
tests/test_scroll_orchestrator.py::test_scrolling_captures_screenshots_at_intervals PASSED
tests/test_scroll_orchestrator.py::test_scrolling_respects_max_cycle_limit PASSED
============================== 6 passed in 9.43s ==============================
```

All tests pass with meaningful coverage:
- Dataclass instantiation and serialization
- Detector injection and content detection
- Scroll continuation until stabilization
- Early termination on static pages
- Screenshot capture timing
- Max cycle limit enforcement

## Self-Check: PASSED

### Files Created Verification
```bash
[ -f "veritas/agents/scout_nav/lazy_load_detector.py" ] && echo "FOUND: lazy_load_detector.py" || echo "MISSING: lazy_load_detector.py"
[ -f "veritas/agents/scout_nav/scroll_orchestrator.py" ] && echo "FOUND: scroll_orchestrator.py" || echo "MISSING: scroll_orchestrator.py"
[ -f "veritas/agents/scout_nav/__init__.py" ] && echo "FOUND: scout_nav/__init__.py" || echo "MISSING: scout_nav/__init__.py"
[ -f "tests/test_scroll_orchestrator.py" ] && echo "FOUND: test_scroll_orchestrator.py" || echo "MISSING: test_scroll_orchestrator.py"
[ -f "tests/__init__.py" ] && echo "FOUND: tests/__init__.py" || echo "MISSING: tests/__init__.py"
```

### Commits Verification
```bash
git log --oneline -5 | grep -q "b8a9fb7" && echo "FOUND: b8a9fb7 (Task 1)" || echo "MISSING: b8a9fb7"
git log --oneline -5 | grep -q "ec39320" && echo "FOUND: ec39320 (Task 2)" || echo "MISSING: ec39320"
git log --oneline -5 | grep -q "b8e0e99" && echo "FOUND: b8e0e99 (Task 3)" || echo "MISSING: b8e0e99"
git log --oneline -5 | grep -q "4aa34f9" && echo "FOUND: 4aa34f9 (Task 4)" || echo "MISSING: 4aa34f9"
```

**All tasks complete with full verification.**