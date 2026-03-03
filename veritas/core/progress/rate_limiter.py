"""
Token-Bucket Rate Limiter for WebSocket Event Throttling

Prevents WebSocket flooding during intensive operations like 5-pass Vision analysis.
Implements the classic token-bucket algorithm with burst capacity and queue-based
priority handling.

From PLAN 09-03: Real-time Progress Streaming
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("veritas.progress.rate_limiter")


@dataclass
class RateLimiterConfig:
    """Configuration for token-bucket rate limiter."""

    max_rate: float = 5.0  # Maximum events per second
    burst: int = 10  # Maximum burst capacity (number of tokens)


@dataclass
class Event:
    """Event queued for emission when rate limiter is full."""

    priority: int  # 0 = highest priority
    data: dict  # Event payload
    timestamp: float


class TokenBucketRateLimiter:
    """
    Token-bucket rate limiter for throttling WebSocket progress events.

    The bucket refills at max_rate tokens per second, up to burst capacity.
    Events with available tokens are emitted immediately.
    Events without available tokens are queued by priority.
    When the queue is full, lowest-priority events are dropped.

    Example:
        rate_limiter = TokenBucketRateLimiter(RateLimiterConfig(max_rate=5.0, burst=10))

        # Try to emit an event
        if await rate_limiter.acquire({"type": "progress", "pct": 50}, priority=0):
            # Event was emitted immediately
            pass
        else:
            # Event was queued (rate limited)
            pass

        # Get queued events when tokens are available
        queued_event = await rate_limiter.get_queued_event()
        if queued_event:
            # Emit the queued event
            pass
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None):
        """Initialize rate limiter with config (or defaults)."""
        self.config = config or RateLimiterConfig()
        self.tokens = float(self.config.burst)  # Start with full bucket
        self.last_refill = time.time()
        self.max_queue_size = 100
        self.dropped_count = 0
        self.event_queue: deque[Event] = deque(maxlen=self.max_queue_size)
        self._lock = asyncio.Lock()

    def _refill_tokens(self):
        """Refill tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now

        # Refill: tokens += elapsed * max_rate
        self.tokens += elapsed * self.config.max_rate

        # Cap at burst capacity
        if self.tokens > self.config.burst:
            self.tokens = float(self.config.burst)

    async def acquire(self, event_data: dict, priority: int = 0) -> bool:
        """
        Try to acquire a token to emit an event.

        If tokens available: consume 1 token and return True (emit immediately).
        If no tokens: queue event and return False (rate limited).

        Args:
            event_data: Event payload to queue if rate limited
            priority: Priority level (0=highest, higher values=lower priority)

        Returns:
            True if event can be emitted immediately, False if queued
        """
        async with self._lock:
            self._refill_tokens()

            if self.tokens >= 1.0:
                # Consume 1 token, emit immediately
                self.tokens -= 1.0
                return True
            else:
                # No tokens available, queue event
                if len(self.event_queue) >= self.max_queue_size:
                    # Queue full, drop lowest-priority event if possible
                    lowest = min(self.event_queue, key=lambda e: e.priority)
                    if priority <= lowest.priority:
                        # Drop queued event to make room (incoming is higher or same priority)
                        self.event_queue.remove(lowest)
                    else:
                        # Drop incoming event (lower priority)
                        self.dropped_count += 1
                        return False

                event = Event(priority=priority, data=event_data, timestamp=time.time())
                self.event_queue.append(event)
                return False

    async def get_queued_event(self) -> Optional[dict]:
        """
        Get next queued event when tokens are available.

        Waits up to 100ms for token refill before returning.

        Returns:
            Event data if available, None if no queued events or no tokens
        """
        await asyncio.sleep(0.1)  # Wait 100ms for token refill
        async with self._lock:
            self._refill_tokens()

            if self.event_queue and self.tokens >= 1.0:
                # Pop highest-priority event
                events = sorted(self.event_queue, key=lambda e: e.priority)
                event = events[0]
                self.event_queue.remove(event)
                self.tokens -= 1.0
                return event.data

            return None

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "tokens_remaining": round(self.tokens, 2),
            "tokens_capacity": self.config.burst,
            "queue_size": len(self.event_queue),
            "max_queue_size": self.max_queue_size,
            "dropped_events": self.dropped_count,
            "max_rate": self.config.max_rate,
        }
