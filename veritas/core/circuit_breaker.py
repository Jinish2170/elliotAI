"""
Circuit Breaker Pattern for Graceful Degradation

Implements the circuit breaker pattern to prevent cascading failures:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit tripped, requests short-circuit to fallback
- HALF_OPEN: Testing if service recovered

Key Features:
- Automatic failure detection with configurable threshold
- Exponential backoff for recovery attempts
- Graceful fallback to alternative functions
- State machine transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger("veritas.core.circuit_breaker")


# ============================================================
# Circuit State Enum
# ============================================================

class CircuitState(str, Enum):
    """Circuit breaker state machine states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


# ============================================================
# Circuit Breaker Configuration
# ============================================================

@dataclass
class CircuitBreakerConfig:
    """
    Configuration for circuit breaker behavior.

    Attributes:
        failure_threshold: Number of failures before tripping to OPEN
        timeout_ms: Time to stay in OPEN before尝试 HALF_OPEN
        half_open_max_calls: Number of test calls allowed in HALF_OPEN
        success_threshold: Number of successes in HALF_OPEN to CLOSE circuit
    """
    failure_threshold: int = 3
    timeout_ms: int = 30000
    half_open_max_calls: int = 1
    success_threshold: int = 1

    def __post_init__(self):
        """Validate configuration values."""
        if self.failure_threshold < 1:
            raise ValueError(f"failure_threshold must be >= 1, got {self.failure_threshold}")
        if self.timeout_ms < 1000:
            raise ValueError(f"timeout_ms must be >= 1000, got {self.timeout_ms}")
        if self.half_open_max_calls < 1:
            raise ValueError(f"half_open_max_calls must be >= 1, got {self.half_open_max_calls}")
        if self.success_threshold < 1:
            raise ValueError(f"success_threshold must be >= 1, got {self.success_threshold}")
        if self.success_threshold > self.half_open_max_calls:
            raise ValueError(
                f"success_threshold ({self.success_threshold}) cannot exceed "
                f"half_open_max_calls ({self.half_open_max_calls})"
            )


# ============================================================
# Result with Fallback
# ============================================================

@dataclass
class ResultWithFallback:
    """
    Wrapper for results that may use fallback.

    Tracks whether the result came from the primary function or
    a fallback, along with the reason for fallback.

    Attributes:
        value: The result value (from primary or fallback)
        is_fallback: True if result came from fallback function
        fallback_reason: Reason why fallback was used
        primary_error: Error from primary function if it failed
    """
    value: Any
    is_fallback: bool = False
    fallback_reason: str = ""
    primary_error: Optional[str] = None

    def __bool__(self) -> bool:
        """Return True if fallback was used."""
        return self.is_fallback


# ============================================================
# Circuit Breaker
# ============================================================

class CircuitBreaker:
    """
    Circuit breaker implementation with state machine.

    Prevents cascading failures by tripping to OPEN state after
    repeated failures, entering HALF_OPEN for testing, and returning
    to CLOSED after successful recovery.

    Example:
        ```python
        breaker = CircuitBreaker("vision_breaker")

        # Define primary and fallback functions
        async def primary_analysis(url: str) -> dict:
            # Expensive VLM analysis
            return analysis_result

        async def fallback_analysis(url: str) -> dict:
            # Simplified cached fallback
            return cached_result

        # Execute with circuit protection
        result = await breaker.call(primary_analysis, fallback_analysis, url="https://example.com")

        if result.is_fallback:
            logger.warning(f"Used fallback: {result.fallback_reason}")
        else:
            logger.info("Primary succeeded")
        ```
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize CircuitBreaker.

        Args:
            name: Unique name for this circuit breaker
            config: Optional configuration (uses defaults if None)
        """
        self._name = name
        self._config = config or CircuitBreakerConfig()

        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: Optional[datetime] = None
        self._last_state_change = datetime.now(timezone.utc)

        # HALF_OPEN call tracking
        self._half_open_calls_made = 0

        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"failure_threshold={self._config.failure_threshold}, "
            f"timeout_ms={self._config.timeout_ms}"
        )

    async def call(
        self,
        primary_fn: Callable[..., Any],
        fallback_fn: Optional[Callable[..., Any]] = None,
        *args,
        timeout: Optional[int] = None,
        **kwargs
    ) -> ResultWithFallback:
        """
        Execute primary function with circuit breaker protection.

        Workflow:
        - If OPEN: check if timeout elapsed -> HALF_OPEN, else use fallback
        - If CLOSED: call primary, track success/failure
        - If HALF_OPEN: allow test calls, use fallback if over limit

        Args:
            primary_fn: Primary async function to call
            fallback_fn: Optional fallback async function
            *args: Positional arguments to pass to function
            timeout: Optional timeout in seconds for primary execution
            **kwargs: Keyword arguments to pass to function

        Returns:
            ResultWithFallback with result and fallback status
        """
        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if self._should_transition_to_half_open():
                self._transition_to_state(CircuitState.HALF_OPEN)
            elif fallback_fn is not None:
                # Circuit still open, use fallback immediately
                return await self._call_fallback(
                    fallback_fn, args, kwargs,
                    reason=f"Circuit OPEN (since {self._opened_at})"
                )
            else:
                # No fallback available, raise error
                error_msg = f"Circuit '{self._name}' is OPEN and no fallback provided"
                logger.warning(error_msg)
                return ResultWithFallback(
                    value=None,
                    is_fallback=True,
                    fallback_reason=error_msg,
                    primary_error="Circuit OPEN"
                )

        # Check HALF_OPEN call limit
        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls_made >= self._config.half_open_max_calls:
                # Test limit reached, use fallback or fail
                if fallback_fn is not None:
                    return await self._call_fallback(
                        fallback_fn, args, kwargs,
                        reason="HALF_OPEN test limit reached"
                    )
                else:
                    error_msg = f"Circuit '{self._name}' HALF_OPEN test limit reached"
                    logger.warning(error_msg)
                    return ResultWithFallback(
                        value=None,
                        is_fallback=True,
                        fallback_reason=error_msg,
                        primary_error="HALF_OPEN limited"
                    )

        # Call primary function
        try:
            if timeout:
                result = await asyncio.wait_for(
                    self._ensure_async(primary_fn)(*args, **kwargs),
                    timeout=timeout
                )
            else:
                result = await self._ensure_async(primary_fn)(*args, **kwargs)

            self._on_success()
            return ResultWithFallback(
                value=result,
                is_fallback=False,
                fallback_reason="",
                primary_error=None
            )
        except asyncio.TimeoutError as e:
            error_msg = f"Primary function timeout after {timeout}s"
            logger.warning(f"Circuit '{self._name}': {error_msg}")
            self._on_failure(error_msg)
            return await self._call_fallback_if_available(fallback_fn, args, kwargs, error_msg)
        except Exception as e:
            error_msg = f"Primary function error: {type(e).__name__}: {str(e)}"
            logger.warning(f"Circuit '{self._name}': {error_msg}")
            self._on_failure(error_msg)
            return await self._call_fallback_if_available(fallback_fn, args, kwargs, error_msg)

    def _on_success(self) -> None:
        """Handle successful primary function call."""
        if self._state == CircuitState.CLOSED:
            # Reset failure count on success in CLOSED state
            self._failure_count = 0
        elif self._state == CircuitState.HALF_OPEN:
            # Track successes in HALF_OPEN
            self._success_count += 1
            self._half_open_calls_made += 1

            # Check if we should transition to CLOSED
            if self._success_count >= self._config.success_threshold:
                logger.info(f"Circuit '{self._name}': Closing after {self._success_count} successes")
                self._transition_to_state(CircuitState.CLOSED)
        else:
            self._half_open_calls_made += 1

    def _on_failure(self, error: str) -> None:
        """
        Handle failed primary function call.

        Args:
            error: Error message describing the failure
        """
        self._failure_count += 1

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls_made += 1
            # Failure in HALF_OPEN -> trip back to OPEN
            logger.warning(
                f"Circuit '{self._name}': Failure in HALF_OPEN, re-tripping to OPEN: {error}"
            )
            self._transition_to_state(CircuitState.OPEN)
        elif self._failure_count >= self._config.failure_threshold:
            # Trip to OPEN after threshold failures
            logger.warning(
                f"Circuit '{self._name}': Tripping to OPEN after "
                f"{self._failure_count} failures: {error}"
            )
            self._transition_to_state(CircuitState.OPEN)
        else:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls_made += 1

    def _should_transition_to_half_open(self) -> bool:
        """
        Check if circuit should transition from OPEN to HALF_OPEN.

        Returns:
            True if timeout_ms has elapsed since opening
        """
        if self._opened_at is None:
            return True

        elapsed_ms = (
            datetime.now(timezone.utc) - self._opened_at
        ).total_seconds() * 1000

        return elapsed_ms >= self._config.timeout_ms

    def _transition_to_state(self, new_state: CircuitState) -> None:
        """
        Transition circuit to new state.

        Args:
            new_state: New state to transition to
        """
        old_state = self._state

        if new_state == CircuitState.OPEN:
            self._opened_at = datetime.now(timezone.utc)
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls_made = 0
            self._success_count = 0
        elif new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls_made = 0
            self._opened_at = None

        self._state = new_state
        self._last_state_change = datetime.now(timezone.utc)

        logger.info(
            f"Circuit '{self._name}': {old_state.value} -> {new_state.value}"
        )

    async def _call_fallback(
        self,
        fallback_fn: Callable[..., Any],
        args: tuple,
        kwargs: dict,
        reason: str
    ) -> ResultWithFallback:
        """
        Call fallback function.

        Args:
            fallback_fn: Fallback function to call
            args: Positional arguments
            kwargs: Keyword arguments
            reason: Reason for using fallback

        Returns:
            ResultWithFallback with fallback value
        """
        try:
            result = await self._ensure_async(fallback_fn)(*args, **kwargs)
            return ResultWithFallback(
                value=result,
                is_fallback=True,
                fallback_reason=reason,
                primary_error=None
            )
        except Exception as e:
            error_msg = f"Fallback function error: {type(e).__name__}: {str(e)}"
            logger.error(f"Circuit '{self._name}': {error_msg}")
            return ResultWithFallback(
                value=None,
                is_fallback=True,
                fallback_reason=reason,
                primary_error=error_msg
            )

    async def _call_fallback_if_available(
        self,
        fallback_fn: Optional[Callable[..., Any]],
        args: tuple,
        kwargs: dict,
        primary_error: str
    ) -> ResultWithFallback:
        """
        Call fallback if available, else return error.

        Args:
            fallback_fn: Optional fallback function
            args: Positional arguments
            kwargs: Keyword arguments
            primary_error: Error from primary function

        Returns:
            ResultWithFallback with fallback value or None
        """
        if fallback_fn is not None:
            return await self._call_fallback(
                fallback_fn, args, kwargs,
                reason=f"Primary failed: {primary_error}"
            )
        else:
            return ResultWithFallback(
                value=None,
                is_fallback=True,
                fallback_reason="No fallback available",
                primary_error=primary_error
            )

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    def reset(self) -> None:
        """Manually reset circuit to CLOSED state."""
        old_state = self._state
        self._transition_to_state(CircuitState.CLOSED)
        logger.info(f"Circuit '{self._name}': Manually reset from {old_state.value}")

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dict with current state, failure count, time since open, etc.
        """
        time_since_open = None
        if self._opened_at is not None:
            time_since_open_ms = (
                datetime.now(timezone.utc) - self._opened_at
            ).total_seconds() * 1000
            time_since_open = f"{time_since_open_ms:.0f}ms"

        return {
            "name": self._name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "opened_at": self._opened_at.isoformat() if self._opened_at else None,
            "time_since_open": time_since_open,
            "half_open_calls_made": self._half_open_calls_made,
            "last_state_change": self._last_state_change.isoformat(),
        }

    async def _ensure_async(
        self,
        fn: Callable[..., Any]
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        """
        Ensure function is async.

        If fn is a coroutine function, return it as-is.
        If fn is a regular function, wrap it in an async wrapper.

        Args:
            fn: Function to check

        Returns:
            Async function
        """
        if asyncio.iscoroutinefunction(fn):
            return fn

        async def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper
