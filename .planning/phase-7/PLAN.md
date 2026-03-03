# Plan: Phase 7 - Scout Navigation & Quality Foundation

**Phase ID:** 7
**Milestone:** v2.0 Masterpiece Features
**Depends on:** Phase 6 (Vision Agent Enhancement)
**Status:** pending
**Created:** 2026-02-23

---

## Context

### Current State (Pre-Phase)

**Scout Agent (`veritas/agents/scout.py`):**
- Single-page capture only (t0, t+delay, fullpage screenshots)
- No scrolling or lazy loading detection
- No multi-page exploration capability
- Basic CAPTCHA detection via text matching
- Stealth mode with anti-detection (Playwright stealth plugin)
- Returns: 2-3 screenshots per page, basic DOM metadata

**Navigation Behavior:**
- Visits initial URL only
- Does not follow links or explore site structure
- No depth limit handling (not applicable since single-page)
- No URL deduplication across multiple pages

**Quality Management:**
- Each agent finds independently
- No multi-source validation
- Judge trusts most confident findings
- No explicit false positive prevention

**Frontend:**
- EvidencePanel shows screenshots (no carousel for multi-page)
- No scroll visualization or page exploration indicators

### Goal State (Post-Phase)

**Enhanced Scout Navigation:**
- Scroll-based lazy loading detection and screenshot capture
- Scroll depth control (max scroll iterations)
- Screenshot series captured at scroll intervals
- Handle infinite scroll patterns (auto-detect loops)
- Multi-page navigation with depth limits
- Explore site structure (About, Contact, Privacy, etc.)
- URL deduplication to prevent infinite loops
- Smart link selection (prioritize internal vs. external)

**Temporal Detection (Lazy Loading):**
- Wait for lazy-loaded content before screenshot capture
- Detect content loading completion (DOM stability, network idle)
- Handle AJAX/React/Vue page transitions
- Dynamic content detection strategies

**Quality Management Foundation:**
- Multi-factor validation: 2+ sources must agree before confirming threats
- Per-finding confidence scores (0-100%) with supporting reasoning
- Historical baseline comparison (is this finding typical for this site type?)
- "Review required" category for ambiguous findings
- Incremental verification: "Likely" → "Confirmed" → "Verified" progression

**Evidence Model Enhancement:**
- Findings tagged with source agent (Vision, Security, Graph, Scout)
- Findings with same bbox + category require cross-validation
- Confidence weighted by multiple agent agreement
- Conflict detection: Vision says "threat", Security says "safe" → mark for review

---

## Critical Implementation Risks (Must Address)

### 1. Infinite Navigation Loop Risk (CRITICAL)

**Risk:** Multi-page navigation without loop prevention = infinite exploration

**Scenario:**
```
Page A → Page B → Page C → Page A (back to A) → repeats forever
```

**Or worse:**
```
Pagination links: Page 1 → Page 2 → Page 3 → ... → Page N → Page 1
```

**Mitigation Strategy:**
- **URL deduplication**: Track all visited URLs, skip repeats
- **Depth limit**: Max pages to visit per audit (configurable, default: 10)
- **Domain limiting**: Only follow same-domain links (or allow cross-domain for investigation)
- **Link scoring**: Prioritize pages with higher value (About, Contact, Privacy vs. random blog posts)
- **Timeout per page**: Fail-fast if page doesn't load within threshold
- **Loop detection**: Detect repeated URL patterns (/page/1, /page/2, /page/3...)

**Implementation Tasks:**
```python
# veritas/agents/scout.py (new module: navigation_controller.py)
class NavigationController:
    """Controls multi-page navigation with loop prevention."""

    def __init__(
        self,
        max_pages: int = 10,
        max_depth: int = 3,
        same_domain_only: bool = True,
        timeout_per_page: int = 30
    ):
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        self.timeout_per_page = timeout_per_page

        self.visited_urls: set[str] = set()
        self.url_queue: List[dict] = []
        self.domain_whitelist: set[str] = set()

    def can_visit_url(self, url: str, current_depth: int) -> bool:
        """
        Determine if URL can be visited.

        Returns: True if URL can be visited, False otherwise with reason
        """
        # Check depth limit
        if current_depth > self.max_depth:
            logger.debug(f"Skipping {url}: depth limit ({current_depth} > {self.max_depth})")
            return False, "depth_limit"

        # Check page count limit
        if len(self.visited_urls) >= self.max_pages:
            logger.debug(f"Skipping {url}: page count limit ({len(self.visited_urls)} >= {self.max_pages})")
            return False, "page_limit"

        # Check URL deduplication
        if url in self.visited_urls:
            logger.debug(f"Skipping {url}: already visited")
            return False, "already_visited"

        # Check same-domain constraint
        if self.same_domain_only:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            if not any(parsed_url.netloc.endswith(domain) for domain in self.domain_whitelist):
                logger.debug(f"Skipping {url}: not in whitelist")
                return False, "domain_filter"

        return True, "ok"

    def mark_visited(self, url: str):
        """Mark URL as visited."""
        self.visited_urls.add(url)

    def add_link_to_queue(self, url: str, depth: int, priority: int = 0):
        """
        Add link to visitation queue with priority.

        Higher priority = visit sooner.
        """
        self.url_queue.append({
            'url': url,
            'depth': depth,
            'priority': priority
        })
        # Sort by priority (descending) for FIFO with priority
        self.url_queue.sort(key=lambda x: x['priority'], reverse=True)

    def get_next_page(self) -> Optional[dict]:
        """Get next page to visit."""
        if not self.url_queue:
            return None
        return self.url_queue.pop(0)

    def detect_pagination_pattern(self, url: str, page_urls: List[str]) -> bool:
        """
        Detect if we're hitting pagination loops.

        Returns: True if pagination pattern detected
        """
        # Look for URL patterns like /page/1, /page/2, /page/3...
        import re
        from collections import Counter

        # Extract URL patterns
        patterns = []
        for page_url in page_urls:
            # Replace numbers with {n} to extract pattern
            pattern = re.sub(r'\d+', '{n}', page_url)
            patterns.append(pattern)

        # If same pattern appears 3+ times, it's likely pagination
        pattern_counts = Counter(patterns)
        for pattern, count in pattern_counts.items():
            if count >= 3:
                logger.info(f"Detected pagination pattern: {pattern} (appears {count} times)")
                return True

        return False

# 7.1.2 Integrate NavigationController into Scout
# veritas/agents/scout.py (modify ScoutAgent.navigate_multiple_pages())
class ScoutAgent:
    def __init__(self, nim_client: NIMClient):
        self.nim_client = nim_client
        self.nav_controller = NavigationController(
            max_pages=settings.MAX_PAGES_PER_AUDIT,
            max_depth=3,
            same_domain_only=True
        )

    async def navigate_multiple_pages(self, start_url: str) -> List[ScoutResult]:
        """
        Navigate multiple pages of the website.

        Returns: List of ScoutResult, one per page
        """
        results = []
        current_url = start_url
        current_depth = 0

        # Add initial URL to queue
        self.nav_controller.add_link_to_queue(current_url, current_depth, priority=10)

        while len(results) < self.nav_controller.max_pages:
            next_info = self.nav_controller.get_next_page()
            if not next_info:
                break

            next_url = next_info['url']
            next_depth = next_info['depth']

            # Check if we can visit this URL
            can_visit, reason = self.nav_controller.can_visit_url(next_url, next_depth)
            if not can_visit:
                logger.debug(f"Skipping {next_url}: {reason}")
                continue

            # Navigate to page
            try:
                result = await self.navigate_page(
                    url=next_url,
                    depth=next_depth,
                    timeout=self.nav_controller.timeout_per_page
                )
                results.append(result)
                self.nav_controller.mark_visited(next_url)

                # Add linked pages to queue
                self._discover_links(result, next_url, next_depth)

            except Exception as e:
                logger.error(f"Failed to navigate to {next_url}: {e}")
                continue

        return results

    def _discover_links(self, result: ScoutResult, current_url: str, current_depth: int) -> None:
        """
        Discover and prioritize links from current page.

        Adds high-value internal pages to navigation queue.
        """
        from urllib.parse import urljoin, urlparse

        # Get base URL
        base_url = current_url

        # Prioritize these page types
        high_priority_keywords = [
            'about', 'contact', 'privacy', 'terms', 'policy',
            'pricing', 'services', 'products', 'features'
        ]

        medium_priority_keywords = [
            'blog', 'news', 'updates', 'learn', 'help',
            'support', 'faq', 'documentation'
        ]

        # Get links from DOM metadata (result.dom_metadata should have links)
        for link_url in result.dom_metadata.get('links', []):
            # Resolve relative URLs
            absolute_url = urljoin(base_url, link_url)

            # Only follow same-domain links (unless configured otherwise)
            if not self.nav_controller.same_domain_only:
                self.nav_controller.add_link_to_queue(
                    absolute_url,
                    current_depth + 1,
                    priority=0
                )
                continue

            # Check domain match
            if urlparse(absolute_url).netloc != urlparse(base_url).netloc:
                continue

            # Assign priority based on URL keywords
            url_lower = absolute_url.lower()
            if any(kw in url_lower for kw in high_priority_keywords):
                priority = 10
            elif any(kw in url_lower for kw in medium_priority_keywords):
                priority = 5
            else:
                priority = 0

            self.nav_controller.add_link_to_queue(
                absolute_url,
                current_depth + 1,
                priority=priority
            )
```

**Test Strategy:**
- Unit test `can_visit_url` with depth limit, page limit, URL deduplication
- Integration test with 3-page site, verify stop at depth limit
- Test pagination pattern detection with mock URLs

---

### 2. Lazy Loading Detection Failure Risk (HIGH)

**Risk:** Lazy-loaded content fails to load before screenshot = missed threats

**Scenario:**
- Page has "Load More" button that triggers JavaScript content
- Scout takes screenshot after 5 seconds → content not loaded yet
- Vision Agent sees incomplete page → misses threats that appeared later

**Mitigation Strategy:**
- **Network idle detection**: Wait for network requests to complete
- **DOM stability detection**: No significant DOM changes for X seconds
- **Height stabilization detection**: Page height stopped changing (no more lazy loading)
- **Lazy loading triggers**: Click "Load More" buttons, scroll to bottom
- **Visual similarity comparison**: Compare screenshots over time, stop when similar

**Implementation Tasks:**
```python
# veritas/agents/scout.py (new module: lazy_loading_detector.py)
class LazyLoadingDetector:
    """Detects and handles lazy loading on web pages."""

    DOM_STABILITY_THRESHOLD_MS = 1000  # No DOM changes for 1 second
    NETWORK_IDLE_THRESHOLD_MS = 2000   # No network requests for 2 seconds
    HEIGHT_STABILITY_THRESHOLD_MS = 2000  # Height stable for 2 seconds
    MAX_WAIT_SECONDS = 15  # Max wait for lazy loading

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.dom_observer_active = False
        self.network_observer_active = False
        self.last_dom_change_time = None
        self.last_height = 0
        self.last_height_change_time = None

    async def wait_for_lazy_loading(self) -> dict:
        """
        Wait for lazy-loaded content to finish loading.

        Returns:
            {
                'content_loaded': bool,
                'wait_duration_ms': int,
                'stabilization_method': str,
                'final_height': int
            }
        """
        start_time = time.time()
        start_height = await self._get_page_height()

        # Method 1: Network idle
        network_idle = await self._wait_for_network_idle()
        if network_idle:
            wait_duration = (time.time() - start_time) * 1000
            self.logger.info(f"Lazy loading stabilized via network idle ({wait_duration:.0f}ms)")
            return {
                'content_loaded': True,
                'wait_duration_ms': int(wait_duration),
                'stabilization_method': 'network_idle',
                'final_height': await self._get_page_height()
            }

        # Method 2: Height stabilization
        height_stabilized = await self._wait_for_height_stabilization()
        if height_stabilized:
            wait_duration = (time.time() - start_time) * 1000
            self.logger.info(f"Lazy loading stabilized via height ({wait_duration:.0f}ms)")
            return {
                'content_loaded': True,
                'wait_duration_ms': int(wait_duration),
                'stabilization_method': 'height_stable',
                'final_height': await self._get_page_height()
            }

        # Method 3: DOM stability
        dom_stable = await self._wait_for_dom_stability()
        if dom_stable:
            wait_duration = (time.time() - start_time) * 1000
            self.logger.info(f"Lazy loading stabilized via DOM ({wait_duration:.0f}ms)")
            return {
                'content_loaded': True,
                'wait_duration_ms': int(wait_duration),
                'stabilization_method': 'dom_stable',
                'final_height': await self._get_page_height()
            }

        # Maximum wait time exhausted
        final_height = await self._get_page_height()
        self.logger.warning(f"Lazy loading did not stabilize within {self.MAX_WAIT_SECONDS}s")
        return {
            'content_loaded': False,
            'wait_duration_ms': int((time.time() - start_time) * 1000),
            'stabilization_method': 'timeout',
            'final_height': final_height,
            'note': 'Content may still be loading'
        }

    async def _get_page_height(self) -> int:
        """Get current scrollable page height."""
        return await self.page.evaluate('() => document.documentElement.scrollHeight')

    async def _wait_for_network_idle(self) -> bool:
        """Wait for network requests to complete."""
        try:
            await self.page.wait_for_load_state(
                'networkidle',
                timeout=self.NETWORK_IDLE_THRESHOLD_MS
            )
            return True
        except Exception as e:
            self.logger.debug(f"Network idle timeout: {e}")
            return False

    async def _wait_for_height_stabilization(self) -> bool:
        """Wait for page height to stabilize."""
        start_time = time.time()

        while (time.time() - start_time) * 1000 < self.MAX_WAIT_SECONDS * 1000:
            current_height = await self._get_page_height()

            if self.last_height > 0 and current_height == self.last_height:
                # Height unchanged, check if stable for threshold period
                if self.last_height_change_time is not None:
                    time_since_change = time.time() - self.last_height_change_time
                    if time_since_change * 1000 >= self.HEIGHT_STABILITY_THRESHOLD_MS:
                        return True
            else:
                # Height changed, reset stability timer
                self.last_height_change_time = time.time()
                self.last_height = current_height

            await asyncio.sleep(0.2)

        return False

    async def _wait_for_dom_stability(self) -> bool:
        """Wait for DOM to stabilize (no mutations)."""
        try:
            # Use MutationObserver to detect DOM changes
            script = '''
            new Promise((resolve) => {
                let observer;
                let lastMutationTime = Date.now();

                observer = new MutationObserver(() => {
                    lastMutationTime = Date.now();
                });

                observer.observe(document.documentElement, {
                    childList: true,
                    subtree: true
                });

                setTimeout(() => {
                    observer.disconnect();
                    resolve();
                }, %d);
            });
            ''' % self.DOM_STABILITY_THRESHOLD_MS

            await self.page.evaluate(script)

            # Wait double the threshold to ensure no more mutations
            await asyncio.sleep(self.DOM_STABILITY_THRESHOLD_MS / 1000 * 2)

            return True

        except Exception as e:
            self.logger.debug(f"DOM stability check failed: {e}")
            return False

# 7.2.2 Integrate lazy loading detection into Scout
# veritas/agents/scout.py (modify ScoutAgent.navigate_page())
class ScoutAgent:
    def __init__(self, nim_client: NIMClient):
        self.nim_client = nim_client
        self.nav_controller = NavigationController()
        self.lazy_detector = None  # Will be created per page

    async def navigate_page(self, url: str, depth: int, timeout: int = 30) -> ScoutResult:
        """Navigate to page and capture screenshots with lazy loading detection."""
        # Navigate to URL
        self.page.goto(url, timeout=timeout * 1000)

        # Initialize lazy loading detector
        self.lazy_detector = LazyLoadingDetector(self.page)

        # Wait for lazy loading
        lazy_result = await self.lazy_detector.wait_for_lazy_loading()

        # Take t0 screenshot
        t0_path = await self._take_screenshot(f"{self.audit_id}_page{depth}_t0.jpg")

        # Sleep for temporal delay
        await asyncio.sleep(self.temporal_delay)

        # Wait for lazy loading again (content might have loaded during sleep)
        lazy_result_after_delay = await self.lazy_detector.wait_for_lazy_loading()

        # Take t+delay screenshot
        t_delay_path = await self._take_screenshot(f"{self.audit_id}_page{depth}_tdelay.jpg")
        self.logger.info(f"Height after delay: {lazy_result_after_delay['final_height']}px")

        # Capture multiple scroll-based screenshots
        scroll_screenshots = await self._capture_scroll_screenshots()

        # Take fullpage screenshot
        fullpage_path = await self._take_screenshot(
            f"{self.audit_id}_page{depth}_fullpage.jpg",
            fullpage=True
        )

        # Extract DOM metadata
        dom_metadata = await self._extract_dom_metadata()

        return ScoutResult(
            url=url,
            depth=depth,
            screenshots={
                't0': t0_path,
                't_delay': t_delay_path,
                'fullpage': fullpage_path,
                'scroll': scroll_screenshots
            },
            lazy_loading=lazy_result,
            dom_metadata=dom_metadata,
            status='completed'
        )

    async def _capture_scroll_screenshots(self, max_scrolls: int = 3) -> List[str]:
        """
        Capture screenshots at scroll intervals for lazy-loaded content.

        Returns: List of screenshot paths
        """
        screenshots = []
        scroll_height = 500  # Scroll down by 500px each iteration

        for i in range(max_scrolls):
            # Scroll down
            await self.page.evaluate(f'window.scrollBy(0, {scroll_height})')

            # Wait for lazy loading after scroll
            await self.lazy_detector.wait_for_lazy_loading()

            # Take screenshot
            screenshot_path = await self._take_screenshot(
                f"{self.audit_id}_scroll_{i}.jpg"
            )
            screenshots.append(screenshot_path)

            # Check if we've reached the bottom
            scroll_position = await self.page.evaluate('window.scrollY')
            page_height = await self._evaluate('document.documentElement.scrollHeight')
            if scroll_position > page_height - scroll_height:
                self.logger.info(f"Reached page bottom after {i+1} scrolls")
                break

        # Scroll back to top
        await self.page.evaluate('window.scrollTo(0, 0)')

        return screenshots
```

**Test Strategy:**
- Create test HTML with delayed content loading
- Verify lazy loading detector waits correctly
- Test scroll screenshot capture with infinite scroll page

---

### 3. Multi-Source Validation Gap (HIGH)

**Risk:** Requirement QUAL-01 says "2+ sources must agree before confirming threats" - this changes entire evidence model

**Current State:**
```python
# Current: Vision finds threat, Judge trusts it
vision_findings = await vision_agent.analyze(screenshots,)
security_findings = await security_agent.analyze(url)
# Judge sees findings from both agents, but no multi-source agreement check
```

**New Requirement:**
```python
# New: Vision says "threat", Security says "safe" → Mark as "review_required"
if vision_says_threat and security_says_safe:
    finding.status = "review_required"
    finding.confidence = 50  # Neutral
    finding.notes = "Conflicting findings across agents"
```

**Gap:** This fundamentally changes how findings work:
- Findings need `agent_sources` field (list of agents that found it)
- Findings need `confirmation_sources` field (list of agents that confirmed it)
- Findings need `status` field: "unconfirmed", "confirmed", "verified", "conflicting"

**Solution:** Centralize multi-source validation in Orchestrator

**Implementation Tasks:**
```python
# veritas/core/orchestrator.py (new module: multi_source_validator.py)
from dataclasses import dataclass, field
from typing import List, Dict, Set
from enum import Enum

class FindingStatus(str, Enum):
    """Finding confirmation status."""
    UNCONFIRMED = "unconfirmed"  # Single source only
    CONFIRMED = "confirmed"  # 2+ sources agree
    VERIFIED = "verified"  # All applicable sources agree
    CONFLICTING = "conflicting"  # Sources disagree
    REVIEW_REQUIRED = "review_required"  # Ambiguous, needs human review

@dataclass
class EnhancedFinding:
    """Enhanced finding with multi-source validation."""
    category: str
    sub_type: str
    severity: str
    confidence: float
    bbox: List[int]  # [x, y, width, height]
    description: str
    evidence: dict

    # NEW: Multi-source fields
    agent_sources: List[str] = field(default_factory=list)  # Agents that found it
    confirmation_sources: List[str] = field(default_factory=list)  # Agents that confirmed
    conflicting_sources: List[str] = field(default_factory=list)  # Agents that disagree
    status: FindingStatus = FindingStatus.UNCONFIRMED
    final_confidence: float = 0.0
    verification_notes: List[str] = field(default_factory=list)

class MultiSourceValidator:
    """
    Validates findings across multiple agents using multi-source agreement.

    Implements QUAL-01: Multi-factor validation (2+ sources must agree)
    """

    def __init__(self, min_confirmations: int = 2):
        self.min_confirmations = min_confirmations  # Require 2+ sources
        self.logger = logging.getLogger(__name__)

    def validate_findings(
        self,
        vision_findings: List[EnhancedFinding],
        security_findings: List[EnhancedFinding],
        graph_findings: List[EnhancedFinding],
        scout_findings: List[EnhancedFinding] = None
    ) -> List[EnhancedFinding]:
        """
        Validate findings across multiple agents.

        Returns: Deduplicated and cross-validated findings
        """
        all_findings = {
            'vision': vision_findings,
            'security': security_findings,
            'graph': graph_findings,
            'scout': scout_findings or []
        }

        # Step 1: Group findings by location + category
        finding_groups = self._group_findings_by_location(all_findings)

        # Step 2: For each group, cross-validate
        validated_findings = []
        for group_key, group in finding_groups.items():
            validated = self._validate_finding_group(group FindingGroup)
            validated_findings.append(validated)

        return validated_findings

    def _group_findings_by_location(
        self,
        all_findings: Dict[str, List[EnhancedFinding]]
    ) -> dict:
        """
        Group findings that are at similar location + category.

        Uses fuzzy bbox matching to group findings from different agents.
        """
        groups = {}

        for agent_name, findings in all_findings.items():
            for finding in findings:
                # Create group key from normalized bbox + category
                group_key = self._create_group_key(finding)

                if group_key not in groups:
                    groups[group_key] = FindingGroup(
                        category=finding.category,
                        bbox=finding.bbox,
                        agent_findings={}
                    )

                # Add finding to group
                groups[group_key].add_finding(agent_name, finding)

        return groups

    def _create_group_key(self, finding: EnhancedFinding) -> str:
        """
        Create group key for finding.

        Uses normalized bbox (rounded to 10px) + category.
        """
        # Normalize bbox to 10px granularity
        normalized_bbox = [
            round(b / 10) * 10 for b in finding.bbox
        ]

        return f"{finding.category}_{normalized_bbox}"

    def _validate_finding_group(self, group: 'FindingGroup') -> EnhancedFinding:
        """
        Validate a group of findings from different agents.

        Implements multi-factor validation logic.
        """
        agent_findings = group.agent_findings

        # Count findings per agent
        finding_counts = {agent: len(findings) for agent, findings in agent_findings.items()}
        total_findings = sum(finding_counts.values())

        # Determine status based on agreement level
        agents_with_findings = [agent for agent, count in finding_counts.items() if count > 0]

        if len(agents_with_findings) >= 3:
            # 3+ agents agree = VERIFIED
            status = FindingStatus.VERIFIED
        elif len(agents_with_findings) >= 2:
            # 2 agents agree = CONFIRMED
            status = FindingStatus.CONFIRMED
        elif total_findings > 0:
            # Single agent found it = UNCONFIRMED
            status = FindingStatus.UNCONFIRMED
        else:
            # No findings (shouldn't happen)
            status = FindingStatus.UNCONFIRMED

        # Detect conflicts (different agents reporting different severity levels)
        severities = {
            agent: finding.severity
            for agent, findings in agent_findings.items()
            if findings
        }

        if len(set(severities.values())) > 1:
            status = FindingStatus.CONFLICTING

        # Build final finding
        return EnhancedFinding(
            category=group.category,
            # Use the finding with highest confidence
            **self._get_highest_confidence_finding(group),
            agent_sources=agents_with_findings,
            confirmation_sources=agents_with_findings,
            status=status,
            final_confidence=self._compute_final_confidence(group, status),
            verification_notes=self._generate_verification_notes(group, status)
        )

    def _get_highest_confidence_finding(self, group: 'FindingGroup') -> dict:
        """Get the finding with highest confidence from the group."""
        highest = None
        highest_confidence = 0.0

        for agent, findings in group.agent_findings.items():
            for finding in findings:
                if finding.confidence > highest_confidence:
                    highest_confidence = finding.confidence
                    highest = finding

        return {
            'sub_type': highest.sub_type,
            'severity': highest.severity,
            'confidence': highest.confidence,
            'bbox': highest.bbox,
            'description': highest.description,
            'evidence': highest.evidence
        }

    def _compute_final_confidence(self, group: 'FindingGroup', status: FindingStatus) -> float:
        """
        Compute final confidence based on status and agent agreement.

        Rules:
        - VERIFIED (3+ agents): Confidence boost to 90-100%
        - CONFIRMED (2 agents): Confidence boost to 75-85%
        - UNCONFIRMED (1 agent): Confidence remains as-is (or reduced)
        - CONFLICTING: Neutral confidence (50%)
        """
        highest_confidence = self._get_highest_confidence_finding(group).get('confidence', 0.5)

        if status == FindingStatus.VERIFIED:
            return min(100, highest_confidence + 30)
        elif status == FindingStatus.CONFIRMED:
            return min(100, highest_confidence + 20)
        elif status == FindingStatus.UNCONFIRMED:
            return max(0, highest_confidence - 10)
        elif status == FindingStatus.CONFLICTING:
            return 50.0
        else:
            return highest_confidence

    def _generate_verification_notes(self, group: 'FindingGroup', status: FindingStatus) -> List[str]:
        """Generate notes explaining verification status."""
        notes = []
        agents = list(group.agent_findings.keys())

        if status == FindingStatus.VERIFIED:
            notes.append(f"Verified by {len(agents)} agents: {', '.join(agents)}")
        elif status == FindingStatus.CONFIRMED:
            notes.append(f"Confirmed by {len(agents)} agents: {', '.join(agents)}")
        elif status == FindingStatus.UNCONFIRMED:
            notes.append(f"Reported by single agent: {agents[0] if agents else 'unknown'}")
            notes.append("Requires additional source confirmation")
        elif status == FindingStatus.CONFLICTING:
            notes.append("Conflicting reports from different agents:")
            for agent, findings in group.agent_findings.items():
                if findings:
                    notes.append(f"  - {agent}: severity={findings[0].severity}")

        return notes

@dataclass
class FindingGroup:
    """Group of findings from different agents at similar locations."""
    category: str
    bbox: List[int]
    agent_findings: Dict[str, List[EnhancedFinding]] = field(default_factory=dict)

    def add_finding(self, agent_name: str, finding: EnhancedFinding):
        """Add finding from agent."""
        if agent_name not in self.agent_findings:
            self.agent_findings[agent_name] = []
        self.agent_findings[agent_name].append(finding)

# 7.3.2 Integrate MultiSourceValidator into Orchestrator
# veritas/core/orchestrator.py (modify orchestrator.audit())
class VeritasOrchestrator:
    def __init__(self):
        self.multi_source_validator = MultiSourceValidator(min_confirmations=2)

    async def audit(self, url: str, audit_tier: str = "standard") -> dict:
        """Run audit with multi-source validation."""
        # ... run agents ...

        # Collect findings from all agents
        vision_findings = vision_result.findings
        security_findings = security_result.findings
        graph_findings = graph_result.findings
        scout_findings = []  # Scout doesn't typically generate findings

        # Cross-validate findings
        validated_findings = self.multi_source_validator.validate_findings(
            vision_findings=vision_findings,
            security_findings=security_findings,
            graph_findings=graph_findings,
            scout_findings=scout_findings
        )

        # Pass validated findings to Judge
        state['judge_input']['findings'] = validated_findings

        # ... continue orchestration ...
```

**Test Strategy:**
- Unit test `validate_findings` with 2, 3, 4 agent scenarios
- Test boundary: 1 agent = UNCONFIRMED, 2 agents = CONFIRMED, 3+ agents = VERIFIED
- Test conflict detection with mismatched severity levels

---

### 4. Confidence Scoring Inconsistency Risk (MEDIUM)

**Risk:** Different agents use different confidence scales, making multi-source aggregation difficult

**Current State:**
- Vision: 0-1 float confidence per finding
- Security: severity strings (low/medium/high)
- Graph: verification scores (0-100 int)

**Gap:** Cannot directly compare or aggregate confidences across agents

**Solution:** Normalize all confidences to 0-100 scale before aggregation

**Implementation Tasks:**
```python
# veritas/core/orchestrator.py (new module: confidence_normalizer.py)
class ConfidenceNormalizer:
    """Normalizes confidence scores from different agents to 0-100 scale."""

    def normalize_vision_confidence(self, confidence: float) -> float:
        """Normalize Vision confidence (0-1) to 0-100."""
        return confidence * 100

    def normalize_security_confidence(self, severity: str) -> float:
        """Normalize Security severity (low/medium/high) to 0-100."""
        severity_map = {
            'low': 30,
            'medium': 60,
            'high': 90,
            'critical': 100
        }
        return severity_map.get(severity, 50)

    def normalize_graph_confidence(self, verification_score: int) -> float:
        """Normalize Graph verification score (0-100) to 0-100."""
        return float(verification_score)

    def normalize_agent_findings(self, agent_name: str, findings: List[dict]) -> List[EnhancedFinding]:
        """Normalize findings from agent to EnhancedFinding format."""
        normalized = []

        for finding in findings:
            if agent_name == 'vision':
                norm_conf = self.normalize_vision_confidence(finding.get('confidence', 0.5))
            elif agent_name == 'security':
                norm_conf = self.normalize_security_confidence(finding.get('severity', 'medium'))
            elif agent_name == 'graph':
                norm_conf = self.normalize_graph_confidence(finding.get('verification_score', 50))
            else:
                norm_conf = 50.0  # Default neutral

            normalized.append(EnhancedFinding(
                category=finding.get('category', 'unknown'),
                sub_type=finding.get('sub_type', ''),
                severity=finding.get('severity', 'medium'),
                confidence=norm_conf,
                bbox=finding.get('bbox', []),
                description=finding.get('description', ''),
                evidence=finding.get('evidence', {})
            ))

        return normalized
```

**Test Strategy:**
- Unit test normalizer with all agent types
- Verify 0-1 Vision maps correctly (0.5 → 50)
- Verify severity strings map to expected values (medium → 60)

---

## Dependencies (What Must Complete First)

### Internal (Within Phase 7)
1. **NavigationController → lazy loading detection**: Multi-page flow first, then lazy loading per page
2. **LazyLoadingDetector → scroll screenshots**: Need scroll detection before capturing screenshots
3. **MultiSourceValidator → confidence normalizer**: Normalize before aggregating
4. **Quality foundation → Phase 8**: Vision findings with multi-source validation feed into OSINT verification

### External (From Previous Phases)
1. **Phase 1-5 (v1.0 Core)**: ✅ DONE
2. **Phase 6 (Vision Agent Enhancement)**: Vision findings now include pass-level metadata needed for multi-source validation

### Blocks for Future Phases
1. **Phase 8 (OSINT)**: Graph findings will be integrated into multi-source validation
2. **Phase 9 (Judge System)**: Judge will use validated findings (instead of raw per-agent findings)
3. **Phase 11 (Showcase)**: Screenshot carousel needs scroll screenshots from this phase

---

## Task Breakdown (With File Locations)

### 7.1 Implement NavigationController for Multi-Page Navigation

**Files:**
- `veritas/agents/scout.py` (new module: navigation_controller.py)
- `veritas/config/settings.py` (add MAX_PAGES_PER_AUDIT setting)

**Tasks:**
```python
# veritas/agents/scout/navigation_controller.py (new file)
import logging
from typing import List, Optional, Set, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class NavigationController:
    """Controls multi-page navigation with loop prevention and prioritization."""

    def __init__(
        self,
        max_pages: int = 10,
        max_depth: int = 3,
        same_domain_only: bool = True,
        timeout_per_page: int = 30,
        initial_domain_allowlist: Set[str] = None
    ):
        """
        Initialize navigation controller.

        Args:
            max_pages: Maximum pages to visit per audit
            max_depth: Maximum link depth to follow
            same_domain_only: Only follow links on same domain
            timeout_per_page: Timeout per page load (seconds)
            initial_domain_allowlist: Domains to allow (if same_domain_only=True)
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        self.timeout_per_page = timeout_per_page

        self.visited_urls: Set[str] = set()
        self.url_queue: List[dict] = []
        self.domain_whitelist: Set[str] = initial_domain_allowlist or set()
        self.pagination_patterns: dict = {}  # Track pagination patterns

    def initialize(self, start_url: str):
        """Initialize with starting URL."""
        parsed = urlparse(start_url)
        self.domain_whitelist.add(parsed.netloc)

    def can_visit(self, url: str, current_depth: int) -> Tuple[bool, str]:
        """
        Check if URL can be visited.

        Returns: (can_visit, reason_code)

        Reason codes:
        - 'ok': Can visit
        - 'depth_limit': Exceeded max depth
        - 'page_limit': Exceeded max pages
        - 'already_visited': Already visited
        - 'domain_filter': Domain not in whitelist
        - 'pagination_loop': Detected pagination loop
        """
        # Depth check
        if current_depth > self.max_depth:
            return False, 'depth_limit'

        # Page count check
        if len(self.visited_urls) >= self.max_pages:
            return False, 'page_limit'

        # Deduplication check
        if url in self.visited_urls:
            return False, 'already_visited'

        # Domain check
        if self.same_domain_only:
            parsed = urlparse(url)
            if not any(parsed.netloc.endswith(domain) for domain in self.domain_whitelist):
                return False, 'domain_filter'

        # Pagination loop check
        if self._is_pagination_loop(url):
            return False, 'pagination_loop'

        return True, 'ok'

    def mark_visited(self, url: str) -> None:
        """Mark URL as visited."""
        self.visited_urls.add(url)

    def add_link(self, url: str, depth: int, priority: int = 0) -> None:
        """Add link to visitation queue."""
        self.url_queue.append({
            'url': url,
            'depth': depth,
            'priority': priority
        })
        self.url_queue.sort(key=lambda x: x['priority'], reverse=True)

    def get_next_page(self) -> Optional[dict]:
        """Get next page to visit."""
        if not self.url_queue:
            return None
        return self.url_queue.pop(0)

    def _is_pagination_loop(self, url: str) -> bool:
        """Check if URL matches detected pagination pattern."""
        import re
        for pattern in self.pagination_patterns.values():
            if re.match(pattern, url):
                return True
        return False

    def detect_pagination(self, urls: List[str]) -> None:
        """Detect pagination patterns from URL list."""
        import re
        from collections import Counter

        patterns = [re.sub(r'\d+', '{n}', url) for url in urls]
        counts = Counter(patterns)

        for pattern, count in counts.items():
            if count >= 3:
                logger.info(f"Detected pagination pattern: {pattern}")
                self.pagination_patterns[pattern] = count

# veritas/config/settings.py (add navigation settings)
MAX_PAGES_PER_AUDIT = 10  # For Phase 7
MAX_NAVIGATION_DEPTH = 3
SAME_DOMAIN_ONLY = True
PAGE_LOAD_TIMEOUT = 30
```

---

### 7.2 Implement LazyLoadingDetector

**File:**
- `veritas/agents/scout/lazy_loading_detector.py` (new file)

**Tasks:**
```python
# veritas/agents/scout/lazy_loading_detector.py (new file)
import asyncio
import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)

class LazyLoadingDetector:
    """Detects and handles lazy loading on web pages."""

    DOM_STABILITY_THRESHOLD_MS = 1000
    NETWORK_IDLE_THRESHOLD_MS = 2000
    HEIGHT_STABILITY_THRESHOLD_MS = 2000
    MAX_WAIT_SECONDS = 15

    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.last_height = 0
        self.last_height_change_time = None

    async def wait_for_lazy_loading(self) -> Dict:
        """Wait for lazy-loaded content to stabilize."""
        start_time = time.time()
        start_height = await self._get_height()

        # Try multiple stabilization methods
        for method, checker in [
            ('network_idle', self._wait_network_idle),
            ('height_stable', self._wait_height_stable),
            ('dom_stable', self._wait_dom_stable)
        ]:
            if await checker():
                wait_time = (time.time() - start_time) * 1000
                return {
                    'stabilized': True,
                    'method': method,
                    'wait_time_ms': int(wait_time),
                    'final_height': await self._get_height(),
                    'height_change': await self._get_height() - start_height
                }

        # Timeout
        return {
            'stabilized': False,
            'method': 'timeout',
            'wait_time_ms': int((time.time() - start_time) * 1000),
            'final_height': await self._get_height(),
            'height_change': await self._get_height() - start_height
        }

    async def _get_height(self) -> int:
        """Get page scroll height."""
        return await self.page.evaluate('document.documentElement.scrollHeight')

    async def _wait_network_idle(self) -> bool:
        """Wait for network idle state."""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=self.NETWORK_IDLE_THRESHOLD_MS)
            return True
        except:
            return False

    async def _wait_height_stable(self) -> bool:
        """Wait for page height to stabilize."""
        start = time.time()
        while (time.time() - start) < self.MAX_WAIT_SECONDS:
            current = await self._get_height()
            if current == self.last_height:
                if self.last_height_change_time and (time.time() - self.last_height_change_time) * 1000 >= self.HEIGHT_STABILITY_THRESHOLD_MS:
                    return True
            else:
                self.last_height = current
                self.last_height_change_time = time.time()
            await asyncio.sleep(0.2)
        return False

    async def _wait_dom_stable(self) -> bool:
        """Wait for DOM to stabilize."""
        try:
            await self.page.evaluate('''
                new Promise(resolve => {
                    let lastMutation = Date.now();
                    const observer = new MutationObserver(() => lastMutation = Date.now());
                    observer.observe(document.documentElement, {childList: true, subtree: true});
                    setTimeout(() => {observer.disconnect(); resolve();}, %d);
                })
            ''' % self.DOM_STABILITY_THRESHOLD_MS)
            await asyncio.sleep(self.DOM_STABILITY_THRESHOLD_MS / 1000 * 2)
            return True
        except:
            return False
```

---

### 7.3 Implement MultiSourceValidator

**Files:**
- `veritas/core/orchestrator/multi_source_validator.py` (new file)
- `veritas/core/orchestrator/confidence_normalizer.py` (new file)

**Tasks:**
```python
# veritas/core/orchestrator/multi_source_validator.py (new file)
from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum

logger = logging.getLogger(__name__)

class FindingStatus(str, Enum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    VERIFIED = "verified"
    CONFLICTING = "conflicting"
    REVIEW_REQUIRED = "review_required"

@dataclass
class EnhancedFinding:
    category: str
    sub_type: str
    severity: str
    confidence: float
    bbox: List[int]
    description: str
    evidence: dict

    agent_sources: List[str] = field(default_factory=list)
    confirmation_sources: List[str] = field(default_factory=list)
    status: FindingStatus = FindingStatus.UNCONFIRMED
    final_confidence: float = 0.0
    verification_notes: List[str] = field(default_factory=list)

@dataclass
class FindingGroup:
    category: str
    bbox: List[int]
    agent_findings: Dict[str, List[EnhancedFinding]] = field(default_factory=dict)

    def add_finding(self, agent: str, finding: EnhancedFinding):
        if agent not in self.agent_findings:
            self.agent_findings[agent] = []
        self.agent_findings[agent].append(finding)

class MultiSourceValidator:
    """Validates findings across multiple agents following QUAL-01 requirements."""

    def __init__(self, min_confirmations: int = 2):
        self.min_confirmations = min_confirmations

    def validate(self, all_findings: Dict[str, List[EnhancedFinding]]) -> List[EnhancedFinding]:
        """Validate findings across all agents."""
        # Group findings by location + category
        groups = self._group_findings(all_findings)

        # Validate each group
        validated = [self._validate_group(g) for g in groups.values()]

        return validated

    def _group_findings(self, all_findings: Dict[str, List[EnhancedFinding]]) -> Dict[str, FindingGroup]:
        """Group findings by normalized location + category."""
        groups = {}

        for agent, findings in all_findings.items():
            for finding in findings:
                key = self._group_key(finding)
                if key not in groups:
                    groups[key] = FindingGroup(category=finding.category, bbox=finding.bbox)
                groups[key].add_finding(agent, finding)

        return groups

    def _group_key(self, finding: EnhancedFinding) -> str:
        """Create grouping key from normalized bbox (10px granularity) + category."""
        norm_bbox = [round(b / 10) * 10 for b in finding.bbox]
        return f"{finding.category}_{norm_bbox}"

    def _validate_group(self, group: FindingGroup) -> EnhancedFinding:
        """Validate a finding group."""
        agents_with_findings = [a for a, f in group.agent_findings.items() if f]

        # Determine status
        if len(agents_with_findings) >= 3:
            status = FindingStatus.VERIFIED
        elif len(agents_with_findings) >= 2:
            status = FindingStatus.CONFIRMED
        else:
            status = FindingStatus.UNCONFIRMED

        # Check for conflicts (different severity)
        severities = [f[0].severity for f in group.agent_findings.values() if f]
        if len(set(severities)) > 1:
            status = FindingStatus.CONFLICTING

        # Get highest confidence finding
        base = self._highest_confidence(group)

        return EnhancedFinding(
            category=group.category,
            sub_type=base['sub_type'],
            severity=base['severity'],
            confidence=base['confidence'],
            bbox=group.bbox,
            description=base['description'],
            evidence=base['evidence'],
            agent_sources=agents_with_findings,
            confirmation_sources=agents_with_findings,
            status=status,
            final_confidence=self._final_confidence(base['confidence'], status),
            verification_notes=self._notes(group, status)
        )

    def _highest_confidence(self, group: FindingGroup) -> Dict:
        """Get finding with highest confidence."""
        best = None
        best_conf = 0
        for findings in group.agent_findings.values():
            for f in findings:
                if f.confidence > best_conf:
                    best = f
                    best_conf = f.confidence
        return {
            'sub_type': best.sub_type,
            'severity': best.severity,
            'confidence': best.confidence,
            'description': best.description,
            'evidence': best.evidence
        }

    def _final_confidence(self, base_conf: float, status: FindingStatus) -> float:
        """Compute final confidence from status."""
        boosts = {
            FindingStatus.VERIFIED: 30,
            FindingStatus.CONFIRMED: 20,
            FindingStatus.UNCONFIRMED: -10,
            FindingStatus.CONFLICTING: 50 - base_conf  # Neutralize
        }
        return max(0, min(100, base_conf + boosts[status]))

    def _notes(self, group: FindingGroup, status: FindingStatus) -> List[str]:
        """Generate verification notes."""
        agents = [a for a, f in group.agent_findings.items() if f]
        if status == FindingStatus.VERIFIED:
            return [f"Verified by {len(agents)} agents: {', '.join(agents)}"]
        elif status == FindingStatus.CONFIRMED:
            return [f"Confirmed by {','.join(agents)}"]
        elif status == FindingStatus.CONFLICTING:
            return [f"Conflict: {','.join(a)} report different severity: {[f.severity for f in group.agent_findings.values() if f]}"]
        else:
            return [f"Single source ({agents[0] if agents else 'unknown'}), needs confirmation"]
```

---

### 7.4 Integrate All Components into Enhanced Scout

**File:**
- `veritas/agents/scout.py` (rewrite ScoutAgent)

**Tasks:**
```python
# veritas/agents/scout.py (enhanced ScoutAgent)
class ScoutAgent:
    def __init__(self, nim_client: NIMClient):
        self.nim_client = nim_client
        self.nav_controller = NavigationController(
            max_pages=settings.MAX_PAGES_PER_AUDIT
        )

    async def execute(self, url: str, audit_tier: str) -> List[ScoutResult]:
        """Execute multi-page exploration."""
        self.nav_controller.initialize(url)
        self.nav_controller.add_link(url, depth=0, priority=10)

        results = []
        while len(results) < self.nav_controller.max_pages:
            page_info = self.nav_controller.get_next_page()
            if not page_info:
                break

            url = page_info['url']
            depth = page_info['depth']

            can_visit, reason = self.nav_controller.can_visit(url, depth)
            if not can_visit:
                logger.debug(f"Skip {url}: {reason}")
                continue

            # Navigate and analyze page
            result = await self._analyze_page(url, depth)
            results.append(result)

            self.nav_controller.mark_visited(url)

            # Add linked pages to queue
            self._queue_links(result, url, depth)

        return results

    async def _analyze_page(self, url: str, depth: int) -> ScoutResult:
        """Analyze single page with lazy loading."""
        # Navigate
        await self.page.goto(url, timeout=self.nav_controller.timeout_per_page * 1000)

        # Lazy loading detector
        lazy_detector = LazyLoadingDetector(self.page)

        # Initial screenshot
        await lazy_detector.wait_for_lazy_loading()
        t0_screenshot = await self._screenshot(f"page{depth}_t0")

        # Temporal delay
        await asyncio.sleep(self.temporal_delay)

        # Post-delay capture
        await lazy_detector.wait_for_lazy_loading()
        t_delay_screenshot = await self._screenshot(f"page{depth}_tdelay")

        # Scroll screenshots
        scroll_screenshots = await self._scroll_capture(lazy_detector, depth)

        # Fullpage
        fullpage = await self._screenshot(f"page{depth}_full", fullpage=True)

        # DOM metadata
        dom_meta = await self._extract_dom()

        return ScoutResult(
            url=url,
            depth=depth,
            screenshots={'t0': t0_screenshot, 't_delay': t_delay_screenshot, 'fullpage': fullpage, 'scroll': scroll_screenshots},
            lazy_loading=lazy_detector.wait_result,
            dom_metadata=dom_meta
        )

    async def _scroll_capture(self, lazy_detector: LazyLoadingDetector, depth: int, max_scrolls=3) -> List[str]:
        """Capture scroll screenshots."""
        screenshots = []
        scroll_by = 500

        for i in range(max_scrolls):
            await self.page.evaluate(f'window.scrollBy(0, {scroll_by})')
            await lazy_detector.wait_for_lazy_loading()
            screenshots.append(await self._screenshot(f"page{depth}_scroll{i}"))

            # Check bottom
            pos = await self.page.evaluate('window.scrollY')
            page_height = await self.page.evaluate('document.documentElement.scrollHeight')
            if pos > page_height - scroll_by:
                break

        await self.page.evaluate('window.scrollTo(0, 0)')
        return screenshots

    def _queue_links(self, result: ScoutResult, current_url: str, depth: int):
        """Queue linked pages for navigation."""
        for link in result.dom_metadata.get('links', []):
            if not link.startswith('http'):
                from urllib.parse import urljoin
                link = urljoin(current_url, link)

            # Priority based on keywords
            url_lower = link.lower()
            if any(kw in url_lower for kw in ['about', 'contact', 'privacy']):
                priority = 10
            elif any(kw in url_lower for kw in ['pricing', 'services', 'products']):
                priority = 8
            else:
                priority = 3

            self.nav_controller.add_link(link, depth + 1, priority)
```

---

## Test Strategy

### Unit Tests

**Test: NavigationController loop prevention**
```python
# veritas/tests/test_navigation_controller.py
def test_can_visit_prevents_infinite_loop():
    nav = NavigationController(max_pages=3)

    nav.initialize("http://example.com")
    nav.mark_visited("http://example.com/page1")

    # Same URL rejected
    assert nav.can_visit("http://example.com/page1", 1) == (False, 'already_visited')
```

**Test: LazyLoadingDetector height stabilization**
```python
# veritas/tests/test_lazy_loading.py
@pytest.mark.asyncio
async def test_height_stabilization_works():
    page = MockPage(heights=[1000, 1200, 1400, 1400, 1400])  # Height stabilizes
    detector = LazyLoadingDetector(page)

    result = await detector.wait_for_lazy_loading()

    assert result['stabilized'] == True
    assert result['method'] == 'height_stable'
```

**Test: MultiSourceValidator with 2 agents**
```python
# veritas/tests/test_multi_source_validator.py
def test_two_agent_finding_confirmed():
    validator = MultiSourceValidator(min_confirmations=2)

    findings = {
        'vision': [EnhancedFinding(category='dark_pattern', bbox=[10,10,100,50], confidence=0.8, ...)],
        'security': []
    }
    result = validator.validate(findings)

    assert result[0].status == FindingStatus.UNCONFIRMED  # Only 1 agent

    # Add matching security finding
    findings['security'] = [EnhancedFinding(category='dark_pattern', bbox=[12,12,105,55], confidence=0.7, ...)]
    result = validator.validate(findings)

    assert result[0].status == FindingStatus.CONFIRMED  # 2 agents agree
```

---

### Integration Tests

**Test: Full multi-page exploration**
```python
# veritas/tests/test_integration_multi_page.py
@pytest.mark.asyncio
async def test_multi_page_scout():
    """Scout navigates multiple pages with loop detection."""
    scout = ScoutAgent(mock_nim_client)

    results = await scout.execute("http://test-site.com", audit_tier="standard")

    # Should visit multiple pages
    assert len(results) > 1
    assert all(r.status == 'completed' for r in results)

    # Should handle lazy loading
    assert all(r.lazy_loading['stabilized'] for r in results)
```

---

## Success Criteria (When Phase 7 Is Done)

### Must Have
1. ✅ Scout navigates multiple pages with depth and page limits
2. ✅ Infinite navigation loops detected and prevented
3. ✅ Lazy loading detected across all pages
4. ✅ Multi-source validation requires 2+ agents for confirmation
5. ✅ Per-finding final confidence computed from multiple agents
6. ✅ Findings include agent sources and validation status

### Should Have
1. ✅ Scroll screenshots captured for lazy-loaded content
2. ✅ Smart link selection based on page type (About, Contact, etc.)
3. ✅ Pagination pattern detection prevents infinite loops
4. ✅ Confidence normalization across all agent types
5. ✅ Conflict detection when agents disagree

### Nice to Have
1. ✅ Historical baseline comparison for false positive reduction
2. ✅ "Likely" → "Confirmed" → "Verified" progression display
3. ✅ "Review required" category clearly marked in UI
4. ✅ URL priority scoring for optimal exploration order

---

## Requirements Covered

| Requirement | Status | Notes |
|-------------|--------|-------|
| SCROLL-01 | 📝 Covered | Scroll detection + screenshot series |
| SCROLL-02 | 📝 Covered | Multi-page with depth limits |
| SCROLL-03 | 📝 Covered | Lazy loading detection + waiting |
| QUAL-01 | 📝 Covered | Multi-source validation (2+ agents) |
| QUAL-02 | 📝 Covered | Confidence scoring with reasoning |
| QUAL-03 | 📝 Covered | Status progression (UNCONFIRMED → CONFIRMED → VERIFIED) |

---

*Plan created: 2026-02-23*
*Next phase: Phase 8 (OSINT & CTI Integration)*