"""
Fallback Manager with Graceful Degradation

Implements graceful degradation ensuring "show must go on" policy:
- FallbackMode enum (NONE, SIMPLIFIED, CACHED, PARTIAL, ALTERNATIVE)
- DegradedResult tracking missing data and quality penalties
- Per-agent circuit breakers with default configurations
- Automatic fallback registration and execution

Key Design:
- DegradedResult always contains usable data (never returns None)
- Quality penalty applied to final trust score (0.2-0.7)
- Missing data tracked in list for transparency
- "Show must go on": audit continues even if agents fail
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from veritas.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState
)

logger = logging.getLogger("veritas.core.degradation")


# ============================================================
# Fallback Mode Enum
# ============================================================

class FallbackMode(str, Enum):
    """Type of fallback strategy used."""
    NONE = "NONE"                # No fallback used (primary succeeded)
    SIMPLIFIED = "SIMPLIFIED"    # Simplified version of data
    CACHED = "CACHED"            # Used cached data
    PARTIAL = "PARTIAL"          # Partial/incomplete data available
    ALTERNATIVE = "ALTERNATIVE"  # Alternative data source


# ============================================================
# Degraded Result
# ============================================================

@dataclass
class DegradedResult:
    """
    Result from agent execution with degradation tracking.

    Ensures "show must go on" policy by always containing usable
    data even when the primary agent fails.

    Attributes:
        result_data: Partial or fallback result data (never None)
        degraded_agent: Which agent type was degraded
        fallback_mode: Type of fallback used (NONE if no degradation)
        missing_data: List of what data is missing/ degraded
        quality_penalty: Penalty to apply to trust score (0.0-1.0)
        error_message: Error message if agent failed
    """
    result_data: dict = None
    degraded_agent: str = ""
    fallback_mode: FallbackMode = FallbackMode.NONE
    missing_data: list[str] = None
    quality_penalty: float = 0.0
    error_message: str = ""

    def __post_init__(self):
        """Initialize default values."""
        if self.result_data is None:
            self.result_data = {}
        if self.missing_data is None:
            self.missing_data = []

        # Ensure quality penalty is in valid range
        self.quality_penalty = max(0.0, min(1.0, self.quality_penalty))

    def is_degraded(self) -> bool:
        """Check if result was degraded (fallback used)."""
        return self.fallback_mode != FallbackMode.NONE or self.quality_penalty > 0.0

    @property
    def has_error(self) -> bool:
        """Check if agent had an error."""
        return bool(self.error_message)


# ============================================================
# Fallback Manager
# ============================================================

class FallbackManager:
    """
    Manages gracefully degraded execution with circuit breakers.

    Registers fallback functions per agent type and executes them
    when the primary fails or circuit breaker trips.

    Key principle: "Show must go on" - DegradedResult always contains
    usable data, never returns None.

    Example:
        ```python
        async def primary_vision(url: str) -> dict:
            # Full VLM analysis
            return full_result

        async def simplified_vision(url: str) -> dict:
            # Fallback: cached or simplified analysis
            return {"simplified": True, "threats": []}

        manager = FallbackManager()
        manager.register_fallback("vision", simplified_vision, FallbackMode.SIMPLIFIED)

        result = await manager.execute_with_fallback("vision", primary_vision, {"url": "https://example.com"})

        if result.is_degraded():
            logger.warning(f"Vision degraded: {result.quality_penalty} penalty")
        ```
    """

    # Default circuit breaker configurations per agent type
    DEFAULT_CONFIGS: dict[str, CircuitBreakerConfig] = {
        "vision": CircuitBreakerConfig(
            failure_threshold=3,
            timeout_ms=60000,      # 60 seconds for VLM analysis
            half_open_max_calls=1,
            success_threshold=1
        ),
        "graph": CircuitBreakerConfig(
            failure_threshold=5,
            timeout_ms=30000,      # 30 seconds for graph analysis
            half_open_max_calls=1,
            success_threshold=1
        ),
        "security": CircuitBreakerConfig(
            failure_threshold=3,
            timeout_ms=45000,      # 45 seconds for security modules
            half_open_max_calls=1,
            success_threshold=1
        ),
        "osint": CircuitBreakerConfig(
            failure_threshold=5,
            timeout_ms=90000,      # 90 seconds for OSINT APIs
            half_open_max_calls=1,
            success_threshold=1
        ),
    }

    def __init__(self):
        """Initialize FallbackManager."""
        # Registry of agent type -> (circuit_breaker, fallback_fn, fallback_mode)
        self._registry: dict[str, tuple[
            CircuitBreaker,
            Optional[Callable],
            FallbackMode
        ]] = {}

        logger.info("FallbackManager initialized")

    def register_fallback(
        self,
        agent_type: str,
        fallback_fn: Optional[Callable],
        fallback_mode: FallbackMode
    ) -> None:
        """
        Register a fallback function for an agent type.

        Creates a CircuitBreaker for the agent with default config
        and stores the fallback function and mode.

        Args:
            agent_type: Agent type (vision, graph, security, osint, judge)
            fallback_fn: Fallback function (None means no fallback)
            fallback_mode: Type of fallback strategy
        """
        # Get or create default config for agent type
        config = self._get_default_config(agent_type)

        # Create circuit breaker with agent type as name
        breaker = CircuitBreaker(f"{agent_type}_breaker", config)

        # Register in registry
        self._registry[agent_type] = (breaker, fallback_fn, fallback_mode)

        logger.info(
            f"Registered fallback for '{agent_type}': "
            f"mode={fallback_mode.value}, circuit={config.failure_threshold} failures"
        )

    async def execute_with_fallback(
        self,
        agent_type: str,
        primary_fn: Callable,
        context: dict,
        timeout: Optional[int] = None
    ) -> DegradedResult:
        """
        Execute primary function with circuit protection and fallback.

        If primary succeeds: DegradedResult with fallback_mode=NONE
        If primary fails: Try fallback, apply quality penalty

        Args:
            agent_type: Agent type being executed
            primary_fn: Primary async function to call
            context: Context dict to pass to function
            timeout: Optional timeout override in seconds

        Returns:
            DegradedResult with result_data and degradation tracking
        """
        # Get registry entry
        if agent_type not in self._registry:
            # No circuit breaker registered, execute directly
            logger.warning(f"No circuit breaker for '{agent_type}', executing directly")
            try:
                result = await self._call_function(primary_fn, context, timeout)
                return self._create_result(result, agent_type, FallbackMode.NONE)
            except Exception as e:
                error_msg = f"Error: {type(e).__name__}: {str(e)}"
                logger.error(f"Direct execution failed for '{agent_type}': {error_msg}")
                return self._create_error_result(agent_type, error_msg)

        breaker, fallback_fn, fallback_mode = self._registry[agent_type]

        # Execute via circuit breaker
        result_wrapper = await breaker.call(
            primary_fn,
            fallback_fn,
            **context,
            timeout=timeout
        )

        if result_wrapper.is_fallback:
            # Primary failed or circuit open - degrade result
            quality_penalty = 0.2  # Penalty for using fallback
            missing_data = [agent_type]

            if result_wrapper.value is not None:
                # Fallback provided data
                result_data = self._normalize_result(result_wrapper.value)
                return DegradedResult(
                    result_data=result_data,
                    degraded_agent=agent_type,
                    fallback_mode=fallback_mode,
                    missing_data=missing_data,
                    quality_penalty=quality_penalty,
                    error_message=result_wrapper.primary_error or ""
                )
            else:
                # No data from fallback (total failure)
                return self._create_error_result(
                    agent_type,
                    result_wrapper.primary_error or fallback_mode.value,
                    fallback_mode=fallback_mode
                )
        else:
            # Primary succeeded
            result_data = self._normalize_result(result_wrapper.value)
            return self._create_result(result_data, agent_type, FallbackMode.NONE)

    def _create_result(
        self,
        result: Any,
        agent_type: str,
        fallback_mode: FallbackMode
    ) -> DegradedResult:
        """
        Create successful DegradedResult.

        Args:
            result: Result from function
            agent_type: Agent type
            fallback_mode: Fallback mode used

        Returns:
            DegradedResult with result_data
        """
        result_data = self._normalize_result(result)
        return DegradedResult(
            result_data=result_data,
            degraded_agent=agent_type,
            fallback_mode=fallback_mode,
            missing_data=[],
            quality_penalty=0.0,
            error_message=""
        )

    def _create_error_result(
        self,
        agent_type: str,
        error_message: str,
        fallback_mode: FallbackMode = FallbackMode.NONE
    ) -> DegradedResult:
        """
        Create error DegradedResult.

        Args:
            agent_type: Agent type that failed
            error_message: Error message
            fallback_mode: Fallback mode attempted

        Returns:
            DegradedResult with quality_penalty=0.7 (total failure)
        """
        return DegradedResult(
            result_data={},  # Empty but usable
            degraded_agent=agent_type,
            fallback_mode=fallback_mode,
            missing_data=[agent_type],
            quality_penalty=0.7,  # High penalty for total failure
            error_message=error_message
        )

    async def _call_function(
        self,
        fn: Callable,
        context: dict,
        timeout: Optional[int] = None
    ) -> Any:
        """
        Call a function with optional timeout.

        Args:
            fn: Function to call
            context: Context dict to pass
            timeout: Optional timeout in seconds

        Returns:
            Function result
        """
        if timeout is not None:
            return await asyncio.wait_for(fn(**context), timeout=timeout)
        else:
            return await fn(**context)

    def _normalize_result(self, result: Any) -> dict:
        """
        Normalize result to dict format.

        Args:
            result: Any result value

        Returns:
            Dict representation of result
        """
        if result is None:
            return {}
        if isinstance(result, dict):
            return result
        if hasattr(result, "to_dict"):
            return result.to_dict()
        if hasattr(result, "__dict__"):
            return dict(result.__dict__)
        return {"value": result}

    def _get_default_config(self, agent_type: str) -> CircuitBreakerConfig:
        """
        Get default circuit breaker config for agent type.

        Args:
            agent_type: Agent type

        Returns:
            CircuitBreakerConfig for agent type, or default
        """
        return self.DEFAULT_CONFIGS.get(
            agent_type,
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout_ms=30000,
                half_open_max_calls=1,
                success_threshold=1
            )
        )

    def get_circuit_state(self, agent_type: str) -> Optional[CircuitState]:
        """
        Get current circuit state for an agent.

        Args:
            agent_type: Agent type

        Returns:
            CircuitState or None if not registered
        """
        if agent_type not in self._registry:
            return None

        breaker, _, _ = self._registry[agent_type]
        return breaker.get_state()

    def get_circuit_stats(self, agent_type: str) -> Optional[dict]:
        """
        Get circuit breaker statistics for an agent.

        Args:
            agent_type: Agent type

        Returns:
            Dict of stats or None if not registered
        """
        if agent_type not in self._registry:
            return None

        breaker, _, _ = self._registry[agent_type]
        return breaker.get_stats()

    def reset_circuit(self, agent_type: str) -> bool:
        """
        Manually reset circuit breaker for an agent.

        Args:
            agent_type: Agent type

        Returns:
            True if reset was successful, False if not found
        """
        if agent_type not in self._registry:
            return False

        breaker, _, _ = self._registry[agent_type]
        breaker.reset()
        logger.info(f"Reset circuit breaker for '{agent_type}'")
        return True

    def get_registered_agents(self) -> list[str]:
        """Get list of registered agent types."""
        return list(self._registry.keys())
