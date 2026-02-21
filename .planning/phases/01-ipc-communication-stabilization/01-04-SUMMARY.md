# Summary: Plan 04 - Modify AuditRunner for Queue IPC

**Status**: Completed
**Completed**: 2026-02-20
**Wave**: 3

---

## What Was Done

### 1. Created `backend/__init__.py`

Set multiprocessing spawn context at module import time for Windows compatibility:
```python
import sys
import multiprocessing

if sys.platform == "win32":
    multiprocessing.set_start_method('spawn', force=True)
```

### 2. Modified `backend/services/audit_runner.py`

#### Added Imports
```python
import multiprocessing as mp
import queue
sys.path.insert(0, str(project_root))
from veritas.core.ipc import (
    determine_ipc_mode, IPC_MODE_QUEUE, IPC_MODE_STDOUT,
    create_queue, serialize_queue,
)
```

#### Modified `__init__` Method
Added IPC mode determination and Queue attributes:
```python
self.ipc_mode = self._determine_ipc_mode()
self.progress_queue: Optional[mp.Queue] = None
self._mgr = None
```

#### Added `_determine_ipc_mode()` Method
Determines IPC mode from environment variables or uses percentage-based default:
```python
def _determine_ipc_mode(self) -> str:
    ipc_mode = determine_ipc_mode(cli_use_queue_ipc=False, cli_use_stdout=False)
    return ipc_mode
```

#### Added Queue Setup in `run()` Method
Configures Queue when IPC mode is Queue:
```python
if self.ipc_mode == IPC_MODE_QUEUE:
    self._mgr = mp.Manager()
    self.progress_queue = self._mgr.Queue(maxsize=1000)
    fd, serialized = serialize_queue(self.progress_queue)
    queue_env_vars = {"AUDIT_QUEUE_FD": str(fd), "AUDIT_QUEUE_KEY": serialized}
    cmd.append("--use-queue-ipc")
```

#### Added `_read_queue_and_stream()` Class Method
Reads ProgressEvent objects from Queue and sends to WebSocket:
- Converts ProgressEvent dataclass to dict format
- Maps progress events to WebSocket event types (phase_start, phase_complete, phase_error)
- Handles queue.Empty exceptions gracefully
- Responds to asyncio.CancelledError for clean shutdown

#### Modified `run()` Method
- Creates background task for queue reading when Queue mode is active
- Passes Queue environment variables to subprocess
- Maintains stdout parsing for validation mode and fallback

#### Added Cleanup in `finally` Block
- Cancels queue reader task on audit completion
- Shuts down multiprocessing Manager to release Queue resources

---

## Mode Behavior

### Queue Mode (IPC_MODE_QUEUE)
1. AuditRunner creates multiprocessing.Manager.Queue(maxsize=1000)
2. Queue is serialized and passed to subprocess via AUDIT_QUEUE_FD and AUDIT_QUEUE_KEY
3. Subprocess receives Queue via deserialize_queue_from_env()
4. ProgressEvent objects flow through Queue instead of stdout markers
5. Backend reads Queue and streams to WebSocket
6. Manager and Queue cleaned up on completion

### Stdout Mode (IPC_MODE_STDOUT)
1. Queue not created (self.progress_queue = None)
2. No Queue environment variables passed to subprocess
3. Subprocess uses stdout ##PROGRESS: markers (existing behavior)
4. Backend parses stdout for progress events (existing behavior)

---

## Verification

1. **Backend spawn context configured**:
   ```
   Start method before import: spawn
   Start method after import: spawn
   ```

2. **AuditRunner IPC mode determined**:
   ```python
   runner = AuditRunner('test', 'https://example.com', 'quick_scan')
   print(f'IPC mode: {runner.ipc_mode}')  # stdout or queue
   # OK - AuditRunner IPC mode determined
   ```

3. **Queue reader method exists**:
   ```python
   assert hasattr(AuditRunner, '_read_queue_and_stream')
   # OK - _read_queue_and_stream method exists
   ```

4. **Progress queue attribute initialized**:
   ```python
   assert runner.progress_queue is not None (or None if stdout mode)
   self._mgr is not None (or None if stdout mode)
   ```

---

## Artifacts Created/Modified

1. `backend/__init__.py` - Sets spawn context (new file)
2. `backend/services/audit_runner.py` - Added Queue IPC support with:
   - IPC mode determination
   - Queue creation and serialization
   - Queue reader background task
   - Manager cleanup

---

## Next Steps

Proceed to **Plan 05**: Add integration tests for Queue IPC and fallback behavior
