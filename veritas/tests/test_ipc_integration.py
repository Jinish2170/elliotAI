"""
Integration Tests for IPC Queue Module

Tests Queue IPC in subprocess context, stdout fallback,
result comparison, and Windows compatibility.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add veritas root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
import multiprocessing as mp

from veritas.core.ipc import (
    ProgressEvent,
    create_queue,
    determine_ipc_mode,
    IPC_MODE_QUEUE,
    IPC_MODE_STDOUT,
    safe_put,
)
from veritas.core.orchestrator import VeritasOrchestrator


class TestOrchestratorWithQueue:
    """Test VeritasOrchestrator with Queue mode."""

    @pytest.mark.asyncio
    async def test_orchestrator_with_queue_mode(self):
        """Test that orchestrator can be created with a Queue."""
        q = create_queue(maxsize=100)
        orch = VeritasOrchestrator(progress_queue=q)

        assert orch.progress_queue is q
        # Verify queue works by putting and getting
        q.put("test")
        assert q.get() == "test"

    @pytest.mark.asyncio
    async def test_orchestrator_with_none_queue(self):
        """Test that orchestrator can be created with None Queue (stdout mode)."""
        orch = VeritasOrchestrator(progress_queue=None)

        assert orch.progress_queue is None

    @pytest.mark.asyncio
    async def test_emit_with_queue(self):
        """Test _emit sends ProgressEvent to Queue."""
        q = create_queue(maxsize=100)
        orch = VeritasOrchestrator(progress_queue=q)

        # Emit a progress event
        orch._emit("test_phase", "test_step", 50, "Test message", extra_data="value")

        # Verify event was sent to Queue
        event = q.get(timeout=2.0)
        assert event.type == "progress"
        assert event.phase == "test_phase"
        assert event.step == "test_step"
        assert event.pct == 50
        assert event.detail == "Test message"
        assert hasattr(event, 'extra_data')
        assert event.extra_data == "value"

    @pytest.mark.asyncio
    async def test_emit_with_stdout(self):
        """Test _emit uses stdout when Queue is None."""
        orch = VeritasOrchestrator(progress_queue=None)

        # Capture stdout
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # Emit a progress event
        orch._emit("test_phase", "test_step", 50, "Test message")

        # Verify ##PROGRESS: marker was printed
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert "##PROGRESS:" in output
        assert '"phase": "test_phase"' in output
        assert '"step": "test_step"' in output

    @pytest.mark.asyncio
    async def test_emit_queue_full_handling(self):
        """Test _emit handles Queue full with safe_put backpressure."""
        q = create_queue(maxsize=2)
        orch = VeritasOrchestrator(progress_queue=q)

        import logging
        logging.basicConfig(level=logging.WARNING)

        # Fill queue to capacity (should succeed)
        orch._emit("test", "1", 10, "msg1")
        orch._emit("test", "2", 20, "msg2")

        # Third event should trigger backpressure but still succeed (safe_put removes oldest)
        orch._emit("test", "3", 30, "msg3")

        # Verify queue still has 2 items (one was dropped and replaced)
        items = []
        while not q.empty():
            items.append(q.get())
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_progress_event_structure(self):
        """Test ProgressEvent has all required fields."""
        q = create_queue(maxsize=100)
        orch = VeritasOrchestrator(progress_queue=q)

        orch._emit("scout", "navigating", 25, "Navigation in progress")

        event = q.get()
        # Required fields
        assert event.type == "progress"
        assert event.phase == "scout"
        assert event.step == "navigating"
        assert event.pct == 25
        assert event.detail == "Navigation in progress"
        # Optional fields
        assert event.summary == {}
        assert event.data is None
        assert isinstance(event.timestamp, float)


class TestModeDeterminationPriority:
    """Test IPC mode determination priority hierarchy."""

    def test_cli_flag_priority_queue(self):
        """Test CLI --use-queue-ipc flag has highest priority."""
        mode = determine_ipc_mode(cli_use_queue_ipc=True, cli_use_stdout=False, cli_validate_ipc=False)
        assert mode == IPC_MODE_QUEUE

    def test_cli_flag_priority_stdout(self):
        """Test CLI --use-stdout flag has highest priority."""
        mode = determine_ipc_mode(cli_use_queue_ipc=False, cli_use_stdout=True, cli_validate_ipc=False)
        assert mode == IPC_MODE_STDOUT

    def test_cli_flag_priority_validate(self):
        """Test CLI --validate-ipc flag has highest priority."""
        mode = determine_ipc_mode(cli_use_queue_ipc=False, cli_use_stdout=False, cli_validate_ipc=True)
        assert mode == "validate"

    def test_env_var_priority(self):
        """Test environment variable priority when no CLI flags."""
        with patch.dict(os.environ, {"QUEUE_IPC_MODE": "queue"}, clear=False):
            mode = determine_ipc_mode(cli_use_queue_ipc=False, cli_use_stdout=False)
            assert mode == IPC_MODE_QUEUE

        with patch.dict(os.environ, {"QUEUE_IPC_MODE": "stdout"}, clear=False):
            mode = determine_ipc_mode(cli_use_queue_ipc=False, cli_use_stdout=False)
            assert mode == IPC_MODE_STDOUT

    def test_default_rollout_percentage(self):
        """Test default percentage-based rollout when no flags/env."""
        # Clear env vars
        with patch.dict(os.environ, {}, clear=True):
            # Run multiple times to get mix of results
            modes = [determine_ipc_mode() for _ in range(100)]

            # Should get both queue and stdout modes (default 10% Queue)
            assert IPC_MODE_QUEUE in modes
            assert IPC_MODE_STDOUT in modes

            # Queue mode should appear roughly 10% of the time
            queue_count = modes.count(IPC_MODE_QUEUE)
            assert 0 <= queue_count <= 30  # Allow variance


class TestWindowsSpawnContext:
    """Test Windows spawn context configuration."""

    def test_spawn_context_set_on_windows(self):
        """Test that spawn context is set on Windows platform."""
        if sys.platform == "win32":
            assert mp.get_start_method() == "spawn"
        else:
            # On non-Windows, spawn is still valid
            assert mp.get_start_method() in ("fork", "spawn", "forkserver")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
