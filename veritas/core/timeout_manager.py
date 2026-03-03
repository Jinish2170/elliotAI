"""
Timeout Manager with Adaptive Timeouts

Implements adaptive timeout calculation based on page complexity metrics:
- TimeoutStrategy enum (FAST, STANDARD, CONSERVATIVE, ADAPTIVE)
- ComplexityMetrics dataclass with 15 complexity/performance fields
- TimeoutConfig with agent-specific timeouts
- Historical learning for execution time estimation

Key Design:
- Adaptive strategy selects timeout based on complexity score thresholds
- Historical learning uses deque(maxlen=10) for rolling averages
- 20% buffer above historical averages for safety
- Estimated completion time for remaining agents
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger("veritas.core.timeout_manager")


# ============================================================
# Timeout Strategy Enum
# ============================================================

class TimeoutStrategy(str, Enum):
    """Timeout strategy for agent execution."""
    FAST = "FAST"
    STANDARD = "STANDARD"
    CONSERVATIVE = "CONSERVATIVE"
    ADAPTIVE = "ADAPTIVE"


# ============================================================
# Complexity Metrics
# ============================================================

@dataclass
class ComplexityMetrics:
    """
    Complexity metrics collected during Scout phase.

    Used by TimeoutManager to calculate adaptive timeouts based on
    page structure and performance characteristics.

    Attributes:
        url: URL that was analyzed
        site_type: Type of site (e_commerce, social, blog, etc.)

    Complexity Factors:
        dom_depth: Average nesting depth of HTML elements
        dom_node_count: Total number of DOM nodes
        script_count: Number of script tags
        stylesheet_count: Number of external stylesheets
        inline_style_count: Number of inline styles
        iframes_count: Number of iframe elements
        has_lazy_load: Whether lazy loading was detected
        lazy_load_threshold: Cycles before lazy-load stabilizes
        screenshot_count: Number of screenshots captured
        viewport_changes: Number of viewport size changes

    Performance Metrics:
        initial_load_time_ms: Time to initial page load
        network_idle_time_ms: Time to network idle state
        dom_content_loaded_time_ms: Time to DOM ready
        total_load_time_ms: Total page load time
    """
    # Identification
    url: str
    site_type: str = "unknown"

    # Complexity Factors
    dom_depth: int = 0
    dom_node_count: int = 0
    script_count: int = 0
    stylesheet_count: int = 0
    inline_style_count: int = 0
    iframes_count: int = 0
    has_lazy_load: bool = False
    lazy_load_threshold: int = 0
    screenshot_count: int = 0
    viewport_changes: int = 0

    # Performance Metrics
    initial_load_time_ms: int = 0
    network_idle_time_ms: int = 0
    dom_content_loaded_time_ms: int = 0
    total_load_time_ms: int = 0

    def calculate_complexity_score(self) -> float:
        """
        Calculate normalized complexity score from metrics.

        Normalizes each factor to 0.0-1.0 and applies weighted sum.

        Weights:
            - DOM node count: 35% (primary complexity driver)
            - Script count: 25% (JavaScript complexity)
            - Lazy loading: 20% (dynamic content)
            - Iframe count: 10% (embedded content)
            - Load time: 10% (performance overhead)

        Returns:
            Float between 0.0 and 1.0
        """
        # Normalize each factor to 0.0-1.0 range
        dom_factor = min(self.dom_node_count / 5000.0, 1.0)
        script_factor = min(self.script_count / 50.0, 1.0)
        iframe_factor = min(self.iframes_count / 5.0, 1.0)
        lazy_factor = 1.0 if self.has_lazy_load else 0.0
        load_factor = min(self.total_load_time_ms / 10000.0, 1.0)

        # Weighted sum
        score = (
            dom_factor * 0.35 +
            script_factor * 0.25 +
            lazy_factor * 0.20 +
            iframe_factor * 0.10 +
            load_factor * 0.10
        )

        logger.debug(
            f"Complexity score: {score:.3f} "
            f"(DOM:{dom_factor:.2f}, Script:{script_factor:.2f}, "
            f"Lazy:{lazy_factor:.2f}, IFrame:{iframe_factor:.2f}, "
            f"Load:{load_factor:.2f})"
        )

        return score

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "url": self.url,
            "site_type": self.site_type,
            "dom_depth": self.dom_depth,
            "dom_node_count": self.dom_node_count,
            "script_count": self.script_count,
            "stylesheet_count": self.stylesheet_count,
            "inline_style_count": self.inline_style_count,
            "iframes_count": self.iframes_count,
            "has_lazy_load": self.has_lazy_load,
            "lazy_load_threshold": self.lazy_load_threshold,
            "screenshot_count": self.screenshot_count,
            "viewport_changes": self.viewport_changes,
            "initial_load_time_ms": self.initial_load_time_ms,
            "network_idle_time_ms": self.network_idle_time_ms,
            "dom_content_loaded_time_ms": self.dom_content_loaded_time_ms,
            "total_load_time_ms": self.total_load_time_ms,
        }


# ============================================================
# Timeout Configuration
# ============================================================

@dataclass
class TimeoutConfig:
    """
    Agent-specific timeout configuration.

    Each agent type gets its own timeout value in seconds.

    Attributes:
        scout_timeout: Timeout for ScoutAgent (scraping, scrolling)
        vision_timeout: Timeout for VisionAgent (VLM analysis)
        security_timeout: Timeout for SecurityAgent (module analysis)
        graph_timeout: Timeout for GraphInvestigator (graph analysis)
        judge_timeout: Timeout for JudgeAgent (decision making)
        osint_timeout: Timeout for OSINT components (API calls)
    """
    scout_timeout: int = 20
    vision_timeout: int = 30
    security_timeout: int = 15
    graph_timeout: int = 10
    judge_timeout: int = 10
    osint_timeout: int = 25

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "scout": self.scout_timeout,
            "vision": self.vision_timeout,
            "security": self.security_timeout,
            "graph": self.graph_timeout,
            "judge": self.judge_timeout,
            "osint": self.osint_timeout,
        }


# ============================================================
# Timeout Strategies Registry
# ============================================================

TIMEOUT_STRATEGIES: dict[TimeoutStrategy, TimeoutConfig] = {
    TimeoutStrategy.FAST: TimeoutConfig(
        scout_timeout=10,
        vision_timeout=15,
        security_timeout=8,
        graph_timeout=5,
        judge_timeout=5,
        osint_timeout=15,
    ),
    TimeoutStrategy.STANDARD: TimeoutConfig(
        scout_timeout=20,
        vision_timeout=30,
        security_timeout=15,
        graph_timeout=10,
        judge_timeout=10,
        osint_timeout=25,
    ),
    TimeoutStrategy.CONSERVATIVE: TimeoutConfig(
        scout_timeout=35,
        vision_timeout=50,
        security_timeout=25,
        graph_timeout=15,
        judge_timeout=15,
        osint_timeout=40,
    ),
}


# ============================================================
# Historical Execution Tracking
# ============================================================

@dataclass
class HistoricalStats:
    """
    Historical execution statistics for learning.

    Tracks execution times per (site_type, agent) combination.

    Attributes:
        execution_times: Deque of recent execution times (maxlen=10)
        success_count: Number of successful executions
        failure_count: Number of failed executions
    """
    execution_times: deque[int] = field(default_factory=lambda: deque(maxlen=10))
    success_count: int = 0
    failure_count: int = 0

    def average_time(self) -> Optional[int]:
        """Get average execution time, or None if no data."""
        if not self.execution_times:
            return None
        return sum(self.execution_times) // len(self.execution_times)


# ============================================================
# Timeout Manager
# ============================================================

class TimeoutManager:
    """
    Manages adaptive timeout calculation and historical learning.

    Selects timeout strategies based on complexity scores and
    uses historical execution times for adaptive learning.

    Example:
        ```python
        manager = TimeoutManager(strategy=TimeoutStrategy.ADAPTIVE)

        # After Scout completes
        metrics = ComplexityMetrics(
            url="https://example.com",
            dom_node_count=2500,
            script_count=30,
            has_lazy_load=False,
            total_load_time_ms=2000,
        )

        config = manager.calculate_timeout_config(metrics)
        # Returns TimeoutConfig based on complexity score

        # Record execution for learning
        manager.record_execution("e_commerce", "vision", 12000, True)

        # Get estimated remaining time
        remaining = manager.get_estimated_remaining_time(
            "e_commerce", ["security", "graph", "judge"]
        )
        ```
    """

    def __init__(self, strategy: TimeoutStrategy = TimeoutStrategy.ADAPTIVE):
        """
        Initialize TimeoutManager.

        Args:
            strategy: Timeout strategy to use (default: ADAPTIVE)
        """
        self._strategy = strategy
        self._historical_data: dict[str, dict[str, HistoricalStats]] = {}

        logger.info(f"TimeoutManager initialized with strategy={strategy.value}")

    def calculate_timeout_config(
        self,
        metrics: ComplexityMetrics
    ) -> TimeoutConfig:
        """
        Calculate timeout configuration based on complexity metrics.

        If strategy is ADAPTIVE:
        - FAST: complexity < 0.30
        - STANDARD: 0.30 <= complexity < 0.60
        - CONSERVATIVE: complexity >= 0.60

        Applies historical adjustment if available (20% buffer).

        Args:
            metrics: ComplexityMetrics from Scout phase

        Returns:
            TimeoutConfig with agent-specific timeouts
        """
        complexity_score = metrics.calculate_complexity_score()

        # Select base strategy based on complexity
        if self._strategy == TimeoutStrategy.ADAPTIVE:
            if complexity_score < 0.30:
                base_strategy = TimeoutStrategy.FAST
            elif complexity_score < 0.60:
                base_strategy = TimeoutStrategy.STANDARD
            else:
                base_strategy = TimeoutStrategy.CONSERVATIVE
        else:
            base_strategy = self._strategy

        base_config = TIMEOUT_STRATEGIES[base_strategy]

        # Apply historical adjustment if available
        adjusted_config = self._apply_historical_adjustment(
            metrics.site_type, base_config
        )

        logger.info(
            f"Config: base={base_strategy.value}, "
            f"complexity={complexity_score:.3f}, "
            f"site_type={metrics.site_type}"
        )

        return adjusted_config

    def _apply_historical_adjustment(
        self,
        site_type: str,
        base_config: TimeoutConfig
    ) -> TimeoutConfig:
        """
        Apply historical adjustment to timeout configuration.

        Uses historical average execution times per agent with 20% buffer.

        Args:
            site_type: Site type (e_commerce, social, etc.)
            base_config: Base TimeoutConfig to adjust

        Returns:
            Adjusted TimeoutConfig
        """
        if site_type not in self._historical_data:
            return base_config

        site_data = self._historical_data[site_type]

        # Adjust each agent timeout based on historical average
        agent_times = {
            ("scout_timeout", "scout"): site_data.get("scout"),
            ("vision_timeout", "vision"): site_data.get("vision"),
            ("security_timeout", "security"): site_data.get("security"),
            ("graph_timeout", "graph"): site_data.get("graph"),
            ("judge_timeout", "judge"): site_data.get("judge"),
            ("osint_timeout", "osint"): site_data.get("osint"),
        }

        adjusted_field = {}
        for (field_name, agent), stats in agent_times.items():
            avg_time = stats.average_time() if stats else None

            if avg_time is not None:
                # Convert to seconds and add 20% buffer
                historical_timeout_sec = (avg_time / 1000) * 1.2
                base_value = getattr(base_config, field_name)
                # Take max of historical and base
                adjusted_field[field_name] = max(
                    int(historical_timeout_sec), base_value
                )
            else:
                adjusted_field[field_name] = getattr(base_config, field_name)

        return TimeoutConfig(**adjusted_field)

    def record_execution(
        self,
        site_type: str,
        agent: str,
        duration_ms: int,
        success: bool
    ) -> None:
        """
        Record execution time for adaptive learning.

        Tracks execution times in rolling history (maxlen=10) per
        (site_type, agent) combination.

        Args:
            site_type: Site type classification
            agent: Agent type (scout, vision, security, graph, judge, osint)
            duration_ms: Execution duration in milliseconds
            success: Whether execution was successful
        """
        if site_type not in self._historical_data:
            self._historical_data[site_type] = {}

        if agent not in self._historical_data[site_type]:
            self._historical_data[site_type][agent] = HistoricalStats()

        stats = self._historical_data[site_type][agent]

        if success:
            stats.execution_times.append(duration_ms)
            stats.success_count += 1
        else:
            stats.failure_count += 1

        logger.debug(
            f"Recorded: site_type={site_type}, agent={agent}, "
            f"duration={duration_ms}ms, success={success}"
        )

    def get_estimated_remaining_time(
        self,
        site_type: str,
        remaining_agents: list[str]
    ) -> int:
        """
        Calculate estimated time for remaining agents.

        Uses historical averages or falls back to strategy defaults.

        Args:
            site_type: Site type classification
            remaining_agents: List of agent names remaining

        Returns:
            Estimated seconds for all remaining agents
        """
        total_seconds = 0

        for agent in remaining_agents:
            # Get historical average or strategy default
            if site_type in self._historical_data:
                stats = self._historical_data[site_type].get(agent)
                avg_ms = stats.average_time() if stats else None
            else:
                avg_ms = None

            if avg_ms is not None:
                # Use historical with 20% buffer
                total_seconds += (avg_ms / 1000) * 1.2
            else:
                # Fallback to STANDARD strategy default
                standard_config = TIMEOUT_STRATEGIES[TimeoutStrategy.STANDARD]
                timeout_field = f"{agent}_timeout"
                timeout = getattr(standard_config, timeout_field, 10)
                total_seconds += timeout

        return int(total_seconds)

    def get_historical_stats(
        self,
        site_type: str,
        agent: str
    ) -> Optional[dict]:
        """
        Get historical statistics for a site_type/agent combination.

        Args:
            site_type: Site type classification
            agent: Agent type

        Returns:
            Dict with average_time, success_count, failure_count, or None
        """
        if site_type not in self._historical_data:
            return None

        stats = self._historical_data[site_type].get(agent)
        if stats is None:
            return None

        return {
            "average_time_ms": stats.average_time(),
            "success_count": stats.success_count,
            "failure_count": stats.failure_count,
            "sample_count": len(stats.execution_times),
        }

    def reset_historical_data(self) -> None:
        """Clear all historical execution data."""
        self._historical_data.clear()
        logger.info("Historical data cleared")
