"""
Completion Time Estimator for Audit Progress

Provides estimated remaining time for long-running audits using Exponential
Moving Average (EMA) of execution times per agent and site type.

From PLAN 09-03: Real-time Progress Streaming
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger("veritas.progress.estimator")


class AgentStatus(Enum):
    """Status of an agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentExecution:
    """Record of an agent execution."""

    agent: str  # Agent name
    site_type: str  # Site type classification
    start_time: float  # Timestamp
    end_time: float = 0.0
    duration_ms: int = 0
    status: AgentStatus = AgentStatus.PENDING


class CompletionTimeEstimator:
    """
    Estimates completion time for audits using EMA of execution times.

    Tracks execution times per (site_type, agent) combination using exponential
    moving average to provide accurate ETA estimates that improve over time.

    When no historical data is available, uses hardcoded defaults for
    common agents.

    EMA Formula:
        new_ema = old_ema * (1 - alpha) + new_value * alpha

    Example:
        estimator = CompletionTimeEstimator(ema_alpha=0.2)

        # Start tracking an agent
        execution = estimator.start_agent("scout", "e_commerce")

        # Complete tracking
        estimator.complete_agent(execution, success=True)

        # Estimate remaining time
        eta = estimator.estimate_remaining("e_commerce", ["vision", "graph", "judge"])
        print(f"Estimated {eta} seconds remaining")
    """

    # Default execution times (in seconds) when no EMA data available
    DEFAULT_TIMES = {
        "scout": 20,
        "vision": 30,
        "security": 15,
        "graph": 10,
        "judge": 10,
        "osint": 25,
        "scout_explore": 15,
    }

    def __init__(self, ema_alpha: float = 0.2, max_history: int = 100):
        """
        Initialize completion time estimator.

        Args:
            ema_alpha: EMA smoothing factor (lower = smoother, higher = faster adaptation)
            max_history: Maximum number of executions to keep in history
        """
        self.ema_alpha = ema_alpha
        self.max_history = max_history
        self._executions: list[AgentExecution] = []
        self._ema_history: dict[str, float] = {}  # {site_type:agent -> EMA time in ms}

    def start_agent(self, agent: str, site_type: str) -> AgentExecution:
        """
        Start tracking an agent execution.

        Args:
            agent: Agent name (e.g., "scout", "vision", "graph")
            site_type: Site type classification (e.g., "e_commerce", "phishing")

        Returns:
            AgentExecution record for this execution
        """
        execution = AgentExecution(
            agent=agent,
            site_type=site_type,
            start_time=time.time(),
            status=AgentStatus.RUNNING,
        )
        self._executions.append(execution)

        # Trim history if needed
        if len(self._executions) > self.max_history:
            self._executions = self._executions[-self.max_history :]

        return execution

    def complete_agent(self, execution: AgentExecution, success: bool = True):
        """
        Mark an agent execution as complete and update EMA.

        Args:
            execution: AgentExecution record from start_agent()
            success: True if execution succeeded, False if failed
        """
        execution.end_time = time.time()
        execution.duration_ms = int((execution.end_time - execution.start_time) * 1000)
        execution.status = AgentStatus.COMPLETED if success else AgentStatus.FAILED

        # Update EMA only for successful executions
        if success:
            self._update_ema(execution)

    def _update_ema(self, execution: AgentExecution):
        """Update EMA for this (site_type, agent) combination."""
        key = f"{execution.site_type}:{execution.agent}"
        ema = self._ema_history.get(key)

        if ema is None:
            # First time seeing this (site_type, agent), use this as initial EMA
            self._ema_history[key] = float(execution.duration_ms)
        else:
            # EMA formula: new_ema = old_ema * (1 - alpha) + new_value * alpha
            new_ema = ema * (1 - self.ema_alpha) + execution.duration_ms * self.ema_alpha
            self._ema_history[key] = new_ema

        logger.debug(
            f"Updated EMA for {key}: {execution.duration_ms}ms -> {self._ema_history[key]:.2f}ms"
        )

    def estimate_remaining(
        self, site_type: str, remaining_agents: list[str]
    ) -> int:
        """
        Estimate remaining time for given agents and site type.

        Args:
            site_type: Site type classification
            remaining_agents: List of agent names remaining to execute

        Returns:
            Estimated remaining time in seconds
        """
        total_ms = 0

        for agent in remaining_agents:
            key = f"{site_type}:{agent}"
            ema = self._ema_history.get(key)

            if ema:
                # Use EMA if available
                total_ms += ema
            else:
                # Use default time if no EMA data
                default_s = self.DEFAULT_TIMES.get(agent, 20)
                total_ms += default_s * 1000

        return total_ms // 1000  # Convert to seconds

    def get_eta(self, site_type: Optional[str] = None) -> Optional[int]:
        """
        Get estimated time remaining for current audit.

        Detects running agents from _executions and calculates ETA.

        Args:
            site_type: Site type (optional, inferred from running execution if None)

        Returns:
            Estimated remaining seconds, or None if no running agent
        """
        # Find running execution
        running = [e for e in self._executions if e.status == AgentStatus.RUNNING]
        if not running:
            return None

        # Use site_type from running execution
        current_site_type = site_type or running[0].site_type
        current_agent = running[0].agent

        # Define remaining agents (simple order-based approach)
        agent_order = ["scout", "vision", "security", "graph", "osint", "judge"]
        if current_agent in agent_order:
            idx = agent_order.index(current_agent)
            remaining_agents = agent_order[idx + 1 :]
        else:
            remaining_agents = []

        # Estimate time for remaining agents
        eta_seconds = self.estimate_remaining(current_site_type, remaining_agents)

        # Add estimated time for current agent
        key = f"{current_site_type}:{current_agent}"
        ema = self._ema_history.get(key)
        if ema:
            # Estimate remaining time for current agent (50% of average if just started)
            current_elapsed = time.time() - running[0].start_time
            estimated_total = ema / 1000  # Convert to seconds
            if current_elapsed > 0:
                remaining_current = max(0, estimated_total - current_elapsed)
            else:
                remaining_current = estimated_total / 2
            eta_seconds += int(remaining_current)
        else:
            # Use default
            eta_seconds += self.DEFAULT_TIMES.get(current_agent, 20)

        return eta_seconds

    def get_stats(self) -> dict:
        """Get estimator statistics."""
        return {
            "ema_history_size": len(self._ema_history),
            "executions_tracked": len(self._executions),
            "running_executions": len([e for e in self._executions if e.status == AgentStatus.RUNNING]),
            "completed_executions": len([e for e in self._executions if e.status == AgentStatus.COMPLETED]),
            "failed_executions": len([e for e in self._executions if e.status == AgentStatus.FAILED]),
            "ema_alpha": self.ema_alpha,
            "max_history": self.max_history,
        }
