# Plan: Phase 11 - Agent Theater & Content Showcase

**Phase ID:** 11
**Milestone:** v2.0 Masterpiece Features
**Depends on:** Phase 9 (Orchestrator), Phase 10 (Cybersecurity)
**Status:** pending
**Created:** 2026-02-23

---

## Context

### Current State (Pre-Phase)

**Frontend:**
- Basic Agent Pipeline with phase status cards
- EvidencePanel showing screenshots
- NarrativeFeed with finding descriptions
- ForensicLog with log entries
- No agent personality or "flexing"
- No green flag celebrations
- No psychology-driven content flow
- Screenshot carousel not implemented
- No gradual reveal patterns

**Agent Display:**
- Static icons for each agent
- No animated progress indicators
- No task completion celebrations
- No "agent doing work" messaging

**Screenshot Display:**
- Single screenshot view
- No carousel for multiple screenshots
- No highlight overlays for findings
- No comparison views

**Progress Indication:**
- Basic phase indicators
- No countdown timers
- No "something happening" pacing

### Goal State (Post-Phase)

**Psychology-Driven Content Flow:**
- Gradual reveal patterns for maintaining engagement
- Agent personality (each agent has distinct character)
- Finding "flexing" of achievements
- Green flag celebration for positive results

**Real-Time Agent Theater Components:**
- Event sequencing with sequence numbers
- Reordering buffers for out-of-order events
- Agent activity streaming with personalities
- "Vision found 3 dark patterns!" type messages
- Task completion animations

**Screenshot Carousel with Gradual Reveal:**
- Highlight overlays for detected dark patterns (coordinates align visually)
- Carousel navigation through screenshot series
- Comparison views (before/after, with/without findings)
- Zoom and pan for detailed inspection

**Running Log with Task Flexing:**
- Log windowing (max 100 entries) with memory monitoring
- Agent activity streaming with timestamps
- Task completion celebration ("Judge: High trust score achieved!")
- Interesting highlights during waiting periods

---

## Implementation Strategy

### 11.1 Agent Personality System

**File:**
- `frontend/src/config/agent_personalities.ts` (new)

**Agent Personalities:**
```typescript
export interface AgentPersonality {
  emoji: string;
  name: string;
  personality: string;
  catchphrases: {
    working: string[];
    complete: string[];
    success: string[];
    error: string[];
  };
}

export const AGENT_PERSONALITIES: Record<string, AgentPersonality> = {
  scout: {
    emoji: "🕵️",
    name: "Stealth Scout",
    personality: "Cautious observer, discovers the terrain",
    catchphrases: {
      working: ["Scouting the perimeter...", "Examining page structure..."],
      complete: ["Map complete! Found {page_count} pages."],
      success: ["Landed safely!"],
      error: ["Navigation blocked..."]
    }
  },
  vision: {
    emoji: "👁️",
    name: "Vision Agent",
    personality: "Detail-oriented pattern detector",
    catchphrases: {
      working: ["Analyzing visual patterns...", "Scanning for dark patterns..."],
      complete: ["Visual scan complete! {count} findings detected."],
      success: ["Pattern identified!"],
      error: ["Visual obscured..."]
    }
  },
  // ... (security, graph, judge)
};
```

### 11.2 Screenshot Carousel Component

**File:**
- `frontend/src/components/audit/ScreenshotCarousel.tsx` (new)

**Features:**
- Carousel navigation with prev/next buttons
- Highlight overlays (SVG rectangles over findings)
- Zoom in/out
- Fullscreen mode
- Toggle findings on/off

**Implementation Key Points:**
```typescript
// Coordinate alignment: finding.bbox must match screenshot dimensions
// Finding bbox is 0-100 scale, convert to pixels
const toPixels = (bbox: number[], width: number, height: number) => ({
  x: (bbox[0] / 100) * width,
  y: (bbox[1] / 100) * height,
  width: (bbox[2] / 100) * width,
  height: (bbox[3] / 100) * height
});
```

### 11.3 Running Log with Task Flexing

**File:**
- `frontend/src/components/audit/RunningLog.tsx` (extend existing)

**Features:**
- Memory monitoring (max 100 entries)
- Timestamp formatting
- Agent emoji + message styling
- Completion celebrations (confetti animation)
- "Interesting fact" messages during waiting

### 11.4 Green Flag Celebration Component

**File:**
- `frontend/src/components/audit/GreenFlagCelebration.tsx` (new)

**Features:**
- Triggered when trust_score >= 80
- Animated celebration banner
- List of green flags found
- Positive reinforcement messaging

### 11.5 Event Sequencing and Buffering

**File:**
- `frontend/src/hooks/useEventSequencer.ts` (new)

**Purpose:**
- WebSocket events may arrive out of order
- Reorder events by sequence number
- Buffer for windowing

### 11.6 Real-Time Pattern Notifications

**File:**
- `frontend/src/components/audit/PatternNotifications.tsx` (new)

**Features:**
- Live feed of discoveries
- Color-coded alerts (red=critical, yellow=warning, green=positive)
- Slide-in animation
- Auto-dismiss after 5 seconds

---

## Dependencies (What Must Complete First)

### Internal (Within Phase 11)
1. **Agent Personality System → Event Sequencing**: Define personalities before creating agent activity messages
2. **Screenshot Carousel → Highlight Overlays**: Capture dimensions before implementing coordinate conversion
3. **Running Log → Event Buffering**: Establish memory monitoring before implementing log windowing
4. **Event Sequencer → Pattern Notifications**: Buffer events before displaying live notifications

### External (From Previous Phases)
1. **Phase 1-5 (v1.0 Core)**: ✅ DONE - Basic frontend components and agent pipeline
2. **Phase 6 (Vision Agent Enhancement)**: Progress emitter provides finding events for showcase
3. **Phase 7 (Quality Foundation)**: Validated findings with confidence scores for display
4. **Phase 8 (OSINT Integration)**: Entity profiles and intelligence network visualization data
5. **Phase 9 (Judge System & Orchestrator)**: Dual-tier verdict for appropriate display selection
6. **Phase 10 (Cybersecurity)**: Security findings for technical tier display and threat intelligence

### Blocks for Future Phases
None - Phase 11 is the final phase in the v2.0 roadmap

---

## Test Strategy

### Frontend Unit Tests

**Test: AgentPersonality configuration**
```typescript
// frontend/src/__tests__/agent_personality.test.ts
import { AGENT_PERSONALITIES } from '@/config/agent_personalities';

describe('AgentPersonality', () => {
  test('all 5 agents have defined personalities', () => {
    expect(AGENT_PERSONALITIES).toHaveProperty('scout');
    expect(AGENT_PERSONALITIES).toHaveProperty('vision');
    expect(AGENT_PERSONALITIES).toHaveProperty('security');
    expect(AGENT_PERSONALITIES).toHaveProperty('graph');
    expect(AGENT_PERSONALITIES).toHaveProperty('judge');
  });

  test('personalities have all required catchphrase categories', () => {
    Object.values(AGENT_PERSONALITIES).forEach(personality => {
      expect(personality.catchphrases).toHaveProperty('working');
      expect(personality.catchphrases).toHaveProperty('complete');
      expect(personality.catchphrases).toHaveProperty('success');
      expect(personality.catchphrases).toHaveProperty('error');
      expect(Array.isArray(personality.catchphrases.working)).toBe(true);
    });
  });

  test('message formatting with params', () => {
    const vision = AGENT_PERSONALITIES.vision;
    const message = vision.catchphrases.complete[0].replace('{count}', '3');
    expect(message).toContain('3');
  });
});
```

**Test: ScreenshotCarousel coordinate conversion**
```typescript
// frontend/src/__tests__/ScreenshotCarousel.test.ts
import { render, screen } from '@testing-library/react';
import ScreenshotCarousel from '@/components/audit/ScreenshotCarousel';

const mockFinding = {
  id: 'dark-pattern-1',
  category: 'countdown_timer',
  description: 'Urgency countdown',
  bbox: [10, 20, 30, 40], // x, y, width, height (0-100 scale)
  confidence: 0.9
};

const mockScreenshot = {
  url: 'data:image/png;base64,abc123',
  width: 1920,
  height: 1080,
  findings: [mockFinding]
};

describe('ScreenshotCarousel', () => {
  test('converts bbox to pixels correctly', () => {
    render(<ScreenshotCarousel screenshots={[mockScreenshot]} />);

    const overlay = screen.getByRole('finding-highlight');
    const style = window.getComputedStyle(overlay);

    // bbox: [10, 20, 30, 40]
    // x: (10/100) * 1920 = 192
    // y: (20/100) * 1080 = 216
    // width: (30/100) * 1920 = 576
    // height: (40/100) * 1080 = 432
    expect(style.left).toBe('192px');
    expect(style.top).toBe('216px');
    expect(style.width).toBe('576px');
    expect(style.height).toBe('432px');
  });

  test('handles multiple screenshots navigation', async () => {
    const screenshots = [mockScreenshot, { ...mockScreenshot, url: 'data:image/png;base64,def456' }];
    render(<ScreenshotCarousel screenshots={screenshots} />);

    const nextButton = screen.getByRole('button', { name: /next/i });
    const prevButton = screen.getByRole('button', { name: /previous/i });

    expect(screen.getByAltText('Screenshot 1')).toBeInTheDocument();

    await userEvent.click(nextButton);
    expect(screen.getByAltText('Screenshot 2')).toBeInTheDocument();

    await userEvent.click(prevButton);
    expect(screen.getByAltText('Screenshot 1')).toBeInTheDocument();
  });
});
```

**Test: RunningLog memory monitoring**
```typescript
// frontend/src/__tests__/RunningLog.test.ts
import { render, act } from '@testing-library/react';
import RunningLog from '@/components/audit/RunningLog';
import { useWebSocket } from '@/hooks/useWebSocket';

jest.mock('@/hooks/useWebSocket');

describe('RunningLog', () => {
  test('maintains max 100 entries with windowing', () => {
    const mockMessages = Array.from({ length: 150 }, (_, i) => ({
      type: 'agent_activity',
      agent: 'vision',
      message: `Finding ${i}`,
      timestamp: Date.now()
    }));

    (useWebSocket as jest.Mock).mockReturnValue({
      messages: mockMessages,
      connected: true
    });

    render(<RunningLog />);

    const logEntries = screen.getAllByRole('log-entry');
    expect(logEntries.length).toBe(100);
    expect(logEntries[0]).toHaveTextContent('Finding 50'); // First displayed entry
    expect(logEntries[99]).toHaveTextContent('Finding 149'); // Last entry
  });

  test('agent emoji colors match personalities', () => {
    const mockMessages = [
      { type: 'agent_activity', agent: 'vision', message: 'Scanning...', timestamp: Date.now() }
    ];

    (useWebSocket as jest.Mock).mockReturnValue({
      messages: mockMessages,
      connected: true
    });

    render(<RunningLog />);

    const visionEmoji = screen.getByText('👁️');
    expect(visionEmoji).toHaveClass('text-vision-color');
  });
});
```

**Test: GreenFlagCelebration trigger condition**
```typescript
// frontend/src/__tests__/GreenFlagCelebration.test.ts
import { render } from '@testing-library/react';
import GreenFlagCelebration from '@/components/audit/GreenFlagCelebration';

describe('GreenFlagCelebration', () => {
  test('triggers when trust_score >= 80', () => {
    render(<GreenFlagCelebration verdict={{ trust_score: 85 }} />);
    expect(screen.getByRole('celebration-banner')).toBeInTheDocument();
  });

  test('does not trigger when trust_score < 80', () => {
    render(<GreenFlagCelebration verdict={{ trust_score: 75 }} />);
    expect(screen.queryByRole('celebration-banner')).not.toBeInTheDocument();
  });

  test('displays green flags found', () => {
    const verdict = {
      trust_score: 90,
      green_flags: ['Valid SSL certificate', 'Contact info visible', 'HTTPS enforced']
    };
    render(<GreenFlagCelebration verdict={verdict} />);

    expect(screen.getByText('Valid SSL certificate')).toBeInTheDocument();
    expect(screen.getByText('Contact info visible')).toBeInTheDocument();
    expect(screen.getByText('HTTPS enforced')).toBeInTheDocument();
  });
});
```

### Integration Tests

**Test: WebSocket communication and event sequencing**
```python
# backend/tests/integration/test_event_sequencing.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.asyncio
async def test_websocket_event_sequence_numbers():
    """Test that events arrive with sequence numbers and can be reordered."""
    client = TestClient(app)

    with client.websocket_connect("/ws/audit") as websocket:
        # Send audit request
        websocket.send_json({"url": "http://test.com"})

        # Collect events
        events = []
        timeout = 30
        start = time.time()

        while time.time() - start < timeout:
            event = websocket.receive_json()
            if event.get('type') == 'agent_progress':
                events.append(event)
            if event.get('type') in ['audit_complete', 'audit_error']:
                break

        # Verify all events have sequence numbers
        for event in events:
            assert 'sequence' in event
            assert isinstance(event['sequence'], int)

        # Verify sequence numbers are monotonically increasing
        sequences = [e['sequence'] for e in events]
        assert sequences == sorted(sequences)

        # Verify no gaps in sequence numbers
        for i in range(1, len(sequences)):
            assert sequences[i] - sequences[i-1] <= 1
```

**Test: Agent coordination and task flexing**
```python
@pytest.mark.asyncio
async def test_agent_task_flexing_messages():
    """Test that agents send "flexing" messages on task completion."""
    client = TestClient(app)

    with client.websocket_connect("/ws/audit") as websocket:
        websocket.send_json({"url": "http://test.com"})

        visions_found = 0
        security_checks = 0

        timeout = 30
        start = time.time()

        while time.time() - start < timeout:
            event = websocket.receive_json()

            # Check for agent flexing messages
            if event.get('type') == 'agent_progress':
                agent = event.get('agent')
                message = event.get('message', '')

                if agent == 'vision' and 'findings detected' in message.lower():
                    visions_found += 1
                elif agent == 'security' and 'completed' in message.lower():
                    security_checks += 1

            if event.get('type') == 'audit_complete':
                break

        # At least one agent should have flexed about findings
        assert visions_found > 0 or security_checks > 0
```

**Test: Event sequencing handles out-of-order events**
```typescript
// frontend/src/__tests__/useEventSequencer.test.ts
import { renderHook, act } from '@testing-library/react-hooks';
import { useEventSequencer } from '@/hooks/useEventSequencer';

describe('useEventSequencer', () => {
  test('reorders out-of-order events by sequence number', async () => {
    const { result } = renderHook(() => useEventSequencer());

    // Simulate out-of-order events
    const outOfOrderEvents = [
      { sequence: 3, message: 'Event 3' },
      { sequence: 1, message: 'Event 1' },
      { sequence: 2, message: 'Event 2' }
    ];

    for (const event of outOfOrderEvents) {
      act(() => {
        result.current.addEvent(event);
      });
    }

    const events = result.current.getOrderedEvents();
    expect(events[0].message).toBe('Event 1');
    expect(events[1].message).toBe('Event 2');
    expect(events[2].message).toBe('Event 3');
  });

  test('buffers events until gap is filled', () => {
    const { result } = renderHook(() => useEventSequencer());

    // Add event with sequence 3 (missing 1 and 2)
    act(() => {
      result.current.addEvent({ sequence: 3, message: 'Event 3' });
    });

    // Should buffered, no ready events
    expect(result.current.getOrderedEvents()).toEqual([]);

    // Add sequence 2
    act(() => {
      result.current.addEvent({ sequence: 2, message: 'Event 2' });
    });

    // Still buffered (missing 1)
    expect(result.current.getOrderedEvents()).toEqual([]);

    // Add sequence 1
    act(() => {
      result.current.addEvent({ sequence: 1, message: 'Event 1' });
    });

    // Now all ready in order
    const events = result.current.getOrderedEvents();
    expect(events.length).toBe(3);
    expect(events[0].message).toBe('Event 1');
    expect(events[1].message).toBe('Event 2');
    expect(events[2].message).toBe('Event 3');
  });
});
```

### Performance Tests

**Test: WebSocket event throttling under high load**
```typescript
// frontend/src/__tests__/performance/eventThrottling.test.ts
import { eventThrottler } from '@/utils/eventThrottler';

describe('eventThrottler performance', () => {
  test('limits events to max 5 per second', async () => {
    const emitted: string[] = [];
    const emitter = (event: string) => emitted.push(event);

    const throttled = eventThrottler(emitter, 5); // 5 events/sec max

    // Send 100 events rapidly
    const startTime = performance.now();
    for (let i = 0; i < 100; i++) {
      throttled(`Event ${i}`);
    }
    const duration = performance.now() - startTime;

    // Should take at least 19 seconds (100 / 5 - 1)
    // First event is immediate, then 19 batches of 5
    await new Promise(resolve => setTimeout(resolve, 20000));

    expect(emitted.length).toBeGreaterThan(90); // Should have emitted most events
    expect(emitted.length).toBeLessThanOrEqual(100); // Can't exceed input
  });

  test('dropped events are counted and logged', () => {
    const emitted: string[] = [];
    const emitter = (event: string) => emitted.push(event);
    const logger = { warn: jest.fn() };

    const throttled = eventThrottler(emitter, 5, logger);

    // Send 10 events immediately (should buffer 5)
    for (let i = 0; i < 10; i++) {
      throttled(`Event ${i}`);
    }

    // Should have warned about dropping events
    expect(logger.warn).toHaveBeenCalledWith(
      expect.stringContaining('Event throttling: dropping')
    );
  });
});
```

**Test: Memory leak prevention in Running Log**
```typescript
// frontend/src/__tests__/performance/memoryLeaks.test.ts
import { render, cleanup } from '@testing-library/react';
import RunningLog from '@/components/audit/RunningLog';

describe('Memory leak prevention', () => {
  test('RunningLog cleans up old entries', () => {
    // Create a large number of log entries
    const messages = Array.from({ length: 500 }, (_, i) => ({
      type: 'agent_activity',
      agent: 'vision',
      message: `Finding ${i}`,
      timestamp: Date.now()
    }));

    const { unmount, rerender } = render(
      <RunningLog messages={messages} />
    );

    // Check that only 100 entries are rendered
    const entries = screen.getAllByRole('log-entry');
    expect(entries.length).toBe(100);

    // Add more entries
    const moreMessages = [...messages, ...Array.from({ length: 200 }, (_, i) => ({
      type: 'agent_activity',
      agent: 'security',
      message: `Finding ${500 + i}`,
      timestamp: Date.now()
    }))];

    rerender(<RunningLog messages={moreMessages} />);

    // Still only 100 entries (sliding window)
    const entriesAfter = screen.getAllByRole('log-entry');
    expect(entriesAfter.length).toBe(100);

    unmount();
  });

  test('ScreenshotCarousel unloads off-screen images', async () => {
    const screenshots = Array.from({ length: 20 }, (_, i) => ({
      url: `data:image/png;base64,${i}`,
      width: 1920,
      height: 1080,
      findings: []
    }));

    const { unmount } = render(<ScreenshotCarousel screenshots={screenshots} />);

    // Only current slide + 1 ahead + 1 behind should be loaded
    const loadedImages = screen.getAllByRole('img');
    expect(loadedImages.length).toBeLessThanOrEqual(3);

    unmount();
  });
});
```

**Test: WebSocket handles 50+ events/sec gracefully**
```python
@pytest.mark.asyncio
async def test_websocket_high_event_load():
    """Test that WebSocket queue handles high event rate without drops."""
    client = TestClient(app)

    with client.websocket_connect("/ws/audit") as websocket:
        websocket.send_json({"url": "http://test.com"})

        events_received = 0
        dropped_events = 0
        start_time = time.time()

        while time.time() - start_time < 10:  # 10 second test
            try:
                event = websocket.receive_json(timeout=0.2)
                events_received += 1
            except TimeoutExpired:
                # Track potential drops (timeouts)
                dropped_events += 1

        # Should have received significant number of events
        # (even when throttled, should get some progress updates)
        assert events_received > 20

        # Event drops should be minimal
        drop_rate = dropped_events / max(1, events_received)
        assert drop_rate < 0.1  # Less than 10% drop rate
```

---

## Success Criteria (When Phase 11 Is Done)

### Must Have
1. ✅ All agents have distinct personalities and emojis
2. ✅ Screenshot carousel with navigation
3. ✅ Highlight overlays align with findings
4. ✅ Running log with task celebration messages
5. ✅ Green flag celebration for high trust scores

### Should Have
1. ✅ Finding "flexing" messages
2. ✅ Event buffering/sequencing
3. ✅ Real-time pattern notifications
4. ✅ Zoom/pan on screenshots

### Nice to Have
1. ✅ Comparision views (before/after)
2. ✅ Confetti animation for completions
3. ✅ Interesting highlights during waits
4. ✅ Agent chat-style interface

---

## Requirements Covered

| Requirement | Status | Notes |
|-------------|--------|-------|
| SHOWCASE-01 | 📝 Covered | Psychology-driven flow, celebrations |
| SHOWCASE-02 | 📝 Covered | Real-time Agent Theater, events |
| SHOWCASE-03 | 📝 Covered | Screenshot Carousel + highlights |
| SHOWCASE-04 | 📝 Covered | Running Log + flexing |

---

*Plan created: 2026-02-23*
*All v2.0 phases planned!*
