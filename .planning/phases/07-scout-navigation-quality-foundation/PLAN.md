# Plan: Phase 7 - Scout Navigation & Quality Foundation

**Phase ID:** 7
**Milestone:** v2.0 Masterpiece Features
**Status:** pending
**Created:** 2026-02-26

---

## Context

### Current State (Pre-Phase)

**Scout Agent (`veritas/agents/scout.py`):**
- Single-page investigation only (landing page)
- Temporal screenshot capture (t0 and t+delay)
- Full-page screenshot via Playwright
- Basic metadata extraction (DOM analysis, forms, links)
- No intelligent scrolling for lazy-loaded content detection
- No multi-page exploration beyond initial URL
- CAPTCHA detection and stealth browser features
- Human simulation (scroll patterns, mouse jitter)

**Vision Agent (`veritas/agents/vision.py`) from Phase 6:**
- 5-pass VLM pipeline with temporal analysis and content type detection
- Pass-specific prompts and adaptive SSIM thresholds
- Progress event streaming to frontend

**Quality/Consensus System:**
- No multi-factor consensus engine
- No confidence scoring breakdown
- No conflict detection between agents
- False positive prevention relies on single-agent thresholds only

**Frontend:**
- Basic Agent Theater with phase status cards
- EvidencePanel shows screenshots but no scroll-aware screenshot series
- No multi-page navigation visual indicators

### Goal State (Post-Phase)

**Scout with Intelligent Scrolling:**
- Intelligent incremental scroll (page height/2 per scroll) with 300-500ms wait after each scroll chunk
- Lazy-load detection using MutationObserver + scroll position monitoring
- Scroll termination: stop when no new content for 2 consecutive checkpoints OR max 15 scroll cycles
- Capture screenshots at scroll intervals and upon scroll termination
- Screenshot series captured from each scroll segment with labels indicating scroll position

**Multi-Page Exploration:**
- Automatic discovery of navigation links from nav bar, footer, and in-page "Learn More" sections
- Priority-based exploration order: 1) Landing page (already visited), 2) Legal pages (Privacy, Terms), 3) About pages, 4) functional pages, 5) outbound footer links
- Max 8 pages total with timeout per page = baseline 15s + lazy loading wait
- Link deduplication by URL with priority ranking by relevance keywords
- Breadcrumb tracking to avoid navigation loops

**Quality Foundation:**
- **ConsensusEngine** with multi-factor validation (2+ sources must agree before "confirmed" status)
- Finding status tiers: Confirmed (2+ sources, >=50%), Unconfirmed (1 source, <50%), Pending (insufficient data), Conflicted (sources disagree)
- Conflict detection when one agent flags safe while another flags threat
- **ConfidenceScorer** with explainable scoring breakdown:
  - 2+ sources, high-severity: 75-100%
  - 2+ sources, medium-severity: 50-75%
  - 1 source, high-severity: 40-60% (unconfirmed)
  - 1 source, medium-severity: 20-40% (unconfirmed)
- Visual breakdown showing contributing factors (e.g., "87%: 3 sources agree, high severity")
- Dynamic recalculation as additional sources contribute findings

**Progress Streaming:**
- Real-time scroll events: `scroll_start`, `scroll_progress`, `scroll_complete`, `screenshot_captured` with scroll position info
- Navigation events: `navigation_start`, `page_visited`, `navigation_complete`
- Consensus events: `finding_verified`, `finding_confirmed`, `finding_conflicted`
- Quality events: `confidence_calculated`, `status_updated`

---

## Critical Implementation Risks (Must Address)

### 1. Infinite Scroll Deadlock on Dynamic Pages (CRITICAL)

**Risk:** Pages with real-time content (tickers, live updates, ads) cause mutations to continue infinitely, preventing scroll termination.

**Analysis:**
- MutationObserver detects ANY DOM change, not just lazy-loaded content
- Without cycle limits, scroll never reaches stabilization threshold
- Current implementation has no scroll termination logic

**Mitigation Strategy:**
- Implement dual termination conditions: max 15 scroll cycles OR 2 consecutive checkpoints with no new content
- Track both mutation signals AND scroll height changes for more accurate detection
- Add per-page timeout (15s + lazy load allowance) to prevent indefinite hanging
- Implement "soft landing" - capture final screenshot even if full scroll not achieved

**Implementation Tasks:**
```python
# veritas/agents/scout/scroll_orchestrator.py (new file)
class ScrollOrchestrator:
    """Manages intelligent scrolling with lazy-load detection."""

    MAX_SCROLL_CYCLES = 15
    STABILIZATION_THRESHOLD = 2  # consecutive cycles with no new content
    SCROLL_CHUNK_RATIO = 0.5  # page height / 2 per scroll
    SCROLL_WAIT_MS = 400  # default wait between scroll chunks

    async def scroll_with_lazy_load_detection(self, page: Page) -> ScrollResult:
        """Incrementally scroll with MutationObserver-based lazy-load detection."""
        # Initialize MutationObserver script
        await self._inject_lazy_load_detector(page)

        cycles_without_content = 0
        for cycle in range(self.MAX_SCROLL_CYCLES):
            await self._scroll_chunk(page)
            await asyncio.sleep(self.SCROLL_WAIT_MS / 1000)

            # Check for new content
            has_new = await self._check_for_new_content(page)
            if has_new:
                cycles_without_content = 0
            else:
                cycles_without_content += 1

            # Termination condition
            if cycles_without_content >= self.STABILIZATION_THRESHOLD:
                logger.info(f"Scroll stabilized after {cycle + 1} cycles")
                break

        return ScrollResult(total_cycles=cycle + 1, stabilized=(cycles_without_content >= 2))
```

### 2. Navigation Runaway Beyond Intended Scope (HIGH)

**Risk:** Link discovery includes outbound social media, tracking pixels, or affiliate links, wasting navigation budget and potentially visiting unrelated domains.

**Analysis:**
- Current metadata extraction already distinguishes internal vs external links
- But no validation against base domain for "internal" classification
- No keyword-based filtering to prioritize relevant page types

**Mitigation Strategy:**
- Validate URLs against base domain hostname (including subdomains)
- Implement allowlist of relevant keywords: about, contact, privacy, terms, faq, team, learn more
- Priority ranking: nav links (priority 1) > footer links (priority 2) > content links (priority 3)
- Depth limit to prevent excessive navigation recursion
- Track visited URLs to avoid revisiting same pages

**Implementation Tasks:**
```python
# veritas/agents/scout/link_explorer.py (new file)
class LinkExplorer:
    """Discovers and prioritizes navigation links for multi-page exploration."""

    RELEVANT_KEYWORDS = ['about', 'contact', 'privacy', 'terms', 'faq', 'team', 'learn more']

    def __init__(self, base_url: str):
        self.base_domain = urlparse(base_url).netloc
        self.visited_urls: set[str] = set()

    async def discover_links(self, page: Page) -> list[LinkInfo]:
        """Extract and categorize links from page."""
        links = await page.evaluate(self._link_extraction_script)

        # Filter to same domain only
        filtered = [l for l in links if self._is_same_domain(l['url'])]

        # Prioritize by relevance
        prioritized = sorted(filtered, key=lambda l: l['priority'])

        # Deduplicate
        unique = {l['url']: l for l in prioritized}

        return list(unique.values())

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to base domain (including subdomains)."""
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc.endswith('.' + self.base_domain)
```

### 3. False Positive Prevention Complexity (MEDIUM)

**Risk:** Multi-factor consensus logic can become complex with multiple edge cases (conflicts, partial data, timing mismatches).

**Analysis:**
- Consensus threshold requires tracking source attribution across all agents
- Conflict detection needs semantic mapping of severity levels
- Dynamic recalculation requires state management as sources add findings over time

**Mitigation Strategy:**
- Use FindingStatus enum with explicit state transitions (PENDING → UNCONFIRMED → CONFIRMED → CONFLICTED)
- Implement simple severity mapping: critical/high/medium/low = threat, info = neutral
- Store source attribution in structured FindingSource dataclass
- Use finding_key normalization to group semantically similar findings (same target, same category)

**Implementation Tasks:**
```python
# veritas/quality/consensus_engine.py (new file)
class ConsensusEngine:
    """Multi-factor consensus system with conflict detection."""

    def add_finding(self, finding_key: str, source: FindingSource) -> FindingStatus:
        """Add finding and update consensus status."""
        # Get or create result
        result = self._get_or_create_result(finding_key)

        # Check for conflicts first
        if self._detect_conflict(result.sources + [source]):
            result.status = FindingStatus.CONFLICTED
            return result.status

        # Add source
        result.sources.append(source)

        # Update status based on source count
        unique_agents = len(set(s.agent_type for s in result.sources))
        if unique_agents >= self.min_sources:
            result.status = FindingStatus.CONFIRMED
            result.aggregated_confidence = self._compute_confidence(result)
        elif len(result.sources) == 1:
            result.status = FindingStatus.UNCONFIRMED
            result.aggregated_confidence = min(49.0, source.confidence * 80)
        else:
            result.status = FindingStatus.PENDING

        return result.status
```

---

## Dependencies (What Must Complete First)

**Phase 6: Vision Agent Enhancement** (Complete 2026-02-24)
- 5-pass VLM pipeline provides visual intelligence foundation
- Event streaming pattern established for progress communication
- Scout and Vision agents coordinate on screenshot capture and analysis

**Why this dependency matters:**
- Quality system needs Vision Agent findings as one of the consensus sources
- Progress streaming pattern from Phase 6 can be extended for scroll/navigation events
- Content type detection from Phase 6 assists in adaptive timeout strategies

---

## Task Breakdown (With File Locations)

### 7.1 Implement Intelligent Scrolling with Lazy-Load Detection

**Requirements:** SCROLL-01, SCROLL-03

**Files:**
- `veritas/agents/scout/scroll_orchestrator.py` (new file)
- `veritas/agents/scout/lazy_load_detector.py` (new file)
- `veritas/agents/scout.py` (extend investigate() method)
- `veritas/core/types.py` (add ScrollResult, ScrollState dataclasses)

**Wave:** 1 (can execute in parallel with 7.2)

**Tasks:**

```python
# 7.1.1 Create ScrollResult and ScrollState dataclasses in types.py
@dataclass
class ScrollState:
    """Current state of scroll orchestration."""
    current_cycle: int
    has_lazy_load: bool
    last_scroll_y: float
    last_scroll_height: float
    cycles_without_content: int
    stabilized: bool

@dataclass
class ScrollResult:
    """Result of scrolling operation."""
    total_cycles: int
    stabilized: bool
    lazy_load_detected: bool
    screenshots_captured: int
    scroll_states: list[ScrollState] = field(default_factory=list)

# 7.1.2 Implement LazyLoadDetector with MutationObserver script
class LazyLoadDetector:
    """Detects lazy-loaded content using MutationObserver."""

    MUTATION_OBSERVER_SCRIPT = """
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
            this.observer.observe(document.body, {childList: true, subtree: true});
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
        }
    };
    """

    async def inject(self, page: Page) -> None:
        """Inject MutationObserver script into page."""
        await page.evaluate(f"({self.MUTATION_OBSERVER_SCRIPT})__lazyLoadDetector.init()")

    async def has_new_content(self, page: Page) -> dict:
        """Check for new content since last check."""
        return await page.evaluate("window.__lazyLoadDetector.hasNewContent()")

    async def reset(self, page: Page) -> None:
        """Reset detector state."""
        await page.evaluate("window.__lazyLoadDetector.reset()")

# 7.1.3 Implement ScrollOrchestrator with intelligent scroll logic
class ScrollOrchestrator:
    """Manages incremental scrolling with lazy-load detection."""

    MAX_SCROLL_CYCLES = 15
    STABILIZATION_THRESHOLD = 2
    SCROLL_CHUNK_RATIO = 0.5
    SCROLL_WAIT_MS = 400

    def __init__(self, evidence_dir: Path, detector: LazyLoadDetector):
        self.evidence_dir = evidence_dir
        self.detector = detector

    async def scroll_page(
        self,
        page: Page,
        audit_id: str,
        screenshot_interval: int = 2
    ) -> ScrollResult:
        """
        Scroll page with lazy-load detection.

        Captures screenshots at each scroll interval and on terminal condition.

        Args:
            page: Playwright page to scroll
            audit_id: ID for screenshot naming
            screenshot_interval: Capture screenshot every N scroll cycles

        Returns:
            ScrollResult with all scroll state and captured screenshots
        """
        await self.detector.inject(page)
        states: list[ScrollState] = []
        screenshots_captured = 0
        cycles_without_content = 0

        for cycle in range(self.MAX_SCROLL_CYCLES):
            # Capture scroll position before
            scroll_y = await page.evaluate("window.scrollY")
            scroll_height = await page.evaluate("document.documentElement.scrollHeight")

            # Scroll chunk
            await page.evaluate(f"window.scrollBy(0, window.innerHeight * self.SCROLL_CHUNK_RATIO)")
            await asyncio.sleep(self.SCROLL_WAIT_MS / 1000)

            # Check for new content
            new_content = await self.detector.has_new_content(page)
            has_lazy_load = new_content['hasMutations'] or new_content['scrollHeightChanged']

            if has_lazy_load:
                cycles_without_content = 0
            else:
                cycles_without_content += 1

            # Capture screenshot at intervals
            if cycle % screenshot_interval == 0 or cycle == self.MAX_SCROLL_CYCLES - 1:
                await self._capture_scroll_screenshot(page, audit_id, cycle)
                screenshots_captured += 1

            # Record state
            states.append(ScrollState(
                current_cycle=cycle,
                has_lazy_load=has_lazy_load,
                last_scroll_y=scroll_y,
                last_scroll_height=scroll_height,
                cycles_without_content=cycles_without_content,
                stabilized=cycles_without_content >= self.STABILIZATION_THRESHOLD
            ))

            # Termination check
            if cycles_without_content >= self.STABILIZATION_THRESHOLD:
                logger.info(f"Scroll stabilized after {cycle + 1} cycles")
                break

        return ScrollResult(
            total_cycles=cycle + 1,
            stabilized=cycles_without_content >= self.STABILIZATION_THRESHOLD,
            lazy_load_detected=any(s.has_lazy_load for s in states),
            screenshots_captured=screenshots_captured,
            scroll_states=states
        )

    async def _capture_scroll_screenshot(self, page: Page, audit_id: str, cycle: int) -> str:
        """Capture screenshot during scroll."""
        filename = f"{audit_id}_scroll_{cycle:02d}.jpg"
        filepath = self.evidence_dir / filename
        scroll_y = await page.evaluate("window.scrollY")

        await page.screenshot(
            path=str(filepath),
            type="jpeg",
            quality=85,
            full_page=False
        )

        logger.debug(f"Scroll screenshot captured: cycle={cycle}, y={scroll_y}")
        return str(filepath)

# 7.1.4 Extend ScoutAgent.investigate() to use ScrollOrchestrator
async def investigate(
    self,
    url: str,
    temporal_delay: Optional[int] = None,
    viewport: str = "desktop",
    enable_scrolling: bool = True
) -> ScoutResult:
    """
    Full forensic investigation with optional intelligent scrolling.

    New parameter:
        enable_scrolling: If True, scroll page to capture lazy-loaded content
    """
    # ... existing code ...

    # --- After metadata extraction, add intelligent scrolling ---
    if enable_scrolling:
        from .scroll_orchestrator import ScrollOrchestrator
        from .lazy_load_detector import LazyLoadDetector

        detector = LazyLoadDetector()
        orchestrator = ScrollOrchestrator(self._evidence_dir, detector)

        scroll_start = time.time()
        scroll_result = await orchestrator.scroll_page(page, audit_id)
        scroll_time = (time.time() - scroll_start) * 1000

        logger.info(
            f"Scroll complete: cycles={scroll_result.total_cycles}, "
            f"stabilized={scroll_result.stabilized}, "
            f"screenshots={scroll_result.screenshots_captured}, "
            f"time={scroll_time:.0f}ms"
        )

        # Append scroll result to ScoutResult
        # ... extend ScoutResult with scroll_result field ...
```

---

### 7.2 Implement Multi-Page Exploration with Link Discovery

**Requirements:** SCROLL-02

**Files:**
- `veritas/agents/scout/link_explorer.py` (new file)
- `veritas/agents/scout.py` (new method: explore_multi_page())
- `veritas/core/types.py` (add LinkInfo, ExplorationResult dataclasses)

**Wave:** 1 (can execute in parallel with 7.1)

**Tasks:**

```python
# 7.2.1 Create LinkInfo and ExplorationResult dataclasses
@dataclass
class LinkInfo:
    """Information about a discovered navigation link."""
    url: str
    text: str
    location: str  # "nav", "footer", "content"
    priority: int  # Lower = higher priority (1=highest)
    depth: int = 0

@dataclass
class PageVisit:
    """Result of visiting a single page during exploration."""
    url: str
    status: str  # SUCCESS | TIMEOUT | ERROR
    screenshot_path: Optional[str]
    page_title: str
    navigation_time_ms: float
    scroll_result: Optional[ScrollResult]

@dataclass
class ExplorationResult:
    """Result of multi-page exploration."""
    base_url: str
    pages_visited: list[PageVisit] = field(default_factory=list)
    total_pages: int = 0
    total_time_ms: float = 0.0
    breadcrumbs: list[str] = field(default_factory=list)
    links_discovered: list[LinkInfo] = field(default_factory=list)

# 7.2.2 Implement LinkExplorer for discovery and prioritization
class LinkExplorer:
    """Discovers and prioritizesnavigation links for multi-page exploration."""

    RELEVANT_KEYWORDS = ['about', 'contact', 'privacy', 'terms', 'faq', 'team', 'learn more']
    MAX_PAGES = 8

    def __init__(self, base_url: str):
        self.base_domain = urlparse(base_url).netloc
        self.visited_urls: set[str] = set()

    async def discover_links(self, page: Page) -> list[LinkInfo]:
        """Extract and categorize links from page."""
        links = await page.evaluate(self._get_link_extraction_script())

        # Filter by domain and keywords
        filtered = [self._filter_link(l) for l in links if l]
        filtered = [l for l in filtered if l is not None]

        # Deduplicate by URL
        unique: dict[str, LinkInfo] = {l.url: l for l in filtered}

        # Sort by priority
        return sorted(unique.values(), key=lambda l: l.priority)

    def _get_link_extraction_script(self) -> str:
        """JavaScript for extracting links with location categorization."""
        return """
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
            const relevantKeywords = [...arguments];  // Passed from Python
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
        """

    def _filter_link(self, link_data: dict) -> Optional[LinkInfo]:
        """Filter link by domain and relevance."""
        url_str = link_data.get('url', '')
        if not url_str:
            return None

        # Check domain
        if not self._is_same_domain(url_str):
            return None

        # Skip already visited
        if url_str in self.visited_urls:
            return None

        # Skip non-HTTP
        parsed = urlparse(url_str)
        if parsed.scheme not in ('http', 'https'):
            return None

        self.visited_urls.add(url_str)

        return LinkInfo(
            url=url_str,
            text=link_data.get('text', ''),
            location=link_data.get('location', ''),
            priority=link_data.get('priority', 3)
        )

    def _is_same_domain(self, url_str: str) -> bool:
        """Check if URL belongs to base domain."""
        parsed = urlparse(url_str)
        return parsed.netloc == self.base_domain or parsed.netloc.endswith('.' + self.base_domain)

# 7.2.3 Implement multi-page exploration in ScoutAgent
async def explore_multi_page(
    self,
    url: str,
    max_pages: int = 8,
    timeout_per_page_ms: int = 15000  # 15s + lazy load allowance
) -> ExplorationResult:
    """
    Explore multiple pages beyond the initial landing page.

    Args:
        url: Starting URL (already visited)
        max_pages: Maximum number of additional pages to visit
        timeout_per_page_ms: Timeout per page navigation

    Returns:
        ExplorationResult with all visited pages and findings
    """
    result = ExplorationResult(base_url=url)
    context = await self._create_stealth_context(viewport="desktop")
    page = await context.new_page()
    audit_id = uuid.uuid4().hex[:8]

    try:
        # Navigate to base URL first if not already visited
        await self._apply_stealth(page)
        await self._safe_navigate(page, url)

        # Discover links from base page
        from .link_explorer import LinkExplorer

        explorer = LinkExplorer(url)
        links = await explorer.discover_links(page)
        result.links_discovered = links

        logger.info(f"Discovered {len(links)} links, exploring up to {max_pages} pages")

        # Explore priority pages
        for link_info in links[:max_pages]:
            start_time = time.time()

            try:
                # Navigate to link
                nav_success = await self._navigate_with_timeout(
                    page, link_info.url, timeout_per_page_ms
                )

                if not nav_success:
                    result.pages_visited.append(PageVisit(
                        url=link_info.url,
                        status="TIMEOUT",
                        screenshot_path=None,
                        page_title="",
                        navigation_time_ms=timeout_per_page_ms,
                        scroll_result=None
                    ))
                    continue

                # Capture evidence
                ss_path = await self._take_screenshot(page, audit_id, f"page_{len(result.pages_visited)}")
                title = await self._safe_title(page)
                nav_time = (time.time() - start_time) * 1000

                # Optional: Apply intelligent scrolling for lazy-loaded content
                scroll_result = None
                try:
                    from .scroll_orchestrator import ScrollOrchestrator
                    from .lazy_load_detector import LazyLoadDetector

                    detector = LazyLoadDetector()
                    orchestrator = ScrollOrchestrator(self._evidence_dir, detector)
                    scroll_result = await orchestrator.scroll_page(page, audit_id)
                except Exception as e:
                    logger.debug(f"Scroll failure (non-critical): {e}")

                result.pages_visited.append(PageVisit(
                    url=link_info.url,
                    status="SUCCESS",
                    screenshot_path=ss_path,
                    page_title=title,
                    navigation_time_ms=nav_time,
                    scroll_result=scroll_result
                ))

                result.breadcrumbs.append(link_info.url)

            except Exception as e:
                logger.error(f"Exploration error for {link_info.url}: {e}")
                result.pages_visited.append(PageVisit(
                    url=link_info.url,
                    status="ERROR",
                    screenshot_path=None,
                    page_title="",
                    navigation_time_ms=(time.time() - start_time) * 1000,
                    scroll_result=None
                ))

        result.total_pages = len(result.pages_visited)
        result.total_time_ms = sum(p.navigation_time_ms for p in result.pages_visited)

        return result

    finally:
        await page.close()
        await context.close()

async def _navigate_with_timeout(self, page: Page, url: str, timeout_ms: int) -> bool:
    """Navigate with adaptive timeout strategies."""
    for wait_strategy in ["networkidle", "domcontentloaded", "load", "commit"]:
        try:
            await page.goto(url, wait_until=wait_strategy, timeout=timeout_ms)
            return True
        except Exception:
            continue
    return False
```

---

### 7.3 Implement Quality Foundation: Consensus Engine (Part 1 of 2)

**Requirements:** QUAL-01, QUAL-02, QUAL-03

**Related Plans:** 7.3 (Consensus Engine) + 7.4 (Confidence Scoring & Validation)

**Files:**
- `veritas/quality/consensus_engine.py` (new file)
- `veritas/core/types.py` (add FindingSource, ConsensusResult, FindingStatus enum)
- `veritas/quality/__init__.py` (new package - extended in 7.4)

**Wave:** 2 (depends on 7.1 and 7.2 for complete findings data)

**Note:** Quality foundation work is split into two plans - 7.3 focuses on ConsensusEngine core logic, 7.4 adds ConfidenceScorer, ValidationStateMachine, and comprehensive tests.

**Tasks:**

```python
# 7.3.1 Create quality data structures in types.py
class FindingStatus(str, Enum):
    """Status of a finding based on multi-factor validation."""
    UNCONFIRMED = "unconfirmed"  # Single source, low confidence (<50%)
    CONFIRMED = "confirmed"      # 2+ sources, high confidence (>=50%)
    CONFLICTED = "conflicted"    # Sources disagree on threat assessment
    PENDING = "pending"          # Insufficient data

@dataclass
class FindingSource:
    """Source attribution for a finding."""
    agent_type: str  # "vision", "osint", "security"
    finding_id: str
    severity: str
    confidence: float  # 0.0-1.0 from source agent
    timestamp: str

@dataclass
class ConsensusResult:
    """Result of multi-factor consensus checking."""
    finding_key: str  # Normalized finding signature
    sources: list[FindingSource] = field(default_factory=list)
    status: FindingStatus = FindingStatus.PENDING
    aggregated_confidence: float = 0.0
    conflict_notes: list[str] = field(default_factory=list)
    confidence_breakdown: dict = field(default_factory=dict)

# 7.3.2 Implement ConsensusEngine with multi-source validation
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
        timestamp: Optional[str] = None
    ) -> FindingStatus:
        """
        Add a finding and update consensus status.

        Args:
            finding_key: Normalized finding signature (same target + category)
            agent_type: Source agent ("vision", "osint", "security")
            finding_id: Unique finding ID from agent
            severity: Severity level (crITICAL, HIGH, MEDIUM, LOW, INFO)
            confidence: Source agent confidence (0.0-1.0)
            timestamp: ISO timestamp (defaults to now)

        Returns:
            Updated FindingStatus after adding this source
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        source = FindingSource(
            agent_type=agent_type,
            finding_id=finding_id,
            severity=severity.upper(),
            confidence=confidence,
            timestamp=timestamp
        )

        # Get or create result
        if finding_key not in self.findings:
            self.findings[finding_key] = ConsensusResult(finding_key=finding_key)

        result = self.findings[finding_key]

        # Check for conflicts BEFORE adding source
        if self._detect_conflict(result.sources, source):
            result.status = FindingStatus.CONFLICTED
            result.conflict_notes.append(
                f"Conflict: {agent_type} ({severity}) conflicts with prior findings"
            )
            return result.status

        # Add source
        result.sources.append(source)

        # Update status based on source count
        unique_agents = len(set(s.agent_type for s in result.sources))
        if unique_agents >= self.min_sources:
            result.status = FindingStatus.CONFIRMED
            result.aggregated_confidence = self._compute_confidence(result)
        elif len(result.sources) == 1:
            result.status = FindingStatus.UNCONFIRMED
            result.aggregated_confidence = min(49.0, confidence * 80)
        else:
            result.status = FindingStatus.PENDING

        return result.status

    def _detect_conflict(self, existing_sources: list[FindingSource], new_source: FindingSource) -> bool:
        """
        Detect if sources conflict on threat vs safe assessment.

        Threat: CRITICAL, HIGH, MEDIUM, LOW
        Safe: INFO
        """
        severity_map = {
            'CRITICAL': True, 'HIGH': True, 'MEDIUM': True, 'LOW': True, 'INFO': False
        }

        all_sources = existing_sources + [new_source]

        is_threat = lambda s: severity_map.get(s.severity, False)
        is_safe = lambda s: not severity_map.get(s.severity, True)

        return any(is_threat(s) for s in all_sources) and any(is_safe(s) for s in all_sources)

    def _compute_confidence(self, result: ConsensusResult) -> float:
        """
        Compute aggregated confidence score (0-100%).

        Factors:
        - Source agreement: 60%
        - Severity: 25%
        - Contextual confidence: 15% (average of source confidences)
        """
        if not result.sources:
            return 0.0

        # Source agreement factor
        source_count = len(set(s.agent_type for s in result.sources))
        source_agreement_score = min(1.0, source_count / self.min_sources)

        # Severity factor
        severity_weights = {'CRITICAL': 1.0, 'HIGH': 0.8, 'MEDIUM': 0.6, 'LOW': 0.4, 'INFO': 0.2}
        max_severity = max(result.sources, key=lambda s: severity_weights.get(s.severity, 0))
        severity_score = severity_weights.get(max_severity.severity, 0.5)

        # Contextual confidence (average of source confidences)
        avg_context_confidence = sum(s.confidence for s in result.sources) / len(result.sources)

        # Weighted calculation
        final_confidence = (
            source_agreement_score * 0.60 * 100 +  # 0-60
            severity_score * 0.25 * 100 +           # 0-25
            avg_context_confidence * 0.15 * 100     # 0-15
        )

        # Apply CONTEXT.md min/max thresholds
        if source_count >= 2 and severity_score >= 0.8:  # 2+ sources, high severity
            return max(75.0, min(100.0, final_confidence))
        elif source_count >= 2 and severity_score >= 0.6:  # 2+ sources, medium severity
            return max(50.0, min(75.0, final_confidence))
        elif source_count == 1 and severity_score >= 0.8:  # 1 source, high severity
            return max(40.0, min(60.0, final_confidence))
        elif source_count == 1 and severity_score >= 0.6:  # 1 source, medium severity
            return max(20.0, min(40.0, final_confidence))

        result.confidence_breakdown = {
            "source_agreement": f"{(source_agreement_score * 100):.0f}%",
            "severity_factor": f"{(severity_score * 25):.0f}%",
            "context_confidence": f"{(avg_context_confidence * 15):.0f}%",
            "source_count": source_count
        }

        return round(final_confidence, 1)

    def get_result(self, finding_key: str) -> Optional[ConsensusResult]:
        """Get consensus result for a finding key."""
        return self.findings.get(finding_key)

    def get_confirmed_findings(self) -> list[ConsensusResult]:
        """Get all findings with CONFIRMED status."""
        return [r for r in self.findings.values() if r.status == FindingStatus.CONFIRMED]

    def get_conflicted_findings(self) -> list[ConsensusResult]:
        """Get all findings with CONFLICTED status."""
        return [r for r in self.findings.values() if r.status == FindingStatus.CONFLICTED]

# 7.3.3 Implement ConfidenceScorer with explainable scoring
class ConfidenceScorer:
    """Calculates and formats explainable confidence scores."""

    SCORE_RANGES = {
        'high_confidence': (75.0, 100.0),
        'medium_confidence': (50.0, 75.0),
        'unconfirmed_high': (40.0, 60.0),
        'unconfirmed_medium': (20.0, 40.0),
        'low_confidence': (0.0, 20.0)
    }

    def format_confidence(self, result: ConsensusResult) -> str:
        """
        Format confidence score with factor breakdown.

        Example: "87%: 3 sources agree, high severity"
        """
        score = result.aggregated_confidence
        breakdown = result.confidence_breakdown

        source_count = breakdown.get('source_count', 0)
        severity_score = float(breakdown.get('severity_factor', '0%').rstrip('%')) / 25

        if source_count >= 2 and severity_score >= 0.8:
            severity_desc = "high severity"
        elif source_count >= 2 and severity_score >= 0.6:
            severity_desc = "medium severity"
        else:
            severity_desc = f"{source_count} source{'s' if source_count > 1 else ''}"

        return f"{score:.0f}%: {severity_desc}"

    def get_confidence_tier(self, score: float) -> str:
        """Get confidence tier based on score."""
        if score >= 75.0:
            return "high_confidence"
        elif score >= 50.0:
            return "medium_confidence"
        elif score >= 40.0:
            return "unconfirmed_high"
        elif score >= 20.0:
            return "unconfirmed_medium"
        else:
            return "low_confidence"

# 7.3.4 Create validation state machine for finding progression
class ValidationStateMachine:
    """
    State machine for incremental verification and refinement.

    Transitions:
    PENDING → UNCONFIRMED (first source)
    UNCONFIRMED → CONFIRMED (2nd source agrees)
    UNCONFIRMED → CONFLICTED (disagreeing source)
    CONFIRMED → CONFLICTED (future conflict)
    """

    def transition(
        self,
        current_status: FindingStatus,
        new_source: FindingSource,
        existing_sources: list[FindingSource],
        min_sources: int = 2
    ) -> FindingStatus:
        """
        Determine next state based on current status and new source.

        Args:
            current_status: Current FindingStatus
            new_source: New finding source being added
            existing_sources: Sources already associated with finding
            min_sources: Minimum sources required for confirmation

        Returns:
            Next FindingStatus
        """
        all_sources = existing_sources + [new_source] if new_source in existing_sources else existing_sources

        # Check for conflicts
        severity_map = {'CRITICAL': True, 'HIGH': True, 'MEDIUM': True, 'LOW': True, 'INFO': False}
        is_threat = lambda s: severity_map.get(s.severity, False)
        is_safe = lambda s: not severity_map.get(s.severity, True)

        has_threat = any(is_threat(s) for s in all_sources)
        has_safe = any(is_safe(s) for s in all_sources)

        if has_threat and has_safe:
            return FindingStatus.CONFLICTED

        # Check source count
        unique_agents = len(set(s.agent_type for s in all_sources))

        if unique_agents >= min_sources:
            return FindingStatus.CONFIRMED
        elif unique_agents >= 1:
            return FindingStatus.UNCONFIRMED
        else:
            return FindingStatus.PENDING

    def can_confirm(self, status: FindingStatus) -> bool:
        """Check if finding is in confirmable state."""
        return status in (FindingStatus.CONFIRMED, FindingStatus.UNCONFIRMED)

    def requires_review(self, status: FindingStatus) -> bool:
        """Check if finding requires manual review."""
        return status == FindingStatus.CONFLICTED

    def is_valid_transition(self, from_status: FindingStatus, to_status: FindingStatus) -> bool:
        """Validate state transition is legal."""
        valid_transitions = {
            FindingStatus.PENDING: {FindingStatus.UNCONFIRMED},
            FindingStatus.UNCONFIRMED: {FindingStatus.CONFIRMED, FindingStatus.CONFLICTED},
            FindingStatus.CONFIRMED: {FindingStatus.CONFLICTED},
            FindingStatus.CONFLICTED: set()
        }
        return to_status in valid_transitions.get(from_status, set())
```

---

## Test Strategy

### 7.1 Intelligent Scrolling Tests

```python
# tests/test_scroll_orchestrator.py

@pytest.mark.asyncio
async def test_scrolling_detects_lazy_loaded_content():
    """Test that scrolling detects and waits for lazy-loaded content."""
    # Mock page with lazy-loading behavior
    # Verify scroll continues until stabilization or max cycles
    pass

@pytest.mark.asyncio
async def test_scrolling_stabilizes_early_on_static_page():
    """Test that scrolling stops early on pages without lazy loading."""
    # Mock page with no new content
    # Verify scroll stabilizes after 2 consecutive no-content cycles
    pass

@pytest.mark.asyncio
async def test_scrolling_captures_screenshots_at_intervals():
    """Test that screenshots are captured at scroll intervals."""
    # Verify screenshot count matches expected based on cycles
    pass

@pytest.mark.asyncio
async def test_scrolling_respects_max_cycle_limit():
    """Test that scrolling stops at max 15 cycles even if not stabilized."""
    # Mock page that never stabilizes
    # Verify total_cycles == 15
    pass
```

### 7.2 Multi-Page Exploration Tests

```python
# tests/test_link_explorer.py

@pytest.mark.asyncio
async def test_link_discovery_prioritizes_nav_links():
    """Test that navigation links get highest priority."""
    # Mock page with nav, footer, and content links
    # Verify nav links have priority 1
    pass

@pytest.mark.asyncio
async def test_link_filtering_restricts_to_same_domain():
    """Test that external links are filtered out."""
    # Mock page with mixed internal/external links
    # Verify only same-domain links returned
    pass

@pytest.mark.asyncio
async def test_multi_page_exploration_respects_max_pages_limit():
    """Test that exploration stops at max 8 pages."""
    # Mock page with many discovered links
    # Verify only 8 pages visited
    pass

@pytest.mark.asyncio
async def test_exploration_breadcrumbs_track_visited_urls():
    """Test that breadcrumbs track exploration path."""
    # Verify visited URLs in order
    pass
```

### 7.3 Quality Foundation Tests

```python
# tests/test_consensus_engine.py

def test_two_sources_confirm_finding():
    """Test that 2 distinct sources produce CONFIRMED status."""
    engine = ConsensusEngine(min_sources=2)
    engine.add_finding("test_key", "vision", "f1", "HIGH", 0.9)
    status = engine.add_finding("test_key", "osint", "f2", "HIGH", 0.85)

    assert status == FindingStatus.CONFIRMED
    assert engine.get_result("test_key").aggregated_confidence >= 75.0

def test_single_source_unconfirmed():
    """Test that single source produces UNCONFIRMED status."""
    engine = ConsensusEngine(min_sources=2)
    status = engine.add_finding("test_key", "vision", "f1", "HIGH", 0.9)

    assert status == FindingStatus.UNCONFIRMED
    assert engine.get_result("test_key").aggregated_confidence < 50.0

def test_conflicting_sources_conflicted():
    """Test that threat vs safe conflict produces CONFLICTED status."""
    engine = ConsensusEngine(min_sources=2)
    engine.add_finding("test_key", "vision", "f1", "HIGH", 0.9)
    status = engine.add_finding("test_key", "osint", "f2", "INFO", 0.95)

    assert status == FindingStatus.CONFLICTED
    assert len(engine.get_result("test_key").conflict_notes) > 0

def test_confidence_breakdown_explainable():
    """Test that confidence breakdown includes all factors."""
    engine = ConsensusEngine(min_sources=2)
    engine.add_finding("test_key", "vision", "f1", "HIGH", 0.9)
    engine.add_finding("test_key", "osint", "f2", "HIGH", 0.85)

    result = engine.get_result("test_key")
    assert "source_agreement" in result.confidence_breakdown
    assert "severity_factor" in result.confidence_breakdown
    assert "context_confidence" in result.confidence_breakdown
```

---

## Success Criteria (When Phase 7 Is Done)

1. **User can observe screenshot series captured during scroll-based lazy loading loading**
   - Screenshots labeled with scroll cycle number captured at intervals
   - Screenshot file names indicate scroll position (e.g., `audit_id_scroll_00.jpg`, `audit_id_scroll_02.jpg`)

2. **User can see exploration beyond landing page including About, Contact, Privacy pages**
   - ScoutResult includes ExplorationResult with visited pages
   - Screenshots captured from priority pages (nav, footer links)

3. **System waits for lazy-loaded content before capturing screenshots**
   - Scroll cycles pause for 300-500ms after each chunk
   - MutationObserver detects new DOM additions
   - Scroll stabilization based on 2 consecutive cycles with no new content

4. **Threat findings require 2+ source agreement before appearing as "confirmed"**
   - Single-source findings shown as UNCONFIRMED with <50% confidence
   - CONFIRMED findings require 2+ distinct agent types (vision, osint, security)

5. **Each finding displays confidence score (0-100%) with supporting reasoning**
   - Confidence breakdown shows source agreement, severity factor, contextual confidence
   - Conflict findings show CONFLICTED status with conflict notes

---

## Requirements Covered

| Requirement ID | Description | Plans | Status |
|----------------|-------------|-------|--------|
| SCROLL-01 | Scout/Vision Agent can scroll pages and capture full screenshot series | 7.1 | pending |
| SCROLL-02 | Scout can navigate to multiple pages beyond initial landing page | 7.2 | pending |
| SCROLL-03 | Lazy loading detection and handling for complete capture | 7.1 | pending |
| QUAL-01 | False positive detection criteria with multi-factor validation | 7.3, 7.4 | pending |
| QUAL-02 | Deep statistics and confidence scoring with explainable factors | 7.3, 7.4 | pending |
| QUAL-03 | Incremental verification and refinement with state transitions | 7.3, 7.4 | pending |

**Coverage:**
- Phase 7 requirements: 6 total
- Mapped to plans: 6 (all requirements assigned)
- Unmapped: 0 ✓

**Plans:**
- Wave 1: 7.1 (Intelligent Scrolling), 7.2 (Multi-Page Exploration)
- Wave 2: 7.3 (Consensus Engine), 7.4 (Confidence Scoring & Validation)
- Total: 4 plans ✓
