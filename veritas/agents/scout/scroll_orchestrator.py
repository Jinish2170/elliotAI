"""
ScrollOrchestrator - Intelligent scrolling with lazy-load detection.

Orchestrates incremental page scrolling with screenshot capture and
lazy-load monitoring for comprehensive page content capture.
"""

import asyncio
import logging
from pathlib import Path

from playwright.async_api import Page

from veritas.agents.scout.lazy_load_detector import LazyLoadDetector
from veritas.core.types import ScrollResult, ScrollState

logger = logging.getLogger("veritas.agents.scout.scroll_orchestrator")


class ScrollOrchestrator:
    """
    Orchestrates intelligent page scrolling with lazy-load detection.

    Performs incremental scrolling with configurable wait times,
    monitoring for DOM mutations to detect lazy-loaded content.
    Captures screenshots at scroll intervals for temporal analysis.

    Usage:
        orchestrator = ScrollOrchestrator(evidence_dir, detector)
        result = await orchestrator.scroll_page(page, audit_id)
    """

    # Class constants
    MAX_SCROLL_CYCLES = 15  # Maximum scroll iterations
    STABILIZATION_THRESHOLD = 2  # Consecutive cycles with no new content
    SCROLL_CHUNK_RATIO = 0.5  # Scroll by page height * 0.5 each cycle
    SCROLL_WAIT_MS = 400  # Wait 400ms after each scroll

    def __init__(self, evidence_dir: Path, detector: LazyLoadDetector):
        """
        Initialize ScrollOrchestrator.

        Args:
            evidence_dir: Directory to store scroll screenshots
            detector: LazyLoadDetector instance for content monitoring
        """
        self._evidence_dir = Path(evidence_dir)
        self._evidence_dir.mkdir(parents=True, exist_ok=True)
        self._detector = detector

    async def scroll_page(
        self,
        page: Page,
        audit_id: str,
        screenshot_interval: int = 2,
    ) -> ScrollResult:
        """
        Perform intelligent incremental scrolling with lazy-load detection.

        Process:
        1. Inject LazyLoadDetector
        2. Scroll incrementally (page_height * 0.5 per cycle)
        3. Wait 400ms for lazy loading
        4. Check for new content via MutationObserver
        5. Track stabilization (2 consecutive cycles with no new content)
        6. Capture screenshots at intervals
        7. Stop when stabilized OR max 15 cycles

        Args:
            page: Playwright Page object
            audit_id: Unique audit ID for screenshot naming
            screenshot_interval: Capture screenshot every N cycles (default: 2)

        Returns:
            ScrollResult with complete scroll statistics and state history
        """
        # Inject detector at start
        await self._detector.inject(page)

        scroll_states = []
        screenshot_paths = []
        lazy_load_detected = False
        cycles_without_content = 0

        logger.info(f"Starting intelligent scroll for {audit_id}")

        for cycle in range(self.MAX_SCROLL_CYCLES):
            # Record current scroll position before scroll
            scroll_y_before = await page.evaluate("window.scrollY")
            scroll_height_before = await page.evaluate("document.documentElement.scrollHeight")

            # Scroll incrementally (page height / 2)
            try:
                await page.evaluate(f"""
                    window.scrollBy(0, window.innerHeight * {self.SCROLL_CHUNK_RATIO})
                """)
            except Exception as e:
                logger.warning(f"Scroll failed at cycle {cycle}: {e}")
                break

            # Wait for lazy loading
            await asyncio.sleep(self.SCROLL_WAIT_MS / 1000)

            # Check for new content
            content_signals = await self._detector.has_new_content(page)

            # Track if lazy loading was ever detected
            has_new_content = content_signals.get("bothSignals", False)
            if has_new_content:
                lazy_load_detected = True

            # Track consecutive cycles without new content
            if has_new_content:
                cycles_without_content = 0
            else:
                cycles_without_content += 1

            stabilized = cycles_without_content >= self.STABILIZATION_THRESHOLD

            # Record current scroll state
            scroll_y_after = await page.evaluate("window.scrollY")
            scroll_height_after = await page.evaluate("document.documentElement.scrollHeight")

            state = ScrollState(
                cycle=cycle,
                has_lazy_load=has_new_content,
                last_scroll_y=scroll_y_after,
                last_scroll_height=scroll_height_after,
                cycles_without_content=cycles_without_content,
                stabilized=stabilized,
            )
            scroll_states.append(state)

            logger.debug(
                f"Scroll cycle {cycle}: y={scroll_y_after}, "
                f"height={scroll_height_after}, new_content={has_new_content}, "
                f"cycles_without_content={cycles_without_content}"
            )

            # Reset detector for next checkpoint
            try:
                await self._detector.reset(page)
            except Exception as e:
                logger.warning(f"Reset detector failed at cycle {cycle}: {e}")

            # Capture screenshot at intervals OR on final cycle
            should_capture = (cycle % screenshot_interval == 0) or stabilized or (cycle == self.MAX_SCROLL_CYCLES - 1)
            if should_capture:
                screenshot_path = await self._capture_scroll_screenshot(page, audit_id, cycle)
                if screenshot_path:
                    screenshot_paths.append(screenshot_path)

            # Stop if stabilized
            if stabilized:
                logger.info(f"Scroll stabilized after {cycle + 1} cycles ({cycles_without_content} consecutive without new content)")
                break

        # Disconnect detector to prevent memory leaks
        await self._detector.disconnect(page)

        return ScrollResult(
            total_cycles=len(scroll_states),
            stabilized=cycles_without_content >= self.STABILIZATION_THRESHOLD,
            lazy_load_detected=lazy_load_detected,
            screenshots_captured=len(screenshot_paths),
            scroll_states=scroll_states,
        )

    async def _capture_scroll_screenshot(
        self,
        page: Page,
        audit_id: str,
        cycle: int,
    ) -> str | None:
        """
        Capture a viewport screenshot at scroll checkpoint.

        Args:
            page: Playwright Page object
            audit_id: Unique audit ID for filename
            cycle: Current scroll cycle number

        Returns:
            Filepath of captured screenshot, or None on failure
        """
        try:
            filename = f"{audit_id}_scroll_{cycle:02d}.jpg"
            filepath = self._evidence_dir / filename

            # Get current scroll position for logging
            scroll_y = await page.evaluate("window.scrollY")
            scroll_height = await page.evaluate("document.documentElement.scrollHeight")

            await page.screenshot(
                path=str(filepath),
                type="jpeg",
                quality=85,
                full_page=False,  # Viewport only
            )

            logger.debug(
                f"Captured scroll screenshot: {filename} "
                f"(y={scroll_y}, height={scroll_height})"
            )

            return str(filepath)
        except Exception as e:
            logger.warning(f"Failed to capture scroll screenshot at cycle {cycle}: {e}")
            return None
