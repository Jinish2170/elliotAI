# Domain Pitfalls: VERITAS v2.0 Masterpiece Features

**Domain:** Forensic Web Auditing Platform Enhancement
**Researched:** 2026-02-23

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Computer Vision Image Alignment

**What goes wrong:** SSIM comparison and difference masks produce incorrect results when screenshots have different resolutions, crop areas, or browser renderings.

**Why it happens:** Playwright screenshots vary by viewport size, responsive layouts render differently.

**Consequences:**
- False positive dark pattern detections
- False negatives (actual manipulation missed)
- Incorrect highlight regions on screenshot carousel

**Prevention:**
1. Fixed viewport size (1920x1080)
2. Image resize normalization using OpenCV
3. Template matching for alignment with findHomography()
4. Focus CV on known element areas (price displays, timer regions)

**Detection:**
- SSIM score unexpectedly low (<0.7) for identical pages
- Difference masks show changes in header/footer (should be static)
- Timer fraud detection triggers on pages without timers

### Pitfall 2: WebSocket Event Flooding

**What goes wrong:** Broadcasting too many WebSocket events causes browser crashes, memory leaks, Framer Motion lag.

**Why it happens:** 5-pass Vision Agent emits events for each finding (could be 50+ per pass).

**Consequences:**
- Frontend becomes unresponsive (UI freezes)
- Framer Motion queues thousands of animations
- WebSocket connections drop due to message size limits
- Memory leaks in React state

**Prevention:**
1. Event throttling (max 5 per second)
2. Batching findings (send as one event per pass)
3. Progress summaries instead of individual findings
4. Frontend debouncing with useEffect cleanup
5. Queue management with asyncio.sleep(0.2) between emits

### Pitfall 3: API Rate Limiting (OSINT Sources)

**What goes wrong:** VirusTotal, PhishTank APIs block requests after exceeding rate limits.

**Why it happens:** 15+ OSINT sources with different limits (VirusTotal: 4 req/min, PhishTank: 1 req/sec).

**Consequences:**
- OSINT reports contain rate-limited placeholders
- Threat scores incorrectly calculated
- Knowledge graph has missing OSINT source nodes
- API keys get suspended for abuse

**Prevention:**
1. Document rate limits in config file
2. Per-source request queues with asyncio.Queue
3. Response caching for 24-72 hours
4. Tiered fallback (use cache or skip with warning)
5. Staggered execution (start largest cooldowns first)

## Moderate Pitfalls

### Pitfall 4: VLM Prompt Engineering Iteration

**What goes wrong:** VLM returns low-quality dark pattern detections with initial prompts.

**Why it happens:** Generic prompts dont detect specific dark patterns (false urgency, sneaking, forced continuity).

**Prevention:**
1. Create 50 labeled test pages
2. A/B test prompt variations, measure F1 score
3. Use few-shot examples in prompts
4. Temperature tuning (0.3-0.5)
5. Prompt versioning with accuracy metrics

### Pitfall 5: LangGraph State Explosion

**What goes wrong:** LangGraph state objects grow unbounded with findings and screenshots.

**Why it happens:** Each agent adds findings to state without cleanup.

**Prevention:**
1. Keep only references (file paths, URLs) in state
2. Delete intermediate screenshots after each pass
3. Lazy loading from disk
4. State checkpointing and cleanup
5. Database persistence for large data

### Pitfall 6: Dual-Tier Verdict Inconsistency

**What goes wrong:** Technical and non-technical verdicts disagree.

**Prevention:**
1. Unified score source for both tiers
2. Cross-validation in pre-commit tests
3. Template mapping based on score thresholds
4. Auditability logs

## Minor Pitfalls

### Pitfall 7: OpenCV Coordinate System Mismatch

**What goes wrong:** OpenCV pixel coords dont align with CSS percentages for frontend highlights.

**Prevention:**
1. Store original screenshot dimensions
2. Convert to percentages before sending to frontend

### Pitfall 8: SQLite Lock Contention

**What goes wrong:** Multiple concurrent audit writes cause database locked errors.

**Prevention:**
1. Single database write per agent
2. Increase SQLite busy_timeout
3. Connection pooling with SQLAlchemy

### Pitfall 9: Playwright Screenshot Capture Timeout

**What goes wrong:** Screenshots captured before page finishes loading dynamic content.

**Prevention:**
1. Wait for content: page.wait_for_selector(body)
2. Explicit delay: page.wait_for_timeout(2000)
3. Use wait_for_load_state=networkidle

## Phase-Specific Warnings

| Phase | Likely Pitfall | Mitigation |
|-------|---------------|------------|
| Phase 1 Vision | VLM prompt iteration longer than expected | Start with 3 passes not 5 |
| Phase 1 Vision | CV temporal false positives | Implement image alignment |
| Phase 1 Vision | Progress emitter floods frontend | Throttle from day 1 |
| Phase 2 OSINT | API rate limits | Document limits, implement caching |
| Phase 2 OSINT | Darknet monitoring legal concerns | Use threat feeds only |
| Phase 3 Judge | Dual-tier inconsistency | Unit tests for score alignment |
| Phase 3 Judge | Site type detection accuracy < 70% | Use LLM + heuristics fallback |
| Phase 4 Security | 25+ modules take too long | Tiered timeout approach |
| Phase 4 Security | CVSS scoring complexity | Start simplified, iterate later |
| Phase 5 Showcase | Carousel coordinates dont align | Store dimensions, use percentages |
| Phase 5 Showcase | Agent Theater animations lag | Test with 100+ events, batch early

## Sources

- OpenCV documentation (SSIM, image alignment, coordinate systems)
- FastAPI WebSocket best practices (event throttling, message limits)
- VirusTotal API documentation (rate limits, quotas)
- LangGraph state management patterns (state best practices, checkpointing)
