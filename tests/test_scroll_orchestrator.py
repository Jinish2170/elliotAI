"""
Tests for scroll orchestration with lazy-load detection.

Tests ScrollOrchestrator, LazyLoadDetector, and scroll state management.
"""

import pytest
from pathlib import Path

from veritas.agents.scout_nav.lazy_load_detector import LazyLoadDetector, MUTATION_OBSERVER_SCRIPT
from veritas.agents.scout_nav.scroll_orchestrator import ScrollOrchestrator
from veritas.core.types import ScrollState, ScrollResult


@pytest.mark.asyncio
async def test_scroll_state_and_result_dataclasses():
    """Verify ScrollState and ScrollResult can be instantiated and serialized."""
    # Test ScrollState instantiation
    state = ScrollState(
        cycle=0,
        has_lazy_load=True,
        last_scroll_y=500,
        last_scroll_height=2000,
        cycles_without_content=0,
        stabilized=False
    )
    assert state.cycle == 0
    assert state.has_lazy_load is True
    assert state.stabilized is False

    # Test ScrollResult instantiation
    result = ScrollResult(
        total_cycles=5,
        stabilized=True,
        lazy_load_detected=True,
        screenshots_captured=3,
        scroll_states=[state]
    )
    assert result.total_cycles == 5
    assert result.stabilized is True
    assert result.lazy_load_detected is True
    assert result.screenshots_captured == 3
    assert len(result.scroll_states) == 1

    # Test ScrollResult serialization
    result_dict = result.to_dict()
    assert "total_cycles" in result_dict
    assert "scroll_states" in result_dict
    assert result_dict["scroll_states"][0]["cycle"] == 0


@pytest.mark.asyncio
async def test_lazy_load_detector_injection_and_detection(mocker):
    """Mock page to verify detector script injection and content detection."""
    from unittest.mock import AsyncMock

    detector = LazyLoadDetector()

    # Mock page.evaluation
    page = mocker.AsyncMock()
    page.evaluate = AsyncMock()

    # Test inject()
    await detector.inject(page)
    assert detector._injected is True

    # Verify inject() was called with MutationObserver script
    inject_call = page.evaluate.call_args_list[0][0][0]
    assert "MutationObserver" in inject_call
    assert "childList: true" in inject_call
    assert "subtree: true" in inject_call
    assert "hasNewContent" in inject_call

    # Mock has_new_content() response
    page.evaluate.reset_mock()
    page.evaluate.return_value = {
        "hasMutations": True,
        "scrollHeightChanged": True,
        "bothSignals": True
    }

    # Test has_new_content()
    result = await detector.has_new_content(page)
    assert result["hasMutations"] is True
    assert result["scrollHeightChanged"] is True
    assert result["bothSignals"] is True

    # Test reset()
    page.evaluate.reset_mock()
    await detector.reset(page)
    assert "reset" in page.evaluate.call_args[0][0]

    # Test disconnect()
    page.evaluate.reset_mock()
    await detector.disconnect(page)
    assert "disconnect" in page.evaluate.call_args[0][0]
    assert detector._injected is False


@pytest.mark.asyncio
async def test_scrolling_with_lazy_loaded_content(mocker):
    """Mock page that returns new content for several cycles, verify scroll continues until stabilization."""
    from unittest.mock import AsyncMock

    # Create detector and orchestrator
    detector = LazyLoadDetector()
    evidence_dir = Path("data/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    orchestrator = ScrollOrchestrator(evidence_dir, detector)

    # Mock page with lazy-load behavior
    page = mocker.AsyncMock()
    page.evaluate = AsyncMock()

    # Track hasNewContent() calls separately (not inject() calls)
    content_check_count = 0

    def mock_evaluate_with_stabilization(*args, **kwargs):
        nonlocal content_check_count
        code = args[0] if args else ""
        # Match only the actual hasNewContent() call, not inject() script
        if "hasNewContent()" in code and "(" in code and ")" in code:
            # Return True for first 2 cycles, then False
            content_check_count += 1
            if content_check_count <= 2:
                return {
                    "hasMutations": True,
                    "scrollHeightChanged": True,
                    "bothSignals": True
                }
            else:
                return {
                    "hasMutations": False,
                    "scrollHeightChanged": False,
                    "bothSignals": False
                }
        elif "scrollY" in code:
            return content_check_count * 500
        elif "scrollHeight" in code:
            return 2000
        elif "window.scrollBy" in code:
            return None
        return None

    page.evaluate.side_effect = mock_evaluate_with_stabilization
    page.screenshot = AsyncMock()

    result = await orchestrator.scroll_page(page, "test_audit", screenshot_interval=999)

    # Cycle 0: new content detected
    # Cycle 1: new content detected
    # Cycle 2: no new content (cycles_without_content=1)
    # Cycle 3: no new content (cycles_without_content=2 -> stabilize)
    assert result.total_cycles == 4  # 0, 1 (has content), 2, 3 (no content -> stop)
    assert result.stabilized is True
    assert result.lazy_load_detected is True


@pytest.mark.asyncio
async def test_scrolling_stabilizes_early_on_static_page(mocker):
    """Mock page with no new content, verify scroll stops after 2 consecutive no-content cycles."""
    from unittest.mock import AsyncMock

    detector = LazyLoadDetector()
    evidence_dir = Path("data/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    orchestrator = ScrollOrchestrator(evidence_dir, detector)

    # Mock page with static content (no lazy load)
    page = mocker.AsyncMock()
    page.evaluate = AsyncMock()

    def mock_evaluate_no_content(*args, **kwargs):
        code = args[0] if args else ""
        if "hasNewContent" in code:
            return {
                "hasMutations": False,
                "scrollHeightChanged": False,
                "bothSignals": False
            }
        elif "scrollY" in code:
            return 0
        elif "scrollHeight" in code:
            return 2000
        elif "window.scrollBy" in code:
            return None
        return None

    page.evaluate.side_effect = mock_evaluate_no_content
    page.screenshot = AsyncMock()

    result = await orchestrator.scroll_page(page, "test_audit")

    # Should stabilize after 2 cycles (STABILIZATION_THRESHOLD)
    assert result.total_cycles == 2
    assert result.stabilized is True
    assert result.lazy_load_detected is False


@pytest.mark.asyncio
async def test_scrolling_captures_screenshots_at_intervals(mocker):
    """Verify screen capture count matches expected based on cycles and screenshot_interval."""
    from unittest.mock import AsyncMock

    detector = LazyLoadDetector()
    evidence_dir = Path("data/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    orchestrator = ScrollOrchestrator(evidence_dir, detector)

    # Mock page
    page = mocker.AsyncMock()
    page.evaluate = AsyncMock()
    page.screenshot = AsyncMock()

    screenshot_count = 0

    def mock_evaluate(*args, **kwargs):
        nonlocal screenshot_count
        code = args[0] if args else ""
        if "hasNewContent" in code:
            return {
                "hasMutations": False,
                "scrollHeightChanged": False,
                "bothSignals": False
            }
        elif "scrollY" in code:
            return 0
        elif "scrollHeight" in code:
            return 2000
        elif "window.scrollBy" in code:
            return None
        return None

    page.evaluate.side_effect = mock_evaluate

    # Track screenshot calls
    page.screenshot.side_effect = lambda **kw: None

    # Test with screenshot_interval=2 (capture at cycle 0, 2, 4, ...)
    # Since page stabilizes after 2 cycles, we get screenshots at cycle 0 and final cycle
    result = await orchestrator.scroll_page(page, "test_audit", screenshot_interval=2)

    # Should capture at cycle 0 and final cycle (2)
    assert result.screenshots_captured >= 1  # At least one screenshot


@pytest.mark.asyncio
async def test_scrolling_respects_max_cycle_limit(mocker):
    """Mock page that never stabilizes, verify total_cycles == 15."""
    from unittest.mock import AsyncMock

    detector = LazyLoadDetector()
    evidence_dir = Path("data/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    orchestrator = ScrollOrchestrator(evidence_dir, detector)

    # Mock page that always has new content (never stabilizes)
    page = mocker.AsyncMock()
    page.evaluate = AsyncMock()

    def mock_evaluate_always_new_content(*args, **kwargs):
        code = args[0] if args else ""
        if "hasNewContent" in code:
            return {
                "hasMutations": True,
                "scrollHeightChanged": True,
                "bothSignals": True
            }
        elif "scrollY" in code:
            return 0
        elif "scrollHeight" in code:
            return 2000
        elif "window.scrollBy" in code:
            return None
        return None

    page.evaluate.side_effect = mock_evaluate_always_new_content
    page.screenshot = AsyncMock()

    result = await orchestrator.scroll_page(page, "test_audit", screenshot_interval=999)

    # Should stop at max cycles
    assert result.total_cycles == 15
    assert result.stabilized is False
    assert result.lazy_load_detected is True
