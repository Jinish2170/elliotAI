# Plan: Phase 6 - Vision Agent Enhancement

**Phase ID:** 6
**Milestone:** v2.0 Masterpiece Features
**Status:** pending
**Created:** 2026-02-23
**Last Modified:** 2026-02-24 (Refinements applied)

---

## Refinements Applied (2026-02-24)

### 1. Adaptive SSIM Thresholds
- Updated from fixed SSIM_THRESHOLD = 0.3 to content-type-aware thresholds
- `e_commerce`: 0.15 (sensitive - dynamic pricing/inventory)
- `subscription`: 0.20 (moderate - SaaS dynamic features)
- `news/blog`: 0.35 (conservative - mostly static content)
- `phishing/scan`: 0.10 (most sensitive - any change could be malicious)
- `default`: 0.30
- Added `_detect_content_type()` method for automatic content inference from URL and Scout metadata

### 2. 5-Tier Confidence Mapping
- Updated from simple 0-100 score to 5-tier alert system:
  - **low** (<20%): Warning only
  - **moderate** (20-40%): Suspicious
  - **suspicious** (40-60%): Likely problematic
  - **likely** (60-80%): Confirmed
  - **critical** (>80%): Definite dark pattern
- Added `get_confidence_tier()` method for tier computation

---

---

## Context

### Current State (Pre-Phase)

**Vision Agent (`veritas/agents/vision.py`):**
- Single-pass VLM analysis per screenshot
- Basic dark pattern detection categories
- Simple prompt: "Look for dark patterns and UI manipulation"
- No pass-level differentiation or sophisticated prompts
- No temporal analysis (compares t0 and t+delay screenshots via string diff only)
- No cross-reference with external threat intelligence
- Progress events: basic `vision_start` and `vision_complete`

**VLM Integration:**
- NIMClient with 4-level fallback (Primary → Fallback → OCR+Heuristics → Manual)
- Response caching (24h TTL) via disk-based JSON cache
- Rate limiting: 1 call/sec with exponential backoff
- Current call pattern: ~1-2 VLM calls per page (1-2 screenshots)

**Frontend:**
- Basic Agent Theater with phase status cards
- EvidencePanel shows screenshots but no pass-level breakdown
- No "Vision Pass 1/2/3/4/5" indicators

### Goal State (Post-Phase)

**5-Pass Vision Agent:**
- Pass 1: Initial visual scan - quick threat detection (high priority patterns)
- Pass 2: Dark pattern detection - sophisticated UI manipulation patterns
- Pass 3: Temporal dynamics - detect dynamic content changes
- Pass 4: Cross-reference with graph - entity verification against visual findings
- Pass 5: Final synthesis - multi-pass confidence scoring with reasoning chain

**Sophisticated VLM Prompts:**
- 5 pass-specific prompts, each optimized for analysis target
- Iterative prompt engineering with test dataset validation
- Confidence normalization across passes (0-100% with justification)
- **5-tier confidence mapping**: low (<20%), moderate (20-40%), suspicious (40-60%), likely (60-80%), critical (>80%)
- Few-shot examples for each pass type

**Computer Vision Temporal Analysis:**
- SSIM (Structural Similarity Index) for screenshot comparison (scikit-image)
- **Adaptive SSIM thresholds** based on content type (e_commerce: 0.15, subscription: 0.20, news/blog: 0.35, phishing/scan: 0.10, default: 0.30)
- Optical flow for detecting movement/dynamic content changes (opencv-python)
- Screenshot diff with fixed viewport alignment
- Memory monitoring for screenshot resource cleanup (critical for 8GB RAM)
- Async ThreadPoolExecutor for CPU-bound CV operations

**Progress Streaming:**
- WebSocket event streaming for vision pass progress
- Event throttling (max 5/sec) to prevent flooding
- Batch findings for efficient transmission
- Pass-level events: `vision_pass_1_start`, `vision_pass_1_findings`, `vision_pass_1_complete`, etc.

**External Intelligence Verification:**
- Cross-reference visual findings with known threat intel (placeholder for Phase 8 OSINT)
- Verify suspicious elements against known threat patterns
- Real-time fact-checking of observed elements

---

## Critical Implementation Risks (Must Address)

### 1. GPU Cost Explosion (CRITICAL)

**Risk:** 5-pass pipeline × 2-3 screenshots per page = 10-15× current GPU usage

**Current:**
- ~1 VLM call per screenshot
- Typical page: 2 screenshots (t0, t+delay) = 2 VLM calls

**New Phase 6:**
- 5 passes × 2 screenshots = 10 VLM calls per page
- 10-page deep audit = 100 VLM calls per audit
- At ~$0.01-0.02 per VLM call = $1-2 per audit (unsustainable for testing)

**Mitigation Strategy:**
- **Implement aggressive caching**: Hash screenshot pixels + pass type for cache key
- **Skip redundant passes**: If Pass 3 (temporal) finds no changes, skip Pass 2 (dark patterns)
- **Tiered prompts**: Use cheaper models for exploratory passes, expensive only for final synthesis (Pass 5)
- **Pass priority gating**: If Pass 1 finds nothing critical, skip remaining passes (only do Pass 5 for completion)
- **Optimize screenshot count**: Reuse same screenshots across passes instead of retaking

**Implementation Tasks:**
```python
# veritas/agents/vision.py
class VisionPassPriority(enum.Enum):
    """Priority levels for vision passes."""
    CRITICAL = 1   # Always run (Pass 1, Pass 5)
    CONDITIONAL = 2 # Run only if previous pass found threats (Pass 2, Pass 4)
    EXPENSIVE = 3   # Run only if Pass 3 detects changes (Pass 3)

def should_run_pass(pass_num: int, cache_key: str, prior_findings: List[Finding]) -> bool:
    """Determine if a pass should execute based on cost/benefit."""
    # Check cache first
    if cache_hit(cache_key):
        return False

    # Critical passes always run
    if pass_num in [1, 5]:
        return True

    # Conditional passes only run if prior findings exist
    if pass_num in [2, 4] and not prior_findings:
        return False

    # Expensive pass (temporal) only if temporal changes detected
    if pass_num == 3 and not has_temporal_changes:
        return False

    return True
```

**Test Strategy:**
- Monitor VLM call count per audit vs. baseline
- Verify caching hit rate > 60% for repeated URLs
- Test pass skipping logic with mock prior findings

---

### 2. Memory Leak Risk - CV Operations (HIGH)

**Risk:** SSIM/Optical flow on screenshots + Playwright browser + AI models = OOM on 8GB RAM Windows

**Analysis:**
- Screenshot size: ~1920×1080×3 bytes = ~6MB per screenshot
- 3 screenshots (t0, t+delay, full-page) = 18MB base
- SSIM computation: Load 2 screenshots into numpy arrays = 36MB
- Optical flow: Intermediate computation arrays = 50-100MB
- NIM VLM context: ~50MB for image encoding
- Playwright browser: ~200-500MB
- **Total potential: 300-700MB per concurrent page**

**Mitigation Strategy:**
- **Resize screenshots before CV**: Downscale to 640×480 for SSIM/optical flow (sufficient for change detection)
- **Explicit memory cleanup**: Del numpy arrays after use, call `gc.collect()`
- **Memory budgeting**: Track RAM usage, fail-fast if approaching 6GB
- **Sequential CV operations**: Never load more than 2 screenshots simultaneously
- **ThreadPoolExecutor**: Move CPU-bound CV operations off asyncio event loop

**Implementation Tasks:**
```python
# veritas/agents/vision.py (new module: temporal_analysis.py)
import gc
import numpy as np
from PIL import Image
import psutil
import logging

logger = logging.getLogger(__name__)

MAX_RAM_USAGE_GB = 6.0  # Fail-fast threshold
RESIZE_WIDTH = 640
RESIZE_HEIGHT = 480

def get_available_memory_gb() -> float:
    """Get available system memory in GB."""
    return psutil.virtual_memory().available / (1024 ** 3)

def resize_screenshot(image_path: str, save_path: str) -> None:
    """Resize screenshot for CV operations to save memory."""
    with Image.open(image_path) as img:
        resized = img.resize((RESIZE_WIDTH, RESIZE_HEIGHT), Image.LANCZOS)
        resized.save(save_path, 'JPEG', quality=85)

def compute_ssim(img1_path: str, img2_path: str) -> float:
    """
    Compute Structural Similarity Index between two screenshots.

    Returns: 0-1 score (0=identical, 1=completely different)
    """
    # Memory check before loading
    if get_available_memory_gb() < 2.0:
        raise MemoryError(f"Insufficient memory for CV operations: {get_available_memory_gb():.2f}GB available")

    try:
        img1 = np.array(Image.open(img1_path).convert('L'))
        img2 = np.array(Image.open(img2_path).convert('L'))

        # Resize for memory efficiency
        from skimage.transform import resize
        img1_small = resize(img1, (RESIZE_HEIGHT, RESIZE_WIDTH), preserve_range=True).astype(np.uint8)
        img2_small = resize(img2, (RESIZE_HEIGHT, RESIZE_WIDTH), preserve_range=True).astype(np.uint8)

        from skimage.metrics import structural_similarity as ssim
        score = ssim(img1_small, img2_small)

        # Explicit cleanup
        del img1, img2, img1_small, img2_small
        gc.collect()

        return score

    except Exception as e:
        logger.error(f"SSIM computation failed: {e}")
        return 0.5  # Neutral score on failure
```

**Test Strategy:**
- Monitor RAM usage during CV operations with `psutil`
- Test with 10-page sequences watching for memory growth
- Verify `gc.collect()` calls prevent leaks

---

### 3. Pass-Level Event Flooding (MEDIUM)

**Risk:** 5 passes × multiple findings each = 20-30 events, flooding WebSocket

**Current Event Rate:**
- ~2 events per vision phase (start, complete)
- Total audit: ~20-30 events

**New Event Rate (Phase 6):**
- 5 passes × 2-3 events per pass = ~10-15 events per vision phase
- Findings: 1 event per finding discovered per pass (could be 10-20 findings)
- **Potential: 30-50 vision events per page**

**Mitigation Strategy:**
- **Event throttling**: Max 5 events/sec for vision-related events
- **Batch findings**: Batch findings per pass into single event with array
- **Event coalescing**: If multiple findings at same coordinates, merge into single event
- **Drop redundant events**: Don't emit `pass_1_complete` if `pass_2_start` immediately follows

**Implementation Tasks:**
```python
# veritas/agents/vision.py
class VisionEventEmitter:
    """Manages vision-related WebSocket events with throttling."""

    def __init__(self, max_events_per_sec: int = 5):
        self.max_events_per_sec = max_events_per_sec
        self.event_queue: List[dict] = []
        self.last_emit_time = 0.0
        self.batch_size = 5  # Batch up to 5 findings

    async def emit_if_allowed(self, event: dict) -> None:
        """
        Emit event only if rate limit allows.

        If throttled, queue for later emission.
        """
        now = time.time()
        time_since_last = now - self.last_emit_time

        if time_since_last >= (1.0 / self.max_events_per_sec):
            await self._emit(event)
            self.last_emit_time = now
        else:
            self.event_queue.append(event)

    async def flush_queue(self) -> None:
        """Flush accumulated queued events (call at pass completion)."""
        while self.event_queue:
            event = self.event_queue.pop(0)
            await self._emit(event)
            self.last_emit_time = time.time()

    async def batch_findings(self, findings: List[Finding], pass_num: int) -> None:
        """
        Emit batched findings as single event.

        Event structure:
        {
            "type": "vision_pass_findings",
            "pass": pass_num,
            "findings": [finding.to_dict() for finding in findings],
            "count": len(findings),
            "batch": true
        }
        """
        batch = [findings[i:i+self.batch_size] for i in range(0, len(findings), self.batch_size)]

        for batch_item in batch:
            event = {
                "type": "vision_pass_findings",
                "pass": pass_num,
                "findings": [f.to_dict() for f in batch_item],
                "count": len(batch_item),
                "batch": True
            }
            await self.emit_if_allowed(event)
```

**Test Strategy:**
- Mock WebSocket and count events during vision phase
- Verify throttling works under high finding count
- Check event order preservation despite batching

---

### 4. Temporal Analysis Coordination Gap (MEDIUM)

**Risk:** Current Vision expects 2 screenshots (t0, t+delay) but doesn't do CV analysis

**Current State:**
```python
# veritas/agents/vision.py (current)
class VisionAgent:
    async def analyze(self, screenshots: List[str]) -> VisionResult:
        # Single pass through VLM for each screenshot
        findings = []
        for screenshot in screenshots:
            vlm_response = await self.nim_client.analyze_image(
                image=screenshot,
                prompt="Look for dark patterns..."
            )
            findings.extend(self._parse_vlm_response(vlm_response))
        return VisionResult(findings=findings)
```

**Gap:** Uses string comparison of screenshots, not CV-based temporal analysis

**Solution:** Integrate CV temporal analysis before VLM passes

**Implementation Tasks:**
```python
# veritas/agents/vision.py (new module: temporal_coordinator.py)
class TemporalCoordinator:
    """Coordinates temporal analysis with vision passes."""

    async def coordinate_analysis(self, t0_screenshot: str, t_delay_screenshot: str, fullpage_screenshot: str) -> dict:
        """
        Coordinate temporal analysis before vision passes.

        Returns:
            {
                "has_temporal_changes": bool,
                "ssim_score": float,
                "optical_flow_changes": Optional[List[Region]],
                "timing_analysis": dict,
                "screenshots_for_vision": List[str]  # Which screenshots to pass to VLM
            }
        """
        # Step 1: Compute SSIM to detect gross changes
        ssim_score = compute_ssim(t0_screenshot, t_delay_screenshot)

        # Step 2: If SSIM indicates changes, run optical flow for region detection
        optical_flow_changes = None
        if ssim_score > 0.3:  # Threshold for "significant change"
            optical_flow_changes = compute_optical_flow(t0_screenshot, t_delay_screenshot)

        # Step 3: Determine which screenshots deserve full VLM analysis
        screenshots_for_vision = []
        if optical_flow_changes is not None:
            # Dynamic content detected - all screenshots need analysis
            screenshots_for_vision = [t0_screenshot, t_delay_screenshot, fullpage_screenshot]
            has_temporal_changes = True
        else:
            # Static page - analyze only fullpage screenshot
            screenshots_for_vision = [fullpage_screenshot]
            has_temporal_changes = False

        return {
            "has_temporal_changes": has_temporal_changes,
            "ssim_score": ssim_score,
            "optical_flow_changes": optical_flow_changes,
            "screenshots_for_vision": screenshots_for_vision
        }

    async def run_vision_passes_with_temporal_context(
        self,
        screenshots: List[str],
        temporal_result: dict,
        emitter: VisionEventEmitter
    ) -> VisionResult:
        """Run 5-pass vision analysis using temporal context."""
        all_findings = []

        for pass_num in range(1, 6):
            # Check if pass should run (cost optimization)
            cache_key = self._get_cache_key(screenshots, pass_num)
            if not should_run_pass(pass_num, cache_key, all_findings):
                continue

            # Emit pass start
            await emitter.emit_if_allowed({
                "type": "vision_pass_start",
                "pass": pass_num,
                "description": self._get_pass_description(pass_num),
                "screenshots": len(screenshots)
            })

            # Select appropriate prompt for this pass
            prompt = self._get_pass_prompt(pass_num, temporal_result)

            # Run VLM on all applicable screenshots
            pass_findings = []
            for screenshot in screenshots:
                vlm_response = await self.nim_client.analyze_image(
                    image=screenshot,
                    prompt=prompt
                )
                pass_findings.extend(self._parse_vlm_response(vlm_response, pass_num))

            all_findings.extend(pass_findings)

            # Batch emit findings
            await emitter.batch_findings(pass_findings, pass_num)

            # Emit pass completion
            await emitter.emit_if_allowed({
                "type": "vision_pass_complete",
                "pass": pass_num,
                "findings_count": len(pass_findings),
                "confidence": self._compute_confidence(pass_findings)
            })

        return VisionResult(findings=all_findings, passes_completed=5)
```

**Test Strategy:**
- Unit test `should_run_pass` with cache hits and prior finding scenarios
- Integration test with mock VLM responses for each pass
- End-to-end test with real screenshots to verify pass sequencing

---

### 5. External Intelligence Verification Gap (LOW)

**Risk:** Requirement SMART-VIS-01 wants cross-referencing with external threat intel, but Phase 8 (OSINT) hasn't run yet

**Current State:** Vision runs independently, no external verification

**Gap:** Pass 4 wants to "cross-reference with graph" but Graph Investigator (Phase 8) hasn't gathered OSINT data yet

**Solution:** Implement placeholder for Phase 8 integration

**Implementation Tasks:**
```python
# veritas/agents/vision.py (pass 4 placeholder)
def _cross_reference_findings(self, findings: List[Finding]) -> List[Finding]:
    """
    Cross-reference visual findings with intelligence sources.

    NOTE: Full implementation in Phase 8 (OSINT Integration).
    This phase implements placeholder structure.

    Args:
        findings: Findings from initial passes

    Returns:
        Findings with external verification flags
    """
    # Placeholder for Phase 8 integration
    for finding in findings:
        finding.verified_externally = False
        finding.external_sources = []  # Will be populated in Phase 8
        finding.confidence_adjusted = finding.confidence  # No adjustment yet

    return findings
```

**Test Strategy:**
- Mock external verification to verify structure works
- Ensure placeholder doesn't break pass sequencing
- Verify flags are set correctly for Phase 8 consumption

---

## Dependencies (What Must Complete First)

### Internal (Within Phase 6)
1. **VLM caching → Pass priority logic**: Cache must exist before pass skipping works
2. **Temporal coordinator → Vision pass execution**: Temporal analysis determines which screenshots pass to VLM
3. **Event emitter → Frontend update**: Vision events must structure correctly before frontend can display

### External (From Previous Phases)
1. **Phase 1-5 (v1.0 Core)**: Stable IPC, state management - ✅ DONE
2. **NIMClient 4-level fallback**: Already exists, will be reused with enhanced caching

### Blocks for Future Phases
1. **Phase 7 (Quality Foundation)**: Vision findings will feed into multi-source validation
2. **Phase 8 (OSINT)**: Pass 4 cross-reference will be enhanced with real OSINT data
3. **Phase 11 (Showcase)**: Vision pass-level events enable Agent Theater breakdown

---

## Task Breakdown (With File Locations)

### 6.1 Implement VLM Caching with Pass-Level Keys

**Files:**
- `veritas/core/nim_client.py` (extend existing cache)
- `veritas/agents/vision.py` (new caching logic)

**Tasks:**
```python
# 6.1.1 Extend NIM cache key to include pass type
def get_cache_key(image_path: str, prompt: str, pass_type: int) -> str:
    """
    Generate cache key including pass type for pass-specific caching.

    Key format: md5(image_bytes + prompt + pass_type)
    """
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    key_data = image_bytes + prompt.encode() + str(pass_type).encode()
    return hashlib.md5(key_data).hexdigest()

# 6.1.2 Implement cache-aware vision pass execution
async def run_pass_with_cache(pass_num: int, screenshot: str, prompt: str) -> Finding:
    cache_key = get_cache_key(screenshot, prompt, pass_num)
    cached = self.nim_client.get_from_cache(cache_key)

    if cached:
        logger.info(f"Cache hit for Pass {pass_num}")
        return Finding.from_dict(cached)

    # Execute VLM call
    vlm_response = await self.nim_client.analyze_image(screenshot, prompt)
    finding = self._parse_vlm_response(vlm_response)

    # Cache result
    self.nim_client.write_to_cache(cache_key, finding.to_dict(), ttl=86400)

    return finding
```

---

### 6.2 Implement Pass Priority Logic

**Files:**
- `veritas/agents/vision.py` (new class: VisionPassPriority)

**Tasks:**
```python
# 6.2.1 Define pass priority enum
class VisionPassPriority(enum.Enum):
    CRITICAL = 1      # Always run: Pass 1 (quick threat), Pass 5 (final synthesis)
    CONDITIONAL = 2   # Run if prior findings: Pass 2 (dark patterns), Pass 4 (cross-reference)
    EXPENSIVE = 3     # Run only if temporal changes: Pass 3 (temporal dynamics)

# 6.2.2 Implement pass skipping logic
def should_run_pass(pass_num: int, prior_findings: List[Finding], has_temporal_changes: bool) -> bool:
    """Determine if pass should execute based on cost/benefit."""
    pass_priority = {
        1: VisionPassPriority.CRITICAL,
        2: VisionPassPriority.CONDITIONAL,
        3: VisionPassPriority.EXPENSIVE,
        4: VisionPassPriority.CONDITIONAL,
        5: VisionPassPriority.CRITICAL
    }[pass_num]

    if pass_priority == VisionPassPriority.CRITICAL:
        return True
    elif pass_priority == VisionPassPriority.CONDITIONAL:
        return len(prior_findings) > 0
    elif pass_priority == VisionPassPriority.EXPENSIVE:
        return has_temporal_changes
```

---

### 6.3 Implement 5 Pass-Specific VLM Prompts

**Files:**
- `veritas/config/dark_patterns.py` (extend existing prompts)
- `veritas/agents/vision.py` (new prompt selection logic)

**Tasks:**
```python
# 6.3.1 Define 5 pass-specific prompts
VISION_PASS_PROMPTS = {
    1: """
    ANNOTATE ALL DARK PATTERN REGIONS you detect.

    For each region, return:
    - bbox: [x, y, width, height] coordinates (0-100 scale)
    - type: one of: countdown_timer, fake_urgency, forced_comparison, social_proof, confirmshaming
    - severity: low/medium/high based on prominence

    Focus on HIGH-PRIORITY patterns: countdowns, fake urgency countdowns, countdown banners.

    Be QUICK and PRECISE. Mark obvious patterns only.
    """,

    2: """
    Perform SOPHISTICATED DARK PATTERN DETECTION.

    For each region, return:
    - bbox: [x, y, width, height] coordinates (0-100 scale)
    - type: specific dark pattern type (see taxonomy below)
    - technique: psychological technique used (urgency, scarcity, social proof, misdirection)
    - confidence: 0-100 based on detection certainty

    DARK PATTERN TAXONOMY:
    - Urgency: fake countdowns, limited time offers, "only X left"
    - Scarcity: fake low inventory, "selling fast", "almost gone"
    - Social Proof: fake reviews, fabricated testimonials, inflated user counts
    - Misdirection: deceptive action buttons, hidden terms, confusing layouts
    - Obstruction: difficult cancellation, confirmshaming, hard-to-close modals

    Be THOROUGH and NUANCED. Detection subtle psychological manipulation.
    """,

    3: """
    Detect TEMPORAL DYNAMIC CONTENT changes.

    Compare this screenshot to previous screenshot (not shown here, but assume you have context).

    Return regions that CHANGED between screenshots:
    - bbox: [x, y, width, height] coordinates (0-100 scale)
    - change_type: content_update, timer_change, element_appear, element_disappear
    - severity: low/medium/high based on suspicion level

    Focus on SUSPICIOUS temporal changes:
    - Countdown timers that reset or change value unexpectedly
    - Price changes during user session
    - Elements that appear/disappear without user action
    - Timer banners that move or switch content

    Be ALERT to temporal manipulation tactics.
    """,

    4: """
    Cross-reference VISUAL FINDINGS with ENTITY VERIFICATION.

    This pass will be enhanced with OSINT data in Phase 8. For now:

    Identify visual elements that require EXTERNAL VERIFICATION:
    - Company logos or brand names
    - Trust badges (SSL certified, verified by X)
    - Certifications or accreditations
    - Social media handles or icons
    - Third-party endorsements

    Return regions and their visual evidence:
    - bbox: [x, y, width, height] coordinates (0-100 scale)
    - entity_type: company, brand, certification, social_media
    - visual_text: any text visible in the region
    - verification_needed: true

    These regions will be cross-referenced with WHOIS, DNS, and threat intel in Phase 8.
    """,

    5: """
    Synthesize ALL PASSES into final confidence scoring.

    Review findings from all previous passes (you have access to their results).

    For each finding:
    - Provide overall confidence score (0-100)
    - Justification: why this finding is credible
    - Risk level: low/medium/high based on pattern type and prominence
    - Evidence supporting this finding

    Also identify PATTERNS that might be FALSE POSITIVES:
    - Legitimate countdown timers for auctions or limited-time events
    - Genuine scarcity indicators (actual inventory limits)
    - Real social proof (verified reviews)

    Return final adjudicated findings with confidence scores.
    """
}

# 6.3.2 Implement prompt selection
def get_pass_prompt(pass_num: int, temporal_result: dict) -> str:
    """Get appropriate prompt for pass number, injecting temporal context."""
    base_prompt = VISION_PASS_PROMPTS[pass_num]

    # Inject temporal context into Pass 3
    if pass_num == 3:
        temporal_context = f"""
        TEMPORAL CONTEXT:
        - SSIM score: {temporal_result['ssim_score']}
        - Has temporal changes: {temporal_result['has_temporal_changes']}
        """
        return base_prompt + temporal_context

    return base_prompt
```

---

### 6.4 Implement Computer Vision Temporal Analysis

**Files:**
- `veritas/agents/vision.py` (new module: temporal_analysis.py)
- `veritas/requirements.txt` (add: scikit-image, opencv-python)

**Tasks:**
```python
# 6.4.1 Create temporal_analysis module
# veritas/agents/vision/temporal_analysis.py (new file)

import gc
import numpy as np
from PIL import Image
from skimage.transform import resize
from skimage.metrics import structural_similarity as ssim
import psutil
import logging

logger = logging.getLogger(__name__)

class TemporalAnalyzer:
    """Computer vision-based temporal analysis for detecting dynamic content changes."""

    RESIZE_WIDTH = 640
    RESIZE_HEIGHT = 480
    OPTICAL_FLOW_THRESHOLD = 0.5  # Threshold for flow magnitude

    # Adaptive SSIM thresholds based on content type (lower = more sensitive)
    SSIM_THRESHOLDS = {
        'e_commerce': 0.15,      # E-commerce has dynamic pricing/inventory
        'subscription': 0.20,     # SaaS pages show dynamic features
        'news/blog': 0.35,        # Static content, higher threshold
        'phishing/scan': 0.10,    # Any change could be malicious
        'default': 0.30
    }

    def __init__(self, content_type: str = 'default'):
        self.content_type = content_type
        self._check_memory_budget()

    @property
    def SSIM_THRESHOLD(self) -> float:
        """Get content-type-appropriate SSIM threshold."""
        return self.SSIM_THRESHOLDS.get(self.content_type, self.SSIM_THRESHOLDS['default'])

    def _check_memory_budget(self):
        """Ensure sufficient memory for CV operations."""
        available_gb = psutil.virtual_memory().available / (1024 ** 3)
        if available_gb < 2.0:
            raise MemoryError(f"Insufficient memory for CV operations: {available_gb:.2f}GB available")

    def _load_and_resize(self, image_path: str) -> np.ndarray:
        """Load image and resize for memory efficiency."""
        with Image.open(image_path) as img:
            img_array = np.array(img.convert('L'))
            return resize(img_array, (self.RESIZE_HEIGHT, self.RESIZE_WIDTH), preserve_range=True).astype(np.uint8)

    def compute_ssim(self, img1_path: str, img2_path: str) -> float:
        """
        Compute Structural Similarity Index between two screenshots.

        Returns: 0-1 score where 1=identical, 0=completely different
        """
        try:
            # Load and resize images
            img1 = self._load_and_resize(img1_path)
            img2 = self._load_and_resize(img2_path)

            # Compute SSIM
            score = ssim(img1, img2)

            # Explicit cleanup
            del img1, img2
            gc.collect()

            return score

        except Exception as e:
            logger.error(f"SSIM computation failed: {e}")
            return 0.5  # Neutral score on failure

    def compute_optical_flow(self, img1_path: str, img2_path: str) -> List[dict]:
        """
        Compute optical flow to detect region-level changes.

        Returns: List of changed regions with bbox coordinates
        """
        try:
            import cv2

            # Load images
            img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

            # Resize for performance
            img1 = cv2.resize(img1, (self.RESIZE_WIDTH, self.RESIZE_HEIGHT))
            img2 = cv2.resize(img2, (self.RESIZE_WIDTH, self.RESIZE_HEIGHT))

            # Compute optical flow (Farneback method)
            flow = cv2.calcOpticalFlowFarneback(
                img1, img2, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )

            # Compute flow magnitude
            magnitude = np.linalg.norm(flow, axis=2)

            # Find regions with significant flow
            flow_mask = magnitude > self.OPTICAL_FLOW_THRESHOLD

            if not np.any(flow_mask):
                # No significant flow detected
                return []

            # Find contours of changed regions
            contours, _ = cv2.findContours(
                flow_mask.astype(np.uint8),
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            # Convert contours to bbox regions
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Convert from 640x480 to original screenshot size (assumed 1920x1080)
                scale_x = 1920 / self.RESIZE_WIDTH
                scale_y = 1080 / self.RESIZE_HEIGHT
                regions.append({
                    'bbox': [int(x * scale_x), int(y * scale_y), int(w * scale_x), int(h * scale_y)],
                    'flow_magnitude': np.mean(magnitude[flow_mask])
                })

            # Cleanup
            del img1, img2, flow, magnitude, flow_mask
            gc.collect()

            return regions

        except ImportError:
            logger.warning("OpenCV not available, skipping optical flow")
            return []
        except Exception as e:
            logger.error(f"Optical flow computation failed: {e}")
            return []

    def analyze_temporal_changes(self, t0_screenshot: str, t_delay_screenshot: str) -> dict:
        """
        Analyze temporal changes between two screenshots.

        Returns:
            {
                'has_changes': bool,
                'ssim_score': float,
                'changed_regions': List[dict],
                'recommendation': 'analyze_all' | 'fullpage_only'
            }
        """
        # Compute SSIM
        ssim_score = self.compute_ssim(t0_screenshot, t_delay_screenshot)

        # Determine if substantial changes exist
        has_changes = ssim_score > self.SSIM_THRESHOLD

        # If significant changes, compute optical flow for region detection
        changed_regions = []
        if has_changes:
            changed_regions = self.compute_optical_flow(t0_screenshot, t_delay_screenshot)

        # Make recommendation for VLM analysis
        if len(changed_regions) > 0:
            recommendation = 'analyze_all'  # Dynamic content detected
        else:
            recommendation = 'fullpage_only'  # Static page

        return {
            'has_changes': has_changes,
            'ssim_score': ssim_score,
            'changed_regions': changed_regions,
            'recommendation': recommendation
        }

# 6.4.2 Integrate temporal analyzer into VisionAgent
# veritas/agents/vision.py (modify existing VisionAgent)
class VisionAgent:
    def __init__(self, nim_client: NIMClient):
        self.nim_client = nim_client
        self.temporal_analyzer = TemporalAnalyzer()  # New
        self.event_emitter = VisionEventEmitter()   # New
```

**Requirements Update:**
```bash
# veritas/requirements.txt
# Add CV dependencies
scikit-image>=0.21.0
opencv-python>=4.8.0
```

---

### 6.5 Implement Vision Event Emitter for Progress Streaming

**Files:**
- `veritas/agents/vision.py` (new class: VisionEventEmitter)
- `frontend/src/lib/types.ts` (extend AuditEvent types)

**Tasks:**
```python
# 6.5.1 Create VisionEventEmitter class
class VisionEventEmitter:
    """Manages vision-related WebSocket events with throttling and batching."""

    def __init__(self, max_events_per_sec: int = 5, batch_size: int = 5):
        self.max_events_per_sec = max_events_per_sec
        self.batch_size = batch_size
        self.event_queue: List[dict] = []
        self.last_emit_time = 0.0
        self.logger = logging.getLogger(__name__)

    async def emit_vision_start(self, total_screenshots: int) -> None:
        """Emit vision analysis start event."""
        await self._emit({
            "type": "vision_start",
            "screenshots": total_screenshots,
            "passes": 5
        })

    async def emit_pass_start(self, pass_num: int, description: str, screenshots_in_pass: int) -> None:
        """Emit vision pass start event."""
        await self._emit({
            "type": "vision_pass_start",
            "pass": pass_num,
            "description": description,
            "screenshots": screenshots_in_pass
        })

    async def emit_pass_findings(self, pass_num: int, findings: List[Finding]) -> None:
        """Emit findings for a pass (batched)."""
        if not findings:
            return

        # Batch findings
        batches = [findings[i:i+self.batch_size] for i in range(0, len(findings), self.batch_size)]

        for batch in batches:
            event = {
                "type": "vision_pass_findings",
                "pass": pass_num,
                "findings": [f.to_dict() for f in batch],
                "count": len(batch),
                "batch": True
            }
            await self._emit(event)

    async def emit_pass_complete(self, pass_num: int, findings_count: int, confidence: float) -> None:
        """Emit vision pass complete event."""
        await self._emit({
            "type": "vision_pass_complete",
            "pass": pass_num,
            "findings_count": findings_count,
            "confidence": confidence
        })

    async def emit_vision_complete(self, total_findings: int, passes_completed: int) -> None:
        """Emit vision analysis complete event."""
        await self._emit({
            "type": "vision_complete",
            "total_findings": total_findings,
            "passes_completed": passes_completed
        })

    async def _emit(self, event: dict) -> None:
        """Emit event with rate limiting."""
        now = time.time()
        time_since_last = now - self.last_emit_time
        min_interval = 1.0 / self.max_events_per_sec

        if time_since_last >= min_interval:
            await self._do_emit(event)
            self.last_emit_time = now
        else:
            self.logger.debug(f"Throttled event: {event['type']}")
            self.event_queue.append(event)

    async def _do_emit(self, event: dict) -> None:
        """Actually emit event via orchestrator's progress emitter."""
        # Use existing NIMClient progress mechanism
        # This will be converted to WebSocket by backend
        print(f"##PROGRESS:{json.dumps(event)}", flush=True)

    async def flush_queue(self) -> None:
        """Flush accumulated queued events."""
        while self.event_queue:
            event = self.event_queue.pop(0)
            await self._do_emit(event)
            self.last_emit_time = time.time()

# 6.5.2 Extend frontend AuditEvent types
# frontend/src/lib/types.ts
export interface VisionPassStartEvent {
  type: 'vision_pass_start';
  pass: number;
  description: string;
  screenshots: number;
}

export interface VisionPassFindingsEvent {
  type: 'vision_pass_findings';
  pass: number;
  findings: Finding[];
  count: number;
  batch: boolean;
}

export interface VisionPassCompleteEvent {
  type: 'vision_pass_complete';
  pass: number;
  findings_count: number;
  confidence: number;
}

export type AuditEvent =
  | PhaseStartEvent
  | PhaseCompleteEvent
  | FindingEvent
  | ScreenshotEvent
  | VisionPassStartEvent        // New
  | VisionPassFindingsEvent     // New
  | VisionPassCompleteEvent     // New
  | AuditResultEvent
  | AuditCompleteEvent;

# 6.5.3 Extend frontend store to handle vision pass events
# frontend/src/lib/store.ts (extend useAuditStore)
handleEvent(event: AuditEvent) {
  switch (event.type) {
    // ... existing cases ...
    case 'vision_pass_start':
      this.updatePhase('vision', { activePass: event.pass });
      break;
    case 'vision_pass_findings':
      this.addFindings(event.findings);
      break;
    case 'vision_pass_complete':
      this.updatePhase('vision', {
        completedPasses: [...(get().phases['vision']?.completedPasses || []), event.pass]
      });
      break;
  }
}
```

---

### 6.6 Integrate All Components into Enhanced VisionAgent

**Files:**
- `veritas/agents/vision.py` (rewrite VisionAgent.analyze() method)

**Tasks:**
```python
class VisionAgent:
    """Enhanced Vision Agent with 5-pass pipeline and temporal analysis."""

    def __init__(self, nim_client: NIMClient):
        self.nim_client = nim_client
        self.event_emitter = VisionEventEmitter()

    def _detect_content_type(self, url: str, scout_result: ScoutResult = None) -> str:
        """
        Detect content type from URL and Scout metadata for adaptive SSIM thresholds.

        Args:
            url: Page URL
            scout_result: Scout result with metadata

        Returns:
            Content type key: 'e_commerce', 'subscription', 'news/blog', 'phishing/scan', or 'default'
        """
        url_lower = url.lower()

        # E-commerce indicators
        e_commerce_patterns = [
            'shop', 'store', 'buy', 'cart', 'checkout', 'order',
            'amazon', 'ebay', 'etsy', 'shopify', 'walmart', 'target'
        ]
        if any(pattern in url_lower for pattern in e_commerce_patterns):
            return 'e_commerce'

        # Subscription/SaaS indicators
        subscription_patterns = [
            'subscrib', 'plan', 'pricing', 'saas', 'trial', 'signup',
            'notion', 'slack', 'zoom', 'github', 'figma', 'adobe'
        ]
        if any(pattern in url_lower for pattern in subscription_patterns):
            return 'subscription'

        # Phishing/scan indicators (from Scout phase results)
        if scout_result and hasattr(scout_result, 'risk'):
            if scout_result.risk >= 0.7:  # High risk pages get sensitive threshold
                return 'phishing/scan'

        # News/blog indicators
        news_patterns = [
            'news', 'blog', 'article', 'post', 'journal', 'medium',
            'substack', 'dev.to', 'wordpress'
        ]
        if any(pattern in url_lower for pattern in news_patterns):
            return 'news/blog'

        return 'default'

    async def analyze(self, screenshots: List[str], scout_result: ScoutResult = None) -> VisionResult:
        """
        Perform 5-pass vision analysis on screenshots.

        Args:
            screenshots: List of screenshot paths from Scout
            scout_result: Scout result with URL metadata

        Returns:
            VisionResult with findings from all passes
        """
        await self.event_emitter.emit_vision_start(len(screenshots))

        all_findings = []

        # Step 0: Detect content type for adaptive SSIM thresholds
        url = scout_result.url if scout_result and hasattr(scout_result, 'url') else ''
        content_type = self._detect_content_type(url, scout_result)
        logger.info(f"Detected content type: {content_type}")

        # Initialize TemporalAnalyzer with content-type-specific thresholds
        self.temporal_analyzer = TemporalAnalyzer(content_type=content_type)

        # Step 1: Temporal analysis (if multiple screenshots)
        temporal_result = None
        has_temporal_changes = False

        if len(screenshots) >= 2 and scout_result:
            # Analyze t0 and t+delay screenshots
            temporal_result = self.temporal_analyzer.analyze_temporal_changes(
                screenshots[0],  # t0
                screenshots[1]   # t+delay
            )
            has_temporal_changes = temporal_result['has_changes']
            logger.info(f"Temporal analysis: SSIM={temporal_result['ssim_score']:.3f}, changes={has_temporal_changes}")

        # Step 2: Determine which screenshots to analyze
        if temporal_result and temporal_result['recommendation'] == 'fullpage_only':
            screenshots_to_analyze = [screenshots[-1]]  # Use fullpage only
        else:
            screenshots_to_analyze = screenshots  # Analyze all

        # Step 3: Run 5-pass analysis
        passes_completed = 0
        for pass_num in range(1, 6):
            # Check if pass should run (cost optimization)
            if not self._should_run_pass(pass_num, all_findings, has_temporal_changes):
                logger.debug(f"Skipping Pass {pass_num}")
                continue

            # Emit pass start
            description = self._get_pass_description(pass_num)
            await self.event_emitter.emit_pass_start(pass_num, description, len(screenshots_to_analyze))

            # Get pass-specific prompt
            prompt = self._get_pass_prompt(pass_num, temporal_result)

            # Run VLM on all applicable screenshots
            pass_findings = []
            for screenshot in screenshots_to_analyze:
                # Check cache
                cache_key = self._get_cache_key(screenshot, prompt, pass_num)
                cached = self.nim_client.get_from_cache(cache_key)

                if cached:
                    logger.debug(f"Cache hit for Pass {pass_num}")
                    pass_findings.extend([Finding.from_dict(cached)])
                    continue

                # Execute VLM
                vlm_response = await self.nim_client.analyze_image(
                    image=screenshot,
                    prompt=prompt
                )

                # Parse response
                findings_from_pass = self._parse_vlm_response(vlm_response, pass_num)
                pass_findings.extend(findings_from_pass)

                # Cache results
                for finding in findings_from_pass:
                    self.nim_client.write_to_cache(
                        self._get_cache_key(screenshot, prompt, pass_num),
                        finding.to_dict(),
                        ttl=86400
                    )

            # Deduplicate findings within pass
            pass_findings = self._deduplicate_findings(pass_findings)

            all_findings.extend(pass_findings)

            # Emit findings and pass completion
            await self.event_emitter.emit_pass_findings(pass_num, pass_findings)
            confidence = self._compute_confidence(pass_findings) if pass_findings else 0.0
            await self.event_emitter.emit_pass_complete(pass_num, len(pass_findings), confidence)

            passes_completed += 1

        # Step 4: Cross-reference Findings (placeholder for Phase 8)
        all_findings = self._cross_reference_findings(all_findings)

        # Step 5: Flush event queue
        await self.event_emitter.flush_queue()

        # Step 6: Emit vision complete
        await self.event_emitter.emit_vision_complete(len(all_findings), passes_completed)

        return VisionResult(
            findings=all_findings,
            passes_completed=passes_completed,
            temporal_analysis=temporal_result
        )

    def _should_run_pass(self, pass_num: int, prior_findings: List[Finding], has_temporal_changes: bool) -> bool:
        """Determine if pass should execute based on cost/benefit."""
        pass_priority = {
            1: VisionPassPriority.CRITICAL,
            2: VisionPassPriority.CONDITIONAL,
            3: VisionPassPriority.EXPENSIVE,
            4: VisionPassPriority.CONDITIONAL,
            5: VisionPassPriority.CRITICAL
        }[pass_num]

        if pass_priority == VisionPassPriority.CRITICAL:
            return True
        elif pass_priority == VisionPassPriority.CONDITIONAL:
            return len(prior_findings) > 0
        elif pass_priority == VisionPassPriority.EXPENSIVE:
            return has_temporal_changes
        return True

    def _get_pass_description(self, pass_num: int) -> str:
        """Get human-readable description for pass."""
        descriptions = {
            1: "Quick visual scan for obvious threats",
            2: "Sophisticated dark pattern detection",
            3: "Temporal dynamics and dynamic content",
            4: "Cross-reference with external intelligence",
            5: "Final synthesis and confidence scoring"
        }
        return descriptions[pass_num]

    def _get_pass_prompt(self, pass_num: int, temporal_result: dict) -> str:
        """Get appropriate prompt for pass number."""
        from veritas.config.dark_patterns import VISION_PASS_PROMPTS
        base_prompt = VISION_PASS_PROMPTS[pass_num]

        # Inject temporal context for Pass 3
        if pass_num == 3 and temporal_result:
            return f"{base_prompt}\n\nTEMPORAL CONTEXT:\n- SSIM score: {temporal_result.get('ssim_score', 0):.3f}\n- Has changes: {temporal_result.get('has_changes', False)}\n- Changed regions: {len(temporal_result.get('changed_regions', []))}"

        return base_prompt

    def _get_cache_key(self, screenshot: str, prompt: str, pass_num: int) -> str:
        """Generate cache key for VLM response."""
        import hashlib
        with open(screenshot, 'rb') as f:
            image_bytes = f.read()
        key_data = image_bytes + prompt.encode() + str(pass_num).encode()
        return hashlib.md5(key_data).hexdigest()

    def _parse_vlm_response(self, vlm_response: dict, pass_num: int) -> List[Finding]:
        """Parse VLM response into Finding objects."""
        findings = []

        # VLM returns JSON with 'regions' array
        # Each region has: bbox, type, severity, confidence
        for region in vlm_response.get('regions', []):
            finding = Finding(
                category=region.get('type', 'unknown'),
                sub_type=f"pass_{pass_num}",
                severity=region.get('severity', 'medium'),
                confidence=region.get('confidence', 0.5),
                bbox=region.get('bbox', []),
                description=region.get('description', ''),
                evidence={'pass': pass_num, 'vlm_response': region}
            )
            findings.append(finding)

        return findings

    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Deduplicate findings by bbox + category."""
        seen = {}
        unique = []

        for finding in findings:
            key = (tuple(finding.bbox), finding.category)
            if key not in seen:
                seen[key] = finding
                unique.append(finding)

        return unique

    def _compute_confidence(self, findings: List[Finding]) -> float:
        """Compute confidence score for findings (0-100)."""
        if not findings:
            return 0.0
        return sum(f.confidence for f in findings) / len(findings) * 100

    def get_confidence_tier(self, confidence_score: float) -> str:
        """
        Map confidence score to 5-tier alert level.

        Args:
            confidence_score: Score from 0-100

        Returns:
            One of: 'low', 'moderate', 'suspicious', 'likely', 'critical'
        """
        CONFIDENCE_TIERS = {
            (0, 20): 'low',          # Warning only
            (20, 40): 'moderate',    # Suspicious
            (40, 60): 'suspicious',  # Likely problematic
            (60, 80): 'likely',      # Confirmed
            (80, 100): 'critical'    # Definite dark pattern
        }

        for (min_val, max_val), tier in CONFIDENCE_TIERS.items():
            if min_val <= confidence_score < max_val:
                return tier
        if confidence_score >= 100:
            return 'critical'
        return 'low'  # Fallback for edge cases

    def _cross_reference_findings(self, findings: List[Finding]) -> List[Finding]:
        """Cross-reference findings with external intelligence (placeholder)."""
        # Placeholder for Phase 8 OSINT integration
        for finding in findings:
            finding.verified_externally = False
            finding.external_sources = []

        return findings
```

---

## Test Strategy

### Unit Tests

**Test: Pass priority logic**
```python
# veritas/tests/test_vision_pass_priority.py
import pytest
from veritas.agents.vision import VisionAgent, VisionPassPriority

def test_should_run_pass_critical_always_runs():
    """Critical passes (1, 5) always run."""
    assert VisionAgent()._should_run_pass(1, [], False) == True
    assert VisionAgent()._should_run_pass(5, [], False) == True

def test_should_run_pass_conditional_requires_findings():
    """Conditional passes (2, 4) only run if prior findings exist."""
    assert VisionAgent()._should_run_pass(2, [], False) == False
    assert VisionAgent()._should_run_pass(2, [mock_finding()], False) == True

def test_should_run_pass_expensive_requires_temporal_changes():
    """Expensive pass (3) only runs if temporal changes detected."""
    assert VisionAgent()._should_run_pass(3, [], False) == False
    assert VisionAgent()._should_run_pass(3, [], True) == True
```

**Test: Temporal analysis caching**
```python
# veritas/tests/test_temporal_analysis.py
import pytest
from veritas.agents.vision.temporal_analysis import TemporalAnalyzer

def test_temporal_analyzer_memory_check():
    """Temporal analyzer raises error when insufficient memory."""
    # Mock psutil to return low memory
    with patch('veritas.agents.vision.temporal_analysis.psutil') as mock_psutil:
        mock_psutil.virtual_memory.return_value.available = 1 * 1024 ** 3  # 1GB

        with pytest.raises(MemoryError, match="Insufficient memory"):
            TemporalAnalyzer()

def test_ssim_computation(self, t0_screenshot, t_delay_screenshot, test_dir):
    """SSIM score between identical images is 1.0."""
    analyzer = TemporalAnalyzer()
    score = analyzer.compute_ssim(t0_screenshot, t0_screenshot)
    assert score == pytest.approx(1.0, abs=0.01)

    # Different images have lower SSIM
    score = analyzer.compute_ssim(t0_screenshot, t_delay_screenshot)
    assert score < 1.0
```

**Test: Event emitter throttling**
```python
# veritas/tests/test_vision_event_emitter.py
import pytest
from veritas.agents.vision import VisionEventEmitter

@pytest.mark.asyncio
async def test_event_emitter_throttling():
    """Event emitter throttles events to max_events_per_sec."""
    emitter = VisionEventEmitter(max_events_per_sec=5)

    # Mock _do_emit to track emissions
    emitted = []
    async def mock_emit(event):
        emitted.append(event)

    with patch.object(emitter, '_do_emit', mock_emit):
        # Emit 10 events rapidly
        for i in range(10):
            await emitter._emit({"type": f"test_{i}"})

        # Only 5 should have been emitted (throttled)
        assert len(emitted) <= 5

    # Flush queue emits the rest
    await emitter.flush_queue()
    assert len(emitted) == 10
```

---

### Integration Tests

**Test: Full vision pipeline with mock VLM**
```python
# veritas/tests/test_vision_pipeline.py
import pytest
from veritas.agents.vision import VisionAgent

@pytest.mark.asyncio
async def test_vision_pipeline_5_pass_execution():
    """Vision agent executes 5 passes with mock VLM."""
    # Mock NIMClient
    nim_client = MagicMock()
    nim_client.analyze_image = AsyncMock(side_effect=[
        # Pass 1 response (quick threat)
        {"regions": [{"bbox": [10, 10, 100, 50], "type": "countdown_timer", "severity": "high"}]},
        # Pass 2 response (dark patterns)
        {"regions": [{"bbox": [10, 10, 100, 50], "type": "false_urgency", "severity": "high"}]},
        # Pass 3 response (temporal)
        {"regions": []},
        # Pass 4 response (cross-reference)
        {"regions": []},
        # Pass 5 response (synthesis)
        {"regions": [{"bbox": [10, 10, 100, 50], "type": "false_urgency", "severity": "high", "confidence": 0.85}]}
    ])

    agent = VisionAgent(nim_client)
    result = await agent.analyze(["test_screenshot.jpg"])

    assert len(result.findings) > 0
    assert result.passes_completed == 5
    assert result.temporal_analysis is not None
```

---

### Performance Tests

**Test: Memory usage during CV operations**
```python
# veritas/tests/test_vision_memory.py
import pytest
import psutil
import gc
from veritas.agents.vision.temporal_analysis import TemporalAnalyzer

def test_cv_memory_does_not_leak():
    """CV operations don't leak memory."""
    analyzer = TemporalAnalyzer()
    process = psutil.Process()

    # Get initial memory
    initial_memory = process.memory_info().rss

    # Run 10 SSIM computations
    for i in range(10):
        analyzer.compute_ssim("test1.jpg", "test2.jpg")
        gc.collect()

    # Final memory should not increase significantly
    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / (1024 * 1024)  # MB

    assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB (threshold: 50MB)"
```

**Test: VLM call count with caching**
```python
# veritas/tests/test_vision_cache.py
import pytest
from veritas.agents.vision import VisionAgent

@pytest.mark.asyncio
async def test_vision_caching_reduces_vlm_calls():
    """Caching reduces VLM calls on repeated analysis."""
    nim_client = MagicMock()
    call_count = 0

    async def mock_analyze(image, prompt):
        nonlocal call_count
        call_count += 1
        return {"regions": []}

    nim_client.analyze_image = mock_analyze
    nim_client.get_from_cache = MagicMock(return_value=None)
    nim_client.write_to_cache = MagicMock()

    agent = VisionAgent(nim_client)

    # First analysis with 3 screenshots, 5 passes = 15 calls (no cache hits)
    await agent.analyze(["shot1.jpg", "shot2.jpg", "shot3.jpg"])
    base_calls = call_count

    # Second analysis on same screenshots = 0 VLM calls (all cache hits)
    nim_client.get_from_cache = MagicMock(return_value={"regions": []})
    await agent.analyze(["shot1.jpg", "shot2.jpg", "shot3.jpg"])

    assert call_count == base_calls, "Caching should prevent duplicate VLM calls"
```

---

## Success Criteria (When Phase 6 Is Done)

### Must Have (Blocker if Missing)
1. ✅ Vision Agent executes 5-pass pipeline (not just single-pass)
2. ✅ Pass-specific prompts are distinct and different per pass
3. ✅ CV temporal analysis (SSIM) runs before VLM passes
4. ✅ Pass priority logic skips unnecessary passes when safe
5. ✅ Vision events emit per pass (pass_start, pass_findings, pass_complete)
6. ✅ VLM caching reduces duplicate calls by >60% on repeated URLs

### Should Have (Warning if Missing)
1. ✅ Optical flow computation detects region-level changes
2. ✅ Event throttling prevents WebSocket flooding (<5 events/sec)
3. ✅ Memory monitoring prevents OOM on 8GB RAM systems
4. ✅ Temporal results influence which screenshots pass to VLM
5. ✅ Cross-reference placeholder structure exists for Phase 8 integration

### Nice to Have (Optional)
1. ✅ Visual pass progress indicators in frontend (Vision Pass 1/5 active)
2. ✅ Finding confidence scores justified by AI reasoning
3. ✅ Pass-level findings deduplication across all 5 passes
4. ✅ Batched finding events for efficient transmission

---

## Requirements Covered

| Requirement | Status | Notes |
|-------------|--------|-------|
| VISION-01 | 📝 Covered | 5-pass pipeline with pass priority |
| VISION-02 | 📝 Covered | Pass-specific prompts with temporal context |
| VISION-03 | 📝 Covered | SSIM + optical flow temporal analysis |
| VISION-04 | 📝 Covered | Pass-level progress events with throttling |
| SMART-VIS-01 | 📝 Covered | Cross-reference placeholder for Phase 8 |
| SMART-VIS-02 | 📝 Covered | Expert-level prompts with confidence scoring |

---

*Plan created: 2026-02-23*
*Next phase: Phase 7 (Scout Navigation & Quality Foundation)*
