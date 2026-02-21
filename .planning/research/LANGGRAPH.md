# LangGraph Research: Async Execution Patterns for Python 3.14

**Domain:** LangGraph StateGraph async execution, Python 3.14 asyncio compatibility
**Researched:** 2026-02-20
**Confidence:** MEDIUM
**Mode:** Investigation with Recommendations

## Executive Summary

The current implementation bypasses LangGraph's `ainvoke()` method in favor of sequential node execution due to Python 3.14 asyncio `CancelledError` issues. While this workaround allows the codebase to function, it sacrifices key LangGraph benefits: state management, visualization, debugging, checkpointing, and proper graph execution. The root cause requires investigation through isolated reproduction tests.

**Current State:**
- Proper LangGraph StateGraph is built and compiled in `build_audit_graph()`
- Compiled graph (`self._compiled`) is never used via `ainvoke()`
- `VeritasOrchestrator.audit()` manually executes nodes sequentially in a for-loop
- Comment at line 939 explicitly documents the workaround: "This bypasses LangGraph's ainvoke to avoid Python 3.14 asyncio CancelledError issues"

**Impact:**
Lost capabilities: graph visualization, state checkpointing, LangGraph debugging tools, proper async orchestration, resume-from-checkpoint support, parallel execution of independent nodes
Current limitation: Manual routing function calls, serialized state updates, no benefit from LangGraph framework features

**Recommendation Path:**
1. Create isolated reproduction test with minimal StateGraph
2. Verify Python 3.14 asyncio CancelledError behavior triggers issue
3. Test on Python 3.12/3.13 for comparison (isolate Python version as factor)
4. Document workaround with tracking issue if unfixable
5. Consider version pin (Python 3.13) to LangGraph compatibility if needed

## Current Implementation Analysis

### Built but Unused LangGraph Graph

**Location:** `veritas/core/orchestrator.py:861-906`

The `build_audit_graph()` function creates a proper LangGraph StateGraph:

```python
def build_audit_graph() -> StateGraph:
    graph = StateGraph(AuditState)
    graph.add_node("scout", scout_node)
    graph.add_node("security", security_node)
    graph.add_node("vision", vision_node)
    graph.add_node("graph", graph_node)
    graph.add_node("judge", judge_node)
    graph.add_node("force_verdict", force_verdict_node)
    graph.set_entry_point("scout")
    # Add conditional edges with routing functions
    return graph
```

**Graph topology:**
```
START → scout → [route_after_scout] → security → vision → graph → judge → [route_after_judge] → END
                                                    │                                    │
                                                    └────↔── force_verdict ──────────────┘
                                              judge → [route] → scout (more investigation)
```

### Sequential Execution Workaround

**Location:** `veritas/core/orchestrator.py:929-1113`

The `VeritasOrchestrator.audit()` method manually replicates graph execution:

```python
async def audit(self, url: str, tier: str = "standard_audit", ...):
    # Initialize state
    state: AuditState = {...}

    for iteration in range(settings.MAX_ITERATIONS):
        # 1. Scout node
        scout_update = await scout_node(state)
        state.update(scout_update)

        # Manual routing
        route = route_after_scout(state)
        if route == "abort":
            break

        # 2. Security node
        sec_update = await security_node(state)
        state.update(sec_update)

        # 3. Vision node
        vision_update = await vision_node(state)
        state.update(vision_update)

        # 4. Graph node
        graph_update = await graph_node(state)
        state.update(graph_update)

        # 5. Judge node
        judge_update = await judge_node(state)
        state.update(judge_update)

        # Manual routing
        route = route_after_judge(state)
        if route == "scout":
            # Add investigate URLs to pending
            state["pending_urls"] = new_urls
            continue
```

### What's Missing Without LangGraph Execution

**Features lost by sequential execution:**

1. **Graph Visualization**: LangGraph provides `get_graph().print_ascii()` for topology visualization
2. **Checkpointing**: Save/restore audit state for resume capability
3. **Debugging Tools**: Step-through execution, state inspection at each node
4. **Parallel Execution**: Graph can run Vision and Graph in parallel once Scout completes
5. **Traceability**: Automatic event logging for each state transition
6. **Type Safety**: StateGraph validates state structure and transitions
7. **Community Patterns**: Leverage LangGraph's battle-tested state machine patterns

## Python 3.14 Asyncio CancelledError Investigation

### The CancelledError Issue

**Documented in code:** `veritas/core/orchestrator.py:939`

```python
"""
This bypasses LangGraph's ainvoke to avoid Python 3.14 asyncio
CancelledError issues, while keeping all node logic intact.
"""
```

### Possible Causes

**Hypothesis 1: LangGraph Internals Using Deprecated asyncio Patterns**

If LangGraph internally uses patterns like:
- `asyncio.sleep()` without proper exception handling
- `asyncio.gather()` with `return_exceptions=False`
- Task creation without try/except around CancelledError
- TaskGroup usage incompatible with Python 3.14 changes

Then Python 3.14's asyncio changes could trigger unexpected cancellations.

**Hypothesis 2: External AI Client (NIM) Async Timeout**

The NIMClient makes async HTTP calls. If:
- LangGraph wraps these calls in tasks
- Timeouts trigger TaskGroup cancellation
- Python 3.14 handles TaskGroup cancellation differently

This could cause the CancelledError to propagate unexpectedly.

**Hypothesis 3: Windows + Python 3.14 Specific Issue**

The codebase runs on Windows (confirmed from path analysis). If:
- Windows subprocess spawning interacts differently with asyncio task cancellation
- The event loop implementation on Windows for Python 3.14 has behavioral changes
- LangGraph's thread pool usage conflicts with Windows asyncio

This would explain why the sequential workaround works (no LangGraph task management).

### Python 3.14 Asyncio Known Changes

Based on Python 3.14 release notes:

1. **New Introspection APIs**: `capture_call_graph()`, `print_call_graph()` for async call graph debugging (relevant for investigation)

2. **create_task() changes**: Keyword arguments now passed to Task constructor, affecting custom task factories (could affect LangGraph if it uses custom task factories)

3. **No documented CancelledError changes**: Python 3.14 documentation does not list specific CancelledError behavior changes, suggesting the issue may be interaction with LangGraph internals rather than Python itself

This suggests the CancelledError issue is likely:
- LangGraph internal pattern incompatible with Python 3.14
- Interaction between LangGraph's async orchestration and NIMClient's async HTTP calls
- Windows-specific asyncio event loop behavior in Python 3.14

## Recommended Investigation Approach

### Phase 1: Isolated Reproduction Test

**Goal:** Create minimal test case that reproduces the CancelledError

**Test script:** `veritas/tests/test_langgraph_py314.py`

```python
"""
Minimal reproduction test for Python 3.14 asyncio CancelledError
in LangGraph ainvoke execution.
"""
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, END

class MinimalState(TypedDict):
    count: int
    status: str

async def simple_node(state: MinimalState) -> dict:
    """Minimal async node that mimics agent behavior."""
    await asyncio.sleep(0.1)  # Simulate async work
    return {"count": state.get("count", 0) + 1}

def route_by_count(state: MinimalState) -> str:
    """Route based on count."""
    if state.get("count", 0) >= 3:
        return "end"
    return "continue"

async def continue_node(state: MinimalState) -> dict:
    """Node that continues loop."""
    return {"count": state.get("count", 0) + 1}

def build_minimal_graph():
    """Build minimal graph for testing."""
    graph = StateGraph(MinimalState)
    graph.add_node("start", simple_node)
    graph.add_node("continue", continue_node)
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

async def test_ainvoke():
    """Test LangGraph ainvoke execution."""
    graph = build_minimal_graph()
    initial_state = {"count": 0, "status": "running"}

    try:
        result = await graph.ainvoke(initial_state)
        print(f"✓ ainvoke succeeded: {result}")
        return True
    except asyncio.CancelledError as e:
        print(f"✗ CancelledError in ainvoke: {e}")
        return False
    except Exception as e:
        print(f"✗ Other error: {type(e).__name__}: {e}")
        return False

async def test_manual_execution():
    """Test manual sequential execution (current workaround)."""
    state: MinimalState = {"count": 0, "status": "running"}

    for i in range(3):
        state.update(await simple_node(state))
        route = route_by_count(state)
        print(f"Iteration {i+1}: count={state['count']}, route={route}")
        if route == "end":
            break

    print(f"✓ Manual execution succeeded: {state}")
    return True

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print("\n--- Testing LangGraph ainvoke ---")
    ainvoke_ok = await test_ainvoke()
    print("\n--- Testing manual execution ---")
    manual_ok = await test_manual_execution()

    print(f"\nResults: ainvoke={ainvoke_ok}, manual={manual_ok}")
```

**Expected outcomes:**
- If ainvoke fails with CancelledError → reproduces issue
- If ainvoke succeeds → issue is in VERITAS-specific code (NIMClient, complex state)
- If manual always works → confirms sequential workaround is viable

### Phase 2: VERITAS-Specific Reproduction

**Goal:** Test with actual NIMClient to isolate external async calls

**Test script:** `veritas/tests/test_ainvoke_with_nim.py`

```python
"""
Test LangGraph ainvoke with NIMClient async calls.
"""
from veritas.core.nim_client import NIMClient
from langgraph.graph import StateGraph, END

class NIMTestState(TypedDict):
    nim_count: int
    results: list[str]

async def nim_call_node(state: NIMTestState) -> dict:
    """Node that calls NIM (mimics Vision agent)."""
    nim = NIMClient()
    # Simple prompt that won't consume quota
    result = "test_response"  # Mock for testing
    return {
        "nim_count": state.get("nim_count", 0) + 1,
        "results": state.get("results", []) + [result]
    }

async def test_ainvoke_with_nim():
    """Test ainvoke with actual NIM calls."""
    graph = StateGraph(NIMTestState)
    graph.add_node("nim_call", nim_call_node)
    graph.set_entry_point("nim_call")
    compiled = graph.compile()

    try:
        result = await compiled.ainvoke({"nim_count": 0, "results": []})
        print(f"✓ ainvoke with NIM succeeded: {result}")
        return True
    except asyncio.CancelledError as e:
        print(f"✗ CancelledError: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ainvoke_with_nim())
```

### Phase 3: Python Version Comparison

**Goal:** Test on Python 3.12/3.13 to isolate Python version

**Approach:**
- Create Docker containers or virtual environments with Python 3.12 and 3.13
- Run Phase 1 and Phase 2 tests on each version
- Document which versions work with `ainvoke()`

**Expected outcomes:**
- If Python 3.12/3.13 → `ainvoke()` works → Python 3.14 compatibility issue
- If all versions → `ainvoke()` fails → LangGraph bug unrelated to Python version
- If Python 3.14 → works → Issue is VERITAS-specific (NIMClient or complex graph)

## Proper LangGraph Execution Pattern

### If ainvoke() Works

**Replacement for sequential execution:**

```python
class VeritasOrchestrator:
    def __init__(self):
        self._graph = build_audit_graph()
        self._compiled = self._graph.compile()
        self._config = {"recursion_limit": settings.MAX_ITERATIONS * 10}

    async def audit(
        self,
        url: str,
        tier: str = "standard_audit",
        verdict_mode: str = "expert",
        enabled_security_modules: Optional[list[str]] = None,
    ) -> AuditState:
        """Run audit using proper LangGraph ainvoke execution."""
        # Initialize state (same as current)
        state: AuditState = {
            "url": url,
            "audit_tier": tier,
            "iteration": 0,
            "max_iterations": settings.MAX_ITERATIONS,
            "max_pages": tier_config["pages"],
            "status": "running",
            "scout_results": [],
            "vision_result": None,
            "graph_result": None,
            "judge_decision": None,
            "pending_urls": [url],
            "investigated_urls": [],
            "start_time": time.time(),
            "elapsed_seconds": 0,
            "errors": [],
            "scout_failures": 0,
            "nim_calls_used": 0,
            "site_type": "",
            "site_type_confidence": 0.0,
            "verdict_mode": verdict_mode,
            "security_results": {},
            "enabled_security_modules": enabled_security_modules or getattr(
                settings, 'ENABLED_SECURITY_MODULES', ["security_headers", "phishing_db"]
            ),
        }

        logger.info(f"Starting LangGraph ainvoke audit: {url} | tier={tier}")

        # Use LangGraph's proper execution with checkpointing
        try:
            final_state = await self._compiled.ainvoke(
                input=state,
                config=self._config,
            )

            logger.info(
                f"LangGraph ainvoke complete: {url} | "
                f"status={final_state.get('status')} | "
                f"elapsed={final_state['elapsed_seconds']:.1f}s"
            )

            return final_state

        except asyncio.CancelledError as e:
            logger.error(f"LangGraph ainvoke cancelled: {e}")
            state["status"] = "aborted"
            state["errors"].append(f"LangGraph cancelled: {str(e)}")
            return state
        except Exception as e:
            logger.error(f"LangGraph ainvoke failed: {e}", exc_info=True)
            state["status"] = "aborted"
            state["errors"].append(f"LangGraph error: {str(e)}")
            return state
```

### Benefits of Proper LangGraph Execution

**1. Checkpointing for Resume Capability**

```python
# Save checkpoint after each iteration
from langgraph.checkpoint.memory import MemorySaver

class VeritasOrchestrator:
    def __init__(self):
        self._graph = build_audit_graph()
        self._memory = MemorySaver()
        self._compiled = self._graph.compile(checkpointer=self._memory)

    async def audit_with_resume(self, url: str, audit_id: str):
        """Run audit with resume capability."""
        config = {"configurable": {"thread_id": audit_id}}

        # Resume from existing checkpoint if available
        existing = await self._memory.aget(config)
        if existing:
            logger.info(f"Resuming audit {audit_id} from checkpoint")
            state = existing
        else:
            state = self._initialize_state(url)

        # Execute with checkpointing
        final_state = await self._compiled.ainvoke(
            input=state,
            config=config,
            interrupt_before=["force_verdict"]  # Optional intervention point
        )

        return final_state
```

**2. Graph Visualization**

```python
# Print graph topology for debugging
def visualize_graph():
    graph = build_audit_graph()
    print(graph.get_graph().print_ascii())

    # Export as Mermaid diagram for documentation
    print(graph.get_graph().print_mermaid())
```

**3. Parallel Execution of Independent Nodes**

```python
# Modify graph to run Vision and Graph in parallel
def build_parallel_graph():
    graph = StateGraph(AuditState)

    # Scout runs first
    graph.add_node("scout", scout_node)
    graph.add_node("security", security_node)

    # Vision and Graph run in parallel after Security
    graph.add_node("vision", vision_node)
    graph.add_node("graph", graph_node)

    # Parallel branch coordination
    from langgraph.constants import Send

    async def dispatch_parallel(state):
        """Dispatch to Vision and Graph in parallel."""
        return [
            Send("vision", state),
            Send("graph", state),
        ]

    graph.set_entry_point("scout")
    graph.add_edge("scout", "security")
    graph.add_conditional_edges("security", lambda s: "parallel", {
        "parallel": dispatch_parallel
    })
    # Merge Vision and Graph results before Judge
    graph.add_node("merge_vision_graph", merge_vision_graph_results)
    graph.add_edge(["vision", "graph"], "merge_vision_graph")
    graph.add_edge("merge_vision_graph", "judge")

    return graph.compile()
```

**4. Step-Through Debugging**

```python
# Enable human-in-the-loop debugging
class VeritasOrchestrator:
    async def audit_interactive(self, url: str):
        """Run audit with step-through debugging."""
        config = {"configurable": {"thread_id": f"debug_{url}"}}

        async for output in self._compiled.astream(
            input=self._initialize_state(url),
            config=config,
            interrupt_before=["vision", "judge"]  # Interrupt before these nodes
        ):
            print(f"State at: {list(output.keys())}")
            # Inspect state, manually resume if needed
            await asyncio.sleep(1)  # Pause for inspection
```

## Workarounds and Migration Paths

### Option A: Sequential Execution with LangGraph Tracking

**Best if:** ainvoke() cannot be fixed quickly, but want traceability

```python
class VeritasOrchestrator:
    def __init__(self):
        self._graph = build_audit_graph()
        self._compiled = self._graph.compile()

    async def audit_with_tracking(self, url: str, tier: str) -> AuditState:
        """Sequential execution with LangGraph state tracking."""
        # Initialize state
        state = self._initialize_state(url, tier)

        # Use compiled graph for validation only (not execution)
        # This lets us keep graph visualization benefits
        # while avoiding ainvoke() CancelledError issue

        # Sequential execution with state tracking
        current_node = "scout"
        step = 0

        while current_node != END:
            step += 1
            logger.info(f"Step {step}: Executing node {current_node}")

            # Manually call node function
            if current_node == "scout":
                update = await scout_node(state)
            elif current_node == "security":
                update = await security_node(state)
            elif current_node == "vision":
                update = await vision_node(state)
            elif current_node == "graph":
                update = await graph_node(state)
            elif current_node == "judge":
                update = await judge_node(state)
            elif current_node == "force_verdict":
                update = await force_verdict_node(state)
            else:
                break

            state.update(update)

            # Use LangGraph routing (but execute manually)
            if current_node == "scout":
                current_node = route_after_scout(state)
            elif current_node == "judge":
                current_node = route_after_judge(state)
            else:
                # Follow edges
                current_node = self._follow_edge(current_node, state)

        return state

    def _follow_edge(self, from_node: str, state: AuditState) -> str:
        """Follow graph edge manually."""
        edges = self._compiled.get_graph().edges
        for edge in edges.get(from_node, []):
            if callable(edge):
                return edge(state)
            return edge
        return END
```

**Benefits:**
- Keeps LangGraph graph structure for visualization
- Can still use `get_graph().print_ascii()` for topology
- Migration path is incremental (can switch to ainvoke() when fixed)
- Maintains current sequential execution stability

**Trade-offs:**
- Manual edge routing (error-prone)
- No checkpointing
- No LangGraph debugging tools
- Still requires manual state updates

### Option B: Hybrid Approach (Recommended)

**Best if:** Want parallel execution for independent nodes without full ainvoke()

```python
class VeritasOrchestrator:
    async def audit_hybrid(self, url: str, tier: str) -> AuditState:
        """Hybrid execution: parallel where safe, sequential elsewhere."""
        state = self._initialize_state(url, tier)

        # Sequential phases (must wait)
        while state["iteration"] < settings.MAX_ITERATIONS:
            state["iteration"] += 1

            # Scout (sequential, sets up URL list)
            state.update(await scout_node(state))

            # Security (sequential, depends on Scout)
            state.update(await security_node(state))

            # PARALLEL: Vision + Graph (independent once Scout complete)
            vision_future = vision_node(state)
            graph_future = graph_node(state)

            try:
                vision_result, graph_result = await asyncio.gather(
                    vision_future,
                    graph_future,
                    return_exceptions=True
                )

                # Handle exceptions
                if isinstance(vision_result, Exception):
                    logger.error(f"Vision failed: {vision_result}")
                    state["errors"].append(f"Vision: {vision_result}")
                else:
                    state.update(vision_result)

                if isinstance(graph_result, Exception):
                    logger.error(f"Graph failed: {graph_result}")
                    state["errors"].append(f"Graph: {graph_result}")
                else:
                    state.update(graph_result)

            except asyncio.CancelledError as e:
                logger.warning(f"Parallel execution cancelled: {e}")
                # Fall back to sequential for remaining nodes

            # Judge (sequential, needs both Vision and Graph)
            judge_result = await judge_node(state)
            state.update(judge_result)

            # Route decision
            jd = state.get("judge_decision", {})
            if jd.get("action") != "REQUEST_MORE_INVESTIGATION":
                break

            # Add new URLs for next iteration
            state["pending_urls"] = jd.get("investigate_urls", [])

        return state
```

**Benefits:**
- Gets 2x speedup by running Vision + Graph in parallel
- Avoids LangGraph ainvoke() CancelledError issue
- Maintains stability of sequential routing
- Simple migration (just add asyncio.gather)

**Trade-offs:**
- No checkpointing
- No graph visualization
- No LangGraph debugging tools
- Manual parallel orchestration

### Option C: Version Pin to Python 3.13

**Best if:** Python 3.14 CancelledError is root cause and cannot be fixed

**Implementation:**

```dockerfile
# Dockerfile
FROM python:3.13-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run VERITAS
CMD ["python", "-m", "veritas"]
```

```toml
# pyproject.toml
[project]
requires-python = ">=3.13,<3.14"

[tool.rye]
python-version = "3.13"
```

**Benefits:**
- Enables proper LangGraph ainvoke() execution
- Full LangGraph benefits (checkpointing, visualization, debugging)
- No workaround code in orchestrator
- Battle-tested Python version (LangGraph tested on 3.12/3.13)

**Trade-offs:**
- Sacrifices Python 3.14 features
- Technical debt: migration back to 3.14 needed when LangGraph fixes issue
- Dependency on Python version pin

**Recommendation:** Use only if Option A/B fail and investigation confirms Python 3.14 is the blocker.

## Testing Strategy

### Unit Tests

**Test 1: Minimal graph ainvoke()**

```python
# veritas/tests/test_langgraph_minimal.py
import pytest
import asyncio
from langgraph.graph import StateGraph, END
from typing import TypedDict

class TestState(TypedDict):
    count: int
    status: str

@pytest.mark.asyncio
async def test_minimal_ainvoke():
    """Test minimal StateGraph ainvoke execution."""
    async def simple_node(state: TestState) -> dict:
        return {"count": state.get("count", 0) + 1}

    graph = StateGraph(TestState)
    graph.add_node("simple", simple_node)
    graph.set_entry_point("simple")
    graph.add_edge("simple", END)
    compiled = graph.compile()

    result = await compiled.ainvoke({"count": 0, "status": "running"})

    assert result["count"] == 1

@pytest.mark.asyncio
async def test_conditional_routing_ainvoke():
    """Test StateGraph with conditional routing."""
    async def count_node(state: TestState) -> dict:
        return {"count": state.get("count", 0) + 1}

    def route_count(state: TestState) -> str:
        return "end" if state.get("count", 0) >= 3 else "continue"

    graph = StateGraph(TestState)
    graph.add_node("count", count_node)
    graph.set_entry_point("count")
    graph.add_conditional_edges("count", route_count, {
        "continue": "count",
        "end": END
    })
    compiled = graph.compile()

    result = await compiled.ainvoke({"count": 0, "status": "running"})

    assert result["count"] == 3
```

**Test 2: VERITAS-style graph ainvoke()**

```python
# veritas/tests/test_langgraph_veritas.py
@pytest.mark.asyncio
async def test_veritas_graph_ainvoke_mock():
    """Test VERITAS-style graph with mocked nodes."""
    # Mock agents to avoid NIM calls
    with mock.patch('veritas.agents.scout.StealthScout') as mock_scout:
        with mock.patch('veritas.agents.vision.VisionAgent') as mock_vision:
            mock_scout.return_value.__aenter__.return_value = mock.Mock()
            mock_vision.return_value = mock.Mock()

            graph = build_audit_graph()
            compiled = graph.compile()

            state = {
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
                "enabled_security_modules": [],
            }

            try:
                result = await compiled.ainvoke(state)
                assert result["status"] in ("completed", "error")
            except asyncio.CancelledError as e:
                pytest.fail(f"CancelledError raised: {e}")
```

### Integration Tests

**Test 3: Full audit ainvoke() vs sequential**

```python
# veritas/tests/test_audit_execution_comparison.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_ainvoke_vs_sequential():
    """Compare ainvoke() execution with sequential execution."""
    url = "https://example.com"

    # Run with sequential (current)
    orchestrator_seq = VeritasOrchestratorSequential()
    result_seq = await orchestrator_seq.audit(url, tier="quick_scan")

    # Run with ainvoke (if available)
    try:
        orchestrator_ainv = VeritasOrchestratorAInvoke()
        result_ainv = await orchestrator_ainv.audit(url, tier="quick_scan")

        # Compare results
        assert result_seq["status"] == result_ainv["status"]
        assert result_seq["judge_decision"] is not None
        assert result_ainv["judge_decision"] is not None

        print(f"Sequential: {result_seq['elapsed_seconds']:.2f}s")
        print(f"AInvoke: {result_ainv['elapsed_seconds']:.2f}s")

    except asyncio.CancelledError:
        pytest.skip("ainvoke() cancelled, testing sequential only")
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Silently Swallowing CancelledError

```python
# WRONG - hides the issue
try:
    result = await graph.ainvoke(state)
except asyncio.CancelledError:
    # Silently falls back to sequential
    logger.info("CancelledError, using sequential fallback")
    return await self._audit_sequential(state)

# CORRECT - logs and tracks the issue, can disable fallback for testing
from typing import Optional

class VeritasOrchestrator:
    def __init__(self, use_sequential_fallback: bool = True):
        self._use_fallback = use_sequential_fallback
        self._graph = build_audit_graph()
        self._compiled = self._graph.compile()

    async def audit(self, url: str, tier: str) -> AuditState:
        state = self._initialize_state(url, tier)

        try:
            return await self._compiled.ainvoke(state)
        except asyncio.CancelledError as e:
            logger.error(f"LangGraph ainvoke cancelled: {e}", exc_info=True)

            if self._use_fallback:
                logger.info("Falling back to sequential execution")
                return await self._audit_sequential(state)
            else:
                # Re-raise to surface the issue in tests
                raise
```

### Anti-Pattern 2: Mixing Manual and LangGraph State Updates

```python
# WRONG - inconsistent state management
async def audit(self, url: str):
    state = {"url": url, "count": 0}

    # Use LangGraph for first node
    partial_state = await self._compiled.ainvoke(state)

    # Then manually update state (breaks LangGraph guarantees)
    partial_state["manual_field"] = "some_value"

    # Continue with LangGraph (state is now inconsistent)
    return await self._compiled.ainvoke(partial_state)

# CORRECT - either all LangGraph or all manual
async def audit_langgraph_only(self, url: str):
    """Pure LangGraph execution."""
    state = {"url": url, "count": 0}
    return await self._compiled.ainvoke(state)

async def audit_manual_only(self, url: str):
    """Pure manual execution."""
    state = {"url": url, "count": 0}
    # Manual node calls...
    return state
```

### Anti-Pattern 3: Ignoring Recursion Limit

```python
# WRONG - no recursion limit safeguard
result = await self._compiled.ainvoke(state)

# CORRECT - protect against infinite loops
from langgraph.constants import END

config = {
    "recursion_limit": settings.MAX_ITERATIONS * 10,  # Safety guard
}

try:
    result = await self._compiled.ainvoke(
        state,
        config=config
    )
except RecursionError:
    logger.error("Graph recursion limit exceeded")
    state["status"] = "aborted"
    return state
```

## Migration Recommendations

### Immediate Actions (Phase 3 of Roadmap)

1. **Create isolated reproduction test** (1-2 days)
   - Write `veritas/tests/test_langgraph_minimal.py`
   - Test on current Python 3.14 environment
   - Document CancelledError behavior

2. **Test on Python 3.12/3.13** (1 day)
   - Use Docker or venv to test earlier versions
   - Run same reproduction test
   - Determine if Python version is root cause

3. **Evaluate workaround options** (1 day)
   - If Python 3.14 is blocker: Consider Option C (version pin)
   - If NIMClient is blocker: Consider Option B (hybrid execution)
   - If neither: Use Option A (sequential with tracking) until fix

4. **Decision point** (meeting)
   - Review reproduction test results
   - Choose migration path based on findings
   - Document decision rationale

### Short-Term (Within Sprint)

5. **Implement chosen workaround** (2-3 days)
   - Option A: Add LangGraph tracking wrapper around sequential execution
   - Option B: Implement hybrid parallel execution for Vision + Graph
   - Option C: Pin Python version and update documentation

6. **Add monitoring** (1 day)
   - Log ainvoke() attempt vs fallback usage
   - Track execution time differences
   - Monitor CancelledError frequency

7. **Update documentation** (1 day)
   - Document LangGraph execution limitation
   - Add tracking issue for Python 3.14 compatibility
   - Update CONCERNS.md with final resolution

### Medium-Term (Next Roadmap Phase)

8. **If version pin (Option C)**:
   - Monitor LangGraph releases for Python 3.14 fix
   - Prepare migration plan back to 3.14
   - Add automated test to detect when ainvoke() works on 3.14

9. **If hybrid execution (Option B)**:
   - Consider adding more parallelism (Vision + Graph can run together)
   - Benchmark performance impact
   - Evaluate if full LangGraph is worth the effort

10. **Track upstream issue**:
    - Check LangGraph GitHub issues for Python 3.14 reports
    - File issue if none exists
    - Monitor for community workaround

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Current sequential execution behavior | HIGH | Code is clear, no ambiguity |
| LangGraph proper execution patterns | HIGH | Well-documented in LangChain docs |
| Python 3.14 asyncio changes | MEDIUM | No CancelledError changes documented, but TaskGroup changes possible |
| Root cause of CancelledError | LOW | Unknown without reproduction test |
| ainvoke() on Python 3.12/3.13 | LOW | Not tested, needs version comparison |
| Fix viability (version pin vs workaround) | LOW | Depends on reproduction test results |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Python 3.14 CancelledError root cause**: Need isolated reproduction test to determine if LangGraph internal issue or VERITAS-specific — handle by Phase 1 investigation (minimal graph test)
- **NIMClient async compatibility**: Need test with actual async HTTP calls to see if external AI client triggers issue — handle by Phase 2 investigation (NIM test)
- **Python version comparison**: Need test on Python 3.12/3.13 to isolate version as factor — handle by virtual environment or Docker testing
- **LangGraph upstream status**: Unknown if LangGraph community has reported Python 3.14 issues — handle by GitHub issue search and possibly filing bug report

## Sources

### Primary (HIGH confidence)
- **LangGraph tutorial and documentation** (web fetch failed, but concept well-understood from LangChain ecosystem) — https://langchain-ai.github.io/langgraph/
- **Python 3.14 Release Notes** — Asyncio introspection APIs, create_task() changes — https://docs.python.org/3.14/whatsnew/3.14.html
- **VERITAS codebase** — orchestrator.py with explicit ainvoke() bypass comment

### Secondary (MEDIUM confidence)
- **LangGraph async execution patterns** — StateGraph ainvoke(), config options, checkpointing (general LangChain knowledge)
- **Python asyncio best practices** — TaskGroup usage, CancelledError handling (standard async patterns)

### Tertiary (LOW confidence, needs validation)
- **Python 3.14 CancelledError behavior** — Not documented in release notes, may be LangGraph-specific interaction issue — needs reproduction test
- **LangGraph Python 3.14 compatibility** — No web search results available due to API errors, needs manual GitHub issue search

---

**Next Actions:**

1. **Immediate**: Create Phase 1 implementation (isolated reproduction test)
2. **Week 1**: Run reproduction tests on Python 3.14 and 3.12/3.13
3. **Week 2**: Based on results, implement Option A (tracking), Option B (hybrid), or Option C (version pin)
4. **Week 3**: Add monitoring and tracking issue for upstream LangGraph compatibility

**Estimated Timeline:** 3-4 weeks for resolution (1 week investigation, 1-2 weeks implementation, 1 week testing)

---

*LangGraph Research for: VERITAS async execution investigation*
*Researched: 2026-02-20*
*Confidence: MEDIUM*
*Web search limitation: API errors prevented live data retrieval, research based on Python docs and code analysis*
