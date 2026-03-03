---
id: 06-06
phase: 6
wave: 5
autonomous: true

objective: Integrate all components into enhanced VisionAgent with 5-pass pipeline, content type detection, and temporal analysis coordination.

files_modified:
  - veritas/agents/vision.py

tasks:
  - Create _detect_content_type() method for adaptive SSIM thresholds
  - Rewrite VisionAgent.analyze() method with 5-pass execution
  - Integrate TemporalAnalyzer, VisionEventEmitter, and pass priority logic
  - Add _should_run_pass(), _get_pass_description(), _parse_vlm_response(), etc.
  - Emit real-time pass progress events (vision_pass_start, pass_findings, pass_complete)

has_summary: false
gap_closure: false
---

# Plan 06-06: Vision Agent Integration

**Goal:** Integrate all Phase 6 components into enhanced VisionAgent with full 5-pass pipeline, adaptive thresholds, and real-time progress streaming.

## Context

After implementing individual components, we need to orchestrate them:
1. Detect content type for adaptive SSIM thresholds
2. Initialize TemporalAnalyzer with content type
3. Run temporal analysis before VLM passes
4. Execute 5-pass pipeline with priority skipping
5. Stream real-time progress events
6. Cross-reference findings (placeholder for Phase 8)

## Implementation

### Task 1: Add content type detection

**File:** `veritas/agents/vision.py`

```python
def _detect_content_type(self, url: str, scout_result: ScoutResult = None) -> str:
    """Detect content type from URL and Scout metadata for adaptive SSIM thresholds."""
    url_lower = url.lower()

    # E-commerce
    e_commerce_patterns = ['shop', 'store', 'buy', 'cart', 'checkout', 'order',
                          'amazon', 'ebay', 'etsy', 'shopify']
    if any(p in url_lower for p in e_commerce_patterns):
        return 'e_commerce'

    # Subscription
    subscription_patterns = ['subscrib', 'plan', 'pricing', 'trial', 'signup',
                           'notion', 'slack', 'zoom', 'github', 'figma']
    if any(p in url_lower for p in subscription_patterns):
        return 'subscription'

    # Phishing/scan
    if scout_result and hasattr(scout_result, 'risk'):
        if scout_result.risk >= 0.7:
            return 'phishing/scan'

    # News/blog
    news_patterns = ['news', 'blog', 'article', 'post', 'medium', 'substack']
    if any(p in url_lower for p in news_patterns):
        return 'news/blog'

    return 'default'
```

### Task 2: Rewrite VisionAgent.analyze() method

**File:** `veritas/agents/vision.py`

```python
async def analyze(self, screenshots: List[str], scout_result: ScoutResult = None) -> VisionResult:
    """Perform 5-pass vision analysis on screenshots."""
    await self.event_emitter.emit_vision_start(len(screenshots))

    all_findings = []

    # Detect content type for adaptive SSIM thresholds
    url = scout_result.url if scout_result and hasattr(scout_result, 'url') else ''
    content_type = self._detect_content_type(url, scout_result)
    logger.info(f"Detected content type: {content_type}")

    # Initialize TemporalAnalyzer with content-type-specific thresholds
    self.temporal_analyzer = TemporalAnalyzer(content_type=content_type)

    # Temporal analysis
    temporal_result = None
    has_temporal_changes = False

    if len(screenshots) >= 2 and scout_result:
        temporal_result = self.temporal_analyzer.analyze_temporal_changes(
            screenshots[0], screenshots[1]
        )
        has_temporal_changes = temporal_result['has_changes']

    # Determine screenshots to analyze
    if temporal_result and temporal_result['recommendation'] == 'fullpage_only':
        screenshots_to_analyze = [screenshots[-1]]
    else:
        screenshots_to_analyze = screenshots

    # Run 5-pass analysis
    passes_completed = 0
    for pass_num in range(1, 6):
        if not self._should_run_pass(pass_num, all_findings, has_temporal_changes):
            logger.debug(f"Skipping Pass {pass_num}")
            continue

        description = self._get_pass_description(pass_num)
        await self.event_emitter.emit_pass_start(pass_num, description, len(screenshots_to_analyze))

        prompt = self._get_pass_prompt(pass_num, temporal_result)

        pass_findings = []
        for screenshot in screenshots_to_analyze:
            cache_key = self._get_cache_key(screenshot, prompt, pass_num)
            cached = self.nim_client.get_from_cache(cache_key)

            if cached:
                pass_findings.extend([Finding.from_dict(cached)])
                continue

            vlm_response = await self.nim_client.analyze_image(screenshot, prompt)
            findings_from_pass = self._parse_vlm_response(vlm_response, pass_num)
            pass_findings.extend(findings_from_pass)

            # Cache results
            for finding in findings_from_pass:
                self.nim_client.write_to_cache(cache_key, finding.to_dict(), ttl=86400)

        pass_findings = self._deduplicate_findings(pass_findings)
        all_findings.extend(pass_findings)

        await self.event_emitter.emit_pass_findings(pass_num, pass_findings)
        confidence = self._compute_confidence(pass_findings) if pass_findings else 0.0
        await self.event_emitter.emit_pass_complete(pass_num, len(pass_findings), confidence)

        passes_completed += 1

    # Cross-reference findings (Phase 8 placeholder)
    all_findings = self._cross_reference_findings(all_findings)

    await self.event_emitter.flush_queue()
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
    descriptions = {
        1: "Quick visual scan for obvious threats",
        2: "Sophisticated dark pattern detection",
        3: "Temporal dynamics and dynamic content",
        4: "Cross-reference with external intelligence",
        5: "Final synthesis and confidence scoring"
    }
    return descriptions[pass_num]

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
    """Compute confidence score (0-100)."""
    if not findings:
        return 0.0
    return sum(f.confidence for f in findings) / len(findings) * 100

def _cross_reference_findings(self, findings: List[Finding]) -> List[Finding]:
    """Cross-reference findings with external intelligence (placeholder for Phase 8)."""
    for finding in findings:
        finding.verified_externally = False
        finding.external_sources = []
    return findings
```

## Success Criteria

1. ✅ VisionAgent executes 5-pass pipeline
2. ✅ Content type detection works for adaptive thresholds
3. ✅ Pass priority logic skips unnecessary passes
4. ✅ Real-time events emitted (pass_start, findings, complete)
5. ✅ Temporal analysis influences screenshot selection
6. ✅ All helper methods implemented correctly

## Dependencies

- Requires: 06-01, 06-02, 06-03, 06-04, 06-05 (all components)
- Blocks: Phase 7 (Quality Foundation), Phase 8 (OSINT)
