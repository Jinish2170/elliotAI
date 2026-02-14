"""
Veritas Analysis — Pattern Matcher

Bridges the dark_patterns taxonomy with agent detection logic.
Provides VLM prompt construction, finding normalization, and
severity-weighted scoring utilities.

This module is the "glue" between:
    - config/dark_patterns.py (taxonomy definitions)
    - agents/vision.py (VLM analysis)
    - agents/judge.py (verdict rendering)

It keeps pattern matching logic centralised so that adding a new
dark pattern type requires changes only in dark_patterns.py and here.
"""

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.dark_patterns import (DARK_PATTERN_TAXONOMY, get_all_vlm_prompts,
                                  get_severity_weight, get_temporal_categories)

logger = logging.getLogger("veritas.pattern_matcher")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class NormalizedFinding:
    """A normalised dark pattern finding with taxonomy reference."""
    category: str           # Top-level category from taxonomy
    sub_type: str           # Sub-type within category
    severity: str           # "low" | "medium" | "high" | "critical"
    severity_weight: float  # Numeric weight from taxonomy
    confidence: float       # 0.0 – 1.0
    source: str             # "vlm" | "dom" | "temporal" | "heuristic"
    evidence: str           # Human description
    raw_data: dict = field(default_factory=dict)


@dataclass
class MatchResult:
    """Result of pattern matching across all sources."""
    findings: list[NormalizedFinding] = field(default_factory=list)
    category_scores: dict[str, float] = field(default_factory=dict)
    overall_visual_score: float = 0.5   # 0-1, higher = cleaner
    pattern_count: int = 0
    critical_count: int = 0


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class PatternMatcher:
    """
    Central pattern matching engine.

    Responsibilities:
        1. Build batched VLM prompts from taxonomy
        2. Parse & normalise VLM responses into NormalizedFindings
        3. Merge DOM and temporal findings into the same finding format
        4. Compute category-level and overall visual scores
    """

    def __init__(self):
        self._taxonomy = DARK_PATTERN_TAXONOMY
        self._vlm_prompts = get_all_vlm_prompts()
        self._temporal_categories = get_temporal_categories()

    # ------------------------------------------------------------------
    # 1. Prompt construction
    # ------------------------------------------------------------------

    def get_screenshot_prompts(self) -> list[dict]:
        """
        Return all VLM prompts that should be sent with a screenshot.

        Returns:
            List of dicts with keys: category, prompt, severity
        """
        prompts = []
        for category, cat_data in self._taxonomy.items():
            for prompt in cat_data.vlm_prompts:
                prompts.append({
                    "category": category,
                    "prompt": prompt,
                    "severity": "medium",
                })
            for sub in cat_data.sub_types:
                prompts.append({
                    "category": category,
                    "sub_type": sub.id,
                    "severity": sub.severity,
                    "prompt": "",  # sub-types use category-level prompts
                })
        # Filter to entries with actual prompts
        return [p for p in prompts if p.get("prompt")]

    def get_temporal_prompts(self) -> list[dict]:
        """
        Return VLM prompts for temporal (before/after) comparison.

        Returns:
            List of dicts for categories that need temporal analysis
        """
        prompts = []
        for category, cat_data in self._taxonomy.items():
            if cat_data.detection_method == "temporal":
                for prompt in cat_data.vlm_prompts:
                    prompts.append({
                        "category": category,
                        "prompt": prompt,
                        "severity": "high",
                    })
        return prompts

    def build_batched_prompt(self, max_categories: int = 3) -> list[str]:
        """
        Build efficient batched prompts that cover multiple patterns per VLM call.

        Instead of one VLM call per sub-type, batch related patterns into
        single prompts to reduce API costs.

        Args:
            max_categories: Maximum number of pattern categories per prompt

        Returns:
            List of batched prompt strings
        """
        batched = []
        categories = list(self._taxonomy.keys())

        for i in range(0, len(categories), max_categories):
            batch_cats = categories[i:i + max_categories]
            sections = []

            for cat in batch_cats:
                cat_data = self._taxonomy[cat]
                sub_type_names = [s.id for s in cat_data.sub_types]
                section = (
                    f"## {cat.replace('_', ' ').title()}\n"
                    f"Check for these patterns: {', '.join(sub_type_names)}"
                )
                sections.append(section)

            prompt = (
                "Analyze this screenshot for the following dark patterns. "
                "For EACH pattern found, respond with a JSON object containing: "
                "detected (bool), category (str), sub_type (str), confidence (0-1), "
                "description (str).\n\n"
                + "\n\n".join(sections) +
                "\n\nRespond with a JSON array of findings. "
                "If no patterns are detected, respond with an empty array []."
            )
            batched.append(prompt)

        return batched

    # ------------------------------------------------------------------
    # 2. VLM response parsing
    # ------------------------------------------------------------------

    def parse_vlm_response(
        self,
        response: str,
        category: str,
        sub_type: str,
    ) -> Optional[NormalizedFinding]:
        """
        Parse a single VLM response into a NormalizedFinding.

        Handles both structured JSON responses and free-text responses.

        Args:
            response: Raw VLM response text
            category: Dark pattern category
            sub_type: Dark pattern sub-type

        Returns:
            NormalizedFinding if pattern was detected, None otherwise
        """
        if not response:
            return None

        response_lower = response.lower().strip()

        # Quick negative check
        negative_indicators = [
            "no dark pattern", "not detected", "no evidence",
            "does not appear", "not found", "none detected",
            '"detected": false', '"detected":false',
        ]
        if any(neg in response_lower for neg in negative_indicators):
            return None

        # Try JSON parse
        parsed = self._extract_json(response)
        if parsed:
            return self._json_to_finding(parsed, category, sub_type)

        # Free-text positive check
        positive_indicators = [
            "detected", "found", "yes", "present",
            "pattern identified", "dark pattern",
        ]
        if any(pos in response_lower for pos in positive_indicators):
            confidence = 0.5  # Lower confidence for free-text
            return NormalizedFinding(
                category=category,
                sub_type=sub_type,
                severity=self._get_severity(category, sub_type),
                severity_weight=get_severity_weight(category, sub_type),
                confidence=confidence,
                source="vlm",
                evidence=response[:200],
                raw_data={"raw_response": response},
            )

        return None

    def parse_batched_response(self, response: str) -> list[NormalizedFinding]:
        """
        Parse a batched VLM response that may contain multiple findings.

        Args:
            response: Raw VLM response text

        Returns:
            List of NormalizedFindings
        """
        findings = []
        parsed = self._extract_json(response)

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("detected", True):
                    cat = item.get("category", "unknown")
                    sub = item.get("sub_type", "unknown")
                    finding = self._json_to_finding(item, cat, sub)
                    if finding:
                        findings.append(finding)
        elif isinstance(parsed, dict):
            if parsed.get("detected", True):
                cat = parsed.get("category", "unknown")
                sub = parsed.get("sub_type", "unknown")
                finding = self._json_to_finding(parsed, cat, sub)
                if finding:
                    findings.append(finding)

        return findings

    # ------------------------------------------------------------------
    # 3. Finding normalisation from other sources
    # ------------------------------------------------------------------

    def normalize_dom_finding(self, dom_finding) -> NormalizedFinding:
        """
        Normalise a DOMFinding (from dom_analyzer) into our standard format.

        Args:
            dom_finding: DOMFinding dataclass from dom_analyzer

        Returns:
            NormalizedFinding
        """
        return NormalizedFinding(
            category=dom_finding.category,
            sub_type=dom_finding.finding_type,
            severity=dom_finding.severity,
            severity_weight=self._severity_to_weight(dom_finding.severity),
            confidence=dom_finding.confidence,
            source="dom",
            evidence=dom_finding.evidence,
            raw_data=dom_finding.element_data if hasattr(dom_finding, 'element_data') else {},
        )

    def normalize_temporal_finding(
        self,
        change_type: str,
        confidence: float,
        evidence: str,
        raw_data: dict = None,
    ) -> NormalizedFinding:
        """
        Normalise a temporal change detection into our standard format.

        Args:
            change_type: Type of temporal change (e.g., "fake_countdown")
            confidence: Detection confidence 0-1
            evidence: Human-readable description
            raw_data: Optional raw data dict

        Returns:
            NormalizedFinding
        """
        # Map temporal change types to taxonomy categories
        category_map = {
            "fake_countdown": "false_urgency",
            "slow_countdown": "false_urgency",
            "fake_scarcity": "false_urgency",
            "fake_social_proof": "social_engineering",
            "price_change": "sneaking",
        }
        category = category_map.get(change_type, "false_urgency")

        return NormalizedFinding(
            category=category,
            sub_type=change_type,
            severity="high",
            severity_weight=get_severity_weight(category, change_type),
            confidence=confidence,
            source="temporal",
            evidence=evidence,
            raw_data=raw_data or {},
        )

    # ------------------------------------------------------------------
    # 4. Scoring
    # ------------------------------------------------------------------

    def compute_match_result(
        self, findings: list[NormalizedFinding]
    ) -> MatchResult:
        """
        Compute aggregate scores from a list of normalised findings.

        Args:
            findings: All normalised findings from all sources

        Returns:
            MatchResult with per-category and overall scores
        """
        result = MatchResult(findings=findings, pattern_count=len(findings))

        if not findings:
            result.overall_visual_score = 0.7
            return result

        # Per-category worst-case score
        category_findings: dict[str, list[NormalizedFinding]] = {}
        for f in findings:
            category_findings.setdefault(f.category, []).append(f)

        for cat, cat_findings in category_findings.items():
            worst_deduction = max(
                f.severity_weight * f.confidence for f in cat_findings
            )
            result.category_scores[cat] = round(
                max(0.0, 1.0 - worst_deduction), 3
            )

        # Overall visual score: weighted average of category scores
        category_weights = {
            "visual_interference": 0.25,
            "false_urgency": 0.25,
            "forced_continuity": 0.15,
            "sneaking": 0.20,
            "social_engineering": 0.15,
        }

        weighted_sum = 0.0
        weight_total = 0.0
        for cat, score in result.category_scores.items():
            w = category_weights.get(cat, 0.10)
            weighted_sum += score * w
            weight_total += w

        # Categories without findings get neutral score
        for cat, w in category_weights.items():
            if cat not in result.category_scores:
                weighted_sum += 0.7 * w
                weight_total += w

        if weight_total > 0:
            result.overall_visual_score = round(weighted_sum / weight_total, 3)

        result.critical_count = sum(
            1 for f in findings if f.severity == "critical"
        )

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_json(self, text: str):
        """Extract JSON from VLM response text."""
        import json

        # Try direct parse
        try:
            return json.loads(text.strip())
        except (json.JSONDecodeError, ValueError):
            pass

        # Try ```json block
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass

        # Try finding any JSON object/array
        for pattern in [r'\{[^{}]*\}', r'\[[^\[\]]*\]']:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except (json.JSONDecodeError, ValueError):
                    pass

        return None

    def _json_to_finding(
        self, data: dict, category: str, sub_type: str
    ) -> Optional[NormalizedFinding]:
        """Convert parsed JSON dict to NormalizedFinding."""
        if not isinstance(data, dict):
            return None

        # Check for explicit non-detection
        if data.get("detected") is False:
            return None

        confidence = float(data.get("confidence", 0.6))
        if confidence < 0.2:
            return None

        # Use JSON-provided values or fall back to caller args
        actual_category = data.get("category", category)
        actual_sub = data.get("sub_type", sub_type)

        return NormalizedFinding(
            category=actual_category,
            sub_type=actual_sub,
            severity=data.get("severity", self._get_severity(actual_category, actual_sub)),
            severity_weight=get_severity_weight(actual_category, actual_sub),
            confidence=confidence,
            source="vlm",
            evidence=data.get("description", data.get("evidence", "")),
            raw_data=data,
        )

    def _get_severity(self, category: str, sub_type: str) -> str:
        """Look up severity from taxonomy."""
        cat_data = self._taxonomy.get(category)
        if cat_data:
            for sub in cat_data.sub_types:
                if sub.id == sub_type:
                    return sub.severity
        return "medium"

    @staticmethod
    def _severity_to_weight(severity: str) -> float:
        """Convert severity string to numeric weight."""
        return {
            "low": 0.2,
            "medium": 0.4,
            "high": 0.7,
            "critical": 1.0,
        }.get(severity, 0.4)
