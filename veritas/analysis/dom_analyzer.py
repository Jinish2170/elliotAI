"""
Veritas Analysis — DOM Analyzer

Structural analysis of web page DOM to detect dark patterns
without any AI/VLM — pure rule-based CSS/HTML inspection.

This is the "zero AI" fallback layer. It works when NIM is down,
when credits are exhausted, or as a pre-filter before expensive VLM calls.

Detection capabilities:
    - Tiny/hidden unsubscribe links (font-size, opacity, color contrast)
    - Pre-selected checkboxes
    - Hidden form fields
    - Excessive tracking scripts
    - Missing privacy/terms links
    - Suspicious redirect chains
"""

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger("veritas.dom_analyzer")


@dataclass
class DOMFinding:
    """A structural finding from DOM analysis."""
    finding_type: str        # e.g., "hidden_unsubscribe", "pre_selected_checkbox"
    category: str            # Maps to dark_patterns taxonomy category
    severity: str            # "low", "medium", "high", "critical"
    confidence: float        # 0.0 to 1.0
    evidence: str            # Human-readable description
    selector: str = ""       # CSS selector that matched
    element_data: dict = field(default_factory=dict)


@dataclass
class DOMAnalysisResult:
    """Complete DOM structural analysis result."""
    findings: list[DOMFinding] = field(default_factory=list)
    structural_score: float = 0.5   # 0-1, higher = more trustworthy
    page_health: dict = field(default_factory=dict)  # General page health indicators
    errors: list[str] = field(default_factory=list)


class DOMAnalyzer:
    """
    Structural DOM analyzer for dark pattern detection.
    Designed to run inside a Playwright page context.

    Usage:
        analyzer = DOMAnalyzer()
        result = await analyzer.analyze(page)  # page = Playwright Page object

        for finding in result.findings:
            print(f"{finding.finding_type}: {finding.evidence}")
    """

    async def analyze(self, page) -> DOMAnalysisResult:
        """
        Run all DOM analysis checks on a Playwright page.

        Args:
            page: Playwright Page object (already navigated to target)

        Returns:
            DOMAnalysisResult with findings and structural score
        """
        result = DOMAnalysisResult()

        try:
            # Run all checks in parallel via JS evaluation
            dom_data = await self._extract_dom_signals(page)

            # Analyze each signal
            result.findings.extend(self._check_hidden_elements(dom_data))
            result.findings.extend(self._check_pre_selected(dom_data))
            result.findings.extend(self._check_forms(dom_data))
            result.findings.extend(self._check_tracking(dom_data))
            result.findings.extend(self._check_missing_pages(dom_data))
            result.findings.extend(self._check_dark_patterns_css(dom_data))

            # Page health metrics
            result.page_health = {
                "total_links": dom_data.get("total_links", 0),
                "total_scripts": dom_data.get("total_scripts", 0),
                "total_forms": dom_data.get("total_forms", 0),
                "has_privacy_link": dom_data.get("has_privacy_link", False),
                "has_terms_link": dom_data.get("has_terms_link", False),
                "has_contact_link": dom_data.get("has_contact_link", False),
                "external_script_count": dom_data.get("external_script_count", 0),
                "inline_script_count": dom_data.get("inline_script_count", 0),
            }

            # Compute structural score from findings
            result.structural_score = self._compute_score(result.findings)

        except Exception as e:
            logger.error(f"DOM analysis failed: {e}")
            result.errors.append(str(e))

        return result

    async def _extract_dom_signals(self, page) -> dict:
        """Extract all DOM signals in one JS evaluation for efficiency."""
        return await page.evaluate("""
            () => {
                // Helper: get computed style property
                const getStyle = (el, prop) => {
                    try {
                        return window.getComputedStyle(el)[prop];
                    } catch(e) { return ''; }
                };

                // Helper: parse color to RGB
                const parseColor = (color) => {
                    const temp = document.createElement('div');
                    temp.style.color = color;
                    document.body.appendChild(temp);
                    const computed = getComputedStyle(temp).color;
                    document.body.removeChild(temp);
                    const match = computed.match(/\\d+/g);
                    return match ? match.map(Number) : [0, 0, 0];
                };

                // Helper: compute contrast ratio
                const luminance = (r, g, b) => {
                    const [rs, gs, bs] = [r, g, b].map(c => {
                        c = c / 255;
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                    });
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                };

                const contrastRatio = (fg, bg) => {
                    const l1 = Math.max(luminance(...fg), luminance(...bg));
                    const l2 = Math.min(luminance(...fg), luminance(...bg));
                    return (l1 + 0.05) / (l2 + 0.05);
                };

                // 1. Find hidden/tiny unsubscribe/cancel links
                const suspiciousLinks = [];
                const keywords = ['unsubscribe', 'cancel', 'opt-out', 'opt out', 'decline', 'reject', 'close', 'dismiss', 'no thanks'];
                document.querySelectorAll('a, button, [role="button"]').forEach(el => {
                    const text = (el.textContent || '').trim().toLowerCase();
                    if (keywords.some(kw => text.includes(kw))) {
                        const fontSize = parseFloat(getStyle(el, 'fontSize')) || 16;
                        const opacity = parseFloat(getStyle(el, 'opacity'));
                        const color = parseColor(getStyle(el, 'color'));
                        const bgEl = el.parentElement || document.body;
                        const bgColor = parseColor(getStyle(bgEl, 'backgroundColor'));
                        const contrast = contrastRatio(color, bgColor);
                        const display = getStyle(el, 'display');
                        const visibility = getStyle(el, 'visibility');

                        suspiciousLinks.push({
                            text: text.substring(0, 50),
                            tag: el.tagName,
                            fontSize,
                            opacity,
                            contrast: Math.round(contrast * 100) / 100,
                            display,
                            visibility,
                            isHidden: display === 'none' || visibility === 'hidden' || opacity < 0.3,
                            isTiny: fontSize < 11,
                            isLowContrast: contrast < 3,
                        });
                    }
                });

                // 2. Find pre-selected checkboxes
                const preSelected = [];
                document.querySelectorAll('input[type="checkbox"][checked], input[type="checkbox"]:checked').forEach(el => {
                    const label = el.labels?.[0]?.textContent?.trim() ||
                                  el.parentElement?.textContent?.trim() || '';
                    const name = el.name || el.id || '';
                    preSelected.push({
                        name,
                        label: label.substring(0, 100),
                        isInForm: !!el.closest('form'),
                    });
                });

                // 3. Form analysis
                const forms = [];
                document.querySelectorAll('form').forEach(f => {
                    const hiddenInputs = f.querySelectorAll('input[type="hidden"]');
                    const passwordInputs = f.querySelectorAll('input[type="password"]');
                    forms.push({
                        action: f.action || '',
                        method: f.method || 'GET',
                        hiddenInputCount: hiddenInputs.length,
                        hasPassword: passwordInputs.length > 0,
                        hiddenNames: Array.from(hiddenInputs).map(i => i.name).filter(Boolean).slice(0, 5),
                    });
                });

                // 4. Script analysis
                const scripts = document.querySelectorAll('script');
                const externalScripts = document.querySelectorAll('script[src]');
                const trackerDomains = ['google-analytics', 'facebook', 'doubleclick', 'hotjar',
                    'mixpanel', 'segment', 'amplitude', 'optimizely', 'crazyegg'];
                const trackers = Array.from(externalScripts).filter(s =>
                    trackerDomains.some(d => (s.src || '').includes(d))
                ).map(s => s.src);

                // 5. Important page links
                const allLinks = Array.from(document.querySelectorAll('a[href]'));
                const linkTexts = allLinks.map(a => ({
                    text: (a.textContent || '').trim().toLowerCase(),
                    href: a.href || ''
                }));

                const hasPrivacy = linkTexts.some(l =>
                    l.text.includes('privacy') || l.href.includes('privacy'));
                const hasTerms = linkTexts.some(l =>
                    l.text.includes('terms') || l.text.includes('tos') || l.href.includes('terms'));
                const hasContact = linkTexts.some(l =>
                    l.text.includes('contact') || l.href.includes('contact'));

                return {
                    suspiciousLinks,
                    preSelected,
                    forms,
                    total_links: allLinks.length,
                    total_scripts: scripts.length,
                    total_forms: forms.length,
                    external_script_count: externalScripts.length,
                    inline_script_count: scripts.length - externalScripts.length,
                    trackers,
                    has_privacy_link: hasPrivacy,
                    has_terms_link: hasTerms,
                    has_contact_link: hasContact,
                };
            }
        """)

    def _check_hidden_elements(self, data: dict) -> list[DOMFinding]:
        """Check for hidden/tiny unsubscribe/cancel/decline elements."""
        findings = []
        for link in data.get("suspiciousLinks", []):
            issues = []
            if link.get("isHidden"):
                issues.append("hidden (display:none / visibility:hidden / very low opacity)")
            if link.get("isTiny"):
                issues.append(f"tiny font ({link.get('fontSize')}px)")
            if link.get("isLowContrast"):
                issues.append(f"low contrast ({link.get('contrast')}:1)")

            if issues:
                findings.append(DOMFinding(
                    finding_type="hidden_element",
                    category="visual_interference",
                    severity="high" if link.get("isHidden") else "medium",
                    confidence=0.8,
                    evidence=(
                        f"'{link.get('text', '')}' element is {', '.join(issues)}"
                    ),
                    element_data=link,
                ))
        return findings

    def _check_pre_selected(self, data: dict) -> list[DOMFinding]:
        """Check for pre-selected checkboxes (sneaking pattern)."""
        findings = []
        for cb in data.get("preSelected", []):
            label = cb.get("label", "")
            # Skip obvious/benign checkboxes
            benign_keywords = ["remember me", "keep me signed", "stay signed"]
            if any(bk in label.lower() for bk in benign_keywords):
                continue

            findings.append(DOMFinding(
                finding_type="pre_selected_checkbox",
                category="sneaking",
                severity="high" if cb.get("isInForm") else "medium",
                confidence=0.75,
                evidence=f"Pre-selected checkbox: '{label[:80]}'",
                element_data=cb,
            ))
        return findings

    def _check_forms(self, data: dict) -> list[DOMFinding]:
        """Check for suspicious form patterns."""
        findings = []
        for form in data.get("forms", []):
            if form.get("hiddenInputCount", 0) > 5:
                findings.append(DOMFinding(
                    finding_type="excessive_hidden_inputs",
                    category="sneaking",
                    severity="medium",
                    confidence=0.5,
                    evidence=(
                        f"Form with {form['hiddenInputCount']} hidden inputs "
                        f"(names: {form.get('hiddenNames', [])})"
                    ),
                    element_data=form,
                ))
        return findings

    def _check_tracking(self, data: dict) -> list[DOMFinding]:
        """Check for excessive tracking scripts."""
        trackers = data.get("trackers", [])
        if len(trackers) > 5:
            return [DOMFinding(
                finding_type="excessive_tracking",
                category="sneaking",
                severity="low",
                confidence=0.6,
                evidence=f"Page loads {len(trackers)} tracking scripts: {', '.join(t[:50] for t in trackers[:5])}",
            )]
        return []

    def _check_missing_pages(self, data: dict) -> list[DOMFinding]:
        """Check for missing privacy/terms/contact pages (legitimacy signal)."""
        findings = []
        if not data.get("has_privacy_link"):
            findings.append(DOMFinding(
                finding_type="missing_privacy_policy",
                category="social_engineering",
                severity="medium",
                confidence=0.6,
                evidence="No privacy policy link found on the page",
            ))
        if not data.get("has_terms_link"):
            findings.append(DOMFinding(
                finding_type="missing_terms",
                category="social_engineering",
                severity="low",
                confidence=0.5,
                evidence="No terms of service link found on the page",
            ))
        return findings

    def _check_dark_patterns_css(self, data: dict) -> list[DOMFinding]:
        """Additional CSS-based dark pattern checks."""
        # This is a placeholder for additional structural checks
        # that can be expanded as more patterns are identified
        raise NotImplementedError(
            "_check_dark_patterns_css(): Additional CSS-based dark pattern checks not yet implemented. "
            "This method is a placeholder for future structural checks."
        )

    def _compute_score(self, findings: list[DOMFinding]) -> float:
        """Compute structural score from DOM findings."""
        if not findings:
            return 0.7  # No findings → slightly positive

        severity_weights = {"low": 0.05, "medium": 0.10, "high": 0.20, "critical": 0.30}
        total_deduction = sum(
            severity_weights.get(f.severity, 0.1) * f.confidence
            for f in findings
        )

        return round(max(0.0, min(1.0, 0.8 - total_deduction)), 3)
