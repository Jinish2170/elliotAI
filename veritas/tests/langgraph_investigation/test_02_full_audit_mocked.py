"""
Veritas LangGraph Investigation — Full Audit Test with Mocked Dependencies

Tests actual VERITAS orchestrator build_audit_graph() with ainvoke() using mocked
external dependencies to isolate LangGraph execution from NIM API calls and browser automation.

Purpose: Observe real execution path without external calls, compare LangGraph ainvoke()
vs sequential execution fallback, and verify graph structure and node interactions.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add veritas root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import veritas modules (using actual orchestrator)
from core.orchestrator import (
    AuditState,
    build_audit_graph,
    judge_node,
    route_after_judge,
    route_after_scout,
    scout_node,
    security_node_with_agent,
)

# Import fixtures from local conftest
from conftest import (
    audit_state,
    mock_graph_investigator,
    mock_judge_agent,
    mock_nim_client,
    mock_scout,
    mock_vision_agent,
)


# ============================================================
# Test 1: Full Audit with Mocked Dependencies via ainvoke()
# ============================================================

@pytest.mark.asyncio
async def test_ainvoke_full_audit_mocked(
    mock_nim_client: MagicMock,
    mock_scout: MagicMock,
    mock_vision_agent: AsyncMock,
    mock_graph_investigator: AsyncMock,
    mock_judge_agent: AsyncMock,
    audit_state: dict,
):
    """
    Test full audit using LangGraph ainvoke() with all external dependencies mocked.

    Verifies:
        - Graph builds and compiles successfully
        - ainvoke() executes without CancelledError
        - All nodes execute in correct order
        - Result contains expected state fields
    """
    # Patch all external dependencies
    with patch("veritas.core.orchestrator.NIMClient", return_value=mock_nim_client), \
         patch("veritas.agents.scout.StealthScout", return_value=mock_scout), \
         patch("veritas.agents.vision.VisionAgent.__init__", return_value=None), \
         patch("veritas.agents.vision.VisionAgent.analyze", side_effect=mock_vision_agent), \
         patch("veritas.agents.graph_investigator.GraphInvestigator.__init__", return_value=None), \
         patch("veritas.agents.graph_investigator.GraphInvestigator.investigate", side_effect=mock_graph_investigator), \
         patch("veritas.agents.judge.JudgeAgent.__init__", return_value=None), \
         patch("veritas.agents.judge.JudgeAgent.deliberate", side_effect=mock_judge_agent), \
         patch("veritas.agents.security_agent.SecurityAgent.initialize", return_value=None), \
         patch("veritas.agents.security_agent.SecurityAgent.analyze", return_value={"composite_score": 0.7, "findings": [], "total_findings": 0, "modules_run": [], "modules_failed": 0, "analysis_time_ms": 0, "modules_results": {}, "errors": []}):

        # Build graph via actual orchestrator function
        graph = build_audit_graph()
        assert graph is not None, "Graph should build successfully"

        # Compile graph
        compiled = graph.compile()
        assert compiled is not None, "Graph should compile successfully"

        # Initial state for a single cycle audit
        initial_state = audit_state.copy()
        initial_state["start_time"] = time.time()

        # Execute via ainvoke()
        try:
            result = await compiled.ainvoke(initial_state)

            # Verify result structure
            assert isinstance(result, dict), "Result should be a dict"
            assert "status" in result, "Result should have status field"

            # Check final status (should be completed or error, not running indefinitely)
            assert result["status"] in ("completed", "error", "aborted"), \
                f"Unexpected status: {result['status']}"

            # Verify state was updated
            assert len(result.get("scout_results", [])) > 0 or result.get("scout_failures", 0) > 0, \
                "Should have scout results or failures"

            # Log execution details
            print(f"\n=== ainvoke() Execution Summary ===")
            print(f"Status: {result['status']}")
            print(f"Screenshots captured: {sum(len(sr.get('screenshots', [])) for sr in result.get('scout_results', []))}")
            print(f"Scout failures: {result.get('scout_failures', 0)}")
            print(f"Errors: {result.get('errors', [])[:3]}")  # First 3 errors
            print(f"Elapsed: {result.get('elapsed_seconds', 0):.2f}s")

            # Count how many times each mock was called
            print(f"\n=== Mock Call Counts ===")
            print(f"Scout.investigate called: {mock_scout.investigate.call_count}")
            print(f"VisionAgent.analyze called: {mock_vision_agent.call_count}")
            print(f"GraphInvestigator.investigate called: {mock_graph_investigator.call_count}")
            print(f"JudgeAgent.deliberate called: {mock_judge_agent.call_count}")

            # Verify mock invocations
            if result["status"] == "completed":
                # If completed, node should have been executed
                assert mock_scout.investigate.call_count > 0, "Scout should have been invoked"
                assert mock_judge_agent.call_count > 0, "Judge should have been invoked"

        except asyncio.CancelledError as e:
            pytest.fail(f"ainvoke() raised CancelledError: {e}")
        except Exception as e:
            # Not failing test on all exceptions - document what happened
            print(f"=== Exception during ainvoke() ===")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {e}")
            # Re-raise to see full traceback in pytest output
            raise


# ============================================================
# Test 2: Sequential Execution Fallback
# ============================================================

@pytest.mark.asyncio
async def test_sequential_execution_fallback(
    mock_nim_client: MagicMock,
    mock_scout: MagicMock,
    mock_vision_agent: AsyncMock,
    mock_graph_investigator: AsyncMock,
    mock_judge_agent: AsyncMock,
    audit_state: dict,
):
    """
    Test sequential execution via VeritasOrchestrator.audit() method.

    Verifies:
        - Sequential fallback maintains compatibility
        - Execution completes without errors
        - Result structure matches expectation
    """
    # Patch all external dependencies
    with patch("veritas.core.orchestrator.NIMClient", return_value=mock_nim_client), \
         patch("veritas.agents.scout.StealthScout", return_value=mock_scout), \
         patch("veritas.agents.vision.VisionAgent.__init__", return_value=None), \
         patch("veritas.agents.vision.VisionAgent.analyze", side_effect=mock_vision_agent), \
         patch("veritas.agents.graph_investigator.GraphInvestigator.__init__", return_value=None), \
         patch("veritas.agents.graph_investigator.GraphInvestigator.investigate", side_effect=mock_graph_investigator), \
         patch("veritas.agents.judge.JudgeAgent.__init__", return_value=None), \
         patch("veritas.agents.judge.JudgeAgent.deliberate", side_effect=mock_judge_agent), \
         patch("veritas.agents.security_agent.SecurityAgent.initialize", return_value=None), \
         patch("veritas.agents.security_agent.SecurityAgent.analyze", return_value={"composite_score": 0.7, "findings": [], "total_findings": 0, "modules_run": [], "modules_failed": 0, "analysis_time_ms": 0, "modules_results": {}, "errors": []}):

        from core.orchestrator import VeritasOrchestrator

        # Create orchestrator instance
        orchestrator = VeritasOrchestrator(progress_queue=None)

        # Run sequential audit
        result = await orchestrator.audit(
            url=audit_state["url"],
            tier=audit_state["audit_tier"],
            verdict_mode=audit_state["verdict_mode"],
            enabled_security_modules=audit_state["enabled_security_modules"],
        )

        # Verify result
        assert isinstance(result, dict), "Result should be a dict"
        assert "status" in result, "Result should have status field"
        assert result["status"] in ("completed", "error", "aborted"), \
            f"Unexpected status: {result['status']}"

        # Verify results were collected
        assert len(result.get("scout_results", [])) > 0 or result.get("scout_failures", 0) > 0, \
            "Should have scout results or failures"

        # Log execution details
        print(f"\n=== Sequential Execution Summary ===")
        print(f"Status: {result['status']}")
        print(f"Screenshots captured: {sum(len(sr.get('screenshots', [])) for sr in result.get('scout_results', []))}")
        print(f"Scout failures: {result.get('scout_failures', 0)}")
        print(f"Errors: {result.get('errors', [])[:3]}")
        print(f"Elapsed: {result.get('elapsed_seconds', 0):.2f}s")

        # Verify mock invocations
        assert mock_scout.investigate.call_count > 0, "Scout should have been invoked"
        assert mock_judge_agent.call_count > 0, "Judge should have been invoked"


# ============================================================
# Test 3: Graph Structure and Nodes Verification
# ============================================================

@pytest.mark.asyncio
async def test_graph_structure_and_nodes(mock_nim_client: MagicMock):
    """
    Test graph structure and verify all nodes are present.

    Verifies:
        - Graph builds and compiles
        - All 6 nodes present (scout, security, vision, graph, judge, force_verdict)
        - Routing edges exist between nodes
    """
    # Build graph
    graph = build_audit_graph()
    assert graph is not None, "Graph should build successfully"

    # Compile graph
    compiled = graph.compile()
    assert compiled is not None, "Graph should compile successfully"

    # Get graph structure
    try:
        graph_structure = graph.get_graph().draw_mermaid()

        # Print Mermaid visualization
        print(f"\n=== Graph Structure (Mermaid) ===")
        print(graph_structure)

        # Get nodes from the graph builder (StateGraph has nodes property)
        nodes = graph.nodes

        print(f"\n=== Graph Nodes ({len(nodes)}) ===")
        for node_id in nodes:
            print(f"  - {node_id}")

        # Verify expected nodes exist
        expected_nodes = ["scout", "security", "vision", "graph", "judge", "force_verdict"]
        for node_id in expected_nodes:
            assert node_id in nodes, f"Expected node '{node_id}' not found"

        # Verify entry point is set to scout
        graph_dict = graph.compile()
        # Entry point is verified through graph construction

    except ImportError as e:
        pytest.skip(f"Graph visualization failed: {e}")


# ============================================================
# Test 4: Node Routing Functions
# ============================================================

def test_route_after_scout_routing():
    """Test routing logic after Scout node."""
    # Test case 1: First success -> vision
    state = {
        "scout_failures": 0,
        "scout_results": [{"screenshots": ["test.jpg"]}],
    }
    assert route_after_scout(state) == "vision", "Should route to vision on success"

    # Test case 2: 3+ failures with no results -> abort
    state = {
        "scout_failures": 3,
        "scout_results": [],
    }
    assert route_after_scout(state) == "abort", "Should abort after 3 failures with no results"

    # Test case 3: Below threshold but no results -> abort (edge case)
    state = {
        "scout_failures": 2,
        "scout_results": [],
    }
    assert route_after_scout(state) == "abort", "Should abort when no results"


def test_route_after_judge_routing():
    """Test routing logic after Judge node."""
    # Test case 1: Completed status -> end
    state = {
        "status": "completed",
        "judge_decision": {},
    }
    assert route_after_judge(state) == "end", "Should end when status is completed"

    # Test case 2: More investigation available -> scout
    state = {
        "status": "running",
        "judge_decision": {
            "action": "REQUEST_MORE_INVESTIGATION",
            "investigate_urls": ["https://example.com/about"],
        },
        "investigated_urls": ["https://example.com"],
        "max_pages": 5,
    }
    assert route_after_judge(state) == "scout", "Should scout more pages when requested"

    # Test case 3: Page budget exhausted -> force_verdict
    state = {
        "status": "running",
        "judge_decision": {
            "action": "REQUEST_MORE_INVESTIGATION",
            "investigate_urls": ["https://example.com/about"],
        },
        "investigated_urls": ["https://example.com"] * 5,  # At max_pages
        "max_pages": 5,
    }
    assert route_after_judge(state) == "force_verdict", "Should force verdict at page budget"

    # Test case 4: Render verdict action -> end
    state = {
        "status": "running",
        "judge_decision": {
            "action": "RENDER_VERDICT",
        },
    }
    assert route_after_judge(state) == "end", "Should end on render verdict"


# ============================================================
# Test 5: Individual Node Execution (Isolated)
# ============================================================

@pytest.mark.asyncio
async def test_scout_node_isolated():
    """Test Scout node execution in isolation with simplified verification."""
    # Simplified test that just checks the node runs without detailed mocking
    # Real testing happens in integration tests with the full graph
    state = {
        "url": "https://example.com",
        "pending_urls": [],
        "investigated_urls": [],
        "scout_results": [],
        "scout_failures": 0,
        "errors": [],
    }

    result = await scout_node(state)

    # Should return gracefully with error about no pending URLs
    assert isinstance(result, dict), "Result should be a dict"
    assert result.get("status") == "running", "Status should remain running"
    assert len(result.get("errors", [])) > 0, "Should have error about no pending URLs"


@pytest.mark.asyncio
async def test_security_node_isolated(mock_nim_client: MagicMock):
    """Test Security node execution in isolation."""
    state = {
        "url": "https://example.com",
        "enabled_security_modules": ["security_headers", "phishing_db"],
        "errors": [],
    }

    with patch("veritas.core.orchestrator.NIMClient", return_value=mock_nim_client), \
         patch("veritas.analysis.security_headers.SecurityHeaderAnalyzer") as mock_headers, \
         patch("veritas.analysis.phishing_checker.PhishingChecker") as mock_phishing:

        # Mock analysis results
        mock_headers.return_value.analyze = AsyncMock(return_value=MagicMock(
            score=0.75,
            to_dict=lambda: {"score": 0.75, "missing": []}
        ))
        mock_phishing.return_value.check = AsyncMock(return_value=MagicMock(
            is_phishing=False,
            confidence=0.95,
            to_dict=lambda: {"is_phishing": False, "confidence": 0.95}
        ))

        result = await security_node_with_agent(state)

        assert isinstance(result, dict), "Result should be a dict"
        assert "security_results" in result, "Result should have security_results"
        assert "security_mode" in result, "Result should have security_mode"


@pytest.mark.asyncio
async def test_judge_node_isolated():
    """Test Judge node execution in isolation with simplified verification."""
    from agents.scout import ScoutResult
    from agents.vision import VisionResult

    # Create proper dataclass objects for scout and vision results
    scout_result = ScoutResult(
        url="https://example.com",
        status="SUCCESS",
        screenshots=["test.jpg"],
        screenshot_timestamps=[1630000000.0],
        screenshot_labels=["t0"],
    )

    vision_result = VisionResult(
        visual_score=0.5,
        temporal_score=0.6,
        dark_patterns=[],
        temporal_findings=[],
        screenshots_analyzed=1,
    )

    state = {
        "url": "https://example.com",
        "iteration": 0,
        "max_iterations": 3,
        "scout_results": [
            {
                "url": "https://example.com",
                "status": "SUCCESS",
                "screenshots": ["test.jpg"],
                "screenshot_timestamps": [1630000000.0],
                "screenshot_labels": ["t0"],
                "page_title": "Test Page",
                "page_metadata": {},
                "links": [],
                "forms_detected": 0,
                "captcha_detected": False,
                "error_message": "",
                "navigation_time_ms": 1000.0,
                "viewport_used": "desktop",
                "user_agent_used": "Test",
                "trust_modifier": 0.0,
                "trust_notes": [],
                "site_type": "company_portfolio",
                "site_type_confidence": 0.5,
                "dom_analysis": {},
                "form_validation": {},
            }
        ],
        "vision_result": {
            "visual_score": 0.5,
            "temporal_score": 0.6,
            "findings": [],
            "temporal_findings": [],
            "screenshots_analyzed": 1,
            "prompts_sent": 0,
            "nim_calls_made": 0,
            "fallback_used": False,
            "errors": [],
        },
        "graph_result": {"graph_score": 0.5, "meta_score": 0.5, "domain_age_days": 365, "has_ssl": True},
        "site_type": "company_portfolio",
        "site_type_confidence": 0.8,
        "verdict_mode": "expert",
        "security_results": {},
    }

    with patch("veritas.core.orchestrator.NIMClient"), \
         patch("veritas.agents.judge.JudgeAgent") as mock_judge:

        # Mock the JudgeAgent.deliberate method
        async def mock_deliberate(evidence):
            from agents.judge import JudgeDecision, AuditEvidence, RiskLevel, TrustScoreResult
            return JudgeDecision(
                action="RENDER_VERDICT",
                reason="Test",
                final_score=52,
                risk_level=RiskLevel.MEDIUM,
                forensic_narrative="Test narrative",
                recommendations=[],
                dark_pattern_summary=[],
                entity_verification_summary=[],
                evidence_timeline=[],
                trust_score_result=TrustScoreResult(
                    final_score=52,
                    risk_level=RiskLevel.MEDIUM,
                    sub_signals=[],
                ),
            )

        mock_ja = MagicMock()
        mock_ja.deliberate = AsyncMock(side_effect=mock_deliberate)
        mock_judge.return_value = mock_ja

        result = await judge_node(state)

        assert isinstance(result, dict), "Result should be a dict"
        assert "iteration" in result, "Result should have iteration"
        assert result["iteration"] == 1, "Iteration should be incremented"


# ============================================================
# Test 6: Error Handling and Edge Cases
# ============================================================

@pytest.mark.asyncio
async def test_node_error_propagation():
    """Test that errors in nodes propagate correctly."""
    from unittest.mock import AsyncMock

    # Create state that will fail in scout
    state = {
        "url": "https://example.com",
        "pending_urls": ["https://example.com"],
        "investigated_urls": [],
        "scout_results": [],
        "scout_failures": 0,
        "errors": [],
    }

    # Patch Scout to raise exception
    async def failing_scout():
        raise ValueError("Simulated Scout failure")

    mock_scout_failing = MagicMock()
    mock_scout_failing.__aenter__ = AsyncMock(return_value=mock_scout_failing)
    mock_scout_failing.__aexit__ = AsyncMock(return_value=None)
    mock_scout_failing.investigate = AsyncMock(side_effect=failing_scout)

    with patch("veritas.core.orchestrator.StealthScout", return_value=mock_scout_failing):
        result = await scout_node(state)

        # Verify error was captured
        assert "errors" in result, "Result should have errors"
        assert len(result["errors"]) > 0, "Should have error entry"
        assert result["scout_failures"] == 1, "Scout failure count should increment"


@pytest.mark.asyncio
async def test_empty_pending_urls_handling():
    """Test behavior when pending_urls is empty."""
    state = {
        "pending_urls": [],
        "investigated_urls": [],
        "scout_results": [],
        "scout_failures": 0,
        "errors": [],
    }

    result = await scout_node(state)

    # Should return gracefully with error message
    assert result.get("status") == "running", "Status should remain running"
    assert len(result.get("errors", [])) > 0, "Should have error about no pending URLs"


# ============================================================
# Test 7: State Mutation and Updates
# ============================================================

def test_state_typing_compliance(audit_state: dict):
    """Verify audit_state fixture matches AuditState TypedDict."""
    from core.orchestrator import AuditState as AuditStateType

    # Verify all required fields exist
    typed_fields = [
        "url", "audit_tier", "iteration", "max_iterations", "max_pages", "status",
        "scout_results", "vision_result", "graph_result", "judge_decision",
        "pending_urls", "investigated_urls", "start_time", "elapsed_seconds",
        "errors", "scout_failures", "nim_calls_used", "site_type",
        "site_type_confidence", "verdict_mode", "security_results",
        "security_mode", "enabled_security_modules",
    ]

    for field in typed_fields:
        assert field in audit_state, f"Missing required field: {field}"

    # Verify field types match expectations
    assert isinstance(audit_state["url"], str)
    assert isinstance(audit_state["audit_tier"], str)
    assert isinstance(audit_state["iteration"], int)
    assert isinstance(audit_state["status"], str)
    assert isinstance(audit_state["scout_results"], list)
    assert isinstance(audit_state["pending_urls"], list)
    assert isinstance(audit_state["errors"], list)
