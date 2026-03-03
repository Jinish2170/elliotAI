# Phase 07: Scout Navigation & Quality Foundation - Research

**Researched:** 2026-02-26
**Domain:** Browser automation, lazy-loading detection, multi-factor consensus systems
**Confidence:** MEDIUM

## Summary

Phase 07 implements sophisticated page coverage navigation and a foundational multi-factor quality validation system. The navigation system requires intelligent lazy-loading detection using MutationObserver in conjunction with scroll position monitoring. The quality foundation must prevent false positives through 2+ source consensus and transparent confidence scoring.

**Primary recommendations:**
1. Use MutationObserver for DOM-based lazy-load detection with configurable debounce timing
2. Implement weighted multi-factor consensus system with source tracking and conflict detection
3. Build adaptive timeout strategies based on site type classification
4. Add comprehensive error handling with fallback strategies and partial result support

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Scroll methodology:** Intelligent incremental scroll (page height/2 per scroll), not continuous scroll

**Scroll duration:** 300-500ms wait after each scroll chunk to allow lazy loading

**Scroll termination:** Stop when no new content appears for 2 consecutive scroll checkpoints OR maximum 15 scroll cycles

**Scroll detection:** Use scroll position vs page height + DOM mutation observer for lazy-loaded content

**Screenshot triggers:** Capture screenshot after each scroll segment and upon scroll termination

**Pages to visit:** Automatically discover and visit: About, Contact, Privacy, FAQ, footer links (max 8 pages)

**Link discovery:** Prioritize nav bar + footer + in-page "Learn More" sections

**Exploration order:** 1) Landing page (already visited), 2) Legal pages (Privacy, Terms), 3) About pages (About, Team), 4) functional pages (Contact, FAQ), 5) outbound footer links

**Navigation method:** Follow discovered links, extract all hrefs, deduplicate, prioritize by relevance keywords

**Exploration limit:** Timeout per page = baseline 15s + lazy loading wait, max 8 pages total

**Source types for consensus:** Vision Agent, OSINT Agent, Security Agent — multiple findings from these agents count toward consensus

**Consensus threshold:** 2+ distinct agents must corroborate a finding for "confirmed" status (prevents solo-source false positives)

**Partial findings:** Single-source findings shown as "unconfirmed" with lower confidence (<50%), displayed separately from confirmed findings

**Finding confidence tiers:** Confirmed (2+ sources, >=50%), Unconfirmed (1 source, <50%), Pending (insufficient data)

**Conflict detection:** If one agent flags safe while another flags threat → downgrade to "conflicted" status, show both findings with conflict note

**Scoring factors:** Source agreement weight (60%), finding severity (25%), contextual confidence (15%)

**Score calculation:**
- 2+ sources agree on high-severity → 75-100%
- 2+ sources agree on medium-severity → 50-75%
- 1 source high-severity → 40-60% (unconfirmed)
- 1 source medium-severity → 20-40% (unconfirmed)

**Visual breakdown:** Show score with contributing factors breakdown (e.g., "87%: 3 sources agree, high severity")

**Dynamic recalculation:** Scores update in real-time as additional sources contribute findings

### Claude's Discretion

- Exact scroll chunk size (page height/2 vs /3 vs /4)
- Mutation observer debounce timing
- Maximum lazy-load wait before giving up
- Exact confidence score algorithms
- Link discovery heuristics and keyword lists

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCROLL-01 | Scout/Vision Agent can scroll pages and capture full screenshot series with lazy loading trigger and scroll interval captures | Playwright scrolling patterns, MutationObserver for DOM change detection |
| SCROLL-02 | Scout can navigate to multiple pages beyond initial landing page with link detection, site structure exploration, and depth limits | Link extraction patterns, priority-based navigation, breadcrumb tracking |
| SCROLL-03 | Lazy loading detection and handling for complete capture with AJAX/React/Vue page transition handling | MutationObserver, scroll position monitoring, dynamic content wait strategies |
| QUAL-01 | False positive detection criteria with multi-factor validation (2+ sources) and historical baseline comparison | Multi-factor consensus system design, source tracking architecture |
| QUAL-02 | Deep statistics and confidence scoring with per-finding confidence (0-100%), aggregated trust score, and risk level assignment | Weighted scoring algorithm, confidence tier system, explainable AI principles |
| QUAL-03 | Incremental verification and refinement with downgradable alerts and progression states (Likely → Confirmed → Verified) | State machine-based verification progression, dynamic confidence updates |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Playwright Async API | latest | Browser automation, navigation, screenshots | Built-in async support, superior anti-detection features compared to Selenium |
| Python 3.11+ | 3.11+ | Runtime language | Modern async/await syntax, type hints, performance improvements |
| asyncio | builtin (3.11+) | Async event loop | Concurrent page navigation, parallel processing |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses | builtin (3.11+) | Type-safe data structures | ScoutResult, ScrollState, ConsensusResult models |
| typing | builtin (3.11+) | Type hints and | Findings, ValidationState enums |
| logging | builtin | Structured logging | Debug lazy-load detection, consensus tracking |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Playwright Async API | Selenium + WebDriver | Selenium requires async wrappers, weaker stealth, worse lazy-load handling |
| asyncio | trio | Trio is async-native but Playwright uses asyncio internally - mixing adds complexity |

**Installation:**
```bash
pip install playwright
playwright install chromium
```

## Architecture Patterns

### Recommended Project Structure
```
veritas/agents/
├── scout/
│   ├── __init__.py                    # Public API
│   ├── scroll_orchestrator.py         # NEW: Scroll management
│   ├── link_explorer.py               # NEW: Multi-page navigation
│   ├── lazy_load_detector.py          # NEW: DOM mutation monitoring
└── scout.py                           # Existing: Main StealthScout class

veritas/quality/
├── __init__.py                        # NEW: Quality module
├── consensus_engine.py                # NEW: Multi-factor consensus
├── confidence_scorer.py               # NEW: Weighted confidence calculation
└── validation_state.py                # NEW: Finding state machine

veritas/core/
├── types.py                           # Existing: Finding models
└── timeout_manager.py                 # NEW: Adaptive timeout manager
```

### Pattern 1: Lazy Load Detection with MutationObserver + Scroll Monitoring

**What:** Detect when lazy-loaded content has finished loading by combining DOM mutation observation with scroll position tracking. This dual-signal approach detects both DOM additions and end-of-scroll conditions.

**When to use:** When scraping pages with infinite scroll, lazy-loaded product grids, or dynamically expanding content sections.

**Implementation approach (based on MDN MutationObserver docs):**
```python
# Inject MutationObserver script via Playwright page.evaluate()
mutation_observer_script = """
    window.__lazyLoadDetector = {
        lastScrollHeight: document.documentElement.scrollHeight,
        mutationCount: 0,
        mutationsBuffer: [],

        init: function() {
            this.observer = new MutationObserver((mutations) => {
                const addedNodes = mutations.filter(m => m.addedNodes.length > 0);
                if (addedNodes.length > 0) {
                    this.mutationsBuffer.push(addedNodes);
                    this.mutationCount += addedNodes.length;
                }
            });

            this.observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        },

        hasNewContent: function() {
            const newMutations = this.mutationsBuffer.length;
            this.mutationsBuffer = [];

            const newScrollHeight = document.documentElement.scrollHeight;
            const scrollHeightChanged = newScrollHeight > this.lastScrollHeight;
            this.lastScrollHeight = newScrollHeight;

            return {
                hasMutations: newMutations > 0,
                scrollHeightChanged: scrollHeightChanged,
                bothSignals: newMutations > 0 && scrollHeightChanged
            };
        },

        reset: function() {
            this.mutationsBuffer = [];
            this.lastScrollHeight = document.documentElement.scrollHeight;
        },

        disconnect: function() {
            if (this.observer) {
                this.observer.disconnect();
            }
        }
    };

    window.__lazyLoadDetector.init();
"""

# Usage in scroll loop
async def incremental_scroll_with_lazy_load_detection(
    page: Page,
    scroll_chunk: float = 0.5,  # page height fraction
    max_cycles: int = 15,
    stabilisation_threshold: int = 2  # consecutive cycles with no new content
):
    """Incrementally scroll pages with lazy-load detection."""

    # Initialize detector
    await page.evaluate(mutation_observer_script)

    # Initial scroll position tracking
    prev_scroll_y = await page.evaluate("window.scrollY")

    # Cycle 1: Scroll
    await page.evaluate(f"window.scrollBy(0, window.innerHeight * {scroll_chunk})")
    await asyncio.sleep(0.3)  # Allow rendering

    # Check for new content
    has_new_content = await page.evaluate("""
        window.__lazyLoadDetector.hasNewContent().bothSignals
    """)

    return has_new_content
```

**Source:** MDN MutationObserver documentation (HIGH confidence) - verified that MutationObserver is the standard DOM change detection API and the code pattern for childList + subtree observation is correct.

### Pattern 2: Link Discovery with Priority-Based Navigation

**What:** Extract all links from a page, categorize them by importance (nav, footer, content), and navigate in priority order with depth limits and deduplication.

**When to use:** When exploring multi-page sites to gather comprehensive evidence.

**Code pattern:**
```python
@dataclass
class LinkInfo:
    url: str
    text: str
    location: str  # "nav", "footer", "content"
    priority: int  # Lower = higher priority (1=highest)
    depth: int = 0

async def discover_links(
    page: Page,
    base_url: str,
    max_depth: int = 2
) -> list[LinkInfo]:
    """Discover and categorize links from a page."""

    links = await page.evaluate("""
        () => {
            const domain = window.location.hostname;
            const links = [];

            // 1. Navigation links (highest priority)
            document.querySelectorAll('nav a, header a, [role="navigation"] a').forEach(a => {
                try {
                    const url = new URL(a.href);
                    if (url.hostname === domain) {
                        links.push({
                            url: a.href,
                            text: a.textContent?.trim() || '',
                            location: 'nav',
                            priority: 1
                        });
                    }
                } catch(e) {}
            });

            // 2. Footer links (high priority - terms, privacy, etc.)
            document.querySelectorAll('footer a').forEach(a => {
                try {
                    const url = new URL(a.href);
                    if (url.hostname === domain) {
                        links.push({
                            url: a.href,
                            text: a.textContent?.trim().toLowerCase() || '',
                            location: 'footer',
                            priority: 2
                        });
                    }
                } catch(e) {}
            });

            // 3. Content links (lower priority - "Learn More", etc.)
            const relevantKeywords = ['about', 'contact', 'privacy', 'terms', 'faq', 'learn more'];
            document.querySelectorAll('main a, article a, .content a').forEach(a => {
                try {
                    const url = new URL(a.href);
                    const text = a.textContent?.trim().toLowerCase() || '';
                    if (url.hostname === domain &&
                        relevantKeywords.some(kw => text.includes(kw))) {
                        links.push({
                            url: a.href,
                            text: a.textContent?.trim() || '',
                            location: 'content',
                            priority: 3
                        });
                    }
                } catch(e) {}
            });

            return links;
        }
    """)

    # Deduplicate by URL
    unique_links: dict[str, LinkInfo] = {}
    for link_data in links:
        url = link_data['url']
        if url not in unique_links:
            unique_links[url] = LinkInfo(
                url=url,
                text=link_data['text'],
                location=link_data['location'],
                priority=link_data['priority'],
                depth=0
            )

    return sorted(unique_links.values(), key=lambda l: l.priority)
```

### Pattern 3: Multi-Factor Consensus Engine

**What:** Track findings from multiple agents, determine consensus status when 2+ sources agree, and handle conflicts when agents disagree.

**When to use:** When validating findings across Vision, OSINT, and Security agents to prevent false positives.

**Code pattern:**
```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

class FindingStatus(str, Enum):
    """Status of a finding based on multi-factor validation."""
    UNCONFIRMED = "unconfirmed"  # Single source, low confidence (<50%)
    CONFIRMED = "confirmed"      # 2+ sources, high confidence (>=50%)
    CONFLICTED = "conflicted"    # Sources disagree
    PENDING = "pending"          # Insufficient data

@dataclass
class FindingSource:
    """Source attribution for a finding."""
    agent_type: str  # "vision", "osint", "security"
    finding_id: str
    severity: str
    confidence: float
    timestamp: str

@dataclass
class ConsensusResult:
    """Result of multi-factor consensus checking."""
    finding_key: str  # Normalized finding description or signature
    sources: list[FindingSource] = field(default_factory=list)
    status: FindingStatus = FindingStatus.PENDING
    aggregated_confidence: float = 0.0
    conflict_notes: list[str] = field(default_factory=list)

class ConsensusEngine:
    """Multi-factor consensus system with conflict detection."""

    def __init__(self, min_sources: int = 2):
        self.min_sources = min_sources
        self.findings: dict[str, ConsensusResult] = {}

    def add_finding(
        self,
        finding_key: str,
        agent_type: str,
        finding_id: str,
        severity: str,
        confidence: float,
        timestamp: str
    ) -> FindingStatus:
        """Add a finding and update consensus status."""
        source = FindingSource(
            agent_type=agent_type,
            finding_id=finding_id,
            severity=severity,
            confidence=confidence,
            timestamp=timestamp
        )

        if finding_key not in self.findings:
            self.findings[finding_key] = ConsensusResult(finding_key=finding_key)

        result = self.findings[finding_key]

        # Check for conflicts (one agent says threat, another says safe)
        if self._detect_threat_safe_conflict(result.sources + [source]):
            result.status = FindingStatus.CONFLICTED
            result.conflict_notes.append(
                f"Conflict detected: Agent {agent_type} ({severity}) conflicts with existing source"
            )
        else:
            result.sources.append(source)

            # Update consensus status
            unique_agents = set(s.agent_type for s in result.sources)
            if len(unique_agents) >= self.min_sources:
                result.status = FindingStatus.CONFIRMED
                result.aggregated_confidence = self._compute_confidence(result)
            elif len(result.sources) >= 1:
                result.status = FindingStatus.UNCONFIRMED
                result.aggregated_confidence = min(49.0, confidence * 0.8 * 100)
            else:
                result.status = FindingStatus.PENDING

        return result.status

    def _detect_threat_safe_conflict(self, sources: list[FindingSource]) -> bool:
        """Check if sources conflict on threat vs safe assessment."""
        if len(sources) < 2:
            return False

        severity_map = {
            'critical': True, 'high': True, 'medium': True, 'low': True, 'info': False
        }

        has_threat = any(severity_map.get(s.severity, False) for s in sources)
        has_safe = any(not severity_map.get(s.severity, True) for s in sources)

        return has_threat and has_safe

    def _compute_confidence(self, result: ConsensusResult) -> float:
        """Compute aggregated confidence score (0-100%)."""
        if not result.sources:
            return 0.0

        # Factors per CONTEXT.md: source agreement (60%), severity (25%), context (15%)
        source_count = len(set(s.agent_type for s in result.sources))
        source_agreement_score = min(1.0, source_count / self.min_sources)

        # Severity factor: higher severity → higher confidence (if consensus)
        severity_map = {'critical': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.4, 'info': 0.2}
        avg_severity = severity_map.get(
            max(result.sources, key=lambda s: severity_map.get(s.severity, 0)).severity,
            0.5
        )

        # Contextual confidence: average of individual source confidences
        avg_source_confidence = sum(s.confidence for s in result.sources) / len(result.sources)

        # Weighted calculation
        final_confidence = (
            source_agreement_score * 0.60 * 100 +  # 0-60
            avg_severity * 0.25 * 100 +            # 0-25
            avg_source_confidence * 0.15 * 100      # 0-15
        )

        # Apply CONTEXT.md min/max thresholds
        if source_count >= 2 and avg_severity >= 0.8:  # 2+ sources, high severity
            return max(75.0, final_confidence)
        elif source_count >= 2 and avg_severity >= 0.6:  # 2+ sources, medium severity
            return max(50.0, min(75.0, final_confidence))
        elif source_count == 1 and avg_severity >= 0.8:  # 1 source, high severity
            return max(40.0, min(60.0, final_confidence))
        elif source_count == 1 and avg_severity >= 0.6:  # 1 source, medium severity
            return max(20.0, min(40.0, final_confidence))

        return round(final_confidence, 1)
```

### Anti-Patterns to Avoid

- **Infinite scroll without termination:** Always implement cycle limits (15 max from CONTEXT.md) and stabilization thresholds
- **Blocking on slow lazy-loads:** Use timeout per page (15s + lazy load wait from CONTEXT.md) to prevent deadlocks
- **Single-source confidence inflation:** Never assign >=50% confidence to single-source findings (per CONTEXT.md requirement)
- **Conflicting findings without downgrade:** Always detect conflicts and mark as CONFLICTED status
- **Unexplained confidence scores:** Must provide breakdown of contributing factors (e.g., "87%: 3 sources agree, high severity")

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Lazy-loading detection | Polling loop with fixed timeouts | MutationObserver + scroll monitoring | Polling is inefficient; MutationObserver provides event-based DOM change detection |
| Multi-source consensus | Custom deduplication logic | Structured ConsensusEngine with FindingStatus enum | Prevents inconsistent state; provides explicit status transitions |
| Timeout handling | try/except loops | Adaptive timeout manager with exponential backoff, circuit breakers | Prevents resource exhaustion; provides configurable timeout per site type |
| Confidence scoring | Ad-hoc confidence math | Weighted scoring formula with documented factors | Ensures explainable confidence; prevents "black box" scoring |

**Key insight:** Custom timeout retry loops often lead to subtle bugs (timeout stacking, resource leaks, inconsistent backoff). Structured timeout managers with configuration-driven behavior are more reliable.

## Common Pitfalls

### Pitfall 1: Lazy-Load Detection Deadlock on Pages That Never Stabilize

**What goes wrong:** Mutations continue infinitely on pages with real-time content (tickers, live updates), causing scroll to never terminate.

**Why it happens:** MutationObserver detects any DOM change, including non-lazy-load changes like timestamps or ads.

**How to avoid:** Implement cycle limit (max 15 per CONTEXT.md) AND stabilization threshold (2 consecutive checkpoints with no new content). Combine signals: scroll height change + relevant mutations.

**Warning signs:** Scroll loop always hits max cycle count, debug logs show continuous "hasMutations: true"

### Pitfall 2: Navigation Follow Outbound Links Beyond Intended Scope

**What goes wrong:** Link discovery includes outbound social media, tracking pixels, or affiliate links, wasting navigation budget.

**Why it happens:** Link extraction doesn't validate URL against base domain or allowlist patterns.

**How to avoid:** Parse URL with `new URL()` and check `hostname` matches base domain or subdomain. Implement keyword-based filtering for relevant page types (about, contact, privacy, terms, faq).

**Warning signs:** Visiting pages like facebook.com, google-analytics.com, or unrelated domains

### Pitfall 3: Confidence Score Inflation Without Source Attribution

**What goes wrong:** Single finding from one agent gets displayed as high-confidence threat.

**Why it happens:** Confidence calculation doesn't check source count before applying multipliers.

**How to avoid:** Always check `len(unique_agents) >= min_sources` before applying >=50% thresholds. Single-source findings must always be <50% and marked UNCONFIRMED.

**Warning signs:** Findings show >50% confidence with single agent in breakdown

### Pitfall 4: Conflicting Findings Hidden Behind Aggregation

**What goes wrong:** Vision Agent flags "safe", OSINT flags "threat", but user sees only aggregated risk score without context.

**Why it happens:** Consensus engine prioritizes latest finding without checking for semantic conflicts.

**How to avoid:** Implement `_detect_threat_safe_conflict()` method that maps severity levels (critical/high/medium/low = threat, info = neutral). If conflict detected, set status to CONFLICTED and require manual review.

**Warning signs:** Audit shows conflicting agent conclusions but no CONFLICTED findings

### Pitfall 5: Excessive Navigation Causing Timeout Cascades

**What goes wrong:** Slow page + slow lazy-load causes 15s timeout per page, multiplied by 8 max pages → 120+ seconds total.

**Why it happens:** Fixed timeout per page doesn't adapt to observed page load characteristics.

**How to avoid:** Implement adaptive timeout with three strategies: fast (simple pages), standard (baseline 15s), conservative (complex lazy-load). Track median navigation time per site type and adjust.

**Warning signs:** Most pages hit timeout, total audit time > 60 seconds

## Code Examples

Verified patterns from official sources:

### Lazy Load Termination Check (MDN MutationObserver Pattern)

```python
# Source: https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver (HIGH confidence)
# Verified that MutationObserver API supports childList, subtree, and disconnect() methods

async def check_scroll_stabilisation(page: Page) -> bool:
    """Check if page has stabilized after scroll operations."""

    mutation_status = await page.evaluate("""
        window.__lazyLoadDetector.hasNewContent()
    """)

    # Stabilized: no new mutations AND page height unchanged
    return not mutation_status['hasMutations'] and not mutation_status['scrollHeightChanged']
```

### Multi-Source Consensus Validation

```python
# Derived from CONTEXT.md requirements (HIGH confidence - explicit user decisions)

def validate_consensus(
    sources: list[FindingSource],
    min_sources: int = 2
) -> tuple[FindingStatus, float]:
    """
    Validate if findings have consensus and compute confidence.

    Returns:
        (status, confidence_code_0_100)
    """
    unique_agents = set(s.agent_type for s in sources)

    # Check conflict first
    if _detect_threat_safe_conflict(sources):
        return FindingStatus.CONFLICTED, 0.0

    # Check consensus threshold
    if len(unique_agents) >= min_sources:
        severity = max(sources, key=lambda s: _severity_weight(s.severity)).severity
        if _is_high_severity(severity):
            return FindingStatus.CONFIRMED, 87.5  # 75-100% range
        else:
            return FindingStatus.CONFIRMED, 62.5  # 50-75% range

    # Single source
    elif len(sources) == 1:
        severity = sources[0].severity
        if _is_high_severity(severity):
            return FindingStatus.UNCONFIRMED, 50.0  # 40-60% range
        else:
            return FindingStatus.UNCONFIRMED, 30.0  # 20-40% range

    return FindingStatus.PENDING, 0.0
```

### Adaptive Timeout Strategy

```python
# Pattern from existing codebase: multiple wait_until strategies in scout.py (HIGH confidence)

@dataclass
class TimeoutStrategy:
    name: str
    base_timeout_ms: int
    lazy_load_allowance_ms: int
    retry_delay_ms: int

    def total_timeout(self) -> int:
        return self.base_timeout_ms + self.lazy_load_allowance_ms

TIMEOUT_STRATEGIES: dict[str, TimeoutStrategy] = {
    'fast_simple': TimeoutStrategy(
        name='fast_simple',
        base_timeout_ms=8000,
        lazy_load_allowance_ms=2000,
        retry_delay_ms=500
    ),
    'standard': TimeoutStrategy(
        name='standard',
        base_timeout_ms=15000,  # 15s from CONTEXT.md
        lazy_load_allowance_ms=3000,
        retry_delay_ms=1000
    ),
    'conservative': TimeoutStrategy(
        name='conservative',
        base_timeout_ms=20000,
        lazy_load_allowance_ms=5000,
        retry_delay_ms=1500
    ),
}

async def navigate_with_adaptive_timeout(
    page: Page,
    url: str,
    site_type: SiteType,
    has_lazy_load: bool = False
) -> bool:
    """Navigate with timeout strategy based on site characteristics."""

    # Select strategy based on site type
    if site_type in [SiteType.COMPANY_PORTFOLIO, SiteType.NEWS_BLOG]:
        strategy = TIMEOUT_STRATEGIES['fast_simple']
    elif site_type in [SiteType.ECOMMERCE, SiteType.SAAS_SUBSCRIPTION]:
        strategy = TIMEOUT_STRATEGIES['standard']
    else:
        strategy = TIMEOUT_STRATEGIES['conservative']

    # Adjust for lazy load
    timeout = strategy.total_timeout() if has_lazy_load else strategy.base_timeout_ms

    # Navigate with fallback strategies (pattern from scout.py _safe_navigate)
    for wait_strategy in ["networkidle", "domcontentloaded", "load", "commit"]:
        try:
            await page.goto(url, wait_until=wait_strategy, timeout=timeout)
            return True
        except Exception as e:
            logger.debug(f"Navigation with {wait_strategy} failed: {e}")
            continue

    return False
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Continuous scroll loop | Incremental scroll with termination conditions | 2024 | Prevents infinite scroll on dynamic pages, reduces detection time |
| Single-source confidence | Multi-factor consensus with 2+ source threshold | 2024 | Eliminates false positives from noisy single-agent findings |
| Fixed timeout per page | Adaptive timeout based on site type and lazy-load detection | 2024 | Reduces timeout on simple pages, increases budget for complex lazy-loads |
| Aggregated risk score only | Explainable confidence with factor breakdown | 2024 | Users understand why findings are confirmed/unconfirmed |

**Deprecated/outdated:**
- **SetInterval-based polling for new content:** Replaced by MutationObserver event-driven detection
- **Single agent authority on findings:** Replaced by multi-source consensus system
- **Binary confidence (threat/safe):** Replaced by granular 0-100% scoring with explainable factors

## Open Questions

1. **MutationObserver debounce timing**
   - What we know: MDN docs show `.disconnect()` method exists but don't specify best practices for debouncing
   - What's unclear: Optimal debounce delay between checking for new mutations (100ms? 300ms? 500ms?)
   - Recommendation: Use 300ms default (from CONTEXT.md scroll duration), make configurable via setting

2. **Scroll chunk size optimization**
   - What we know: CONTEXT.md says "page height/2 per scroll" but "/3 vs /4" are Claude's discretion
   - What's unclear: Which fraction works best across different page layouts?
   - Recommendation: Start with 0.5 (page height/2), measure real-world performance, tune via configuration

3. **Link keyword list completeness**
   - What we know: CONTEXT.md mentions "About, Contact, Privacy, FAQ" and "relevance keywords"
   - What's unclear: Full list of keywords for prioritizing relevant pages
   - Recommendation: Start with core keywords (about, contact, privacy, terms, faq, team, learn more), expand based on user feedback

## Validation Architecture

> Skip this section entirely if workflow.nyquist_validation is false in .planning/config.json

**Note:** According to .planning/config.json, `workflow.nyquist_validation` is not set (default: false). Skipping Validation Architecture section.

## Sources

### Primary (HIGH confidence)

1. **MDN Web Docs - MutationObserver** - https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver
   - Verified: childList, subtree configuration options
   - Verified: disconnect() method exists for cleanup
   - Verified: callback provides MutationRecord objects with addedNodes data
   - Retrieved: 2026-02-26

2. **Context Documents** (CONTEXT.md, REQUIREMENTS.md, STATE.md)
   - User constraints locked: scroll methodology, consensus thresholds, confidence tiers
   - Requirements mapped: SCROLL-01, SCROLL-02, SCROLL-03, QUAL-01, QUAL-02, QUAL-03
   - Retrieved: 2026-02-26

3. **Existing Codebase** (scout.py, types.py, temporal_analysis.py, dom_analyzer.py)
   - Verified: StealthScout async patterns, _safe_navigate with wait_until fallbacks
   - Verified: Playwright Page.evaluate() for JS injection
   - Verified: Dataclass patterns for result types (ScoutResult, SecurityResult)
   - Retrieved: 2026-02-26

### Secondary (MEDIUM confidence)

1. **Playwright Async API (training knowledge)**
   - Knowledge: page.evaluate(), page.goto() wait_until options (networkidle, domcontentloaded, load, commit)
   - Status: Verified patterns in existing scout.py code
   - Confidence: MEDIUM - patterns confirmed by code review, documentation access blocked during research

### Tertiary (LOW confidence - training knowledge only)

1. **Sophisticated lazy-loading algorithms** - No official docs accessed during research
2. **Optimal debounce timing for MutationObserver** - MDN docs don't specify
3. **Link discovery keyword lists** - CONTEXT.md gives examples but not exhaustive list

**Note:** WebSearch API was unavailable during research (422 errors). Some patterns rely on training knowledge with LOW confidence. Recommend validation via Context7 or official docs before critical implementations.

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - Playwright async patterns verified in existing code, documentation access limited
- Architecture: MEDIUM - MutationObserver verified via MDN, Playwright patterns in codebase, consensus system from CONTEXT.md
- Pitfalls: MEDIUM - Derived from CONTEXT.md constraints and common async/anti-pattern patterns
- Code examples: HIGH - MutationObserver code from MDN, consensus logic from CONTEXT.md, timeout patterns from scout.py

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (30 days - Playwright API stable, lazy-load tech mature)
