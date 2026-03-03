---
id: 06-05
phase: 6
wave: 4
autonomous: true

objective: Implement VisionEventEmitter with throttling and batching to prevent WebSocket flooding during 5-pass analysis.

files_modified:
  - veritas/agents/vision.py
  - frontend/src/lib/types.ts
  - frontend/src/lib/store.ts

tasks:
  - Create VisionEventEmitter class with max_events_per_sec throttling
  - Implement batch_findings() for efficient transmission
  - Add flush_queue() for event queue management
  - Extend frontend AuditEvent types with vision pass events
  - Update frontend store to handle vision pass events

has_summary: false
gap_closure: false
---

# Plan 06-05: Vision Event Emitter

**Goal:** Manage vision-related WebSocket events with throttling (max 5/sec) and batching (5 findings per event) to prevent flooding.

## Context

5 passes × multiple findings each = 30-50 events per page would flood WebSocket. Event emitter uses:
- **Throttling:** Max 5 events/sec
- **Batching:** Up to 5 findings per event
- **Coalescing:** Merge findings at same coordinates

## Implementation

### Task 1: Create VisionEventEmitter class

**File:** `veritas/agents/vision.py`

```python
class VisionEventEmitter:
    """Manages vision WebSocket events with throttling and batching."""

    def __init__(self, max_events_per_sec: int = 5, batch_size: int = 5):
        self.max_events_per_sec = max_events_per_sec
        self.batch_size = batch_size
        self.event_queue: List[dict] = []
        self.last_emit_time = 0.0
        self.logger = logging.getLogger(__name__)

    async def emit_vision_start(self, total_screenshots: int) -> None:
        await self._emit({
            "type": "vision_start",
            "screenshots": total_screenshots,
            "passes": 5
        })

    async def emit_pass_start(self, pass_num: int, description: str, screenshots_in_pass: int) -> None:
        await self._emit({
            "type": "vision_pass_start",
            "pass": pass_num,
            "description": description,
            "screenshots": screenshots_in_pass
        })

    async def emit_pass_findings(self, pass_num: int, findings: List[Finding]) -> None:
        if not findings:
            return

        batches = [findings[i:i+self.batch_size] for i in range(0, len(findings), self.batch_size)]
        for batch in batches:
            event = {
                "type": "vision_pass_findings",
                "pass": pass_num,
                "findings": [f.to_dict() for f in batch],
                "count": len(batch),
                "batch": True
            }
            await self._emit(event)

    async def emit_pass_complete(self, pass_num: int, findings_count: int, confidence: float) -> None:
        await self._emit({
            "type": "vision_pass_complete",
            "pass": pass_num,
            "findings_count": findings_count,
            "confidence": confidence
        })

    async def _emit(self, event: dict) -> None:
        """Emit event with rate limiting."""
        now = time.time()
        time_since_last = now - self.last_emit_time
        min_interval = 1.0 / self.max_events_per_sec

        if time_since_last >= min_interval:
            await self._do_emit(event)
            self.last_emit_time = now
        else:
            self.event_queue.append(event)

    async def _do_emit(self, event: dict) -> None:
        """Actually emit event via progress emitter."""
        print(f"##PROGRESS:{json.dumps(event)}", flush=True)

    async def flush_queue(self) -> None:
        """Flush accumulated queued events."""
        while self.event_queue:
            event = self.event_queue.pop(0)
            await self._do_emit(event)
            self.last_emit_time = time.time()
```

### Task 2: Extend frontend types

**File:** `frontend/src/lib/types.ts`

```typescript
export interface VisionPassStartEvent {
  type: 'vision_pass_start';
  pass: number;
  description: string;
  screenshots: number;
}

export interface VisionPassFindingsEvent {
  type: 'vision_pass_findings';
  pass: number;
  findings: Finding[];
  count: number;
  batch: boolean;
}

export interface VisionPassCompleteEvent {
  type: 'vision_pass_complete';
  pass: number;
  findings_count: number;
  confidence: number;
}

export type AuditEvent =
  | PhaseStartEvent
  | PhaseCompleteEvent
  | FindingEvent
  | ScreenshotEvent
  | VisionPassStartEvent
  | VisionPassFindingsEvent
  | VisionPassCompleteEvent
  | AuditResultEvent
  | AuditCompleteEvent;
```

### Task 3: Update frontend store

**File:** `frontend/src/lib/store.ts`

```typescript
handleEvent(event: AuditEvent) {
  switch (event.type) {
    // existing cases...

    case 'vision_pass_start':
      this.updatePhase('vision', { activePass: event.pass });
      break;

    case 'vision_pass_findings':
      this.addFindings(event.findings);
      break;

    case 'vision_pass_complete':
      this.updatePhase('vision', {
        completedPasses: [...(get().phases['vision']?.completedPasses || []), event.pass]
      });
      break;
  }
}
```

## Success Criteria

1. ✅ VisionEventEmitter emits events with throttling
2. ✅ Batching groups up to 5 findings per event
3. ✅ Frontend types include vision pass events
4. ✅ Store handles vision pass events correctly
5. ✅ Test shows no event flooding under high finding count

## Dependencies

- Requires: 06-01, 06-02, 06-03, 06-04 (all foundation blocks)
