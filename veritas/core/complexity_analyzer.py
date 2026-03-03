"""
Complexity Analyzer for Metrics Collection

Analyzes Scout, Vision, and Security results to extract complexity metrics
for adaptive timeout calculation.

Design:
- Extracts 15 complexity metrics from agent results
- Handles missing fields gracefully with defaults
- Provides timeout strategy suggestions based on scores
"""

import logging
from typing import Optional

from veritas.core.timeout_manager import (
    ComplexityMetrics,
    TimeoutStrategy
)

logger = logging.getLogger("veritas.core.complexity_analyzer")


# ============================================================
# Complexity Analyzer
# ============================================================

class ComplexityAnalyzer:
    """
    Analyzes agent results to extract complexity metrics.

    Extracts DOM structure, performance, and activity metrics from
    Scout, Vision, and Security results for adaptive timeout calculation.

    Example:
        ```python
        analyzer = ComplexityAnalyzer()

        metrics = analyzer.analyze_page(scout_result, vision_result, security_result)

        timeout_strategy = analyzer.get_timeout_suggestion(metrics.calculate_complexity_score())
        # Returns TimeoutStrategy.FAST, STANDARD, or CONSERVATIVE
        ```
    """

    def __init__(self):
        """Initialize ComplexityAnalyzer."""
        logger.info("ComplexityAnalyzer initialized")

    def analyze_page(
        self,
        scout_result: Optional[Any] = None,
        vision_result: Optional[Any] = None,
        security_result: Optional[Any] = None
    ) -> ComplexityMetrics:
        """
        Analyze page from agent results and extract complexity metrics.

        Extracts metrics from ScoutResult, VisionResult, and SecurityResult:
        - DOM depth, node count, script count, stylesheet count
        - Inline style count, iframe count, lazy load detection
        - Screenshot count, viewport changes
        - Performance metrics (load times)

        Handles missing fields gracefully using defaults.

        Args:
            scout_result: ScoutResult from ScoutAgent (optional)
            vision_result: VisionResult from VisionAgent (optional)
            security_result: SecurityResult from SecurityAgent (optional)

        Returns:
            ComplexityMetrics with extracted metrics
        """
        # Extract URL
        url = self._extract_url(scout_result, vision_result, security_result)

        # Extract site type
        site_type = self._extract_site_type(scout_result)

        # Extract DOM metrics
        dom_depth = self._extract_dom_depth(scout_result)
        dom_node_count = self._extract_dom_node_count(scout_result, vision_result)
        script_count = self._extract_script_count(scout_result, security_result)
        stylesheet_count = self._extract_stylesheet_count(scout_result)
        inline_style_count = self._extract_inline_style_count(vision_result)
        iframes_count = self._extract_iframes_count(scout_result, security_result)

        # Detect lazy loading
        has_lazy_load, lazy_load_threshold = self._extract_lazy_load(scout_result, vision_result)

        # Extract performance metrics
        initial_load_time_ms = self._extract_initial_load_time(scout_result)
        network_idle_time_ms = self._extract_network_idle_time(scout_result)
        dom_content_loaded_time_ms = self._extract_dom_content_loaded_time(scout_result)
        total_load_time_ms = self._extract_total_load_time(scout_result)

        # Extract screenshot and viewport metrics
        screenshot_count = self._extract_screenshot_count(vision_result)
        viewport_changes = self._extract_viewport_changes(scout_result)

        metrics = ComplexityMetrics(
            url=url,
            site_type=site_type,
            dom_depth=dom_depth,
            dom_node_count=dom_node_count,
            script_count=script_count,
            stylesheet_count=stylesheet_count,
            inline_style_count=inline_style_count,
            iframes_count=iframes_count,
            has_lazy_load=has_lazy_load,
            lazy_load_threshold=lazy_load_threshold,
            screenshot_count=screenshot_count,
            viewport_changes=viewport_changes,
            initial_load_time_ms=initial_load_time_ms,
            network_idle_time_ms=network_idle_time_ms,
            dom_content_loaded_time_ms=dom_content_loaded_time_ms,
            total_load_time_ms=total_load_time_ms,
        )

        logger.debug(
            f"Analyzed complexity for {url}: "
            f"nodes={dom_node_count}, scripts={script_count}, "
            f"iframes={iframes_count}, lazy_load={has_lazy_load}, "
            f"load={total_load_time_ms}ms"
        )

        return metrics

    def get_timeout_suggestion(
        self,
        complexity_score: float
    ) -> TimeoutStrategy:
        """
        Get timeout strategy suggestion based on complexity score.

        Thresholds:
        - FAST: complexity < 0.30 (simple pages)
        - STANDARD: 0.30 <= complexity < 0.60 (moderate pages)
        - CONSERVATIVE: complexity >= 0.60 (complex pages)

        Args:
            complexity_score: Complexity score 0.0-1.0

        Returns:
            TimeoutStrategy suggestion
        """
        if complexity_score < 0.30:
            return TimeoutStrategy.FAST
        elif complexity_score < 0.60:
            return TimeoutStrategy.STANDARD
        else:
            return TimeoutStrategy.CONSERVATIVE

    # ============================================================
    # Field Extraction Helpers
    # ============================================================

    def _extract_url(
        self,
        scout_result: Optional[Any] = None,
        vision_result: Optional[Any] = None,
        security_result: Optional[Any] = None
    ) -> str:
        """Extract URL from the first non-None result."""
        for result in [scout_result, vision_result, security_result]:
            if result is not None:
                if isinstance(result, dict):
                    return result.get("url", "")
                if hasattr(result, "url"):
                    return result.url
        return ""

    def _extract_site_type(self, scout_result: Optional[Any]) -> str:
        """Extract site type from Scout result."""
        if scout_result is None:
            return "unknown"

        # Try dict access
        if isinstance(scout_result, dict):
            return scout_result.get("site_type", "unknown")

        # Try attribute access
        if hasattr(scout_result, "site_type"):
            return scout_result.site_type

        return "unknown"

    def _extract_dom_depth(self, scout_result: Optional[Any]) -> int:
        """Extract DOM depth from Scout result HTML structure."""
        if scout_result is None:
            return 0

        # Try attribute access first
        if hasattr(scout_result, "dom_depth"):
            return getattr(scout_result, "dom_depth", 0)

        # Try dict access for nested fields
        if isinstance(scout_result, dict):
            # Check for direct field
            if "dom_depth" in scout_result:
                return int(scout_result["dom_depth"])

            # Check for nested in html_analysis
            html_analysis = scout_result.get("html_analysis", {})
            if "dom_depth" in html_analysis:
                return int(html_analysis["dom_depth"])

            # Check for nested in metrics
            metrics = scout_result.get("metrics", {})
            if "dom_depth" in metrics:
                return int(metrics["dom_depth"])

        return 0

    def _extract_dom_node_count(
        self,
        scout_result: Optional[Any] = None,
        vision_result: Optional[Any] = None
    ) -> int:
        """Extract DOM node count from Scout or Vision result."""
        # Try vision result first
        if vision_result is not None:
            if isinstance(vision_result, dict):
                if "dom_nodes" in vision_result:
                    return len(vision_result["dom_nodes"])
                if "dom_node_count" in vision_result:
                    return int(vision_result["dom_node_count"])

            if hasattr(vision_result, "dom_nodes"):
                return len(vision_result.dom_nodes)
            if hasattr(vision_result, "dom_node_count"):
                return vision_result.dom_node_count

        # Try scout result
        if scout_result is not None:
            if isinstance(scout_result, dict):
                if "dom_node_count" in scout_result:
                    return int(scout_result["dom_node_count"])

            if hasattr(scout_result, "dom_node_count"):
                return scout_result.dom_node_count

        return 0

    def _extract_script_count(
        self,
        scout_result: Optional[Any] = None,
        security_result: Optional[Any] = None
    ) -> int:
        """Extract script count from Scout or Security result."""
        # Try scout result
        if scout_result is not None:
            if isinstance(scout_result, dict):
                if "scripts" in scout_result:
                    return len(scout_result["scripts"])
                if "script_count" in scout_result:
                    return int(scout_result["script_count"])

            if hasattr(scout_result, "scripts"):
                return len(scout_result.scripts)
            if hasattr(scout_result, "script_count"):
                return scout_result.script_count

        # Try security result
        if security_result is not None:
            if isinstance(security_result, dict):
                if "script_tags" in security_result:
                    return len(security_result["script_tags"])
                if "js_count" in security_result:
                    return int(security_result["js_count"])

            if hasattr(security_result, "script_tags"):
                return len(security_result.script_tags)
            if hasattr(security_result, "js_count"):
                return security_result.js_count

        return 0

    def _extract_stylesheet_count(self, scout_result: Optional[Any]) -> int:
        """Extract stylesheet count from Scout result."""
        if scout_result is None:
            return 0

        if isinstance(scout_result, dict):
            if "stylesheets" in scout_result:
                return len(scout_result["stylesheets"])
            if "stylesheet_count" in scout_result:
                return int(scout_result["stylesheet_count"])

        if hasattr(scout_result, "stylesheets"):
            return len(scout_result.stylesheets)
        if hasattr(scout_result, "stylesheet_count"):
            return scout_result.stylesheet_count

        return 0

    def _extract_inline_style_count(self, vision_result: Optional[Any]) -> int:
        """Extract inline style count from Vision result."""
        if vision_result is None:
            return 0

        if isinstance(vision_result, dict):
            # Check for detected_styles with inline=true
            styles = vision_result.get("detected_styles", [])
            inline_count = sum(1 for s in styles if s.get("inline") is True)
            if inline_count > 0:
                return inline_count

            if "inline_style_count" in vision_result:
                return int(vision_result["inline_style_count"])

        if hasattr(vision_result, "detected_styles"):
            inline_count = sum(1 for s in vision_result.detected_styles if getattr(s, "inline", False))
            return inline_count

        if hasattr(vision_result, "inline_style_count"):
            return vision_result.inline_style_count

        return 0

    def _extract_iframes_count(
        self,
        scout_result: Optional[Any] = None,
        security_result: Optional[Any] = None
    ) -> int:
        """Extract iframe count from Scout or Security result."""
        # Try scout result
        if scout_result is not None:
            if isinstance(scout_result, dict):
                if "iframes" in scout_result:
                    return len(scout_result["iframes"])
                if "iframe_count" in scout_result:
                    return int(scout_result["iframe_count"])

            if hasattr(scout_result, "iframes"):
                return len(scout_result.iframes)
            if hasattr(scout_result, "iframe_count"):
                return scout_result.iframe_count

        # Try security result
        if security_result is not None:
            if isinstance(security_result, dict):
                if "iframe_count" in security_result:
                    return int(security_result["iframe_count"])

            if hasattr(security_result, "iframe_count"):
                return security_result.iframe_count

        return 0

    def _extract_lazy_load(
        self,
        scout_result: Optional[Any] = None,
        vision_result: Optional[Any] = None
    ) -> tuple[bool, int]:
        """Extract lazy load detection from Scout or Vision result."""
        has_lazy_load = False
        lazy_load_threshold = 0

        # Try scout result
        if scout_result is not None:
            if isinstance(scout_result, dict):
                if scout_result.get("has_lazy_load"):
                    has_lazy_load = True
                    lazy_load_threshold = int(scout_result.get("lazy_load_cycles", 0))

            if hasattr(scout_result, "has_lazy_load"):
                has_lazy_load = scout_result.has_lazy_load
                lazy_load_threshold = getattr(scout_result, "lazy_load_cycles", 0)

        # Try vision result
        if not has_lazy_load and vision_result is not None:
            if isinstance(vision_result, dict):
                if vision_result.get("detected_lazy_load"):
                    has_lazy_load = True

            if hasattr(vision_result, "detected_lazy_load"):
                has_lazy_load = vision_result.detected_lazy_load

        return has_lazy_load, lazy_load_threshold

    def _extract_initial_load_time(self, scout_result: Optional[Any]) -> int:
        """Extract initial load time from Scout result."""
        if scout_result is None:
            return 0

        if isinstance(scout_result, dict):
            # Check for nested in performance or metrics
            performance = scout_result.get("performance", {})
            if "initial_load_time_ms" in performance:
                return int(performance["initial_load_time_ms"])

            if "initial_load_time_ms" in scout_result:
                return int(scout_result["initial_load_time_ms"])

        if hasattr(scout_result, "performance"):
            return getattr(scout_result.performance, "initial_load_time_ms", 0)

        if hasattr(scout_result, "initial_load_time_ms"):
            return scout_result.initial_load_time_ms

        return 0

    def _extract_network_idle_time(self, scout_result: Optional[Any]) -> int:
        """Extract network idle time from Scout result."""
        if scout_result is None:
            return 0

        if isinstance(scout_result, dict):
            performance = scout_result.get("performance", {})
            if "network_idle_time_ms" in performance:
                return int(performance["network_idle_time_ms"])
            if "network_idle_time_ms" in scout_result:
                return int(scout_result["network_idle_time_ms"])

        if hasattr(scout_result, "performance"):
            return getattr(scout_result.performance, "network_idle_time_ms", 0)

        if hasattr(scout_result, "network_idle_time_ms"):
            return scout_result.network_idle_time_ms

        return 0

    def _extract_dom_content_loaded_time(self, scout_result: Optional[Any]) -> int:
        """Extract DOM content loaded time from Scout result."""
        if scout_result is None:
            return 0

        if isinstance(scout_result, dict):
            performance = scout_result.get("performance", {})
            if "dom_content_loaded_time_ms" in performance:
                return int(performance["dom_content_loaded_time_ms"])
            if "dom_content_loaded_time_ms" in scout_result:
                return int(scout_result["dom_content_loaded_time_ms"])

        if hasattr(scout_result, "performance"):
            return getattr(scout_result.performance, "dom_content_loaded_time_ms", 0)

        if hasattr(scout_result, "dom_content_loaded_time_ms"):
            return scout_result.dom_content_loaded_time_ms

        return 0

    def _extract_total_load_time(self, scout_result: Optional[Any]) -> int:
        """Extract total load time from Scout result."""
        if scout_result is None:
            return 0

        if isinstance(scout_result, dict):
            performance = scout_result.get("performance", {})
            if "total_load_time_ms" in performance:
                return int(performance["total_load_time_ms"])
            if "total_load_time_ms" in scout_result:
                return int(scout_result["total_load_time_ms"])

        if hasattr(scout_result, "performance"):
            return getattr(scout_result.performance, "total_load_time_ms", 0)

        if hasattr(scout_result, "total_load_time_ms"):
            return scout_result.total_load_time_ms

        return 0

    def _extract_screenshot_count(self, vision_result: Optional[Any]) -> int:
        """Extract screenshot count from Vision result."""
        if vision_result is None:
            return 0

        if isinstance(vision_result, dict):
            if "screenshots" in vision_result:
                return len(vision_result["screenshots"])
            if "screenshot_count" in vision_result:
                return int(vision_result["screenshot_count"])

        if hasattr(vision_result, "screenshots"):
            return len(vision_result.screenshots)
        if hasattr(vision_result, "screenshot_count"):
            return vision_result.screenshot_count

        return 0

    def _extract_viewport_changes(self, scout_result: Optional[Any]) -> int:
        """Extract viewport change count from Scout result."""
        if scout_result is None:
            return 0

        if isinstance(scout_result, dict):
            if "viewport_changes" in scout_result:
                return len(scout_result["viewport_changes"])
            if "viewport_change_count" in scout_result:
                return int(scout_result["viewport_change_count"])

        if hasattr(scout_result, "viewport_changes"):
            return len(scout_result.viewport_changes)
        if hasattr(scout_result, "viewport_change_count"):
            return scout_result.viewport_change_count

        return 0
