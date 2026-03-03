---
id: 06-03
phase: 6
wave: 3
autonomous: true

objective: Implement 5 pass-specific VLM prompts optimized for each analysis target (quick threat, dark patterns, temporal, cross-reference, synthesis).

files_modified:
  - veritas/config/dark_patterns.py
  - veritas/agents/vision.py

tasks:
  - Define VISION_PASS_PROMPTS dictionary with 5 pass-specific prompts
  - Add 5-tier confidence mapping get_confidence_tier() method
  - Implement get_pass_prompt() with temporal context injection

has_summary: false
gap_closure: false
---

# Plan 06-03: 5 Pass-Specific VLM Prompts

**Goal:** Replace generic prompts with 5 specialized prompts, each optimized for its analysis target, with 5-tier confidence mapping.

## Context

Single generic prompt is insufficient for sophisticated dark pattern detection. Each pass needs domain-specific instructions:
- **Pass 1:** Quick scan for countdown/urgency
- **Pass 2:** Full dark pattern taxonomy
- **Pass 3:** Temporal change detection
- **Pass 4:** Entity extraction for Phase 8
- **Pass 5:** Synthesis with false positive detection

## Implementation

### Task 1: Define 5 pass-specific prompts

**File:** `veritas/config/dark_patterns.py`

```python
VISION_PASS_PROMPTS = {
    1: """
    ANNOTATE ALL DARK PATTERN REGIONS you detect.

    For each region, return:
    - bbox: [x, y, width, height] coordinates (0-100 scale)
    - type: countdown_timer, fake_urgency, forced_comparison, social_proof, confirmshaming
    - severity: low/medium/high based on prominence

    Focus on HIGH-PRIORITY patterns: countdowns, fake urgency countdowns, countdown banners.

    Be QUICK and PRECISE. Mark obvious patterns only.
    """,

    2: """
    Perform SOPHISTICATED DARK PATTERN DETECTION.

    DARK PATTERN TAXONOMY:
    - Urgency: fake countdowns, limited time offers, "only X left"
    - Scarcity: fake low inventory, "selling fast", "almost gone"
    - Social Proof: fake reviews, fabricated testimonials, inflated counts
    - Misdirection: deceptive action buttons, hidden terms, confusing layouts
    - Obstruction: difficult cancellation, confirmshaming, hard-to-close modals

    Return bbox, type, technique, confidence for each region.
    Be THOROUGH and NUANCED.
    """,

    3: """
    Detect TEMPORAL DYNAMIC CONTENT changes.

    Compare this screenshot to previous screenshot context.

    Return regions that CHANGED between screenshots:
    - bbox: [x, y, width, height]
    - change_type: content_update, timer_change, element_appear, element_disappear
    - severity: low/medium/high

    Focus on SUSPICIOUS temporal changes: timers that reset, price changes, element appearances.
    """,

    4: """
    Cross-reference VISUAL FINDINGS with ENTITY VERIFICATION.

    Identify visual elements requiring EXTERNAL VERIFICATION:
    - Company logos/brand names, trust badges, certifications
    - Social media handles, third-party endorsements

    Return bbox, entity_type, visual_text, verification_needed=true.
    These will be cross-referenced in Phase 8 OSINT.
    """,

    5: """
    Synthesize ALL PASSES into final confidence scoring.

    Review findings from all previous passes.

    For each finding: confidence (0-100), justification, risk level, evidence.

    Identify FALSE POSITIVES: legitimate countdowns, genuine scarcity, real social proof.

    Return final adjudicated findings.
    """
}
```

### Task 2: Add 5-tier confidence mapping

**File:** `veritas/agents/vision.py`

```python
def get_confidence_tier(self, confidence_score: float) -> str:
    """Map confidence score to 5-tier alert level."""
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
    return 'low'
```

### Task 3: Implement prompt selection with temporal context

**File:** `veritas/agents/vision.py`

```python
def get_pass_prompt(self, pass_num: int, temporal_result: dict) -> str:
    """Get appropriate prompt for pass number, injecting temporal context."""
    from veritas.config.dark_patterns import VISION_PASS_PROMPTS
    base_prompt = VISION_PASS_PROMPTS[pass_num]

    # Inject temporal context into Pass 3
    if pass_num == 3:
        temporal_context = f"""
        TEMPORAL CONTEXT:
        - SSIM score: {temporal_result.get('ssim_score', 0):.3f}
        - Has temporal changes: {temporal_result.get('has_changes', False)}
        - Changed regions: {len(temporal_result.get('changed_regions', []))}
        """
        return base_prompt + temporal_context

    return base_prompt
```

## Success Criteria

1. ✅ 5 distinct prompts defined in config
2. ✅ get_confidence_tier() maps scores to 5 tiers
3. ✅ Pass 3 receives temporal context when appropriate
4. ✅ Prompts imported and used in vision passes

## Dependencies

- Requires: 06-01 (VLM Caching)
- Parallel with: 06-04 (Temporal Analysis)
