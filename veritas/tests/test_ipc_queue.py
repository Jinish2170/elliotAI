"""
Unit Tests for IPC Queue Module

Tests Queue creation, serialization, and Windows spawn context
compatibility for subprocess communication.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add veritas root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from veritas.core.ipc import (
    ProgressEvent,
    create_queue,
    serialize_queue,
    safe_put,
    IPC_MODE_QUEUE,
    IPC_MODE_STDOUT,
    IPC_MODE_VALIDATE,
    determine_ipc_mode,
    get_rollout_percentage,
)
import logging
import multiprocessing
import time


class TestProgressEvent:
    """Tests for ProgressEvent dataclass."""

    def test_progress_event_creation(self):
        """Test creating ProgressEvent with all fields."""
        event = ProgressEvent(
            type="phase_start",
            phase="Scout",
            step="navigating",
            pct=10,
            detail="Navigating to target URL",
            summary={"pages_scouted": 1},
        )

        assert event.type == "phase_start"
        assert event.phase == "Scout"
        assert event.step == "navigating"
        assert event.pct == 10
        assert event.detail == "Navigating to target URL"
        assert event.summary == {"pages_scouted": 1}
        assert isinstance(event.timestamp, float)

    def test_progress_event_defaults(self):
        """Test ProgressEvent with minimal fields using defaults."""
        before = time.time()
        event = ProgressEvent(type="progress")
        after = time.time()

        assert event.type == "progress"
        assert event.phase == ""
        assert event.step == ""
        assert event.pct == 0
        assert event.detail == ""
        assert event.summary == {}
        assert event.data is None
        assert before <= event.timestamp <= after

    def test_progress_event_serializable(self):
        """Test that ProgressEvent can be converted to dict for JSON serialization."""
        event = ProgressEvent(
            type="phase_complete",
            phase="Vision",
            step="analyzing",
            pct=50,
            detail="Analysis complete",
            summary={"images": 5, "texts": 10},
        )

        # Can access __dict__ for serialization
        event_dict = {
            "type": event.type,
            "phase": event.phase,
            "step": event.step,
            "pct": event.pct,
            "detail": event.detail,
            "summary": event.summary,
        }

        assert event_dict["type"] == "phase_complete"
        assert event_dict["summary"] == {"images": 5, "texts": 10}


class TestQueueCreation:
    """Tests for Queue creation utilities."""

    def test_create_queue_default(self):
        """Test creating queue with default maxsize."""
        q = create_queue()
        assert q is not None
        # Verify queue works by putting and getting
        q.put("test")
        assert q.get() == "test"

    def test_create_queue_custom_maxsize(self):
        """Test creating queue with custom maxsize."""
        q = create_queue(maxsize=10)
        assert q is not None
        # Verify queue works by putting and getting
        q.put("test")
        assert q.get() == "test"

    def test_queue_put_get(self):
        """Test putting and getting items from queue."""
        q = create_queue(maxsize=100)
        test_data = {"test": "data", "number": 123}

        q.put(test_data)
        result = q.get()
        assert result == test_data

    def test_queue_full_backpressure(self):
        """Test queue backpressure handling when full."""
        import queue as q_module
        q = create_queue(maxsize=5)
        logger = logging.getLogger("test")

        # Fill queue to capacity
        for i in range(5):
            q.put(i)

        # 6th item should fail with queue.Full
        with pytest.raises(q_module.Full):
            q.put(999, timeout=0.1)


class TestSafePut:
    """Tests for safe_put helper with backpressure handling."""

    def test_safe_put_success(self):
        """Test safe_put successfully puts event."""
        q = create_queue(maxsize=100)
        logger = logging.getLogger("test")
        event = ProgressEvent(type="test")

        result = safe_put(q, event, logger)
        assert result is True

    def test_safe_put_backpressure_retries(self):
        """Test safe_put removes oldest item on full queue and retries."""
        q = create_queue(maxsize=2)
        logger = logging.getLogger("test")

        # Fill queue to capacity
        assert safe_put(q, ProgressEvent(type="test1"), logger) is True
        assert safe_put(q, ProgressEvent(type="test2"), logger) is True

        # Queue is now full, should drop oldest and succeed
        result = safe_put(q, ProgressEvent(type="test3"), logger, timeout=0.1)
        assert result is True

        # Verify queue still has 2 items (test2, test3)
        items = []
        while not q.empty():
            items.append(q.get())
        assert len(items) == 2
        assert items[0].type == "test2" or items[0].type == "test3"
        assert items[1].type == "test2" or items[1].type == "test3"

    def test_safe_put_dict_event(self):
        """Test safe_put works with dict events too."""
        q = create_queue(maxsize=100)
        logger = logging.getLogger("test")
        event = {"type": "test", "data": "value"}

        result = safe_put(q, event, logger)
        assert result is True


class TestQueueSerialization:
    """Tests for Queue serialization and deserialization."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Queue serialization platform-specific")
    def test_queue_serialization(self):
        """Test that queue can be serialized and reconstructed."""
        q = create_queue(maxsize=100)
        test_data = {"test": "serialization", "value": 42}

        q.put(test_data)

        # Serialize queue
        fileno, serialized = serialize_queue(q)
        assert isinstance(fileno, str)
        assert isinstance(serialized, str)
        assert len(serialized) > 0


class TestModeDetermination:
    """Tests for IPC mode determination logic."""

    def test_determine_cli_flag_priority(self):
        """Test CLI flags have highest priority."""
        # Validate flag overrides everything
        mode = determine_ipc_mode(cli_validate_ipc=True)
        assert mode == IPC_MODE_VALIDATE

        # Queue flag overrides env
        with patch.dict(os.environ, {"QUEUE_IPC_MODE": "stdout"}):
            mode = determine_ipc_mode(cli_use_queue_ipc=True)
            assert mode == IPC_MODE_QUEUE

        # Stdout flag overrides env
        with patch.dict(os.environ, {"QUEUE_IPC_MODE": "queue"}):
            mode = determine_ipc_mode(cli_use_stdout=True)
            assert mode == IPC_MODE_STDOUT

    def test_determine_env_var_mode(self):
        """Test environment variable mode selection."""
        # Queue mode from env
        with patch.dict(os.environ, {"QUEUE_IPC_MODE": "queue"}):
            mode = determine_ipc_mode()
            assert mode == IPC_MODE_QUEUE

        # Stdout mode from env
        with patch.dict(os.environ, {"QUEUE_IPC_MODE": "stdout"}):
            mode = determine_ipc_mode()
            assert mode == IPC_MODE_STDOUT

        # Fallback mode from env
        with patch.dict(os.environ, {"QUEUE_IPC_MODE": "fallback"}):
            mode = determine_ipc_mode()
            assert mode == IPC_MODE_STDOUT

    def test_determine_default_rollout(self):
        """Test default percentage-based rollout."""
        # Clear env vars for default behavior
        with patch.dict(os.environ, {}, clear=True):
            # Test multiple calls - some should be queue, some stdout based on random
            modes = [determine_ipc_mode() for _ in range(100)]

            # With default 10% rollout, we should get mix
            assert IPC_MODE_QUEUE in modes
            assert IPC_MODE_STDOUT in modes

            # Queue mode should appear roughly 10% of the time
            queue_count = modes.count(IPC_MODE_QUEUE)
            assert 0 <= queue_count <= 30  # Allow variance

    def test_custom_rollout_percentage(self):
        """Test custom rollout percentage from environment."""
        with patch.dict(os.environ, {"QUEUE_IPC_ROLLOUT": "0.5"}):
            modes = [determine_ipc_mode() for _ in range(200)]
            queue_count = modes.count(IPC_MODE_QUEUE)

            # With 50% rollout, should get roughly half
            assert 60 <= queue_count <= 140  # Allow variance around 100

    def test_get_rollout_percentage(self):
        """Test get_rollout_percentage helper function."""
        # Test default
        with patch.dict(os.environ, {}, clear=True):
            assert get_rollout_percentage() == 0.1

        # Test custom value
        with patch.dict(os.environ, {"QUEUE_IPC_ROLLOUT": "0.75"}):
            assert get_rollout_percentage() == 0.75

        # Test clamping to valid range (0.0-1.0)
        with patch.dict(os.environ, {"QUEUE_IPC_ROLLOUT": "1.5"}):
            assert get_rollout_percentage() == 1.0

        with patch.dict(os.environ, {"QUEUE_IPC_ROLLOUT": "-0.5"}):
            assert get_rollout_percentage() == 0.0

        # Test invalid value defaults to 0.1
        with patch.dict(os.environ, {"QUEUE_IPC_ROLLOUT": "invalid"}):
            assert get_rollout_percentage() == 0.1


class TestWindowsSpawnContext:
    """Tests for Windows spawn context configuration."""

    def test_spawn_context_configured(self):
        """Test that spawn context is set on Windows."""
        if sys.platform == "win32":
            # On Windows, start method should be 'spawn'
            assert multiprocessing.get_start_method() == "spawn"
        else:
            # On non-Windows, start method can be other valid methods
            assert multiprocessing.get_start_method() in ("fork", "spawn", "forkserver")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
