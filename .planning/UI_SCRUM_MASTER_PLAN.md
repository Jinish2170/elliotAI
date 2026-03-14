# SCRUM MASTER TACTICAL PLAN: VERITAS UI IMPLEMENTATION

## 0. EXECUTIVE SUMMARY & CRITICAL GAP ANALYSIS
Before executing the `UI_ARCHITECTURE.md` blueprint, we must identify and preemptively resolve structural conflicts between React's rendering engine, high-frequency WebSockets, and our rigid UI constraints.

### 🔴 Identified Implementation Conflicts & Mitigations
| Identified Conflict | Why it will fail if ignored | The Engineered Mitigation |
| :--- | :--- | :--- |
| **DOM Thrashing (Render Collapse)** | WebSockets firing 50+ events/sec will trigger React re-renders across the entire app, locking the main thread and freezing the UI. | **Selective Zustand Slices (`useStore(s => s.slice, shallow)`)** + **Data Virtualization (`react-window`)**. Components ONLY subscribe to their specific data shards. |
| **CSS Specificity Wars** | Existing Tailwind/UI libraries usually force `border-radius`, generic sans-serif fonts, and consumer padding. | Establish a global `.veritas-terminal` CSS wrapper that aggressively resets `border-radius: 0px !important`, enforces `box-sizing`, and locks the physical layout using `CSS Grid` (no flex wrapping). |
| **Mobile / Responsive Collapse** | A Bloomberg terminal physically cannot exist on an iPhone screen. Flexbox wrapping will destroy the Gestalt grouping psychology. | **Hard Viewport Locks.** We declare `min-width: 1280px`. If viewed on mobile, display an intercept overlay: *"VERITAS requires an operator terminal. Screen too small."* |
| **Ghost Data Cascades** | `store.ts` arrays starting empty (`[]`) will cause `undefined` mapping errors if rendered before the backend populates them. | **Strict Nil-Tiers.** `?` optional chaining everywhere + `<GhostPanel>` skeleton components that statically render `[ AWAITING STREAM... ]` before data arrival. |

---

## 1. SPRINT 1: THE FOUNDATION & THE VOID (Infrastructure)
**Goal:** Establish the unbreakable structural grid, CSS tokens, and defense mechanisms. No real data yet, just wireframes and failsafes.

*   **Story 1.1:** Inject CSS Variables & Typography. Install `JetBrains Mono`. Define `#00FF41` (Terminal Green) and `#050505` (Void Base) root tokens.
*   **Story 1.2:** Build the rigid 4-Zone `CSS Grid` Layout. `100vw/100vh` locked. `overflow: hidden` on the window.
*   **Story 1.3:** Build the `TerminalPanel` master component wrapper. This wrapper must include:
    *   Hard `1px #333` borders, 0px radius.
    *   Intrinsic `<React.ErrorBoundary>` wrapper.
    *   Terminal-style title bar (e.g., `[SYS.LOG]`).
*   **Definition of Done:** A purely structural, dark screen with sharp geometric boxes that perfectly match the 4-zone theory. Resizing the window does NOT break the boxes; it clips them.

---

## 2. SPRINT 2: COGNITIVE ANCHORS (Zones 1 & 2)
**Goal:** Build the primary focal points where the human eye naturally lands (F-Pattern/Z-Pattern). This gives the system its "soul."

*   **Story 2.1:** Global Ticker (Zone 1). Implement scrolling text bar for Target URL and Live Connection Status (Red/Green LED pulse).
*   **Story 2.2:** The Trust Score Component (Zone 2). Build the typography logic that calculates its hex color interpolating from Green to Red based on number (0-100).
*   **Story 2.3:** The Verdict Summary (Zone 2). Connect `dualVerdict` from the Zustand store. Implement the "Glitch Reveal" CSS animation when the verdict arrives from the backend.
*   **Definition of Done:** The UI receives a fake websocket payload and instantly flashes a glowing Trust Score and verdict, drawing the eye directly to the center-top screen.

---

## 3. SPRINT 3: THE INVESTIGATIVE MATRIX (Zone 3 Dense Modules)
**Goal:** Implement the complex data visualizers. This requires charting libraries and heavy mapping.

*   **Story 3.1:** CVSS Radar Chart (Panel 3A). Map `cvssMetrics` to a Recharts/D3 radar polygon.
*   **Story 3.2:** MITRE & Darknet Matrix (Panel 3B & 3C). Build dense, spreadsheet-like grids. Implement Hover-Tooltip logic for `cveEntries` descriptions.
*   **Story 3.3:** The Failsafe Fallbacks. Write the logic that displays `[NOMINAL - NO VECTORS DETECTED]` if `cveEntries` is `[]` when the audit completes.
*   **Definition of Done:** Matrices correctly map complex multi-tier arrays without breaking their boundaries. Data is easy to read without scrolling.

---

## 4. SPRINT 4: THE PERIPHERAL PULSES (Zone 4 Rails)
**Goal:** Hook up the high-frequency streaming data to the left and right peripheral rails. Memory optimization is critical here.

*   **Story 4.1:** Left Rail `LogEntry` Stream. Implement `react-window` or virtualized list. Bind specifically to `useStore(state => state.logs)`. Ensure it auto-scrolls to the bottom smoothly like a real terminal.
*   **Story 4.2:** Right Rail Scout Imagery. Create the image stack component that renders base64/URL screenshots as they stream in, with a tiny metadata caption (`timestamp`, `url`).
*   **Story 4.3:** Performance Profiling. Run React Profiler. Verify that a flood of 100 logs does NOT cause the Center Verdict Matrix to re-render.
*   **Definition of Done:** The entire terminal looks alive. The periphery is constantly moving with hacking data, but the core layout remains unshaken, responsive, and uses <200mb RAM.