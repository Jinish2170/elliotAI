---
id: 09-03
phase: 9
wave: 2
autonomous: true
completed: true

objective: Implement real-time progress streaming with token-bucket rate limiting, progressive screenshot delivery, and user engagement pacing (5-10s activity signals).

files_modified:
  - veritas/core/progress/__init__.py
  - veritas/core/progress/rate_limiter.py
  - veritas/core/progress/event_priority.py
  - veritas/core/progress/emitter.py
  - veritas/core/progress/estimator.py
  - veritas/core/orchestrator.py
  - veritas/agents/scout.py
  - veritas/agents/vision.py

tasks: 6
requirements:
  - "PROG-01"
  - "PROG-02"
  - "PROG-03"

depends_on:
  - "09-01"
  - "09-02"

has_summary: true
gap_closure: false

duration_seconds: 2459
duration_minutes: 41
completed_date: "2026-02-28T10:33:09Z"

subsystem: progress_streaming

tech_added:
  - "TokenBucketRateLimiter: token-bucket rate limiting with burst capacity and priority queue"
  - "EventPriority: CRITICAL(0), HIGH(1), MEDIUM(2), LOW(3) enum for event prioritization"
  - "ProgressEmitter: WebSocket event streaming with rate limiting and batching"
  - "CompletionTimeEstimator: EMA-based completion time estimation per (site_type, agent)"
  - "Image compression: 200x150 JPEG thumbnails via PIL"

tech_patterns:
  - "Rate limiting: token-bucket algorithm with priority-based queue management"
  - "Batching: Findings batched (5 per event) to reduce WebSocket traffic"
  - "EMA smoothing: Exponential moving average for execution time prediction"
  - "Optional injection: progress_emitter parameter with backward compatibility"

key_files_created:
  - "veritas/core/progress/rate_limiter.py"
  - "veritas/core/progress/event_priority.py"
  - "veritas/core/progress/emitter.py"
  - "veritas/core/progress/estimator.py"
  - "veritas/core/progress/__init__.py"

key_files_modified:
  - "veritas/core/orchestrator.py"
  - "veritas/agents/scout.py"
  - "veritas/agents/vision.py"

decisions:
  - "Token-bucket rate limiting: 5 events/sec max with burst=10 for WebSocket throttling"
  - "Priority queue: Lower priority events dropped when queue full, higher priority protected"
  - "Thumbnail compression: 200x150 JPEG Q70 to reduce bandwidth for screenshots"
  - "Findings batching: 5 findings per findings_batch event to prevent WebSocket flooding"
  - "EMA alpha=0.2: Smoothing factor for execution time prediction, balances responsiveness vs stability"
  - "Optional progress streaming: use_progress_streaming flag enables new WebSocket path, maintains backward compatibility"
  - "User engagement pacing: 5-10s heartbeat interval with interesting highlights during long-running agents"

metrics:
  tasks: 6
  files: 8
  duration_seconds: 2459
  duration_minutes: 41

deviations: "None - plan executed exactly as written."
---

# Phase 09 Plan 03: Real-time Progress Streaming Summary

**One-liner:** WebSocket-based real-time progress streaming with token-bucket rate limiting, intelligent batching, and EMA-based completion time estimation.

## Overview

Implemented a comprehensive real-time progress streaming system for long-running audits. The system uses token-bucket rate limiting to prevent WebSocket flooding during intensive operations like 5-pass Vision analysis, with thumbnail compression and intelligent batching to optimize bandwidth utilization.

## Key Components

### TokenBucketRateLimiter (`veritas/core/progress/rate_limiter.py`)

- Classic token-bucket algorithm with burst capacity (10 tokens)
- Max rate: 5 events/second
- Priority-based queue: lower priority events dropped when full
- Thread-safe with asyncio.Lock
- Statistics: tokens_remaining, queue_size, dropped_events

### EventPriority (`veritas/core/progress/event_priority.py`)

- CRITICAL (0): Agent failures, circuit breaker trips (never dropped)
- HIGH (1): Findings, phase completions
- MEDIUM (2): Screenshots, progress updates
- LOW (3): Info messages, heartbeats

### ProgressEmitter (`veritas/core/progress/emitter.py`)

- WebSocket event streaming with integrated rate limiting
- Screenshot emission with thumbnail compression (200x150 JPEG Q70)
- Findings batching: 5 per findings_batch event
- Agent status: started/running/completed/failed/degraded
- Error emission with recoverable flag
- User engagement: heartbeat and interesting highlights

### CompletionTimeEstimator (`veritas/core/progress/estimator.py`)

- EMA-based execution time tracking per (site_type, agent)
- Default times: scout=20s, vision=30s, graph=10s, judge=10s, osint=25s
- Real-time ETA calculation with remaining agents
- Agent execution tracking: PENDING, RUNNING, COMPLETED, FAILED, SKIPPED

## Agent Integration

### Scout Agent (`veritas/agents/scout.py`)

- Agent status at start and completion
- Screenshot streaming with thumbnail compression
- Progress updates at key stages (15%, 30%, 50%, 60%, 75%, 100%)
- Error emission for CAPTCHA (recoverable=False) and navigation failures
- Progress during scroll cycles

### Vision Agent (`veritas/agents/vision.py`)

- Pass-by-pass progress (Pass 1: 10%, Pass 2: 30%, Pass 3: 50%, Pass 4: 70%, Pass 5: 90%)
- Finding streaming for dark patterns in Pass 2
- Interesting highlights for findings count
- Error handling for VLM and temporal analysis failures
- Skip detection with progress updates

### Orchestrator (`veritas/core/orchestrator.py`)

- Overall progress tracking (0%, 5%, 10%, 25%, 30%, 50%, 70%, 75%, 90%, 100%)
- Agent status for all agents (Scout, Security, Vision, Graph, Judge)
- Estimated remaining time calculation and emission
- Degradation status with fallback reason
- Interesting highlights for findings and trust scores
- Final flush before completion

## Requirements Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| PROG-01 | COMPLETE | Progressive screenshot streaming with 200x150 thumbnails, live scroll visualization, connection health |
| PROG-02 | COMPLETE | Real-time notifications with 5-findings batching, color-coded alerts (CRITICAL/HIGH/MEDIUM/LOW), incremental confidence |

## Deviations from Plan

None - plan executed exactly as written.

## Files Created

1. `veritas/core/progress/__init__.py` - Module exports
2. `veritas/core/progress/rate_limiter.py` - TokenBucketRateLimiter (158 lines)
3. `veritas/core/progress/event_priority.py` - EventPriority enum (24 lines)
4. `veritas/core/progress/emitter.py` - ProgressEmitter (240 lines)
5. `veritas/core/progress/estimator.py` - CompletionTimeEstimator (239 lines)

## Files Modified

1. `veritas/agents/scout.py` - Progress streaming hooks (90 additions)
2. `veritas/agents/vision.py` - Progress streaming hooks (100 additions)
3. `veritas/core/orchestrator.py` - Progress streaming hooks (116 additions)

## Commits

| Hash | Message |
|------|---------|
| f33728b | feat(09-03): create token-bucket rate limiter for WebSocket throttling |
| 7e68a33 | feat(09-03): create event priority and progress emitter |
| d7e0deb | feat(09-03): create completion time estimator with EMA |
| 60e6258 | feat(09-03): integrate progress streaming with Scout Agent |
| 9ca7a26 | feat(09-03): integrate progress streaming with Vision Agent |
| 67de0dc | feat(09-03): integrate progress streaming with Orchestrator |

## Extension Points

- New agent types can add progress streaming hooks
- Custom event types can be added via ProgressEmitter.emit_event()
- Rate limiter config can be adjusted per environment (max_rate, burst)
- Interesting highlight templates can be customized per phase
- Thumbnail size and JPEG quality can be tuned for bandwidth constraints

## Testing

To enable progress streaming:

```python
from veritas.core.progress import ProgressEmitter
from veritas.core import VeritasOrchestrator

# Create progress emitter with WebSocket connection
emitter = ProgressEmitter(websocket=ws_connection)

# Run orchestrator with progress streaming enabled
orchestrator = VeritasOrchestrator(
    use_progress_streaming=True,
    progress_emitter=emitter
)
state = await orchestrator.audit("https://example.com")
```

For agents (backward compatible):

```python
# Scout Agent uses progress_emitter from instance
scout = StealthScout(progress_emitter=emitter)
result = await scout.investigate("https://example.com", progress_emitter=emitter)

# Vision Agent uses progress_emitter from instance
vision = VisionAgent(progress_emitter=emitter)
result = await vision.analyze_5_pass(screenshots, progress_emitter=emitter)
```

## Self-Check: PASSED

All 6 tasks completed and committed:
- Task 1: Token-bucket rate limiter (f33728b)
- Task 2: Event priority and progress emitter (7e68a33)
- Task 3: Completion time estimator (d7e0deb)
- Task 4: Scout Agent integration (60e6258)
- Task 5: Vision Agent integration (9ca7a26)
- Task 6: Orchestrator integration (67de0dc)

All files created and verified:
- veritas/core/progress/__init__.py
- veritas/core/progress/rate_limiter.py
- veritas/core/progress/event_priority.py
- veritas/core/progress/emitter.py
- veritas/core/progress/estimator.py

All commits verified in git log.
