# LangGraph State Machine Investigation

**Phase:** 03 - LangGraph State Machine Investigation
**Start Date:** 2026-02-21
**Python Version:** 3.11.5 (actual) / 3.14 (originally documented)
**Status:** Investigation in progress

---

## Overview

This directory contains investigation tests for the LangGraph `ainvoke()` behavior on Python 3.11+ with asyncio. The investigation aims to isolate the root cause of a reported `CancelledError` issue and determine whether LangGraph's proper state machine execution can be enabled for VERITAS.

### Investigation Purpose

The VERITAS orchestrator currently bypasses LangGraph's `ainvoke()` method in favor of sequential node execution. This was documented as a workaround for "Python 3.14 asyncio CancelledError issues." However, this workaround sacrifices key LangGraph benefits:

- Graph visualization
- State checkpointing and resume capability
- Proper async orchestration
- Parallel execution of independent nodes
- LangGraph debugging tools

This investigation seeks to determine:
1. Does the CancelledError actually occur on the running Python version (3.11.5)?
2. Where does the issue originate (LangGraph internals, NIMClient, subprocess isolation)?
3. Can the issue be fixed, or should we use a documented workaround?

### Python Version Note

**Critical finding:** The running Python version is **3.11.5**, not 3.14 as originally documented in STATE.md. This suggests:

1. The documentation may be outdated
2. The issue may have been misdiagnosed as Python 3.14-specific
3. Investigating on 3.11.5 may reveal different behavior than previously assumed

---

## Test Directory Structure

```
veritas/tests/langgraph_investigation/
├── test_01_minimal_graph.py          # Minimal isolated reproduction test
├── test_02_full_audit_mocked.py      # Full audit with mocked NIMClient (planned)
├── test_03_behavioral_differences.py # Execution flow comparison (planned)
└── README.md                          # This file
```

### Test Files

#### test_01_minimal_graph.py

**Purpose:** Isolated minimal reproduction test to verify basic LangGraph `ainvoke()` behavior.

**Tests:**
- `test_ainvoke_minimal_graph`: Execute minimal StateGraph via `ainvoke()`
- `test_ainvoke_vs_manual_execution`: Compare `ainvoke()` with manual sequential execution
- `test_graph_visualization`: Generate graph visualization (requires `grandalf`)
- `test_conditional_routing`: Test state-dependent routing behavior
- `test_error_handling_in_node`: Verify error propagation

**Key Finding:** All tests pass on Python 3.11.5. LangGraph `ainvoke()` works correctly without `CancelledError`.

**Status:** ✅ Complete - 4 tests pass, 1 skipped (grandalf missing)

#### test_02_full_audit_mocked.py (planned)

**Purpose:** Full VERITAS audit graph with mocked external dependencies to observe real execution paths.

**What it tests:**
- Complete AuditState with all fields
- All VERITAS agent nodes (Scout, Security, Vision, Graph, Judge)
- NIMClient async calls (mocked)
- Real-world graph topology with conditional routing

**Why mock:** Avoids external API calls, NIM quota consumption, and network flakiness while preserving async behavior.

#### test_03_behavioral_differences.py (planned)

**Purpose:** Compare execution flow between `ainvoke()` and sequential execution.

**What it observes:**
- Event order and timing
- State transitions at each node
- Error propagation differences
- Async task lifecycle behavior

**Why important:** Differences in execution flow provide the strongest evidence for root cause identification.

---

## Investigated Components

### 1. LangGraph Internals

**Areas of investigation:**
- StateGraph lifecycle and compilation
- `ainvoke()` async event handling
- Conditional routing and edge traversal
- Graph visualization and introspection
- Checkpointing capabilities

**Tools:**
- Minimal StateGraph reproduction (test_01_minimal_graph.py)
- `graph.get_graph().print_ascii()` for visualization
- `sys.version_info` for version tracking

**Status:** ✅ Investigated - LangGraph internals work correctly on Python 3.11.5

### 2. NIMClient Interaction

**Areas of investigation:**
- How NIM async operations interact with LangGraph state machine
- AsyncOpenAI client integration
- Rate limiting and semaphore usage
- Timeout handling and error propagation

**Planned tests:**
- Full audit with mocked NIMClient (test_02_full_audit_mocked.py)
- Real NIM API call test (optional, if mock test passes)

**Status:** ⏳ Pending - requires test_02_full_audit_mocked.py

### 3. Subprocess Orchestrator

**Areas of investigation:**
- How subprocess isolation affects LangGraph execution on Windows
- Windows-specific `subprocess.spawn` context behavior
- Queue IPC vs stdout parsing effects on asyncio
- Event loop differences (proactor vs selector on Windows)

**Planned investigation:**
- Direct vs subprocess execution comparison
- Windows subprocess behavior testing

**Status:** ⏳ Pending - requires additional test setup

---

## Running Tests

### Prerequisites

All tests require:
- Python 3.11+ (actual running version: 3.11.5)
- pytest with pytest-asyncio plugin
- langgraph package

```bash
# Verify Python version
python --version  # Should be 3.11.5 or higher

# Install testing dependencies (if needed)
pip install pytest pytest-asyncio
```

### Run All Investigation Tests

```bash
cd veritas
python -m pytest tests/langgraph_investigation/ -v
```

### Run Specific Test File

```bash
# Minimal graph tests
python -m pytest tests/langgraph_investigation/test_01_minimal_graph.py -v

# Full audit mocked (when created)
python -m pytest tests/langgraph_investigation/test_02_full_audit_mocked.py -v

# Behavioral differences (when created)
python -m pytest tests/langgraph_investigation/test_03_behavioral_differences.py -v
```

### Run Individual Test

```bash
# Run manual verification
python veritas/tests/langgraph_investigation/test_01_minimal_graph.py
```

### Enable Graph Visualization

```bash
# Install grandalf for ASCII graph generation
pip install grandalf

# Run with visualization enabled
python -m pytest tests/langgraph_investigation/test_graph_visualization.py -v -s
```

---

## Expected Findings (Template)

### Phase 1: Minimal Reproduction (test_01_minimal_graph.py)

**Question:** Does LangGraph `ainvoke()` work with a minimal graph?

**Result:**
- ✅ `ainvoke()` executes successfully on Python 3.11.5
- ✅ No `CancelledError` observed
- ✅ Conditional routing works correctly
- ✅ Result matches manual sequential execution

**Interpretation:** The issue is NOT in LangGraph's basic `ainvoke()` implementation on Python 3.11.5. The root cause (if any) lies in:
1. Complex VERITAS graph integration
2. NIMClient async interaction
3. Subprocess isolation on Windows

### Phase 2: Full Audit Mocked (test_02_full_audit_mocked.py) - Pending

**Question:** Does `ainvoke()` fail with the full VERITAS graph using mocked NIM calls?

**Result:** TBD - test not yet created

**Interpretation:** TBD

### Phase 3: Behavioral Differences (test_03_behavioral_differences.py) - Pending

**Question:** Where does execution behavior diverge between `ainvoke()` and sequential?

**Result:** TBD - test not yet created

**Interpretation:** TBD

---

## Resolution Path

Based on investigation results, one of the following resolutions will be recommended:

### Option A: Fix Root Cause (Preferred)

If investigation identifies a specific root cause (NIMClient interaction, subprocess isolation, etc.), implement a fix to enable proper LangGraph `ainvoke()` execution.

**Benefits:**
- Full LangGraph benefits (checkpointing, visualization, debugging)
- No workaround code in orchestrator
- Community patterns and future compatibility

**Effort:** Depends on root cause

### Option B: Sequential Execution with Detailed Tracking

If root cause cannot be fixed quickly, improve sequential execution with detailed logging and state tracking to regain traceability.

**Benefits:**
- Maintains current stability
- Adds observability for debugging
- Incremental migration path

**Trade-offs:**
- No checkpointing
- No graph visualization
- Manual state management

### Option C: Hybrid Execution

Run LangGraph for simple cases (no NIM calls, flat graph), sequential for complex cases.

**Benefits:**
- Some LangGraph benefits retained
- Gradual adoption path
- Safety fallback for complex flows

**Trade-offs:**
- Dual execution paths
- Increased complexity

### Option D: Version Pin

If Python version incompatibility is confirmed (needs verification), consider Python 3.12 or 3.13 for VERITAS.

**Benefits:**
- Full LangGraph compatibility
- Battle-tested Python version

**Trade-offs:**
- Loses Python 3.11 features
- Migration overhead
- Technical debt for future Python 3.14+ migration

---

## Notes on Python Version Discrepancy

**Documented:** Python 3.14 (STATE.md)
**Actual running:** Python 3.11.5

**Possible explanations:**
1. STATE.md was written when Python 3.14 was planned but not yet installed
2. Environment changed after initial documentation
3. Different environments exist (development vs deployment)
4. Documentation error

**Impact on investigation:**
- Focus on Python 3.11+ behavior, not 3.14-specific issues
- Documented CancelledError may be out of date or inaccurate
- Testing on Python 3.12/3.13 may still be valuable for comparison

**Action item:** Update STATE.md with actual Python version after investigation complete.

---

## Related Documentation

- **Phase Context:** `C:/files/coding dev era/elliot/elliotAI/.planning/phases/03-langgraph-state-machine-investigation/03-CONTEXT.md`
- **Phase Research:** `C:/files/coding dev era/elliot/elliotAI/.planning/phases/03-langgraph-state-machine-investigation/03-RESEARCH.md`
- **LANGGRAPH Research:** `C:/files/coding dev era/elliot/elliotAI/.planning/research/LANGGRAPH.md`
- **VERITAS Orchestrator:** `veritas/core/orchestrator.py` (sequential bypass at line 939)
- **State:** `.planning/STATE.md`

---

## Investigator Notes

### 2026-02-21 - Initial Investigation (test_01_minimal_graph.py)

**Test Results:**
- test_ainvoke_minimal_graph: ✅ PASSED
- test_ainvoke_vs_manual_execution: ✅ PASSED
- test_graph_visualization: ⏭️ SKIPPED (grandalf missing)
- test_conditional_routing: ✅ PASSED
- test_error_handling_in_node: ✅ PASSED

**Key Finding:**
- LangGraph `ainvoke()` works correctly on Python 3.11.5
- No `CancelledError` observed in minimal graph
- This suggests the reported issue is NOT in LangGraph's core implementation

**Next Steps:**
- Create test_02_full_audit_mocked.py to test with VERITAS graph
- Test with actual NIMClient async calls (mocked)
- Compare execution flow for behavioral differences

**Hypothesis:**
The `ainvoke()` bypass comment in orchestrator.py (line 939) may be:
1. Outdated documentation from a past issue
2. Related to complex VERITAS integration, not LangGraph itself
3. Based on incorrect Python version assumption (3.14 vs 3.11.5)

**Recommendation:**
Proceed to Phase 2 investigation (full audit with mocks) to rule out NIMClient and VERITAS-specific integration issues.

---

*Investigation README created: 2026-02-21*
*Phase 03: LangGraph State Machine Investigation*
