# VERITAS UI ARCHITECTURE: The "Expert Terminal"

## 1. VISION & PSYCHOLOGICAL NARRATIVE
The Veritas Terminal is designed for the **Expert Operator**. It abandons consumer-grade "whitespace-heavy" design in favor of a high-density, mission-critical interface inspired by Bloomberg Terminals, Aegis combat systems, and aerospace HUDs. 

### Psychological Principles Leveraged:
- **Gestalt Proximity & Enclosure:** Data grouped in strict, 1px bordered boxes creates subconscious associations, lowering cognitive processing time.
- **Preattentive Visual Processing:** The eye detects anomaly colors (Red/Amber) in ~200ms before conscious reading. 90% of the UI remains neutral (dark gray/dim green) so anomalies "scream" for attention.
- **Saccadic Masking (The Z-Pattern):** Critical global state (Verdict, Trust Score) sits top-left/center. Flowing data (logs) sits on the periphery to stimulate peripheral motion awareness without exhausting central focus.
- **Cognitive Consistency:** Monospace typography aligns decimal points and characters perfectly. The brain compares vertical shapes instead of reading numbers.

---

## 2. DESIGN SYSTEM & TOKENS

### 2.1 Color Palette
Strict, mathematically calculated contrast ratios for prolonged viewing without eye strain.
- **Base/Canvas:** `#050505` (Deep void, reduces screen glare).
- **Panel Backgrounds:** `#0A0A0A` to `#111111` (Elevated layers).
- **Grid/Borders:** `#222222` to `#333333` (Visible but non-distracting wireframing). Sharp `0px` border-radius.
- **Primary Text:** `#A0A0A0` (Muted gray-white to prevent retina burn).
- **Data Variables (Monospace):** `#00FF41` (Classic terminal phosphor green, signifies normal/active).
- **Warning/Anomaly:** `#FFB000` (High-visibility Amber).
- **Critical/Malicious:** `#FF003C` (Stark, alarming Red).
- **Dim/Inactive:** `#444444` (For pending inputs or ghosted UI).

### 2.2 Typography Hierarchy
- **Font Family (Prose/Labels):** `Inter` or `Geist` (clean, highly legible sans-serif).
- **Font Family (Data/Metrics/Logs):** `JetBrains Mono` or `Fira Code` (strict monospace).
- **Sizing Grid:** Base `12px` for dense data, `10px` for metadata labels, `24px` for headers, `72px` for Trust Score.

### 2.3 Spatial Grid & Padding
- **Base Unit:** `4px` (Enterprise standard).
- **Inner Panel Padding:** `8px` (Tight) or `12px` (Medium).
- **Inter-Panel Gaps:** `2px` (Creates a tight, monolithic structural feel like a spreadsheet).

---

## 3. LAYOUT TOPOLOGY (4-ZONE STRUCTURAL MAPPING)

The screen is a fixed viewport (`100vh`, `100vw`). No global scrolling. Only localized scrolling inside specific data panels (`overflow-y: auto`, invisible scrollbars).

### ZONE 1: TACTICAL HEADER (Height: 5%)
- **Placement:** Top-spanning horizontal bar.
- **Elements:** Target URL, Target IP, Active Phase, Total Time, Connected Agents (Pulse dots).
- **Psychology:** "Situational Awareness." Proves the system is alive and focused on the correct target.

### ZONE 2: THE VERDICT MATRIX (Height: 25%, Center)
- **Placement:** Center-Top.
- **Elements:**
  - **Trust Score:** Massive `72px` number. Color interpolates from Green to Red.
  - **Site Classification:** Direct, 3-word classification (e.g., "MALICIOUS PHISHING INFRASTRUCTURE").
  - **Dual-Verdict Summary:** Brief, high-contrast text. 
- **Psychology:** "Immediate Gratification." Answers the primary operator question within 0.5 seconds of glancing at the screen.

### ZONE 3: INVESTIGATIVE PANELS (Height: 70%, Center/Bottom)
- **Placement:** Grid below the Verdict Matrix.
- **Panel 3A (CVSS & Threat Vector):** Radar chart bridging `cvss_metrics`. 
- **Panel 3B (OSINT & Darknet Context):** `tor2web_anonymous_breach`, `cveEntries`, `marketplace_threats`.
- **Panel 3C (MITRE ATT&CK Array):** Grid of `mitre_technique_mapped` active states.
- **Psychology:** Spatial categorization. Analysts know exactly where to look for specific domain data.

### ZONE 4: PERIPHERAL PULSE (Left: 20% Width, Right: 25% Width)
- **Left Rail (System Pulse):** Raw agent logs (`log_entry`), phase tasks, and terminal output. Virtualized list to handle thousands of rows.
- **Right Rail (Evidence/Graph):** Rendered Scout screenshots and Knowledge Graph DOM structure.
- **Psychology:** "Glass Box Transparency." Seeing the raw matrix stream and screenshots provides trust in the AI's otherwise abstract calculations.

---

## 4. CORPORATE FAILSAFES & COMPENSATORY ARCHITECTURE (Frontend Resilience)

If the Python backend hallucinates, drops packets, or crashes mid-stream, the frontend MUST NOT white-screen or break layout. The UI must degrade gracefully.

### 4.1 Failsafe 1: Graceful Nil-State Rendering (The "Ghost UI")
- **Scenario:** Backend fails to send `cvss_metrics` due to an LLM extraction error.
- **Implementation:** UI panels are rendered *before* data arrives using a "Ghosting" technique (`color: #333`).
- **UI Fallback:** Instead of a blank box, the CVSS panel shows `"SEC_METRICS......... [AWAITING STREAM]"`. If audit completes without it, it resolves to `"SEC_METRICS......... [NULL_YIELD_FROM_AGENT]"`.
- **Psychology:** Communicates that the system *knows* the data should be there, but the analysis organically yielded nothing, preventing user anxiety over "broken software."

### 4.2 Failsafe 2: Error Boundaries per Panel
- **Scenario:** Malformed deep-nested JSON causes a React rendering crash in the MITRE component.
- **Implementation:** Every UI panel is wrapped in a discrete `<React.ErrorBoundary>`. 
- **UI Fallback:** If the MITRE panel crashes, it isolately renders a stark red box: `[MODULE_PANIC: MITRE_RENDER_ERR]` while the rest of the application continues functioning flawlessly.

### 4.3 Failsafe 3: Data Coercion & Schema Defense at the Store Level
- **Scenario:** Backend sends `cve_id: null` or an array instead of a string.
- **Implementation:** `store.ts` must coerce types strictly or gracefully discard malformed shards *before* they hit React components. Optional chaining (`?.`) throughout component renderers.
- **UI Fallback:** Defaults to `"UNKNOWN_CVE"` rather than crashing `String.prototype.match` or similar methods.

---

## 5. PERFORMANCE & RENDER OPTIMIZATION (Enterprise Grade)

Handling thousands of WebSocket events per minute requires military-grade React optimization.
1. **React.memo() heavily utilized:** Panels only re-render if their specific slice of the Zustand state changes.
2. **Data-Grid Virtualization (`react-window` / `react-virtuoso`):** The Left Rail logs will accumulate 5,000+ entries. Rendering all DOM nodes will freeze the browser. Virtualization ensures only the visible 30 logs exist in the DOM.
3. **Throttled WebSocket Merging:** Rapid-fire events (like `console_output` bursts) are bucketed and flushed to the state array every `100ms` via `useEventSequencer` to prevent continuous layout thrashing.
4. **CSS Hardware Acceleration:** Glitch effects, borders, and radars use `transform: translateZ(0)` and `opacity` transitions, keeping rendering off the main CPU thread so the JS thread is entirely dedicated to processing WS packets.