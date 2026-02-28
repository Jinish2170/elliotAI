# Phase 11: Agent Theater & Content Showcase - Research

**Date:** 2026-02-28
**Milestone:** v2.0 Masterpiece Features
**Researcher:** Claude (Hive-Mind Parallel Research)
**Discovery Level:** Level 2 - Standard Research

---

## Research Objectives

Conduct parallel research on UI patterns and frameworks for implementing an engaging real-time visual feedback system with agent personalities, progressive disclosure, and celebration patterns for Phase 11.

### Research Topics

1. **Real-Time React Patterns** - Component patterns for handling high-frequency WebSocket events
2. **Progressive Disclosure UI** - Patterns for gradual information reveal
3. **Event Sequencing & Buffering** - Patterns for handling out-of-order WebSocket events
4. **Agent Personality Design** - Frameworks for character-based agent communication
5. **Carousel & Overlay Systems** - Screenshot navigation with finding highlights
6. **Celebration & Animation** - Positive reinforcement and task completion patterns

---

## Parallel Research Results (Hive-Mind Consensus)

### Research Topic 1: Real-Time React Component Patterns

**Research Lead:** Researcher-01 (React & Event Streaming)
**Consensus:** ✓ APPROVED for implementation

**Findings:**

1. **Debouncing vs Throttling Patterns**
   - **Debouncing**: Useful for user input (search, form fields) - wait Xms after last event
   - **Throttling**: Better for high-frequency events (WebSocket streams) - max once every Xms
   - **Recommendation**: Use throttling for WebSocket event processing (~5 events/sec max, consistent with Phase 6)

2. **React Pattern Options:**
   - `useReducer` with action batching: Good for complex state, but can be verbose
   - Zustand middleware actions: Existing pattern in codebase (useAuditStore) - OPTIMAL CHOICE
   - React Query/WebSocket hooks: Not needed for current architecture

3. **High-Performance Event Handling:**
   - Use `requestAnimationFrame` for visual updates (prevents unnecessary re-renders)
   - Batch state updates using `useEffect` with dependency arrays
   - Limit log entries (windowing pattern) to prevent memory leaks

**Existing Codebase Patterns Discovered:**
- `useAuditStream` handles WebSocket connection
- `useAuditStore` (Zustand) manages state with `handleEvent` pattern
- Phase 6 used token-bucket rate limiting (5 events/sec)

**Implementation Recommendation:**
- Extend existing `useAuditStore` with new event handlers for agent activity
- Add throttling middleware to prevent event storms
- Use windowing pattern for log entries (max 100, sliding window)

---

### Research Topic 2: Progressive Disclosure UI Patterns

**Research Lead:** Researcher-02 (UX & Information Architecture)
**Consensus:** ✓ APPROVED for implementation

**Findings:**

1. **Progressive Disclosure Principles:**
   - **Initial State**: Show high-level summary (agent names, status)
   - **Progressive Reveal**: Show details as events arrive (findings, messages)
   - **Full Context**: Show detailed analysis after completion
   - **Key Principle**: Always something happening (every 5-10 seconds)

2. **Pattern Options:**
   - **Accordion/Expandable Rows**: Good for findings (already exists in EvidencePanel)
   - **Slide-in Notifications**: Good for real-time alerts (use existing framer-motion)
   - **Staggered Animations**: Good for sequential reveal (AnimatePresence with delay)

3. **Pacing Patterns:**
   - **Micro-interactions**: Small animations during idle periods (pulse effects, loading spinners)
   - **Contextual Education**: "Did You Know?" cards between phases (already exists in NarrativeFeed)
   - **Agent "Thinking" States**: Show agent working state with animated indicators

**Existing Codebase Patterns Discovered:**
- NarrativeFeed has "Did You Know?" cards between phases
- AgentCard has pulsing glow for active agents
- EvidencePanel uses expandable finding rows

**Implementation Recommendation:**
- Extend NarrativeFeed with agent-specific activity messages
- Add "flexing" messages when tasks complete ("Vision found 3 dark patterns!")
- Add idle state animations using framer-motion
- Use existing AnimatePresence with stagger delays for progressive reveal

---

### Research Topic 3: Event Sequencing & Buffering

**Research Lead:** Researcher-03 (Real-Time Systems)
**Consensus:** ✓ APPROVED for implementation

**Findings:**

1. **WebSocket Event Ordering Problem:**
   - Events may arrive out of order (network latency, parallel processing)
   - Sequence numbers needed for proper ordering
   - Buffer required to hold out-of-order events

2. **Pattern Options:**
   - **Simple Counter**: Increment sequence number on backend, sort on frontend
   - **Timestamp-based**: Use server timestamps, sort chronologically
   - **Vector Clocks**: Overkill for single-server architecture

3. **Implementation Pattern (Simple Counter - RECOMMENDED):**
   ```typescript
   interface SequencedEvent {
     sequence: number;  // Monotonically increasing
     type: string;
     data: any;
   }

   class EventBuffer {
     private buffer: Map<number, SequencedEvent> = new Map();
     private nextSequence: number = 0;

     addEvent(event: SequencedEvent): SequencedEvent[] | null {
       this.buffer.set(event.sequence, event);
       return this.flushReady();
     }

     flushReady(): SequencedEvent[] {
       const ready: SequencedEvent[] = [];
       while (this.buffer.has(this.nextSequence)) {
         ready.push(this.buffer.get(this.nextSequence)!);
         this.buffer.delete(this.nextSequence);
         this.nextSequence++;
       }
       return ready;
     }
   }
   ```

**Existing Codebase Patterns Discovered:**
- Phase 6 Vision Agent uses `##PROGRESS:` stdout markers for progress tracking
- Existing events don't have sequence numbers (unordered)
- NarrativeFeed uses timestamp-based ordering

**Implementation Recommendation:**
- Add `sequence` field to all WebSocket events (backend increment counter)
- Create `useEventSequencer` hook with buffering pattern
- Update `handleEvent` in useAuditStore to use sequencer
- Fallback to timestamp ordering for backward compatibility

---

### Research Topic 4: Agent Personality Design

**Research Lead:** Researcher-04 (UX Design & Psychology)
**Consensus:** ✓ APPROVED for implementation

**Findings:**

1. **Agent Personality Framework:**
   - **Visual Identity**: Emoji, color theme, icon style
   - **Voice/Tone**: Working messages, completion messages, celebration messages
   - **Character Traits**: Scout (stealthy, cautious), Vision (analytical, detail-oriented), Security (protective, thorough), Graph (investigative, connecting), Judge (authoritative, balanced)

2. **Message Pattern Options:**
   - **Static Messages**: Pre-defined strings (simple, maintainable) - RECOMMENDED
   - **Template-based**: String interpolation with context (e.g., "{count} dark patterns found")
   - **AI-generated**: LLM-generated messages (overkill, unpredictable)

3. **Celebration Pattern:**
   - **Visual**: Confetti animation (paper.js or canvas-confetti)
   - **Text**: "Flex" messages (exaggerated accomplishment)
   - **Audio**: Not recommended (user preferences vary)

**Existing Codebase Patterns Discovered:**
- PHASE_META has basic agent metadata (label, icon, description)
- AgentCard uses emoji icons for each phase
- NarrativeFeed has completion card

**Implementation Recommendation:**
- Create `frontend/src/config/agent_personalities.ts` with:
  - AgentPersona interface (emoji, name, personality, catchphrases)
  - AGENT_PERSONALITIES constant with 5 agent personalities
  - Template strings with parameters (e.g., "{count}", "{duration}")
- Use canvas-confetti for celebrations (lightweight, widely used)
- Add "flex" messages to NarrativeFeed on task completion

---

### Research Topic 5: Screenshot Carousel & Overlay Systems

**Research Lead:** Researcher-05 (UI Components & Graphics)
**Consensus:** ✓ APPROVED for implementation

**Findings:**

1. **Carousel Pattern Options:**
   - **Custom Component**: Full control, no dependencies - RECOMMENDED
   - **Swiper.js**: Feature-rich but adds ~80KB
   - **React Slick**: Deprecated, not recommended

2. **Overlay Pattern for Findings:**
   - **SVG Overlay**: Vector graphics, precise positioning - RECOMMENDED
   - **CSS Absolute**: Simple but less precise
   - **Canvas**: Performance overhead for simple rectangles

3. **Coordinate System:**
   - Backend: Finding bbox is 0-100 scale (percentage-based)
   - Frontend: Convert to pixels based on actual image dimensions
   - Formula: `pixel = (percentage / 100) * dimension`

4. **Zoom/Pan Pattern:**
   - **Lightbox with zoom**: Expand to modal, scroll/pinch to zoom
   - **Inline zoom**: Expand in-place, less intrusive - RECOMMENDED
   - **Deep zoom.js**: Overkill for current use case

**Existing Codebase Patterns Discovered:**
- EvidencePanel has ScreenshotGallery with lightbox modal
- Screenshot type has label, index, data (base64) properties
- Findings have category, pattern_type, severity, confidence

**Implementation Recommendation:**
- Create `frontend/src/components/audit/ScreenshotCarousel.tsx` with:
  - Carousel navigation (prev/next buttons, keyboard shortcuts, swipe support)
  - SVG overlays for finding highlights (precise bbox positioning)
  - Inline zoom with pan (transform: scale/translate)
  - Toggle findings on/off
  - Thumbnail navigation strip
- Extend Finding type with `bbox: [number, number, number, number]` (x, y, width, height percentages)
- Add highlight color mapping (red=critical, orange=high, amber=medium, green=low)

---

### Research Topic 6: Celebration & Animation Patterns

**Research Lead:** Researcher-06 (Animations & UX)
**Consensus:** ✓ APPROVED for implementation

**Findings:**

1. **Celebration Pattern Options:**
   - **canvas-confetti**: Lightweight (40KB), zero dependencies, easy API - RECOMMENDED
   - **React-confetti**: React wrapper, but adds React overhead
   - **Custom Canvas**: More control but reinventing the wheel

2. **Green Flag Celebration Pattern:**
   - **Trigger**: `trust_score >= 80` (positive audit result)
   - **Visual**: Banner animation, checkmark icons, green color scheme
   - **Content**: List of green flags (valid SSL, HTTPS enforced, etc.)

3. **Task Completion Pattern:**
   - **Individual**: Small celebration on each finding/phase completion
   - **Milestone**: Medium celebration on phase complete
   - **Final Celebration**: Large celebration on audit complete

4. **Framer Motion Pattern (Existing in codebase):**
   - `AnimatePresence`: Exit animations
   - `motion.div`: Enter/move animations
   - `whileHover`, `whileTap`: Interaction states

**Existing Codebase Patterns Discovered:**
- NarrativeFeed has CompletionCard with checkmark emoji
- AgentCard has completions with checkmark icon
- Framer Motion used extensively

**Implementation Recommendation:**
- Install canvas-confetti: `npm install canvas-confetti`
- Create `frontend/src/components/audit/GreenFlagCelebration.tsx` with:
  - Banner animation (slide-in, expand)
  - Green flags list with checkmark icons
  - Trigger condition: `trust_score >= 80`
- Add confetti to existing CompletionCard in NarrativeFeed
- Add micro-celebrations to task completion events (small particle burst)

---

## Research Summary & Implementation Plan

### Dependencies Required

**npm packages:**
- `canvas-confetti` - Confetti animations (~40KB)

**Backend modifications:**
- Add `sequence` field to all WebSocket events (monotonic counter)
- Add `bbox` field to Finding events (coordinate overlay support)
- Add `green_flags` field to audit result

**Frontend files to create:**
- `frontend/src/config/agent_personalities.ts` - Agent personality configuration
- `frontend/src/hooks/useEventSequencer.ts` - Event buffering hook
- `frontend/src/components/audit/ScreenshotCarousel.tsx` - New carousel component
- `frontend/src/components/audit/GreenFlagCelebration.tsx` - New celebration component
- `frontend/src/components/audit/RunningLog.tsx` - Extended log component (extend ForensicLog)

**Frontend files to modify:**
- `frontend/src/lib/types.ts` - Add bbox to Finding, add GreenFlag type
- `frontend/src/lib/store.ts` - Add event sequencer integration, new event handlers
- `frontend/src/components/audit/NarrativeFeed.tsx` - Add celebration animations, personality messages

### Architecture Overview

```
WebSocket Events
    ↓ (with sequence numbers)
useEventSequencer (buffer/reorder)
    ↓
useAuditStore.handleEvent()
    ↓
State updates (Zustand)
    ↓
Components (AgentCard, NarrativeFeed, ScreenshotCarousel)
    ↓
Animated UI (Framer Motion + canvas-confetti)
```

### Plan Split Strategy

Based on research findings and GSD methodology (2-3 tasks per plan, ~50% context):

**Plan 11-01: Agent Personality System & Event Sequencing** (Wave 1)
- Task 1: Create agent personalities configuration
- Task 2: Create event sequencer hook with buffering
- Task 3: Integrate sequencer into existing store and components

**Plan 11-02: Screenshot Carousel & Highlight Overlays** (Wave 2)
- Task 1: Extend types with bbox and finding coordinates
- Task 2: Create ScreenshotCarousel component with overlays
- Task 3: Add zoom/pan and navigation features

**Plan 11-03: Running Log & Celebration System** (Wave 2)
- Task 1: Extend ForensicLog into RunningLog with windowing
- Task 2: Create GreenFlagCelebration component
- Task 3: Integrate canvas-confetti and celebrations across components

**Wave Structure:**
- Wave 1: Plan 11-01 (autonomous, parallel execution ready)
- Wave 2: Plans 11-02, 11-03 (depends on 11-01 for sequencing/personalities)

---

## Research Conclusion

All research topics completed successfully. Implementation ready to proceed with:
1. Event sequencing for reliable WebSocket message ordering
2. Agent personalities for engaging character-based communication
3. Screenshot carousel with precision finding overlays
4. Celebration system with canvas-confetti animations
5. Progressive disclosure patterns for paced information reveal
6. Real-time event throttling for performance

**Consensus Reached:** ✓ unanimously approved for implementation

**Next Step:** Create PLAN.md files based on research findings.

---

*Research completed: 2026-02-28*
*Hive-mind consensus achieved on all 6 research topics*
