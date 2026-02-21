"""
IPC (Inter-Process Communication) Utilities for Veritas

Provides Queue-based communication between backend and Veritas subprocess
for structured progress events, replacing fragile stdout marker parsing.

Windows Compatibility:
- Uses multiprocessing spawns context on Windows (required for subprocess IPC)
- Queue serialization for cross-process passing via environment variables
"""

import base64
import logging
import multiprocessing
import pickle
import queue
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("veritas.ipc")

# ============================================================
# Windows Spawn Context Configuration
# ============================================================

# Set spawn context ONCE at module import time (REQUIRED for Windows)
if sys.platform == "win32":
    multiprocessing.set_start_method('spawn', force=True)


# ============================================================
# ProgressEvent Dataclass
# ============================================================

@dataclass
class ProgressEvent:
    """Structured progress event for Queue-based IPC.

    This dataclass defines the schema for events sent from Veritas subprocess
    to backend via multiprocessing Queue, enabling structured parsing without
    fragile stdout marker searches.
    """
    type: str  # Event type: phase_start, phase_complete, finding, screenshot, etc.
    phase: str = ""  # Audit phase name (e.g., "Scout", "Vision", "Graph", "Judge")
    step: str = ""  # Step within phase (e.g., "navigating", "scanning", "done", "error")
    pct: int = 0  # Progress percentage (0-100)
    detail: str = ""  # Human-readable detail message
    summary: dict = None  # Optional summary dict with phase results
    data: bytes = None  # Binary data for screenshots or other attachments
    timestamp: float = field(default_factory=time.time)  # Event timestamp

    def __post_init__(self):
        if self.summary is None:
            self.summary = {}


# ============================================================
# Security Mode Progress Events (Plan 02-03)
# ============================================================

@dataclass
class SecurityModeStarted(ProgressEvent):
    """Event emitted when security analysis mode is selected.

    Tracks whether SecurityAgent (agent mode) or security_node function
    (function mode) is being used for the current audit.

    Fields:
        security_mode: "agent", "function", or "function_fallback"
        module_count: Number of security modules to run
        rollout_enabled: True if rollout percentage is active
    """
    security_mode: str = ""  # "agent", "function", or "function_fallback"
    module_count: int = 0
    rollout_enabled: bool = False


@dataclass
class SecurityModeCompleted(ProgressEvent):
    """Event emitted when security analysis completes.

    Contains execution metrics for monitoring and debugging.

    Fields:
        security_mode: Security mode that was used
        analysis_time_ms: Total analysis time in milliseconds
        modules_run: List of module names that ran successfully
        modules_failed: List of module names that failed
        findings_count: Total security findings found
        composite_score: Composite security score (0.0 to 1.0)
    """
    security_mode: str = ""
    analysis_time_ms: int = 0
    modules_run: list[str] = field(default_factory=list)
    modules_failed: list[str] = field(default_factory=list)
    findings_count: int = 0
    composite_score: float = 0.0


# ============================================================
# IPC Mode Constants
# ============================================================

IPC_MODE_QUEUE = "queue"
IPC_MODE_STDOUT = "stdout"
IPC_MODE_VALIDATE = "validate"  # Run both and compare results


# ============================================================
# Queue Creation Utilities
# ============================================================

def create_queue(maxsize: int = 1000) -> multiprocessing.Queue:
    """Create a multiprocessing.Manager Queue for IPC.

    Args:
        maxsize: Maximum number of items in the queue (default: 1000)

    Returns:
        multiprocessing.Queue configured with specified maxsize

    Note:
        Uses multiprocessing.Manager() for cross-process Queue support,
        which is required for Windows subprocess communication.
    """
    return multiprocessing.Manager().Queue(maxsize=maxsize)


def safe_put(q: multiprocessing.Queue, event: Any, logger_obj: logging.Logger,
             timeout: float = 1.0) -> bool:
    """Safely put event into Queue with timeout and backpressure handling.

    Args:
        q: The Queue to put the event into
        event: The event (ProgressEvent or dict) to put into Queue
        logger_obj: Logger instance for logging warnings/errors
        timeout: Timeout in seconds for Queue.put (default: 1.0)

    Returns:
        bool: True if put succeeded, False if failed (queue full or error)

    Note:
        Logs WARNING when queue is full (backpressure).
        On queue.Full, optionally removes oldest item and retries once.
    """
    try:
        q.put(event, timeout=timeout)
        return True
    except queue.Full:
        # Get event type for logging
        event_type = getattr(event, 'type', str(type(event).__name__))

        # Try to remove oldest and retry once (backpressure relief)
        try:
            q.get(timeout=0.1)
            logger_obj.warning(f"Progress queue full, dropped oldest event: {event_type}")
            q.put(event, timeout=timeout)
            return True
        except (queue.Empty, queue.Full):
            logger_obj.warning(f"Progress queue still full, dropping event: {event_type}")
            return False
    except Exception as e:
        logger_obj.error(f"Queue put error: {e}")
        return False


# ============================================================
# Queue Serialization for Subprocess Passing
# ============================================================

def serialize_queue(queue: multiprocessing.Queue) -> tuple[str, str]:
    """Serialize Queue for passing to subprocess via environment variables.

    Args:
        queue: The multiprocessing Queue to serialize

    Returns:
        tuple: (fileno, serialized) where:
            - fileno: File descriptor/identifier string
            - serialized: Base64-encoded pickled pipeline handle

    Note:
        Uses multiprocessing.reduction.reduce_connection() to get the pipeline
        handle, then base64-encodes pickled result for env var passing.
    """
    from multiprocessing import reduction

    # Get pipeline handle for Queue
    fileno, handle = reduction.reduce_connection(queue)[0]

    # Base64-encode pickled handle for environment passing
    serialized = base64.b64encode(pickle.dumps(handle)).decode('utf-8')

    return (str(fileno), serialized)


def deserialize_queue_from_env() -> Optional[multiprocessing.Queue]:
    """Deserialize Queue from environment variables (subprocess-side).

    Reads AUDIT_QUEUE_FD and AUDIT_QUEUE_KEY from environment and
    reconstructs the multiprocessing Queue.

    Returns:
        multiprocessing.Queue: Reconstructed Queue, or None on failure

    Note:
        Logs ERROR on deserialization failure instead of raising.
        Called in subprocess to receive Queue from parent process.
    """
    from multiprocessing import reduction

    fd = os.getenv("AUDIT_QUEUE_FD")
    key = os.getenv("AUDIT_QUEUE_KEY")

    if fd is None or key is None:
        logger.error("Missing AUDIT_QUEUE_FD or AUDIT_QUEUE_KEY environment variables")
        return None

    try:
        # Reconstruct handle from base64 pickled data
        handle = pickle.loads(base64.b64decode(key))
        # Rebuild Queue from handle
        queue_obj = reduction.rebuild_connection((None, handle), int(fd))
        return queue_obj
    except Exception as e:
        logger.error(f"Failed to deserialize Queue: {e}")
        return None


# ============================================================
# Mode Determination Logic
# ============================================================

def get_rollout_percentage() -> float:
    """Get Queue IPC rollout percentage from environment.

    Reads QUEUE_IPC_ROLLOUT env var (float 0.0-1.0), defaults to 0.1 (10%).
    Clamps to valid range.

    Returns:
        float: Rollout percentage between 0.0 and 1.0
    """
    rollout = os.getenv("QUEUE_IPC_ROLLOUT", "0.1")
    try:
        percentage = float(rollout)
    except ValueError:
        percentage = 0.1

    # Clamp to 0.0-1.0 range
    return max(0.0, min(1.0, percentage))


def determine_ipc_mode(
    cli_use_queue_ipc: bool = False,
    cli_use_stdout: bool = False,
    cli_validate_ipc: bool = False,
) -> str:
    """Determine IPC mode based on CLI flags, environment, and rollout.

    Priority hierarchy (per CONTEXT.md):
    1. CLI flags (highest priority)
    2. Environment variable QUEUE_IPC_MODE
    3. Default: percentage-based rollout using QUEUE_IPC_ROLLOUT

    Args:
        cli_use_queue_ipc: Force Queue mode via --use-queue-ipc flag
        cli_use_stdout: Force stdout mode via --use-stdout flag
        cli_validate_ipc: Run both modes via --validate-ipc flag

    Returns:
        str: IPC mode (IPC_MODE_QUEUE, IPC_MODE_STDOUT, or IPC_MODE_VALIDATE)
    """
    # Priority 1: CLI flags override everything
    if cli_validate_ipc:
        return IPC_MODE_VALIDATE
    if cli_use_queue_ipc:
        return IPC_MODE_QUEUE
    if cli_use_stdout:
        return IPC_MODE_STDOUT

    # Priority 2: Environment variable
    env_mode = os.getenv("QUEUE_IPC_MODE", "").lower()
    if env_mode == IPC_MODE_QUEUE:
        return IPC_MODE_QUEUE
    elif env_mode in (IPC_MODE_STDOUT, "fallback"):
        return IPC_MODE_STDOUT

    # Priority 3: Default percentage-based rollout
    rollout = get_rollout_percentage()
    if random.random() < rollout:
        return IPC_MODE_QUEUE
    else:
        return IPC_MODE_STDOUT


# Import os here (needed for environment variable access)
import os  # noqa: E402
