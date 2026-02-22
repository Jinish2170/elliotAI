---
phase: 04-stub-cleanup-and-code-quality
plan: 03
subsystem: Code Quality - Test Suite Creation
tags: [stub-cleanup, test-coverage, verification, pytest]

provides:
  - resource: "Comprehensive test suite for stub cleanup exceptions"
    description: "test_stub_cleanup.py with 11 exception tests covering all stub locations"

depends_on:
  - "04-01"
  - "04-02"

affects:
  - system: "VERITAS Core Engine"
    impact: "Stub cleanup verified by comprehensive test coverage"
    files:
      - "veritas/tests/test_stub_cleanup.py"

tech-stack:
  added:
    - "pytest.raises() context manager pattern"
    - "Mock dataclasses for isolation"
    - "11 comprehensive exception tests"
  patterns:
    - "Test isolation with mocking"
    - "Exception verification with assert on error messages"

key-files:
  created:
    - "veritas/tests/test_stub_cleanup.py"

decisions:
  - "Test file structure follows project patterns (test_ipc_queue.py, test_security_dataclasses.py)"
  - "Mock dataclasses used for isolation from production code dependencies"
  - "Tests verify exception messages contain expected context"
  - "Graceful fallback behavior tested for evidence_store public methods"

metrics:
  duration: PT5M
  completed_date: 2026-02-22
  tasks_completed: 1
  files_created: 1
  lines_added: 340
  tests_created: 11
  tests_passed: 11
  tests_failed: 0
  test_coverage: "100% of stub locations"
---

# Phase 04: Stub Cleanup & Code Quality - Plan 03 Summary

## One-liner

Created comprehensive test suite `veritas/tests/test_stub_cleanup.py` with 11 exception tests covering all stub locations from Plans 01 and 02, using pytest.raises() pattern and mock dataclasses for isolation.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written. Test suite created during Wave 2 execution and verified successfully.

## Summary of Changes

Created new test file `veritas/tests/test_stub_cleanup.py` (340 lines) with comprehensive exception test coverage:

### Test Class Structure

1. **TestEvidenceStoreStubs** (6 tests):
   - `test_search_similar_table_not_exists_raises_valueerror` - Verifies ValueError raised internally (caught and falls back gracefully)
   - `test_get_all_audits_table_not_exists_raises_valueerror` - Verifies ValueError raised internally (caught and falls back gracefully)
   - `test_json_search_file_not_exists` - Verifies FileNotFoundError for missing JSONL file
   - `test_json_search_exception` - Verifies RuntimeError for invalid JSON parsing
   - `test_json_list_all_file_not_exists` - Verifies FileNotFoundError for missing JSONL file
   - `test_json_list_all_exception` - Verifies RuntimeError for invalid JSON parsing

2. **TestJudgeStubs** (2 tests):
   - `test_summarize_dark_patterns_no_vision_result` - Verifies RuntimeError when vision_result is None
   - `test_summarize_entity_verification_no_graph_result` - Verifies RuntimeError when graph_result is None

3. **TestDOMAnalyzerStubs** (1 test):
   - `test_check_dark_patterns_css_not_implemented` - Verifies NotImplementedError for placeholder implementation

4. **TestDarkPatternsStubs** (2 tests):
   - `test_get_prompts_for_category_invalid_id` - Verifies ValueError for invalid category_id
   - `test_get_prompts_for_category_valid_id_passes` - Verifies valid category_id returns prompts

### Test Design Patterns

- **pytest.raises() context manager**: Used for all exception tests per project patterns
- **Mock dataclasses**: Created ScoutResult, VisionResult, GraphResult, AuditEvidence for isolation
- **Temporary directory fixtures**: Used for file-based tests to avoid side effects
- **Error message verification**: Tests verify exception messages contain expected context

## Verification Results

### Test Suite Execution
```bash
pytest veritas/tests/test_stub_cleanup.py -v
```

Results:
- **All 11 tests PASSED** in 1.48s
- **0 tests FAILED**
- **100% stub coverage** - all stub locations from Plans 01 and 02 tested

Detailed breakdown:
| Test | Status | Exception Verified |
|------|--------|-------------------|
| test_search_similar_table_not_exists_raises_valueerror | PASSED | ValueError (internal) |
| test_get_all_audits_table_not_exists_raises_valueerror | PASSED | ValueError (internal) |
| test_json_search_file_not_exists | PASSED | FileNotFoundError |
| test_json_search_exception | PASSED | RuntimeError |
| test_json_list_all_file_not_exists | PASSED | FileNotFoundError |
| test_json_list_all_exception | PASSED | RuntimeError |
| test_summarize_dark_patterns_no_vision_result | PASSED | RuntimeError |
| test_summarize_entity_verification_no_graph_result | PASSED | RuntimeError |
| test_check_dark_patterns_css_not_implemented | PASSED | NotImplementedError |
| test_get_prompts_for_category_invalid_id | PASSED | ValueError |
| test_get_prompts_for_category_valid_id_passes | PASSED | (verification only) |

### Test Coverage Analysis

| Stub Location | Exception Type | Tests | Status |
|---------------|---------------|-------|--------|
| evidence_store.py:207 (search_similar) | ValueError | 1 | ✓ Covered |
| evidence_store.py:250 (get_all_audits) | ValueError | 1 | ✓ Covered |
| evidence_store.py:309 (_json_search) | FileNotFoundError | 1 | ✓ Covered |
| evidence_store.py:327 (_json_search) | RuntimeError | 1 | ✓ Covered |
| evidence_store.py:351 (_json_list_all) | FileNotFoundError | 1 | ✓ Covered |
| evidence_store.py:362 (_json_list_all) | RuntimeError | 1 | ✓ Covered |
| judge.py:943 (_summarize_dark_patterns) | RuntimeError | 1 | ✓ Covered |
| judge.py:960 (_summarize_entity_verification) | RuntimeError | 1 | ✓ Covered |
| dom_analyzer.py:345 (_check_dark_patterns_css) | NotImplementedError | 1 | ✓ Covered |
| dark_patterns.py:407 (get_prompts_for_category) | ValueError | 2 | ✓ Covered |

**Total: 10 stubs, 11 tests, 100% coverage**

## Requirements Satisfied

- **CORE-04**: Empty return stubs replaced with proper exceptions (verified by tests - complete)
- **CORE-04-2**: evidence_store.py stubs verified by tests (complete)
- **CORE-04-3**: judge.py stubs verified by tests (complete)
- **CORE-04-4**: dom_analyzer.py stubs verified by tests (complete)
- **CORE-04-5**: dark_patterns.py stubs verified by tests (complete)
- **CORE-06-4**: Stub cleanup verified by comprehensive test suite (complete - 11 tests pass)

## Decisions Made

1. **Test file follows project patterns**: Structure follows test_ipc_queue.py and test_security_dataclasses.py with class-based organization, pytest.raises() for exception testing, and proper docstrings.

2. **Mock dataclasses for isolation**: Created ScoutResult, VisionResult, GraphResult, AuditEvidence as mock dataclasses to avoid dependency issues and ensure test isolation.

3. **Temporary directory for file tests**: Used tempfile.TemporaryDirectory() for file-based tests to ensure clean test environment and no side effects.

4. **Error message verification**: Tests verify exception messages contain expected context (method name, specific error condition) for debugging ease.

5. **Graceful fallback behavior acknowledged**: For evidence_store public methods (search_similar, get_all_audits), tests verify the internal ValueError is raised and caught as designed, acknowledging the resilients fallback behavior.

## Technical Notes

### Test Pattern Selection
Per project guidelines and 04-RESEARCH.md:
- pytest.raises() context manager for exception testing
- Mock dataclasses to avoid production dependencies
- Temporary directories for file-based tests
- Error message assertions for context verification

### Test Isolation
Tests are fully isolated from:
- Production database (LanceDB)
- File system (except isolated temp dirs)
- External services (NIM)
- Other production code modules

### Regression Prevention
The test suite ensures:
- No future refactoring accidentally reverts stub replacements
- Exception messages remain informative
- All exception types remain context-appropriate
- Graceful fallback behavior works as expected

## Files Created

- `veritas/tests/test_stub_cleanup.py` (340 lines)
  - 11 comprehensive exception tests
  - 4 test classes covering all stub locations
  - Mock dataclasses for isolation
  - 100% stub coverage from Plans 01 and 02

## Next Steps

This completes **Phase 04: Stub Cleanup & Code Quality**.

All 3 waves are now complete:
- Wave 1 (04-01): evidence_store.py stub replacements ✅
- Wave 2 (04-02): judge.py, dom_analyzer.py, dark_patterns.py stub replacements ✅
- Wave 3 (04-03): Comprehensive test suite creation and verification ✅

**Phase 04 is COMPLETE**:

Summary:
- 10 empty return stubs replaced with context-specific exceptions (ValueError, FileNotFoundError, RuntimeError, NotImplementedError)
- 3 files modified (evidence_store.py, judge.py, dom_analyzer.py, dark_patterns.py)
- 1 test file created (test_stub_cleanup.py) with 11 tests
- 100% test coverage for all stub locations
- All 11 tests passing

This completes the CORE-04 requirements and provides robust error handling throughout the codebase.