"""
Event Priority Enumeration for Progress Streaming

Defines priority levels for progress events to ensure critical events
are always emitted immediately even when rate limited.

From PLAN 09-03: Real-time Progress Streaming
"""

import enum


class EventPriority(enum.IntEnum):
    """
    Priority levels for progress events.

    Lower value = higher priority (CRITICAL events are emitted first).

    Attributes:
        CRITICAL: Agent failures, circuit breaker trips (must not be dropped)
        HIGH: Findings, phase completions (important for user awareness)
        MEDIUM: Screenshots, progress updates (nice to have)
        LOW: Info messages, heartbeats (can be queued or dropped)
    """

    CRITICAL = 0  # Agent failure, circuit breaker tripped
    HIGH = 1  # Findings, phase completion
    MEDIUM = 2  # Screenshot, progress updates
    LOW = 3  # Info messages, heartbeats
