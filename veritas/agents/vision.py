"""
Veritas Agent 2 — Visual Forensics Unit (Computer Vision)

The "Eyes" of Veritas. Analyzes screenshots captured by the Scout agent
using NVIDIA NIM Vision-Language Models to detect dark patterns.

Pipeline:
    1. Receives screenshot paths from Scout
    2. Selects relevant VLM prompts from the dark pattern taxonomy
    3. Sends each screenshot to NIM VLM with forensic prompts
    4. Parses structured JSON responses
    5. Computes per-category and aggregate visual scores
    6. Returns a VisionResult with all findings + score

Fallback chain (inherited from NIMClient):
    NIM VLM Primary → NIM VLM Fallback → Tesseract OCR + Heuristics → No-AI stub

Patterns from:
    - config/dark_patterns.py → DARK_PATTERN_TAXONOMY (prompt source)
    - core/nim_client.py → analyze_image(), batch_analyze_image()
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.dark_patterns import (DARK_PATTERN_TAXONOMY, get_all_vlm_prompts,
                                  get_severity_weight, get_temporal_categories)
from core.nim_client import NIMClient

# Lazy imports for optional modules (avoid circular import with TemporalFinding)
# from analysis.temporal_analyzer import TemporalAnalyzer  — imported in method
# from analysis.pattern_matcher import PatternMatcher       — imported in method

logger = logging.getLogger("veritas.vision")


# ============================================================
# Data Structures
# ============================================================

@dataclass
class DarkPatternFinding:
    """A single detected dark pattern instance."""
    category_id: str          # e.g., "visual_interference"
    pattern_type: str         # e.g., "misdirected_click"
    confidence: float         # 0.0 to 1.0
    severity: str             # "low", "medium", "high", "critical"
    evidence: str             # Description of what was found
    screenshot_path: str      # Which screenshot this was detected in
    raw_vlm_response: str     # Full VLM response text for audit trail
    model_used: str           # Which model produced this finding
    fallback_mode: bool       # True if not using primary NIM VLM


@dataclass
class TemporalFinding:
    """Result of comparing Screenshot_A (t0) vs Screenshot_B (t+delay)."""
    finding_type: str         # "fake_countdown", "fake_scarcity", "consistent"
    value_at_t0: str          # Timer/counter value at first capture
    value_at_t_delay: str     # Timer/counter value at second capture
    delta_seconds: float      # Time between captures
    is_suspicious: bool       # True if the values suggest deception
    explanation: str           # Human-readable explanation
    confidence: float          # 0.0 to 1.0


@dataclass
class VisionResult:
    """Complete result from the Visual Forensics analysis."""
    # Findings
    dark_patterns: list[DarkPatternFinding] = field(default_factory=list)
    temporal_findings: list[TemporalFinding] = field(default_factory=list)

    # Scores (0.0 to 1.0 — higher = MORE trustworthy / fewer dark patterns)
    visual_score: float = 1.0
    temporal_score: float = 1.0

    # Stats
    screenshots_analyzed: int = 0
    prompts_sent: int = 0
    nim_calls_made: int = 0
    cache_hits: int = 0
    fallback_used: bool = False

    # Diagnostics
    errors: list[str] = field(default_factory=list)

    @property
    def total_patterns_found(self) -> int:
        return len(self.dark_patterns)

    @property
    def critical_patterns(self) -> list[DarkPatternFinding]:
        return [p for p in self.dark_patterns if p.severity == "critical"]

    @property
    def has_fake_timers(self) -> bool:
        return any(
            tf.finding_type == "fake_countdown" and tf.is_suspicious
            for tf in self.temporal_findings
        )

    @property
    def temporal_finding_ids(self) -> list[str]:
        """IDs of suspicious temporal findings — used by trust scorer override rules."""
        return [
            tf.finding_type for tf in self.temporal_findings if tf.is_suspicious
        ]


# ============================================================
# Vision Agent
# ============================================================

class VisionAgent:
    """
    Agent 2: Analyzes screenshots for dark patterns using VLM.

    Usage:
        agent = VisionAgent()

        result = await agent.analyze(
            screenshots=["evidence/abc_t0.jpg", "evidence/abc_t10.jpg", "evidence/abc_fullpage.jpg"],
            screenshot_labels=["t0", "t10", "fullpage"],
            url="https://suspicious-site.com"
        )

        print(f"Dark patterns found: {result.total_patterns_found}")
        print(f"Visual score: {result.visual_score}")
        print(f"Fake timers: {result.has_fake_timers}")
    """

    def __init__(self, nim_client: Optional[NIMClient] = None):
        self._nim = nim_client or NIMClient()
        self._temporal_categories = set(get_temporal_categories())
        # Optional pattern matcher for batched prompt efficiency
        self._pattern_matcher = None
        try:
            from analysis.pattern_matcher import PatternMatcher
            self._pattern_matcher = PatternMatcher()
        except Exception:
            logger.debug("PatternMatcher not available — using individual prompts")

    # ================================================================
    # Public: Full Analysis Pipeline
    # ================================================================

    async def analyze(
        self,
        screenshots: list[str],
        screenshot_labels: list[str],
        url: str = "",
        categories: Optional[list[str]] = None,
        site_type: str = "",
    ) -> VisionResult:
        """
        Full visual forensics analysis on a set of screenshots.

        Args:
            screenshots: List of file paths to screenshot images
            screenshot_labels: Labels matching screenshots (e.g., ["t0", "t10", "fullpage"])
            url: The target URL (for logging / context)
            categories: Specific dark pattern categories to check. None = check all.

        Returns:
            VisionResult with all findings and scores
        """
        result = VisionResult()

        if not screenshots:
            logger.warning("VisionAgent.analyze called with no screenshots")
            return result

        # Determine which categories to analyze
        # Site-type-aware: prioritise categories relevant to the site type
        active_taxonomy = DARK_PATTERN_TAXONOMY
        if categories:
            active_taxonomy = {
                k: v for k, v in DARK_PATTERN_TAXONOMY.items() if k in categories
            }
        elif site_type:
            # Reorder so priority categories for this site type are analysed first
            try:
                from config.site_types import SITE_TYPE_PROFILES, SiteType
                st = SiteType(site_type)
                profile = SITE_TYPE_PROFILES.get(st)
                if profile and profile.priority_patterns:
                    priority = [p for p in profile.priority_patterns if p in active_taxonomy]
                    rest = [k for k in active_taxonomy if k not in priority]
                    ordered = {k: active_taxonomy[k] for k in priority + rest}
                    active_taxonomy = ordered
                    logger.info(f"Reordered categories for site_type={site_type}: priority={priority}")
            except Exception:
                pass  # Ignore — use default order

        logger.info(
            f"Starting visual analysis of {url} | "
            f"screenshots={len(screenshots)} | categories={list(active_taxonomy.keys())}"
        )

        # -----------------------------------------------------------
        # Phase 1: Static analysis (non-temporal) on fullpage or t0
        # -----------------------------------------------------------
        primary_screenshot = self._select_primary_screenshot(
            screenshots, screenshot_labels
        )
        if primary_screenshot:
            await self._analyze_static_patterns(
                primary_screenshot, active_taxonomy, result
            )

        # -----------------------------------------------------------
        # Phase 2: Temporal analysis (Screenshot_A vs Screenshot_B)
        #          VLM + pixel/OCR heuristic cross-validation
        # -----------------------------------------------------------
        t0_path, t_delay_path = self._find_temporal_pair(
            screenshots, screenshot_labels
        )
        if t0_path and t_delay_path:
            # Phase 2a: VLM-based temporal analysis
            await self._analyze_temporal_patterns(
                t0_path, t_delay_path, screenshot_labels, result
            )

            # Phase 2b: Heuristic temporal analysis (pixel-diff + OCR)
            #           Acts as ground-truth validation for VLM claims
            try:
                from analysis.temporal_analyzer import TemporalAnalyzer
                heuristic_analyzer = TemporalAnalyzer()
                heuristic_findings = heuristic_analyzer.compare_screenshots(
                    t0_path, t_delay_path, delay_seconds=10.0
                )
                for hf in heuristic_findings:
                    if hf.is_suspicious:
                        # Check if VLM already caught this
                        already_found = any(
                            tf.finding_type == hf.finding_type and tf.is_suspicious
                            for tf in result.temporal_findings
                        )
                        if not already_found:
                            # Heuristic found something VLM missed — add it
                            hf.explanation += " (detected by pixel/OCR heuristics)"
                            result.temporal_findings.append(hf)
                            result.dark_patterns.append(DarkPatternFinding(
                                category_id="false_urgency",
                                pattern_type=hf.finding_type,
                                confidence=hf.confidence,
                                severity="high",
                                evidence=hf.explanation,
                                screenshot_path=t0_path,
                                raw_vlm_response="[heuristic-temporal-analyzer]",
                                model_used="pixel_ocr_heuristic",
                                fallback_mode=True,
                            ))
                            logger.info(f"Heuristic temporal finding: {hf.finding_type}")
                        else:
                            logger.debug(f"VLM+heuristic agree on: {hf.finding_type}")
            except Exception as e:
                logger.debug(f"Heuristic temporal analysis unavailable: {e}")
        else:
            logger.debug("No temporal screenshot pair found — skipping temporal analysis")
            result.temporal_score = 0.5  # Neutral — no data to judge

        # -----------------------------------------------------------
        # Phase 3: Compute visual score from findings
        # -----------------------------------------------------------
        result.visual_score = self._compute_visual_score(result.dark_patterns)
        result.temporal_score = self._compute_temporal_score(result.temporal_findings)
        result.screenshots_analyzed = len(screenshots)

        # Capture NIM stats
        nim_stats = self._nim.get_stats()
        result.nim_calls_made = nim_stats["api_calls"]
        result.cache_hits = nim_stats["cache_hits"]
        result.fallback_used = nim_stats["fallback_count"] > 0

        logger.info(
            f"Visual analysis complete for {url} | "
            f"patterns={result.total_patterns_found} | "
            f"visual_score={result.visual_score:.2f} | "
            f"temporal_score={result.temporal_score:.2f} | "
            f"nim_calls={nim_stats['api_calls']} | "
            f"cache_hits={nim_stats['cache_hits']}"
        )

        return result

    async def run_pass_with_cache(
        self,
        pass_num: int,
        screenshot: str,
        prompt: str,
        category_id: str = "",
    ) -> list[DarkPatternFinding]:
        """
        Execute vision pass with pass-specific caching.

        This method implements pass-level caching for the Vision Agent's
        5-pass pipeline, enabling smart pass skipping when results are
        already cached.

        Args:
            pass_num: Pass identifier (1-5 for Vision Agent passes)
            screenshot: Path to screenshot image
            prompt: The VLM forensic prompt
            category_id: Optional category ID for result parsing

        Returns:
            List of DarkPatternFinding objects for this pass

        Raises:
            Exception: If VLM analysis fails (with full error logging)
        """
        cache_key = self._nim.get_cache_key(screenshot, prompt, pass_num)
        cached = self._nim._read_cache(cache_key)

        if cached:
            logger.info(f"Cache hit for Pass {pass_num}")
            # Convert cached dict back to DarkPatternFinding objects
            cached_findings = cached.get("findings", [])
            findings = []
            for f_data in cached_findings:
                try:
                    findings.append(DarkPatternFinding(**f_data))
                except (TypeError, KeyError):
                    logger.warning(f"Failed to restore cached finding: {f_data}")
            return findings

        # Execute VLM call with pass_type for proper cache key
        vlm_response = await self._nim.analyze_image(
            image_path=screenshot,
            prompt=prompt,
            category_hint=category_id
        )

        # Parse response into DarkPatternFinding objects
        findings = self._parse_vlm_response(
            vlm_response, category_id,
            DARK_PATTERN_TAXONOMY.get(category_id) if category_id else None,
            screenshot
        )

        # Cache result as dict (24h TTL is default in _write_cache)
        cache_data = {
            "findings": [f.__dict__ for f in findings],
            "prompt": prompt,
            "pass_num": pass_num,
            "model": vlm_response.get("model", "unknown"),
            "fallback_mode": vlm_response.get("fallback_mode", False),
        }
        self._nim._write_cache(cache_key, cache_data)

        return findings

    # ================================================================
    # Private: Static Pattern Analysis
    # ================================================================

    async def _analyze_static_patterns(
        self,
        screenshot_path: str,
        taxonomy: dict,
        result: VisionResult,
    ):
        """
        Run all non-temporal VLM prompts against a screenshot.
        Each category's prompts are sent sequentially (batched per image).
        """
        for cat_id, category in taxonomy.items():
            # Skip temporal-only categories in static analysis
            if category.detection_method == "temporal":
                continue

            for prompt in category.vlm_prompts:
                result.prompts_sent += 1

                try:
                    vlm_result = await self._nim.analyze_image(
                        image_path=screenshot_path,
                        prompt=prompt,
                        category_hint=cat_id,
                    )

                    findings = self._parse_vlm_response(
                        vlm_result, cat_id, category, screenshot_path
                    )
                    result.dark_patterns.extend(findings)

                    if vlm_result.get("fallback_mode"):
                        result.fallback_used = True

                except Exception as e:
                    error_msg = f"VLM analysis failed for {cat_id}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

    # ================================================================
    # Private: Temporal Pattern Analysis
    # ================================================================

    async def _analyze_temporal_patterns(
        self,
        t0_path: str,
        t_delay_path: str,
        labels: list[str],
        result: VisionResult,
    ):
        """
        Compare Screenshot_A (t0) vs Screenshot_B (t+delay) for:
        - Fake countdown timers (value resets or doesn't decrease correctly)
        - Fake scarcity ("Only 2 left" that never changes)
        - Fake social proof counters
        """
        temporal_tax = {
            k: v for k, v in DARK_PATTERN_TAXONOMY.items()
            if v.detection_method == "temporal"
        }

        for cat_id, category in temporal_tax.items():
            for prompt in category.vlm_prompts:
                result.prompts_sent += 2  # One for each screenshot

                try:
                    # Analyze Screenshot_A
                    vlm_a = await self._nim.analyze_image(
                        image_path=t0_path,
                        prompt=prompt,
                        category_hint=f"{cat_id}_t0",
                    )

                    # Analyze Screenshot_B
                    vlm_b = await self._nim.analyze_image(
                        image_path=t_delay_path,
                        prompt=prompt,
                        category_hint=f"{cat_id}_t_delay",
                    )

                    # Compare the two responses
                    temporal = self._compare_temporal_responses(
                        vlm_a, vlm_b, cat_id, prompt
                    )
                    if temporal:
                        result.temporal_findings.append(temporal)

                        # If suspicious, also add as a dark pattern finding
                        if temporal.is_suspicious:
                            result.dark_patterns.append(DarkPatternFinding(
                                category_id=cat_id,
                                pattern_type=temporal.finding_type,
                                confidence=temporal.confidence,
                                severity="critical" if "countdown" in temporal.finding_type else "high",
                                evidence=temporal.explanation,
                                screenshot_path=t0_path,
                                raw_vlm_response=f"T0: {vlm_a.get('response', '')}\nT+delay: {vlm_b.get('response', '')}",
                                model_used=vlm_a.get("model", "unknown"),
                                fallback_mode=vlm_a.get("fallback_mode", False),
                            ))

                except Exception as e:
                    error_msg = f"Temporal analysis failed for {cat_id}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

    def _compare_temporal_responses(
        self,
        vlm_a: dict,
        vlm_b: dict,
        category_id: str,
        prompt: str,
    ) -> Optional[TemporalFinding]:
        """
        Compare VLM responses from two time points to detect deception.

        Logic:
        - Extract values (timer text, stock count, viewer count) from both responses
        - If timer value at t+delay >= timer value at t0 → FAKE (should have decreased)
        - If stock count is identical → SUSPICIOUS
        - If viewer count is identical → SUSPICIOUS
        """
        try:
            response_a = vlm_a.get("response", "")
            response_b = vlm_b.get("response", "")

            data_a = self._extract_json_from_response(response_a)
            data_b = self._extract_json_from_response(response_b)

            if not data_a or not data_b:
                return None

            # --- Timer comparison ---
            timer_a = data_a.get("timer_value", "")
            timer_b = data_b.get("timer_value", "")

            if timer_a and timer_b:
                if timer_a == timer_b:
                    return TemporalFinding(
                        finding_type="fake_countdown",
                        value_at_t0=timer_a,
                        value_at_t_delay=timer_b,
                        delta_seconds=10.0,
                        is_suspicious=True,
                        explanation=(
                            f"Countdown timer shows '{timer_a}' at t0 and '{timer_b}' "
                            f"at t+10s — timer appears frozen/reset (should have decreased)"
                        ),
                        confidence=0.85,
                    )
                # Could also compare parsed time values for non-matching reset
                # (e.g., 04:59 → 05:00 means it reset)

            # --- Scarcity comparison ---
            scarcity_a = data_a.get("scarcity_text", "")
            scarcity_b = data_b.get("scarcity_text", "")

            if scarcity_a and scarcity_b:
                if scarcity_a == scarcity_b:
                    return TemporalFinding(
                        finding_type="fake_scarcity",
                        value_at_t0=scarcity_a,
                        value_at_t_delay=scarcity_b,
                        delta_seconds=10.0,
                        is_suspicious=True,
                        explanation=(
                            f"Scarcity indicator shows '{scarcity_a}' at both time points — "
                            f"static value suggests fake scarcity messaging"
                        ),
                        confidence=0.70,
                    )

            # No temporal anomaly detected
            return TemporalFinding(
                finding_type="consistent",
                value_at_t0=timer_a or scarcity_a or "",
                value_at_t_delay=timer_b or scarcity_b or "",
                delta_seconds=10.0,
                is_suspicious=False,
                explanation="No temporal anomalies detected between screenshots",
                confidence=0.5,
            )

        except Exception as e:
            logger.warning(f"Temporal comparison error: {e}")
            return None

    # ================================================================
    # Private: VLM Response Parsing
    # ================================================================

    def _parse_vlm_response(
        self,
        vlm_result: dict,
        category_id: str,
        category,
        screenshot_path: str,
    ) -> list[DarkPatternFinding]:
        """
        Parse a VLM response into structured DarkPatternFinding objects.
        Handles both valid JSON responses and free-text responses.
        """
        findings = []
        response_text = vlm_result.get("response", "")
        model = vlm_result.get("model", "unknown")
        is_fallback = vlm_result.get("fallback_mode", False)

        # Try to parse as JSON first
        data = self._extract_json_from_response(response_text)

        if data:
            findings.extend(self._findings_from_json(
                data, category_id, category, screenshot_path,
                response_text, model, is_fallback
            ))
        else:
            # Fallback: try to extract findings from free-text
            findings.extend(self._findings_from_text(
                response_text, category_id, category, screenshot_path,
                model, is_fallback
            ))

        return findings

    def _findings_from_json(
        self, data: dict, category_id: str, category,
        screenshot_path: str, raw_response: str, model: str, fallback: bool,
    ) -> list[DarkPatternFinding]:
        """Extract findings from a parsed JSON VLM response."""
        findings = []

        # Handle {"findings": [...]} format
        json_findings = data.get("findings", [])
        if isinstance(json_findings, list):
            for finding in json_findings:
                if not isinstance(finding, dict):
                    continue

                confidence = float(finding.get("confidence", 0.5))
                if confidence < 0.3:
                    continue  # Too low confidence to report

                pattern_type = finding.get("pattern_type", category_id)
                severity = self._lookup_severity(category_id, pattern_type)

                evidence_parts = []
                for key in ["pair", "element", "description", "issue", "dominant",
                            "size_ratio", "contrast_difference"]:
                    if key in finding:
                        evidence_parts.append(f"{key}: {finding[key]}")

                findings.append(DarkPatternFinding(
                    category_id=category_id,
                    pattern_type=pattern_type,
                    confidence=confidence,
                    severity=severity,
                    evidence=" | ".join(evidence_parts) if evidence_parts else str(finding),
                    screenshot_path=screenshot_path,
                    raw_vlm_response=raw_response,
                    model_used=model,
                    fallback_mode=fallback,
                ))

        # Handle single-finding response formats
        # (e.g., {"timer_found": true, "timer_value": "04:59", ...})
        single_finding_keys = [
            "timer_found", "scarcity_found", "cancel_visible",
            "guilt_language_found", "pre_selected_found",
            "price_transparent", "free_claim", "testimonials_found",
            "badges_found", "authority_claims",
        ]

        for key in single_finding_keys:
            if key not in data:
                continue

            value = data[key]
            is_pattern = False

            if isinstance(value, bool):
                # True for positive detectors, False for "cancel_visible" / "price_transparent"
                if key in ("cancel_visible", "price_transparent"):
                    is_pattern = value is False  # Not visible → pattern detected
                else:
                    is_pattern = value is True
            elif isinstance(value, list) and len(value) > 0:
                is_pattern = True

            if is_pattern:
                confidence = float(data.get("confidence", 0.6))
                if confidence < 0.3:
                    continue

                pattern_type = data.get("pattern_type", category_id)
                severity = self._lookup_severity(category_id, pattern_type)

                # Build evidence from all non-meta fields
                evidence_parts = []
                for k, v in data.items():
                    if k not in ("confidence", "pattern_type") and v:
                        evidence_parts.append(f"{k}: {v}")

                findings.append(DarkPatternFinding(
                    category_id=category_id,
                    pattern_type=pattern_type,
                    confidence=confidence,
                    severity=severity,
                    evidence=" | ".join(evidence_parts),
                    screenshot_path=screenshot_path,
                    raw_vlm_response=raw_response,
                    model_used=model,
                    fallback_mode=fallback,
                ))

        return findings

    def _findings_from_text(
        self, text: str, category_id: str, category,
        screenshot_path: str, model: str, fallback: bool,
    ) -> list[DarkPatternFinding]:
        """
        Fallback: extract findings from free-text VLM response.
        Only used when JSON parsing fails.
        """
        findings = []
        text_lower = text.lower()

        # Check if the response indicates a positive detection
        positive_indicators = [
            "detected", "found", "identified", "present", "suspicious",
            "yes", "appears to be", "likely", "confirms",
        ]
        negative_indicators = [
            "no dark pattern", "none detected", "clean", "no suspicious",
            "not found", "none found", "no issues",
        ]

        for neg in negative_indicators:
            if neg in text_lower:
                return findings  # Clean — no patterns

        for pos in positive_indicators:
            if pos in text_lower:
                # Extract a finding with moderate confidence
                findings.append(DarkPatternFinding(
                    category_id=category_id,
                    pattern_type=category_id,
                    confidence=0.5,  # Lower confidence for free-text extraction
                    severity="medium",
                    evidence=text[:300],  # Truncate for readability
                    screenshot_path=screenshot_path,
                    raw_vlm_response=text,
                    model_used=model,
                    fallback_mode=fallback,
                ))
                break  # Only one finding per free-text response

        return findings

    # ================================================================
    # Private: Scoring
    # ================================================================

    def _compute_visual_score(self, patterns: list[DarkPatternFinding]) -> float:
        """
        Compute visual trust score (0-1, higher = more trustworthy).

        Formula: 1.0 - (sum of weighted pattern severities, capped at 1.0)
        Each detected pattern deducts based on its severity × confidence.
        """
        if not patterns:
            return 1.0  # No dark patterns → fully trustworthy visually

        total_deduction = 0.0
        for p in patterns:
            weight = get_severity_weight(p.severity)
            total_deduction += weight * p.confidence

        # Normalize: more patterns = worse, but cap at 0.0
        # Divide by expected-max to keep scoring proportional
        max_expected = 5.0  # 5 high-severity patterns = score of 0
        normalized = min(total_deduction / max_expected, 1.0)

        return round(max(0.0, 1.0 - normalized), 3)

    def _compute_temporal_score(self, temporals: list[TemporalFinding]) -> float:
        """
        Compute temporal trust score (0-1, higher = more trustworthy).
        Any fake timer/counter detection heavily penalizes the score.
        """
        if not temporals:
            return 0.5  # No data — neutral

        suspicious = [t for t in temporals if t.is_suspicious]
        if not suspicious:
            return 1.0  # Clean temporal analysis

        # Each suspicious finding deducts proportionally
        total_deduction = sum(s.confidence for s in suspicious)
        max_expected = 2.0  # 2 suspicious findings at full confidence = score of 0

        return round(max(0.0, 1.0 - min(total_deduction / max_expected, 1.0)), 3)

    # ================================================================
    # Private: Helpers
    # ================================================================

    def _select_primary_screenshot(
        self, screenshots: list[str], labels: list[str]
    ) -> Optional[str]:
        """Select the best screenshot for static (non-temporal) analysis."""
        # Prefer fullpage, then t0, then any
        for preferred in ["fullpage", "t0", "subpage"]:
            for path, label in zip(screenshots, labels):
                if label == preferred:
                    return path
        return screenshots[0] if screenshots else None

    def _find_temporal_pair(
        self, screenshots: list[str], labels: list[str]
    ) -> tuple[Optional[str], Optional[str]]:
        """Find the t0 and t+delay screenshot pair."""
        t0_path = None
        t_delay_path = None

        for path, label in zip(screenshots, labels):
            if label == "t0":
                t0_path = path
            elif label.startswith("t") and label != "t0":
                t_delay_path = path

        return t0_path, t_delay_path

    def _extract_json_from_response(self, text: str) -> Optional[dict]:
        """
        Extract JSON from a VLM response that may contain markdown or preamble.
        Handles: pure JSON, ```json blocks, JSON buried in text.
        """
        if not text:
            return None

        # Try 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try 2: Extract from ```json ... ``` block
        import re
        json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_block:
            try:
                return json.loads(json_block.group(1))
            except json.JSONDecodeError:
                pass

        # Try 3: Find first {...} in text
        brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _lookup_severity(self, category_id: str, pattern_type: str) -> str:
        """Look up the severity of a pattern type from the taxonomy."""
        category = DARK_PATTERN_TAXONOMY.get(category_id)
        if category:
            for sub in category.sub_types:
                if sub.id == pattern_type:
                    return sub.severity
        return "medium"  # Default
