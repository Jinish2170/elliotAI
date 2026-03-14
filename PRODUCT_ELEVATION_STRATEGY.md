# Veritas Product Elevation Strategy

## 1. The Core Problem
The underlying AI engine (Veritas) is powerful, but the current implementation fails to deliver the promised "expert-level" product experience. 
1. **UI/UX Disconnect**: The recent shift to a "Bloomberg terminal" style made the UI feel like an "old broken box" rather than a sleek, modern, enterprise-grade AI security tool.
2. **Missing "Wow" Factor**: The removal of the "Theater" view destroyed the visibility of real-time AI processing. Users need to *see* the AI working (scraping, judging, analyzing) in an impressive way.
3. **Fragile Data Pipelines**: The WebSocket connection between the Python backend and Next.js frontend has mismatched data schemas. Findings get lost, metrics don't update linearly, and markdown isn't rendering correctly.

## 2. The Vision (Target State)
We need to pivot the design language from "Dense 90s Terminal" to "Modern Enterprise AI" (inspired by Linear, Vercel, and Palantir).

*   **Aesthetics**: Deep dark mode, subtle glassmorphism, glowing accents (cyan/emerald/purple based on the active agent), crisp typography (Inter/Geist + JetBrains Mono), and smooth layout animations.
*   **The Theater**: A central visual element that shows the active payload. When the Scout is navigating, show a live wireframe or progress pulse. When Vision is scanning, show the screenshot with scanning laser effects. When the Graph is building, show an interactive node network.
*   **Bulletproof Pipeline**: A unified, strictly typed event source. If the backend finds a critical vulnerability, it immediately flashes on screen, increments the counter, and updates the risk score smoothly.

## 3. Execution Phases

### Phase 1: Pipeline & Data Integrity (The Foundation)
*   **Audit the WebSocket Stream**: Map every event emitted by `audit_runner.py` to `store.ts`. Ensure 1:1 parity without dropping data.
*   **Real-time State Sync**: Remove batching delays that make the app feel broken. If an AI call is made, the UI should instantly reflect it.
*   **Robust Error Handling**: If an agent fails or takes too long, the UI should gracefully show a "degraded mode" or retry state, not just silently freeze or display "0".

### Phase 2: UI/UX Modernization (The Shell)
*   **Ditch the "Boxy" Layout**: Remove heavy borders and cramped panels. Use spacious flex layouts, subtle background gradients, and floating panels.
*   **Modern Component Library**: Upgrade the agent status indicators, finding rows, and metric tickers to use smooth Framer Motion transitions. No jarring jumps.
*   **Typography & Colors**: Re-tune the color palette to be more professional. Less harsh contrast, more layered subtle lighting.

### Phase 3: The "Live Theater" (The Experience)
*   **Interactive Centerpiece**: Build a dynamic central component that changes based on the active phase:
    *   *Init/Scout*: Target lock animation, IP resolving, map location.
    *   *Vision*: Display the captured screenshot overlaid with bounding boxes and bounding box animations.
    *   *Graph*: A dynamic force-directed graph showing the OSINT network expanding.
    *   *Judge*: A clean terminal revealing the final trusted narrative being typed out in real-time.

## 4. Next Steps
1. Review and approve this strategy.
2. Begin Phase 1 (Pipeline integrity) to ensure data is 100% accurate.
3. Begin Phase 2 (UI Modernization) focusing on the main Audit View layout.