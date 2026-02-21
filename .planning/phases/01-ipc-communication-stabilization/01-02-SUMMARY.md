# Summary: Plan 02 - Add CLI Flags and Mode Selection Logic

**Status**: Completed
**Completed**: 2026-02-20
**Wave**: 1

---

## What Was Done

### 1. Modified `veritas/__main__.py`

#### Added CLI Arguments
Added three new CLI flags **before** existing arguments (highest priority order):
- `--use-queue-ipc`: Force Queue mode for IPC
- `--use-stdout`: Force stdout mode (disable Queue IPC)
- `--validate-ipc`: Run both Queue and stdout modes and compare results

#### Added IPC Mode Determination
- Imported `determine_ipc_mode`, `IPC_MODE_QUEUE`, `IPC_MODE_STDOUT`, `IPC_MODE_VALIDATE` from `core.ipc`
- Determined IPC mode based on priority hierarchy: CLI flags > Environment variables > Default (10% rollout)
- Added logging to display selected IPC mode

### 2. Mode Determination Logic (Already in ipc.py from Plan 01)

The `determine_ipc_mode()` function implements the priority hierarchy:
1. **Priority 1 - CLI flags**: Override all other settings
2. **Priority 2 - Environment variables**: `QUEUE_IPC_MODE` (queue/stdout/fallback)
3. **Priority 3 - Default**: Percentage-based rollout using `QUEUE_IPC_ROLLOUT` (default 10%)

---

## Mode Determination Behavior

### CLI Flag Override Examples
```bash
# Force Queue mode (highest priority)
python -m veritas https://example.com --use-queue-ipc

# Force stdout mode
python -m veritas https://example.com --use-stdout

# Validate both modes
python -m veritas https://example.com --validate-ipc
```

### Environment Variable Examples
```bash
# Use Queue mode from environment
QUEUE_IPC_MODE=queue python -m veritas https://example.com

# Use stdout mode from environment
QUEUE_IPC_MODE=stdout python -m veritas https://example.com
```

### Default Rollout Behavior
When no flags or env vars are specified:
- Uses `QUEUE_IPC_ROLLOUT` env var (default 0.1 = 10%)
- Randomly selects Queue mode based on rollout percentage
- Defaults to stdout for remaining percentage

---

## Verification

1. **CLI flags visible in --help output**:
   ```
   --use-queue-ipc       Use multiprocessing.Queue for IPC instead of stdout
   --use-stdout          Force stdout mode (disable Queue IPC)
   --validate-ipc        Run both Queue and stdout modes and compare results
   ```

2. **Mode determination verified**:
   - CLI `use_queue_ipc=True` returns `IPC_MODE_QUEUE`
   - CLI `use_stdout=True` returns `IPC_MODE_STDOUT`
   - Env var `QUEUE_IPC_MODE=queue` returns `IPC_MODE_QUEUE`

3. **Logging displays selected mode**:
   - Queue mode: "IPC mode: Queue"
   - Stdout mode: "IPC mode: Stdout"
   - Validate mode: "IPC mode: VALIDATE (running both Queue and stdout)"

---

## Artifacts Modified

1. `veritas/__main__.py` - Added CLI flags and IPC mode determination

---

## Next Steps

Proceed to **Plan 03**: Modify VeritasOrchestrator to support dual-mode emission via Queue or stdout
