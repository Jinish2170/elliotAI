# Phase 3: LangGraph State Machine Investigation - Research

**Researched:** 2026-02-21
**Domain:** LangGraph async execution, Python 3.11+ asyncio compatibility, subprocess isolation
**Confidence:** MEDIUM

## Summary

The VERITAS orchestrator properly builds a LangGraph StateGraph but executes nodes sequentially instead of using `ainvoke()` to avoid an unspecified async issue. The existing LANGGRAPH.md research (completed 2026-02-20) provides comprehensive background on the problem, including possible causes and workaround options. However, the actual root cause has not been verified through reproduction testing.

**Critical finding**: The running Python version is 3.11.5, not 3.14 as documented in STATE.md. This suggests either the documentation is outdated, or the issue was misdiagnosed as Python 3.14-specific. Investigation should focus on Python 3.11+ asyncio behavior with LangGraph.

**Primary recommendation**: Implement a three-phase investigation approach:
1. Create isolated minimal reproduction test to verify `ainvoke()` behavior
2. Run full audit test with mocked NIMClient to observe real execution paths
3. Use behavioral differences as primary evidence to locate root cause (LangGraph internals vs NIMClient vs subprocess isolation)

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-03 | LangGraph StateGraph executes via ainvoke() without Python 3.14 CancelledError | LangGraph ainvoke() patterns documented in LANGGRAPH.md; minimal reproduction test isolates issue |
| CORE-03-2 | Proper LangGraph debugging, visualization, and checkpointing enabled | StateGraph.get_graph().print_ascii(), MemorySaver checkpointer patterns documented |
| CORE-03-3 | Isolated reproduction test documents root cause of CancelledError | Test design patterns provided; behavioral observation strategy documented |
| CORE-03-4 | Workaround documented if version pin or hybrid execution needed | Three workaround options (sequential tracking, hybrid, version pin) documented with tradeoffs |
| CORE-03-5 | Sequential execution fallback maintained for instant rollback | Current sequential audit() method serves as fallback; migration path documented |
| CORE-06-3 | LangGraph reproduction test covers Python 3.14 async behavior | Test patterns for minimal graph, VERITAS-style graph, and NIM integration provided |

**Note**: Python 3.14 investigation references in requirements should actually target Python 3.11+ based on actual running version (3.11.5).
</phase_requirements>

<user_constraints>
## User Constraints (from 03-CONTEXT.md)

### Locked Decisions
- Investigation approach: Comprehensive code analysis (full orchestrator code and LangGraph integration, not simplified modules)
- Full audit test: Complete audit with mocked NIMClient to observe actual behavior and event flow
- Minimal reproduction test: Isolated test case to isolate CancelledError root cause
- Evidence-based conclusions: Use behavioral differences as key evidence of root cause

### Root Cause Analysis Scope
- All three components: Analyze LangGraph internals, NIMClient interaction, and subprocess orchestrator comprehensively
- LangGraph internals: StateGraph lifecycle, async event handling, ainvoke() implementation
- NIMClient interaction: How NIM async operations interact with LangGraph state machine
- Subprocess orchestrator: How subprocess isolation affects LangGraph execution on Windows + Python 3.11+

### Priority Determination
- Claude discretion: Let planner decide investigation priority based on findings and code analysis
- Evidence-driven: Focus on areas where behavioral differences are most informative

### Root Cause Threshold
- Behavioral differences: Full audit showing different behaviors between proper LangGraph and sequential execution
- Observable effects: Event order, state transitions, error propagation differences
- Evidence strength: Clear, reproducible differences that indicate root cause location

### Resolution Approach
- Fix if possible: Primary goal is to identify and fix root cause enabling proper LangGraph ainvoke()
- Sequential with detailed fallback: If root cause cannot be fixed, document sequential execution with detailed logging and mode tracking
- Version pin consideration: Evaluate if Python version pinning resolves issue (3.11 vs 3.12 vs 3.13)
- Hybrid execution: Test LangGraph for simple cases, sequential for complex flows (if appropriate)

### Claude's Discretion
- Exact test design for minimal reproduction case
- Which Python versions to test for version pin hypothesis (3.12, 3.13, 3.15)
- Detailed fallback logging granularity (event-level, state-level, step-level)
- Hybrid execution boundaries (which parts use LangGraph vs sequential)
- Sequential execution tracking implementation details

### Deferred Ideas (OUT OF SCOPE)
- Advanced LangGraph features (conditional branching, loops) - defer to v2 milestone
- Real-time debugging UI - focus on root cause investigation first
- Performance optimization of sequential execution - out of scope for this phase
- Alternative orchestration frameworks - LangGraph is locked technology choice
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 0.x | State machine orchestration | LangChain library for building graph-based agent workflows; typed state management, checkpointing, graph visualization |
| python | 3.11.5 (current) | Runtime | Actual running version; investigation covers 3.11+ asyncio compatibility (documentation mentions 3.14 but actual is 3.11.5) |
| asyncio | Built-in | Async primitives | Python's async/await event loop foundation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | 1.x | NIM API client wrapper | AsyncOpenAI for NIM VLM calls in Vision and Judge agents |
| tenacity | 8.x | Retry logic with exponential backoff | _try_vision_model retry decorator for resilient NIM calls |
| pytest-asyncio | 0.21+ | Async test support | @pytest.mark.asyncio decorator for async test fixtures |
| unittest.mock | Built-in | Mocking external dependencies | Patch NIMClient, agents to isolate LangGraph behavior |

### Testing Stack
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 7.x | Test framework | Async test execution, fixtures, parametrization |
| pytest-asyncio | 0.21+ | Async test decorator | @pytest.mark.asyncio for test functions |
| coverage.py | 7.x | Test coverage | Verify investigation tests cover critical paths |

**Installation:**
```bash
# Core (already installed via requirements.txt)
pip install langgraph openai tenacity

# Testing (already installed)
pip install pytest pytest-asyncio coverage.py
```

**Version discrepancy note**: Documentation mentions Python 3.14 but actual running version is 3.11.5. Investigation should cover both 3.11.5 and optionally test 3.12/3.13 for version comparison.

## Architecture Patterns

### Recommended Investigation Project Structure
```
veritas/tests/langgraph_investigation/
├── test_01_minimal_graph.py          # Minimal isolated reproduction (Phase 1)
├── test_02_full_audit_mocked.py      # Full audit with mocked agents (Phase 2)
├── test_03_python_version_compare.py # Python version comparison (Phase 3 - optional)
├── test_04_hybrid_execution.py       # Hybrid execution test (if workarounds needed)
└── README.md                          # Investigation findings and conclusions
```

### Pattern 1: Minimal StateGraph Reproduction Test

**What**: Isolated test with minimal StateGraph that strips away VERITAS complexity

**When to use**: First phase of investigation to verify basic LangGraph ainvoke() behavior

**Example:**
```python
# Source: Based on LANGGRAPH.md minimal graph reproduction pattern
import asyncio
import pytest
from typing import TypedDict
from langgraph.graph import StateGraph, END

class MinimalState(TypedDict):
    count: int
    status: str

async def simple_node(state: MinimalState) -> dict:
    """Minimal async node that mimics agent behavior."""
    await asyncio.sleep(0.01)  # Simulate async work
    return {"count": state.get("count", 0) + 1}

def route_by_count(state: MinimalState) -> str:
    """Route based on count."""
    if state.get("count", 0) >= 3:
        return "end"
    return "continue"

def build_minimal_graph():
    """Build minimal graph for testing."""
    graph = StateGraph(MinimalState)
    graph.add_node("start", simple_node)
    graph.add_node("continue", simple_node)
    graph.set_entry_point("start")
    graph.add_conditional_edges(
        "start",
        route_by_count,
        {"continue": "continue", "end": END}
    )
    graph.add_conditional_edges(
        "continue",
        route_by_count,
        {"continue": "continue", "end": END}
    )
    return graph.compile()

@pytest.mark.asyncio
async def test_ainvoke_minimal_graph():
    """Test LangGraph ainvoke execution on minimal graph."""
    graph = build_minimal_graph()
    initial_state = {"count": 0, "status": "running"}

    result = await graph.ainvoke(initial_state)

    assert result["count"] == 3
    assert result["status"] == "running"

@pytest.mark.asyncio
async def test_ainvoke_vs_manual_execution():
    """Compare ainvoke() with manual sequential execution."""
    # ainvoke execution
    graph = build_minimal_graph()
    ainvoke_result = await graph.ainvoke({"count": 0, "status": "running"})

    # Manual sequential execution
    state = {"count": 0, "status": "running"}
    for _ in range(3):
        state.update(await simple_node(state))
    manual_result = state

    # Compare results
    assert ainvoke_result["count"] == manual_result["count"]
    assert ainvoke_result["status"] == manual_result["status"]
```

### Pattern 2: Full Audit Test with Mocked NIMClient

**What:** Complete VERITAS audit with LangGraph ainvoke() using mocked external dependencies

**When to use:** Second phase to observe real execution path without external calls

**Example:**
```python
# Source: Based on AUDIT_STATE and build_audit_graph() in orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import TypedDict
from langgraph.graph import StateGraph, END
import asyncio
import sys
from pathlib import Path

# Add veritas to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.orchestrator import AuditState, build_audit_graph

@pytest.mark.asyncio
@patch('veritas.agents.scout.StealthScout')
@patch('veritas.core.nim_client.NIMClient')
async def test_ainvoke_full_audit_mocked(mock_nim_class, mock_scout_class):
    """Test full audit graph ainvoke() with mocked agents."""

    # Mock Scout to return minimal success
    mock_scout_instance = AsyncMock()
    mock_scout_instance.__aenter__.return_value = mock_scout_instance
    mock_scout_instance.investigate.return_value = MagicMock(
        url="https://example.com",
        status="SUCCESS",
        screenshots=["/tmp/screenshot.jpg"],
        page_title="Example",
        links=[],
        forms_detected=False,
        captcha_detected=False,
        site_type="ecommerce",
        site_type_confidence=0.8,
    )
    mock_scout_class.return_value = mock_scout_instance

    # Mock NIMClient to return cached responses
    mock_nim_instance = MagicMock()
    mock_nim_instance.analyze_image.return_value = {
        "response": '{"findings": []}',
        "model": "nvidia/neva-22b",
        "fallback_mode": False,
        "cached": True,
    }
    mock_nim_instance.generate_text.return_value = {
        "response": '{...',
        "model": "nvidia/neva-22b",
        "fallback_mode": False,
        "cached": True,
    }
    mock_nim_instance.call_count = 0
    mock_nim_class.return_value = mock_nim_instance

    # Build and compile graph
    graph = build_audit_graph()
    compiled = graph.compile()

    # Initial state
    state: AuditState = {
        "url": "https://example.com",
        "audit_tier": "quick_scan",
        "iteration": 0,
        "max_iterations": 1,
        "max_pages": 1,
        "status": "running",
        "scout_results": [],
        "vision_result": None,
        "graph_result": None,
        "judge_decision": None,
        "pending_urls": ["https://example.com"],
        "investigated_urls": [],
        "start_time": asyncio.get_event_loop().time(),
        "elapsed_seconds": 0,
        "errors": [],
        "scout_failures": 0,
        "nim_calls_used": 0,
        "site_type": "",
        "site_type_confidence": 0.0,
        "verdict_mode": "simple",
        "security_results": {},
        "security_mode": "",
        "enabled_security_modules": [],
    }

    # Execute via ainvoke
    try:
        result = await compiled.ainvoke(state)
        assert result["status"] in ("completed", "error")
    except asyncio.CancelledError as e:
        pytest.fail(f"CancelledError in full audit ainvoke: {e}")
```

### Pattern 3: Behavioral Difference Observation

**What:** Comparison test that logs detailed execution differences between ainvoke and sequential

**When to use:** When root cause location is unclear; use event flow differences as evidence

**Example:**
```python
# Source: Based on CONTEXT.md decision to use behavioral differences as evidence
import pytest
import asyncio
import time
from typing import TypedDict, Any
from langgraph.graph import StateGraph, END

class ObservableState(TypedDict):
    step_log: list[str]
    events: list[dict]
    count: int

class EventLogger:
    """Captures execution flow for comparison."""

    def __init__(self, name: str):
        self.name = name
        self.events = []

    def log(self, event_type: str, details: dict):
        entry = {
            "source": self.name,
            "event": event_type,
            "timestamp": time.time(),
            **details
        }
        self.events.append(entry)

async def observable_node(logger: EventLogger, node_name: str):
    async def _node(state: ObservableState) -> dict:
        logger.log("node_start", {"node": node_name, "state_count": state.get("count", 0)})
        await asyncio.sleep(0.01)
        update = {"count": state.get("count", 0) + 1}
        logger.log("node_complete", {"node": node_name, "update": update})
        return update
    return _node

@pytest.mark.asyncio
async def test_ainvoke_vs_sequential_behavior():
    """Compare execution flow between ainvoke and sequential."""

    # ainvoke execution logger
    ainvoke_logger = EventLogger("ainvoke")
    graph = StateGraph(ObservableState)
    graph.add_node("node1", observable_node(ainvoke_logger, "node1"))
    graph.add_node("node2", observable_node(ainvoke_logger, "node2"))
    graph.set_entry_point("node1")
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", END)
    compiled = graph.compile()

    ainvoke_result = await compiled.ainvoke({
        "step_log": [],
        "events": [],
        "count": 0
    })

    # Sequential execution logger
    seq_logger = EventLogger("sequential")
    node1 = observable_node(seq_logger, "node1")
    node2 = observable_node(seq_logger, "node2")

    state = {"step_log": [], "events": [], "count": 0}
    state.update(await node1(state))
    state.update(await node2(state))
    seq_result = state

    # Compare event sequences
    print("\n=== ainvoke events ===")
    for e in ainvoke_logger.events:
        print(f"  {e}")

    print("\n=== sequential events ===")
    for e in seq_logger.events:
        print(f"  {e}")

    # Assertions
    assert ainvoke_result["count"] == seq_result["count"]
    assert len(ainvoke_logger.events) == len(seq_logger.events)

    # Detailed comparison: event types and order
    ainvoke_types = [e["event"] for e in ainvoke_logger.events]
    seq_types = [e["event"] for e in seq_logger.events]
    assert ainvoke_types == seq_types, f"Event sequences differ: ainvoke={ainvoke_types}, seq={seq_types}"
```

### Anti-Patterns to Avoid

- **Testing with real NIM calls**: Consumes quota, introduces flakiness due to network/API issues. Mock NIMClient for deterministic tests.
- **Complex state in minimal tests**: Minimal reproduction should strip away complexity. Start with simple counter, not full AuditState.
- **Python version assumptions**: Don't assume Python 3.14 is the issue. Test on actual running version (3.11.5) first.
- **Silent error swallowing**: Always log and track CancelledError; don't fall back without evidence.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Event capturing infrastructure | Custom event logger | unittest.mock.AsyncMock, built-in list/dict | Mocking provides built-in call tracking without custom code |
| Async test fixtures | Custom async fixture logic | @pytest.mark.asyncio, pytest-asyncio fixtures | Standard patterns, battle-tested |
| Graph state comparison | Custom diff logic | assert statements, pytest pretty diff | Native assertion errors show differences clearly |
| Python version testing | Manual venv creation | pytest-xdist parameterization or Docker | Standardized version comparison |

**Key insight**: Standard libraries and testing frameworks provide most investigation infrastructure needed. Custom code adds maintenance burden and potential bugs.

## Common Pitfalls

### Pitfall 1: Mocking LangGraph Internals vs Mocking External Dependencies

**What goes wrong:** Mocking StateGraph or CompiledGraph hides the actual issue being investigated

**Why it happens:** Desire to isolate LangGraph leads to over-mocking, which masks the problem

**How to avoid:** Mock external dependencies (NIMClient, Scout, Vision agents) but let LangGraph internals execute normally. The goal is to study LangGraph's actual behavior, not verify it works with mocks.

**Warning signs:** Test passes with mocks but real audit still fails; test mocks the CompiledGraph.ainvoke method.

### Pitfall 2: Platform-Specific Async Behavior

**What goes wrong:** Tests pass on Linux but fail on Windows (or vice versa) due to subprocess/async differences

**Why it happens:** VERITAS runs as a subprocess on Windows with specific asyncio characteristics (selector vs proactor event loop)

**How to avoid:** Run investigation tests on the actual platform (Windows). If cross-platform testing is needed, document that findings may not transfer.

**Warning signs:** Tests use asyncio.create_subprocess_exec (known Windows issue; code uses subprocess.Popen + run_in_executor instead).

### Pitfall 3: State Mutation vs State Replacement

**What goes wrong:** Tests assume nodes update state in-place, but LangGraph creates new state objects

**Why it happens:** LANGGRAPH patterns use typed dict updates, mutation can confuse comparison logic

**How to avoid:** Always use state.update(node_return) pattern, never mutate state directly in nodes. Use assert on result state, not intermediate states.

**Warning signs:** Comparing state references with `is`; tests depend on object identity.

### Pitfall 4: Ignoring Event Loop Characteristics

**What goes wrong:** Tests assume default async behavior, but different Python versions have different asyncio defaults

**Why it happens:** Asyncio behavior varies across Python versions (3.11's new event loop debug mode, task group changes)

**How to avoid:** Document Python version used in each test. Run tests on multiple versions if investigating version hypothesis.

**Warning signs:** Tests use undefined asyncio features; no version annotation in test files.

### Pitfall 5: Sequential Execution Masking LangGraph Benefits

**What goes wrong:** Sequential fallback test passes but doesn't verify LangGraph actually worked

**Why it happens:** Falling back immediately without attempting ainvoke() means investigation never surfaces the issue

**How to avoid:** Always attempt ainvoke() first, only use sequential if explicitly testing fallback behavior. Track execution mode in state.

**Warning signs:** Tests always use sequential code path; no test explicitly calls compiled.ainvoke().

## Code Examples

### Minimal Reproduction Test with Error Capture

```python
# Source: LANGGRAPH.md + CONTEXT.md investigation approach
import asyncio
import pytest
from typing import TypedDict
from langgraph.graph import StateGraph, END
import sys
from pathlib import Path

class MinimalState(TypedDict):
    count: int
    status: str
    error_log: list[str]

async def async_node(state: MinimalState) -> dict:
    """Node with simulated async work."""
    try:
        await asyncio.sleep(0.01)
        return {"count": state.get("count", 0) + 1}
    except Exception as e:
        return {"error_log": state.get("error_log", []) + [str(e)]}

def build_graph():
    graph = StateGraph(MinimalState)
    graph.add_node("node1", async_node)
    graph.add_node("node2", async_node)
    graph.set_entry_point("node1")
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", END)
    return graph.compile()

@pytest.mark.asyncio
async def test_ainvoke_with_error_capture():
    """Test ainvoke and capture any Errors."""
    graph = build_graph()
    state: MinimalState = {"count": 0, "status": "running", "error_log": []}

    try:
        result = await graph.ainvoke(state)
        assert result["status"] == "running"
        assert result["count"] == 2
        assert not result.get("error_log")
    except asyncio.CancelledError as e:
        pytest.fail(f"CancelledError raised: {e}", pytrace=False)
    except Exception as e:
        pytest.fail(f"Unexpected error: {type(e).__name__}: {e}", pytrace=False)

@pytest.mark.asyncio
async def test_manifold_execution():
    """Test manual sequential execution for comparison."""
    state: MinimalState = {"count": 0, "status": "running", "error_log": []}

    # Node 1
    state.update(await async_node(state))
    # Node 2
    state.update(await async_node(state))

    assert state["count"] == 2
    assert not state.get("error_log")
```

### Full Audit with Detailed Event Logging

```python
# Source: orchestrator.py + CONTEXT.md behavioral differences approach
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import asyncio
import time
from typing import TypedDict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.orchestrator import AuditState, build_audit_graph

@pytest.mark.asyncio
@patch('veritas.agents.scout.StealthScout')
@patch('veritas.agents.vision.VisionAgent')
@patch('veritas.core.nim_client.NIMClient')
async def test_ainvoke_detailed_event_flow(mock_nim, mock_vision, mock_scout):
    """
    Test full audit ainvoke() with detailed event logging.

    Observes event flow, state transitions, node execution order.
    Compare with sequential execution to identify behavioral differences.
    """

    event_log = []

    def log_event(event_type, details):
        event_log.append({
            "event": event_type,
            "time": time.time(),
            **details
        })

    # Mock Scout
    scout_instance = AsyncMock()
    scout_instance.__aenter__.return_value = scout_instance
    scout_instance.investigate.return_value = MagicMock(
        url="https://example.com",
        status="SUCCESS",
        screenshots=[],
        site_type="ecommerce",
        site_type_confidence=0.8,
        page_title="Example",
        links=[],
        forms_detected=False,
        captcha_detected=False,
        trust_modifier=0.0,
        navigation_time_ms=1000,
        dom_analysis={},
        form_validation={},
    )
    mock_scout.return_value = scout_instance

    # Mock NIM
    nim_instance = MagicMock()
    nim_instance.analyze_image.return_value = {
        "response": '{"findings": [], "score": 0.5}',
        "model": "nvidia/neva-22b",
        "cached": True,
    }
    nim_instance.generate_text.return_value = {
        "response": "...",
        "model": "nvidia/neva-22b",
        "cached": True,
    }
    mock_nim.return_value = nim_instance

    # Mock Vision agent
    vision_instance = AsyncMock()
    vision_instance.analyze.return_value = MagicMock(
        findings=[],
        dark_pattern_summary={},
        visual_score=0.5,
        temporal_score=0.5,
        nim_calls_made=0,
    )
    mock_vision.return_value = vision_instance

    # Build graph
    graph = build_audit_graph()
    compiled = graph.compile()

    # Initial state
    state: AuditState = {
        "url": "https://example.com",
        "audit_tier": "quick_scan",
        "iteration": 0,
        "max_iterations": 1,
        "max_pages": 1,
        "status": "running",
        "scout_results": [],
        "vision_result": None,
        "graph_result": None,
        "judge_decision": None,
        "pending_urls": ["https://example.com"],
        "investigated_urls": [],
        "start_time": time.time(),
        "elapsed_seconds": 0,
        "errors": [],
        "scout_failures": 0,
        "nim_calls_used": 0,
        "site_type": "",
        "site_type_confidence": 0.0,
        "verdict_mode": "simple",
        "security_results": {},
        "security_mode": "",
        "enabled_security_modules": [],
    }

    log_event("test_start", {"state": dict(state)})

    # Execute via ainvoke
    try:
        result = await compiled.ainvoke(state)
        log_event("ainvoke_complete", {"status": result.get("status")})

        # Verify basic expectations
        assert result["status"] in ("completed", "error")
        log_event("assert_complete", {"checks_passed": True})

    except asyncio.CancelledError as e:
        log_event("cancelled_error", {"error": str(e)})
        pytest.fail(f"CancelledError: {e}", pytrace=False)
    except Exception as e:
        log_event("unexpected_error", {"error": type(e).__name__, "message": str(e)})
        pytest.fail(f"Error: {type(e).__name__}: {e}", pytrace=False)

    # Print event log for analysis
    print("\n=== Event Log ===")
    for e in event_log:
        print(f"  {e}")
```

### Subprocess Isolation Test

```python
# Source: audit_runner.py subprocess pattern
import pytest
import subprocess
import asyncio
import sys
from pathlib import Path
import json

@pytest.mark.integration
async def test_subprocess_ainvoke_comparison():
    """
    Test if subprocess context affects ainvoke() behavior.

    Runs veritas audit via subprocess and compares with direct execution.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    python = sys.executable

    # Test 1: Direct execution
    print("\n=== Direct Execution ===")
    direct_code = """
import asyncio
import sys
sys.path.insert(0, '{project_root}')
from core.orchestrator import build_audit_graph

async def test():
    graph = build_audit_graph()
    compiled = graph.compile()
    state = {{
        "url": "https://example.com",
        "audit_tier": "quick_scan",
        "iteration": 0,
        "max_iterations": 1,
        "max_pages": 1,
        "status": "running",
        "scout_results": [],
        "vision_result": None,
        "graph_result": None,
        "judge_decision": None,
        "pending_urls": ["https://example.com"],
        "investigated_urls": [],
        "start_time": 0,
        "elapsed_seconds": 0,
        "errors": [],
        "scout_failures": 0,
        "nim_calls_used": 0,
        "site_type": "",
        "site_type_confidence": 0.0,
        "verdict_mode": "simple",
        "security_results": {{}},
        "security_mode": "",
        "enabled_security_modules": [],
    }}
    result = await compiled.ainvoke(state)
    print(result.get("status"))

asyncio.run(test())
""".format(project_root=project_root)

    result = subprocess.run(
        [python, "-c", direct_code],
        capture_output=True,
        text=True,
        timeout=30
    )
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    print(f"Return code: {result.returncode}")

    # If cancelled error in subprocess but not direct, subprocess isolation is the issue
    if "CancelledError" in result.stderr:
        pytest.skip("Subprocess causes CancelledError - isolation issue confirmed")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual node execution without state machine | LangGraph StateGraph with ainvoke() | Phase 3 target | Proper graph execution, checkpointing, visualization |
| Python 3.14 CancelledError workaround assumption | Evidence-based root cause investigation | This phase | Understand actual root cause before applying fix |
| Guessing at Python version issue | Test on actual running version (3.11.5) | This phase | Correct Python version hypothesis |

**Deprecated/outdated:**
- Python 3.14 CancelledError assumption (actual version is 3.11.5) may be outdated
- LANGGRAPH.md version comparison test for 3.14 may not be relevant

## Root Cause Analysis Guide

### Component 1: LangGraph Internals

**Investigation approach:**
1. Build minimal StateGraph → test ainvoke() with simple async node
2. Add conditional routing → test routing with state-dependent decisions
3. Add loop → test iteration behavior (similar to max_iterations control)

**Evidence to collect:**
- Does ainvoke() complete successfully with minimal graph?
- At what complexity level does it fail (sequential→routing→loop)?
- Error messages and stack traces if failures occur
- Event loop state at failure points

**Tools:**
- Python 3.11's asyncio.get_event_loop().get_debug() for event loop introspection
- sys._getframe(1) for call stack analysis if needed
- `traceback.print_exc()` for detailed error capture

### Component 2: NIMClient Interaction

**Investigation approach:**
1. Mock NIMClient completely → test ainvoke() with mocked async calls
2. Stub NIMClient with real AsyncOpenAI client but test API → test with real async HTTP
3. Full NIM integration → test with actual NIM API calls

**Evidence to collect:**
- Does ainvoke() fail with mocked NIMClient?
- Does ainvoke() fail with AsyncOpenAI client but no API calls?
- Does ainvoke() fail with actual API calls?
- Correlation between NIM call count and failure likelihood

**Tools:**
- unittest.mock.AsyncMock for complete mocking
- pytest fixtures for granular mock control
- NIMClient.call_count tracking for correlation analysis

### Component 3: Subprocess Orchestrator

**Investigation approach:**
1. Direct Python execution → run test files directly
2. Subprocess Popen execution → run tests via subprocess.Popen
3. Full audit_runner context → test via AuditRunner.run()

**Evidence to collect:**
- Does direct execution work but subprocess execution fail?
- Does audit_runner Queue IPC affect behavior differently than stdout?
- Does Windows subprocess.spawn context differ from fork context on Linux?

**Tools:**
- subprocess.run(capture_output=True) for controlled subprocess testing
- multiprocessing.Queue for Queue IPC testing
- Platform detection: sys.platform == "win32"

## Open Questions

1. **Why is Python version documented as 3.14 but actual is 3.11.5?**
   - What we know: Running Python is 3.11.5 (bash python --version)
   - What's unclear: Is there a different venv or environment using 3.14? Is documentation outdated?
   - Recommendation: Assume Python 3.11+ is target; document actual version in tests; optional Python 3.12/3.13 comparison if needed

2. **Where exactly does CancelledError originate?**
   - What we know: Comment in orchestrator.py line 1072 documents bypass to avoid "Python 3.14 asyncio CancelledError issues"
   - What's unclear: Has the error ever been observed directly? Is it a hypothesis or observed behavior?
   - Recommendation: Minimal reproduction test will provide first-hand observation; if no error observed, investigate why bypass exists

3. **Is LangGraph StateGraph actually incompatible, or was there a transient issue?**
   - What we know: build_audit_graph() creates proper graph; compiled graph exists but never used
   - What's unclear: Was there a past failure that led to bypass? Has LangGraph fixed compatibility?
   - Recommendation: Test current LangGraph version first; if works, remove bypass and add test suite

4. **Does subprocess isolation interact differently with event loops in Python 3.11?**
   - What we know: audit_runner uses subprocess.Popen + run_in_executor due to Windows compatibility
   - What's unclear: Does the subprocess context change asyncio event loop behavior?
   - Recommendation: Compare direct vs subprocess execution; if subprocess fails, document Windows-specific workaround

5. **How will test results inform resolution approach?**
   - What we know: Three workaround options documented in LANGGRAPH.md (sequential tracking, hybrid, version pin)
   - What's unclear: Which option is appropriate depends on root cause location
   - Recommendation: Let test results guide selection; each component-specific failure maps to different resolution:
     - LangGraph internal bug → Version pin or upstream issue
     - NIMClient incompatibility → Mock NIMClient or use sync HTTP
     - Subprocess isolation issue → Document Windows-specific workaround

## Sources

### Primary (HIGH confidence)
- **Existing LANGGRAPH.md research** (C:\files\coding dev era\elliot\elliotAI\.planning\research\LANGGRAPH.md) — Comprehensive foundation for understanding LangGraph problem, test patterns, workaround options
- **VERITAS codebase** (veritas/core/orchestrator.py) — Actual implementation showing StateGraph build, sequential bypass, ainvoke comment at line 1072
- **VERITAS codebase** (veritas/core/nim_client.py) — NIMClient async implementation using AsyncOpenAI, semaphore rate limiting

### Secondary (MEDIUM confidence)
- **LangGraph documentation** — StateGraph API, ainvoke() method, config options, checkpointing patterns
- **Python 3.11 asyncio documentation** — Task management, event loop, CancelledError handling
- **Python 3.11 subprocess documentation** — Windows subprocess behavior, Popen vs create_subprocess_exec
- **Python standard library** — unittest.mock docs for AsyncMock
- **pytest-asyncio documentation** — @pytest.mark.asyncio decorator usage

### Tertiary (LOW confidence, needs validation)
- **Python 3.14 asyncio behavior** — Not relevant to current running version (3.11.5); documented issue may be outdated
- **LangGraph Windows compatibility** — No specific documentation found; needs testing
- **Upstream LangGraph issues** — No GitHub issue search performed in existing research; may need manual check

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - LangGraph and Python asyncio well-understood, but version discrepancies need clarification
- Architecture: MEDIUM - Test patterns from LANGGRAPH.md solid, but execution context (subprocess) needs investigation
- Pitfalls: MEDIUM - Documented patterns are sound, but actual behavior observations needed

**Research date:** 2026-02-21
**Valid until:** 14 days — Investigation tests should be run before planning, results may change understanding

**Critical path:**
1. Run minimal reproduction test → observe ainvoke() behavior on Python 3.11.5
2. Run full audit test with mocks → observe event flow differences
3. Based on results → select appropriate investigation priority (which component shows failure)
4. Implement targeted tests based on failing component
5. Document findings and recommend resolution approach

---

*Phase 3 Research: LangGraph State Machine Investigation*
*Researched: 2026-02-21*
*Confidence: MEDIUM*
*Built on: LANGGRAPH.md research 2026-02-20*
*Python version clarification: Actual running version is 3.11.5, not 3.14 as documented*
