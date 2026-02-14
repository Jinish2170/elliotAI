"""
Veritas Analysis — Temporal Analyzer

Compares Screenshot_A (t0) vs Screenshot_B (t+delay) at the pixel level
to detect visual changes that indicate deceptive dynamic content.

Methods:
    1. Pixel-diff: Compute structural similarity (SSIM) between screenshots
    2. Region-of-interest: Focus on timer/counter regions identified by VLM
    3. OCR-diff: Extract text from both, compare numeric values

This module works independently of VLM — it's the heuristic fallback
for temporal analysis when NIM credits are exhausted.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger("veritas.temporal")


# ============================================================
# Data Structures (reuse from vision agent)
# ============================================================

from agents.vision import TemporalFinding

# ============================================================
# Temporal Analyzer
# ============================================================

class TemporalAnalyzer:
    """
    Pixel-level and OCR-level temporal analysis.
    Works without NIM API — uses Pillow + optional Tesseract.

    Usage:
        analyzer = TemporalAnalyzer()
        findings = analyzer.compare_screenshots(
            t0_path="evidence/abc_t0.jpg",
            t_delay_path="evidence/abc_t10.jpg",
            delay_seconds=10,
        )

        for finding in findings:
            print(f"{finding.finding_type}: {finding.explanation}")
    """

    def compare_screenshots(
        self,
        t0_path: str,
        t_delay_path: str,
        delay_seconds: float = 10.0,
    ) -> list[TemporalFinding]:
        """
        Compare two screenshots captured at different times.

        Returns list of temporal findings (may be empty if no anomalies).
        """
        findings = []

        # Phase 1: Pixel-level similarity
        similarity = self._compute_similarity(t0_path, t_delay_path)
        if similarity is not None:
            # Very high similarity (>0.99) on a page with timers = suspicious
            # (timers should have visually changed)
            if similarity > 0.995:
                findings.append(TemporalFinding(
                    finding_type="static_page",
                    value_at_t0="(pixel analysis)",
                    value_at_t_delay="(pixel analysis)",
                    delta_seconds=delay_seconds,
                    is_suspicious=False,
                    explanation=(
                        f"Page is virtually identical between captures "
                        f"(similarity={similarity:.4f}). No dynamic content detected."
                    ),
                    confidence=0.6,
                ))

        # Phase 2: OCR-based text comparison
        ocr_findings = self._ocr_compare(t0_path, t_delay_path, delay_seconds)
        findings.extend(ocr_findings)

        return findings

    def _compute_similarity(
        self, path_a: str, path_b: str,
    ) -> Optional[float]:
        """
        Compute visual similarity between two images.
        Returns 0.0 (completely different) to 1.0 (identical).
        """
        try:
            import numpy as np
            from PIL import Image

            img_a = np.array(Image.open(path_a).convert("L").resize((640, 480)))
            img_b = np.array(Image.open(path_b).convert("L").resize((640, 480)))

            # Normalized cross-correlation (simpler than SSIM, no scipy needed)
            a_norm = (img_a - img_a.mean()) / (img_a.std() + 1e-8)
            b_norm = (img_b - img_b.mean()) / (img_b.std() + 1e-8)
            correlation = (a_norm * b_norm).mean()

            return float(max(0.0, min(1.0, correlation)))

        except ImportError:
            logger.debug("PIL/numpy not available for pixel comparison")
            return None
        except Exception as e:
            logger.warning(f"Pixel comparison failed: {e}")
            return None

    def _ocr_compare(
        self, t0_path: str, t_delay_path: str, delay_seconds: float,
    ) -> list[TemporalFinding]:
        """
        Extract text from both screenshots via OCR and compare
        numeric/timer values.
        """
        findings = []

        try:
            import pytesseract
            from PIL import Image

            text_a = pytesseract.image_to_string(Image.open(t0_path))
            text_b = pytesseract.image_to_string(Image.open(t_delay_path))
        except ImportError:
            logger.debug("Tesseract not available for OCR comparison")
            return findings
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return findings

        # Extract timer patterns (HH:MM:SS or MM:SS)
        timer_pattern = re.compile(r'\d{1,2}:\d{2}(?::\d{2})?')
        timers_a = timer_pattern.findall(text_a)
        timers_b = timer_pattern.findall(text_b)

        if timers_a and timers_b:
            for ta, tb in zip(timers_a, timers_b):
                seconds_a = self._timer_to_seconds(ta)
                seconds_b = self._timer_to_seconds(tb)

                if seconds_a is not None and seconds_b is not None:
                    expected_decrease = delay_seconds
                    actual_decrease = seconds_a - seconds_b

                    if seconds_b >= seconds_a:
                        # Timer went UP or stayed same — likely reset
                        findings.append(TemporalFinding(
                            finding_type="fake_countdown",
                            value_at_t0=ta,
                            value_at_t_delay=tb,
                            delta_seconds=delay_seconds,
                            is_suspicious=True,
                            explanation=(
                                f"Timer showed '{ta}' at t0 and '{tb}' at t+{delay_seconds}s. "
                                f"Timer did not decrease (went from {seconds_a}s to {seconds_b}s) — "
                                f"likely a fake countdown that resets."
                            ),
                            confidence=0.85,
                        ))
                    elif actual_decrease < expected_decrease * 0.5:
                        # Timer decreased less than expected — might be slowed
                        findings.append(TemporalFinding(
                            finding_type="slow_countdown",
                            value_at_t0=ta,
                            value_at_t_delay=tb,
                            delta_seconds=delay_seconds,
                            is_suspicious=True,
                            explanation=(
                                f"Timer showed '{ta}' at t0 and '{tb}' at t+{delay_seconds}s. "
                                f"Expected ~{expected_decrease}s decrease but only saw {actual_decrease:.0f}s — "
                                f"timer may be artificially slowed."
                            ),
                            confidence=0.6,
                        ))

        # Extract "Only X left" / "X people viewing" patterns
        stock_pattern = re.compile(r'(?:only\s+)?(\d+)\s*(?:left|remaining|available|in stock)', re.I)
        viewer_pattern = re.compile(r'(\d+)\s*(?:people|users?|visitors?)\s*(?:viewing|watching|looking)', re.I)

        for pattern, name in [(stock_pattern, "fake_scarcity"), (viewer_pattern, "fake_social_proof")]:
            match_a = pattern.search(text_a)
            match_b = pattern.search(text_b)

            if match_a and match_b:
                val_a = match_a.group(1)
                val_b = match_b.group(1)

                if val_a == val_b:
                    findings.append(TemporalFinding(
                        finding_type=name,
                        value_at_t0=match_a.group(0),
                        value_at_t_delay=match_b.group(0),
                        delta_seconds=delay_seconds,
                        is_suspicious=True,
                        explanation=(
                            f"'{name}' indicator shows '{match_a.group(0)}' at both time points "
                            f"({delay_seconds}s apart). Static values suggest fabricated data."
                        ),
                        confidence=0.7,
                    ))

        return findings

    def _timer_to_seconds(self, timer_str: str) -> Optional[int]:
        """Convert a timer string (MM:SS or HH:MM:SS) to total seconds."""
        try:
            parts = timer_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return None
        except (ValueError, IndexError):
            return None
