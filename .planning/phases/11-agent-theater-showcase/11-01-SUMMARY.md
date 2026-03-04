---
phase: 11
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/config/agent_personalities.ts
  - frontend/src/hooks/useEventSequencer.ts
  - frontend/src/lib/types.ts
  - frontend/src/lib/store.ts
  - frontend/src/components/audit/AgentCard.tsx
  - frontend/src/components/audit/NarrativeFeed.tsx
 subsystem: agent-theater
tags: [personalities, event-sequencer, websocket, real-time, agent-interaction]

tech_stack:
  added:
    - agent_personalities.ts (configuration module)
    - useEventSequencer hook
    - EventSequencer class
    - PersonalityContext type
  patterns:
    - Singleton pattern (event sequencer)
    - Factory pattern (personality message generation)
    - Observer pattern (log-based feed updates)

key_files:
  created:
    - frontend/src/config/agent_personalities.ts
    - frontend/src/hooks/useEventSequencer.ts
  modified:
    - frontend/src/lib/types.ts (added bbox, context, params fields)
    - frontend/src/lib/store.ts (integrated event sequencer)
    - frontend/src/components/audit/AgentCard.tsx (personality messages)
    - frontend/src/components/audit/NarrativeFeed.tsx (PersonalityCard)

decisions:
  - "Use singleton for EventSequencer to maintain state across Zustand store instances"
  - "Personality messages use variable substitution for dynamic values ({count}, {score})"
  - "Throttle personality events in feed (30% of working messages) to avoid overwhelming users"
  - "Backward compatibility: events without sequence numbers processed immediately"

metrics:
  duration: "8 minutes"
  completed_date: "2026-02-28"
  tasks_completed: 3
  files_created: 2
  files_modified: 4
  lines_added: 891
  lines_removed: 172
---

# Phase 11 Plan 1: Agent Personality System & Event Sequencing Summary

Character-based agent communication system with WebSocket event ordering, enabling the foundation for Agent Theater by defining 5 distinct agent personalities (SCOUT: 🕵️ stealthy observer, VISION: 👁️ analytical pattern detector, SECURITY: 🛡️ protective auditor, GRAPH: 🌐 investigative connector, JUDGE: ⚖️ authoritative adjudicator) and ensuring reliable WebSocket message processing through intelligent event buffering and sequencing.

## Executed Tasks

| Task | Name | Commit | Files Changed |
| ---- | ---- | ------ | ------------- |
| 1 | Create agent personality configuration system | fbeb137 | frontend/src/config/agent_personalities.ts (new, 160 lines) |
| 2 | Create event sequencer hook for WebSocket ordering | 026cfbb | frontend/src/hooks/useEventSequencer.ts (new, 150 lines) |
| 3 | Integrate sequencer and add personality messages | 58f175f | store.ts, AgentCard.tsx, NarrativeFeed.tsx |

### Task 1: Agent Personality Configuration System

Created `frontend/src/config/agent_personalities.ts` with:
- **AgentPersona interface**: emoji, name, personality trait, catchphrases (working/complete/success/error), color
- **5 agent personalities**:
  - Scout (🕵️ Stealth Scout): "Scouting the perimeter...", "Map complete! {count} pages."
  - Vision (👁️ Vision Agent): "Analyzing visual patterns...", "Visual scan complete! {count} findings."
  - Security (🛡️ Security Sentinel): "Checking security headers...", "Security audit complete! {count} checks passed."
  - Graph (🌐 Network Investigator): "Cross-referencing entities...", "Network analysis complete! {count} entities."
  - Judge (⚖️ Forensic Judge): "Weighing all evidence...", "Verdict complete! Trust score: {score}."
- **getPersonalityMessage function**: Random message selection with variable substitution
- **Helper functions**: getWorkingMessage, getCompletionMessage, getSuccessMessage, getErrorMessage

**Catchphrase format with variables:**
- Complete messages use `{count}` or `{score}` placeholders
- Dynamic parameters via `params?: Record<string, number | string>`

### Task 2: Event Sequencer Hook

Created `frontend/src/hooks/useEventSequencer.ts` with:
- **SequencedEvent interface**: sequence number, event type, data payload
- **EventSequencer class**:
  - `addEvent(event)`: Buffer event with sequence number
  - `getReadyEvents()`: Return consecutive events starting from nextSequence
  - `getNextSequence()`: Get expected next sequence number
  - `reset()`: Clear buffer and reset counter
  - `getBufferSize()`: Get pending event count
- **Buffering logic**: Use Map<number, SequencedEvent> for O(1) lookups
- **useEventSequencer hook**: Returns sequencer methods with React integration

**Sequencing algorithm:**
1. Events arrive with monotonically increasing sequence numbers from backend
2. Out-of-order events buffered in map keyed by sequence
3. `getReadyEvents()` collects consecutive events starting from nextSequence
4. Events only returned when all preceding events are available

### Task 3: Integration & Component Updates

**Store integration (`frontend/src/lib/store.ts`):**
- Added EventSequencer singleton module (shared across Zustand instances)
- Modified `handleEvent()` to check for `event.sequence`
- If sequence present: buffer via sequencer, process ready events in order
- If sequence absent: process immediately (backward compatibility)
- Added `agent_personality` event handler: updates phase.message and adds log entry
- Refactored event processing into `processSingleEvent()` helper function

**AgentCard component (`frontend/src/components/audit/AgentCard.tsx`):**
- Added personality message display when agent status is "active"
- Messages auto-refresh every 8-10 seconds (randomized)
- Added flex message display when phase completes (using getCompletionMessage with params)
- Personality messages shown with styling appropriate to agent state (active: pulsing, complete: green)

**NarrativeFeed component (`frontend/src/components/audit/NarrativeFeed.tsx`):**
- Added "personality" entry type to FeedEntry
- Created PersonalityCard component: shows agent emoji, name, and personality message
- Throttled personality events: 30% of working messages, 100% of complete messages
- Added prevLogsCount ref to track new personality log entries
- Personality events added to feed when logs with context field arrive

**Type extensions (`frontend/src/lib/types.ts`):**
- Finding already had `bbox?: [number, number, number, number]` (pre-existing)
- LogEntry already had `context?: "working" | "complete" | "success" | "error"` (pre-existing)
- LogEntry already had `params?: Record<string, unknown>` (pre-existing)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Auto-fix] Syntax error in agent_personalities.ts**
- **Found during:** Task 1
- **Issue:** Line 134 had `],` (closing array) instead of `},` (closing object)
- **Fix:** Changed `catchphrases {...}],` to `catchphrases {...},`
- **Files modified:** frontend/src/config/agent_personalities.ts
- **Commit:** fbeb137

### Pre-existing Changes

The following files were modified before this plan execution (by parallel processes or previous sessions):
- `frontend/src/lib/types.ts`: Already included bbox, context, params fields (from Plan 11-02 research)
- `frontend/src/lib/store.ts`: Already had finding/screenshot association logic (from Plan 11-02)

These were compatible with plan requirements and not reverted.

## Verification Results

### Build Status
- TypeScript compilation: PASSED
- Next.js build: PASSED
- Static page generation: 5 pages

### Functional Verification
1. **Agent Personality System**: AGENT_PERSONALITIES exported with 5 distinct personalities
2. **Message Generation**: getPersonalityMessage() returns formatted messages with variable substitution
3. **Event Sequencer**: EventSequencer.addEvent() buffers events, getReadyEvents() returns ordered sequence
4. **Store Integration**: useAuditStore.handleEvent() uses sequencer for events with sequence field
5. **AgentCard**: Shows personality working messages and completion flex messages
6. **NarrativeFeed**: Shows PersonalityCard events for agent activity
7. **Type Safety**: Finding type has bbox field, LogEntry has context/params fields

## Auth Gates

None encountered during this plan execution.

## Implementation Notes

### Event Sequencing Strategy
The sequencer guarantees ordered event processing even with network latency:
- Backend assigns monotonically increasing sequence numbers to all events
- Frontend buffers out-of-order events
- Events only processed when all predecessors are available
- Backward compatibility maintained for non-sequenced events

### Personality Message Strategy
- Working messages appear consistently while agent is active (8-10s refresh)
- Complete/flex messages show summary stats (count, score) upon task completion
- Feed throttted to avoid overwhelming UI (30% working messages in feed)
- All personality messages stored in logs with context for audit trail

### Agent Characterization
Each agent has distinct personality traits:
- **Scout**: Cautious methodical approach, terrain mapping terminology
- **Vision**: Analytical detail-focus, pattern detection vocabulary
- **Security**: Protective defensive posture, fortress/safety metaphors
- **Graph**: Investigative connecting language, network/web terminology
- **Judge**: Authoritative weighing language, legal/court references

## Next Steps

This plan provides the foundation for the remaining Phase 11 plans:
- **Plan 11-02**: Screenshot Carousel & Highlight Overlays (already in progress/complete)
- **Plan 11-03**: Running Log & Celebration System (already in progress/complete)

The personality system and event sequencer are ready for backend integration to add sequence numbers to all WebSocket events.

---

*Self-Check: PASSED*
- All created files exist
- All commits verified in git log
- TypeScript compiles without errors
- Next.js builds and generates static pages successfully
