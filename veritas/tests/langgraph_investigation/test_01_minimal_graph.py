"""
Minimal reproduction test for LangGraph ainvoke() behavior with Python 3.11+ asyncio.

Purpose: Isolate CancelledError root cause by stripping away VERITAS complexity.
Establish baseline LangGraph behavior on minimal graph to observe any async issues.

Tests:
- test_ainvoke_minimal_graph: Execute minimal StateGraph via ainvoke()
- test_ainvoke_vs_manual_execution: Compare ainvoke with manual sequential execution
- test_graph_visualization: Verify graph visualization output

Python version note: Running on Python 3.11.5, not 3.14 as originally documented.
Investigation covers 3.11+ asyncio compatibility with LangGraph.
"""
import asyncio
import pytest
import sys
import time
from typing import TypedDict
from pathlib import Path

# Add veritas to path for module imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from langgraph.graph import StateGraph, END


class MinimalState(TypedDict):
    """Minimal state for isolated LangGraph testing."""
    count: int
    status: str
    error_log: list[str]


async def async_node(state: MinimalState) -> dict:
    """
    Minimal async node that simulates agent behavior.

    Performs simple async work (sleep) and increments state counter.
    Wraps error handling to capture any exceptions for logging.
    """
    try:
        # Simulate async work (like NIM call or agent processing)
        await asyncio.sleep(0.01)

        # Return state update
        return {"count": state.get("count", 0) + 1}
    except Exception as e:
        # Log error to state for investigation
        return {"error_log": state.get("error_log", []) + [str(e)]}


def route_by_count(state: MinimalState) -> str:
    """
    Simple routing function based on state counter.

    Routes to "end" once count reaches 3, otherwise continues.
    """
    if state.get("count", 0) >= 3:
        return "end"
    return "continue"


def build_minimal_graph() -> StateGraph:
    """
    Build minimal StateGraph for LangGraph testing.

    Graph structure:
        START -> start -> [route_by_count] -> continue -> [route_by_count] -> END

    This isolates LangGraph behavior without VERITAS complexity.
    """
    graph = StateGraph(MinimalState)

    # Add nodes (both use the same async_node for minimal complexity)
    graph.add_node("start", async_node)
    graph.add_node("continue", async_node)

    # Set entry point
    graph.set_entry_point("start")

    # Add conditional edges with routing
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
    """
    Test LangGraph ainvoke() execution on minimal graph.

    This is the primary test to verify basic LangGraph behavior.
    Expected to complete without CancelledError on Python 3.11+.

    If CancelledError occurs, it indicates:
    - LangGraph async implementation issue
    - Windows + Python 3.11 asyncio event loop incompatibility
    - LangGraph version-specific bug

    Logs Python version for investigation reference.
    """
    graph = build_minimal_graph()

    print(f"\nPython version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Initial state
    initial_state: MinimalState = {
        "count": 0,
        "status": "running",
        "error_log": []
    }

    try:
        # Execute via LangGraph ainvoke
        result = await graph.ainvoke(initial_state)

        # Verify result
        assert result["status"] == "running", "Status should remain unchanged"
        assert result["count"] == 3, f"Count should be 3, got {result['count']}"
        assert not result.get("error_log"), f"No errors expected, got: {result.get('error_log', [])}"

        print(f"✓ ainvoke() succeeded: count={result['count']}, status={result['status']}")
        print(f"✓ No CancelledError observed on Python {sys.version_info.major}.{sys.version_info.minor}")

    except asyncio.CancelledError as e:
        # This is the error we're investigating
        pytest.fail(
            f"CancelledError raised in minimal graph ainvoke on Python {sys.version_info.major}.{sys.version_info.minor}.\n"
            f"This confirms LangGraph async issue.\n"
            f"Error: {e}\n"
            f"Next steps: Investigate subprocess isolation, Windows event loop, or LangGraph version.",
            pytrace=True
        )
    except Exception as e:
        # Unexpected error
        pytest.fail(
            f"Unexpected error in minimal graph ainvoke: {type(e).__name__}: {e}",
            pytrace=True
        )


@pytest.mark.asyncio
async def test_ainvoke_vs_manual_execution():
    """
    Compare ainvoke() execution with manual sequential execution.

    This test proves that:
    1. ainvoke() behavior matches manual sequential execution
    2. Any CancelledError is specific to LangGraph, not the node logic
    3. The async_node function works correctly in isolation

    If ainvoke fails but manual passes, the issue is in LangGraph internals.
    """
    # Test 1: ainvoke execution
    graph = build_minimal_graph()
    ainvoke_result = await graph.ainvoke({
        "count": 0,
        "status": "running",
        "error_log": []
    })

    print(f"ainvoke() result: count={ainvoke_result['count']}")

    # Test 2: Manual sequential execution
    state = MinimalState(count=0, status="running", error_log=[])

    iterations = 0
    max_iterations = 10  # Safety guard
    while state.get("count", 0) < 3 and iterations < max_iterations:
        state.update(await async_node(state))
        iterations += 1

    manual_result = dict(state)

    print(f"Manual execution result: count={manual_result['count']}, iterations={iterations}")

    # Compare results
    assert ainvoke_result["count"] == manual_result["count"], (
        f"Count mismatch: ainvoke={ainvoke_result['count']}, manual={manual_result['count']}"
    )
    assert ainvoke_result["status"] == manual_result["status"]
    assert not ainvoke_result.get("error_log")
    assert not manual_result.get("error_log")

    print(f"✓ ainvoke() matches manual execution: count={ainvoke_result['count']}")


@pytest.mark.asyncio
async def test_graph_visualization():
    """
    Test graph visualization via LangGraph's print_ascii().

    Verifies that:
    1. Graph structure is correctly defined
    2. Visualization produces parseable output (if grandalf installed)
    3. Graph can be inspected for debugging purposes

    This enables future debugging and investigation of graph topology.

    Note: Requires `grandalf` package for ASCII visualization.
    If not installed, test verifies graph structure without visualization.
    """
    graph = build_minimal_graph()

    # Verify graph has expected nodes (works without grandalf)
    actual_nodes = set(graph.get_graph().nodes.keys())
    expected_nodes = {"start", "continue", "__start__", "__end__"}

    assert expected_nodes.issubset(actual_nodes), (
        f"Missing expected nodes. Expected: {expected_nodes}, Actual: {actual_nodes}"
    )

    print(f"✓ Graph structure verified, nodes: {sorted(actual_nodes)}")

    # Generate visualization (requires grandalf)
    try:
        ascii_graph = graph.get_graph().print_ascii()
        print(f"\n{ascii_graph}")
        print(f"✓ Graph visualization successful")
    except ImportError as e:
        # grandalf not installed - not critical for investigation
        pytest.skip(f"Graph visualization requires grandalf package: {e}\nInstall with: pip install grandalf")
    except Exception as e:
        # Other visualization errors
        pytest.fail(
            f"Graph visualization failed: {type(e).__name__}: {e}\n"
            f"This indicates graph structure issue.",
            pytrace=True
        )


@pytest.mark.asyncio
async def test_conditional_routing():
    """
    Test LangGraph conditional routing with state-dependent decisions.

    Verifies that:
    1. Routing function receives correct state
    2. Conditional edges work correctly
    3. Graph terminates at END as expected

    This isolates routing behavior from node execution.
    """
    graph = build_minimal_graph()

    result = await graph.ainvoke({
        "count": 0,
        "status": "routing_test",
        "error_log": []
    })

    # Should run exactly 3 times (0 -> 1 -> 2 -> 3, then route to END)
    assert result["count"] == 3
    assert result["status"] == "routing_test"

    print(f"✓ Conditional routing correct: executed 3 times, terminated at END")


@pytest.mark.asyncio
async def test_error_handling_in_node():
    """
    Test error handling when node encounters exception.

    Verifies that:
    1. Errors in nodes are captured properly
    2. Error state is propagated correctly
    3. Test framework catches test failures

    This provides baseline for comparing error behavior with full VERITAS graph.
    """

    async def failing_node(state: MinimalState) -> dict:
        """Node that deliberately raises an exception."""
        await asyncio.sleep(0.001)
        raise ValueError("Test error for error handling verification")

    graph = StateGraph(MinimalState)
    graph.add_node("fail", failing_node)
    graph.set_entry_point("fail")
    graph.add_edge("fail", END)
    compiled = graph.compile()

    # The node raises ValueError, which should propagate
    with pytest.raises(ValueError, match="Test error for error handling verification"):
        await compiled.ainvoke({
            "count": 0,
            "status": "error_test",
            "error_log": []
        })

    print("✓ Error propagation working correctly")


if __name__ == "__main__":
    # Run tests directly for manual verification
    print("=" * 60)
    print("Running minimal graph tests manually")
    print(f"Python version: {sys.version}")
    print("=" * 60)

    async def main():
        print("\n--- Test 1: ainvoke minimal graph ---")
        try:
            await test_ainvoke_minimal_graph()
        except Exception as e:
            print(f"FAILED: {e}")

        print("\n--- Test 2: ainvoke vs manual ---")
        try:
            await test_ainvoke_vs_manual_execution()
        except Exception as e:
            print(f"FAILED: {e}")

        print("\n--- Test 3: graph visualization ---")
        try:
            await test_graph_visualization()
        except Exception as e:
            print(f"FAILED: {e}")

        print("\n--- Test 4: conditional routing ---")
        try:
            await test_conditional_routing()
        except Exception as e:
            print(f"FAILED: {e}")

        print("\n--- Test 5: error handling ---")
        try:
            await test_error_handling_in_node()
        except Exception as e:
            print(f"FAILED: {e}")

    asyncio.run(main())
    print("\n" + "=" * 60)
    print("Manual test run complete")
    print("=" * 60)
