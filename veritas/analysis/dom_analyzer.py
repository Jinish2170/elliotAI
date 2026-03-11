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
            result.findings.extend(self._check_cookie_consent(dom_data))
            result.findings.extend(self._check_popup_modals(dom_data))
            result.findings.extend(self._check_subscription_traps(dom_data))

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

                    // Phase 17: Cookie consent analysis
                    cookieConsent: (() => {
                        const bannerSels = [
                            '[class*="cookie" i]', '[id*="cookie" i]',
                            '[class*="consent" i]', '[id*="consent" i]',
                            '[class*="gdpr" i]', '[id*="gdpr" i]',
                            '[class*="onetrust" i]', '#CybotCookiebotDialog',
                        ];
                        let banner = null;
                        for (const s of bannerSels) {
                            try { banner = document.querySelector(s); if (banner) break; } catch(e) {}
                        }
                        if (!banner) return { found: false };

                        const buttons = Array.from(banner.querySelectorAll('button, a[role="button"], [class*="btn" i]'));
                        const acceptBtn = buttons.find(b => /accept|agree|allow|got it|ok/i.test(b.textContent));
                        const rejectBtn = buttons.find(b => /reject|decline|deny|refuse|necessary only|essential/i.test(b.textContent));
                        const manageBtn = buttons.find(b => /manage|settings|preferences|customize|options/i.test(b.textContent));

                        const btnInfo = (el) => {
                            if (!el) return null;
                            const r = el.getBoundingClientRect();
                            return {
                                text: (el.textContent || '').trim().substring(0, 60),
                                width: r.width, height: r.height,
                                fontSize: parseFloat(getStyle(el, 'fontSize')) || 14,
                                bgColor: getStyle(el, 'backgroundColor'),
                                color: getStyle(el, 'color'),
                                tag: el.tagName,
                            };
                        };
                        return {
                            found: true,
                            acceptButton: btnInfo(acceptBtn),
                            rejectButton: btnInfo(rejectBtn),
                            manageButton: btnInfo(manageBtn),
                            totalButtons: buttons.length,
                        };
                    })(),

                    // Phase 17: Popup / modal analysis
                    popups: (() => {
                        const modalSels = [
                            '[class*="modal" i]', '[class*="popup" i]', '[class*="overlay" i]',
                            '[role="dialog"]', '[aria-modal="true"]',
                        ];
                        const results = [];
                        for (const s of modalSels) {
                            try {
                                document.querySelectorAll(s).forEach(el => {
                                    const display = getStyle(el, 'display');
                                    const visibility = getStyle(el, 'visibility');
                                    if (display === 'none' || visibility === 'hidden') return;
                                    const rect = el.getBoundingClientRect();
                                    if (rect.width < 100 || rect.height < 50) return;

                                    const closeBtn = el.querySelector('[class*="close" i], [aria-label*="close" i], button:has(svg)');
                                    const closeSize = closeBtn ? closeBtn.getBoundingClientRect() : null;
                                    results.push({
                                        selector: s,
                                        coversViewport: rect.width > window.innerWidth * 0.7 && rect.height > window.innerHeight * 0.5,
                                        hasCloseButton: !!closeBtn,
                                        closeButtonTiny: closeSize ? (closeSize.width < 20 || closeSize.height < 20) : false,
                                        hasEmailInput: !!el.querySelector('input[type="email"]'),
                                        text: (el.textContent || '').trim().substring(0, 200),
                                    });
                                });
                            } catch(e) {}
                        }
                        return results;
                    })(),

                    // Phase 17: Subscription / auto-renewal traps
                    subscriptionTraps: (() => {
                        const body = document.body.innerText || '';
                        const patterns = {
                            autoRenew: /auto[- ]?renew|automatically\s+(?:renew|charge|bill)/i.test(body),
                            freeTrialBilling: /free\s+trial.*(?:credit\s+card|billing|payment)|(?:credit\s+card|payment).*free\s+trial/i.test(body),
                            hiddenRecurring: /recurring\s+charge|billed\s+(?:monthly|annually|weekly)|subscription\s+fee/i.test(body),
                            cancelAnytime: /cancel\s+(?:any\s*time|at\s+any)/i.test(body),
                        };
                        // Check if recurring/billing text is in fine print
                        const finePrintEls = document.querySelectorAll('.fine-print, .terms, .disclaimer, [class*="small-text" i], [class*="legal" i]');
                        let billingInFinePrint = false;
                        finePrintEls.forEach(el => {
                            if (/billed|charged|renew|recurring/i.test(el.textContent || '')) {
                                billingInFinePrint = true;
                            }
                        });
                        patterns.billingInFinePrint = billingInFinePrint;
                        return patterns;
                    })(),
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
        """Additional CSS-based dark pattern checks beyond hidden-element scanning."""
        findings = []

        # Check for suspiciously low-contrast links that aren't already caught
        # by _check_hidden_elements (which focuses on action keywords).
        for link in data.get("suspiciousLinks", []):
            # Extremely low contrast (< 1.5:1) on non-hidden elements is a
            # strong dark pattern signal — text blends into background.
            if (link.get("contrast", 4.5) < 1.5
                    and not link.get("isHidden")
                    and not link.get("isTiny")):
                findings.append(DOMFinding(
                    finding_type="near_invisible_text",
                    category="visual_interference",
                    severity="high",
                    confidence=0.8,
                    evidence=(
                        f"Link '{link.get('text', '')}' has near-invisible "
                        f"contrast ratio {link.get('contrast')}:1 (WCAG minimum 4.5:1)"
                    ),
                ))

        # Check for excessive hidden form inputs (data harvesting signal)
        for form in data.get("forms", []):
            hidden_count = form.get("hiddenInputCount", 0)
            if hidden_count > 5:
                findings.append(DOMFinding(
                    finding_type="excessive_hidden_inputs",
                    category="data_harvesting",
                    severity="medium",
                    confidence=0.6,
                    evidence=(
                        f"Form with action='{form.get('action', '')}' contains "
                        f"{hidden_count} hidden inputs (possible tracking/fingerprinting)"
                    ),
                ))

        return findings

    def _check_cookie_consent(self, data: dict) -> list[DOMFinding]:
        """Check cookie consent banners for manipulative dark patterns."""
        findings = []
        consent = data.get("cookieConsent", {})
        if not consent.get("found"):
            return findings

        accept = consent.get("acceptButton")
        reject = consent.get("rejectButton")
        manage = consent.get("manageButton")

        # No reject/decline option at all — forced consent
        if accept and not reject:
            # "Manage" alone doesn't count as easy rejection
            findings.append(DOMFinding(
                finding_type="forced_cookie_consent",
                category="sneaking",
                severity="high",
                confidence=0.8,
                evidence=(
                    "Cookie banner has an 'Accept' button but no 'Reject' or 'Decline' option. "
                    "Users are forced to accept all cookies or dig into settings."
                ),
            ))

        # Accept button visually dominant over reject
        if accept and reject:
            a_area = (accept.get("width", 0) or 0) * (accept.get("height", 0) or 0)
            r_area = (reject.get("width", 0) or 0) * (reject.get("height", 0) or 0)
            a_font = accept.get("fontSize", 14) or 14
            r_font = reject.get("fontSize", 14) or 14

            if a_area > 0 and r_area > 0 and a_area > r_area * 2:
                findings.append(DOMFinding(
                    finding_type="cookie_accept_dominant",
                    category="visual_interference",
                    severity="medium",
                    confidence=0.7,
                    evidence=(
                        f"'Accept' button ({accept.get('text', '')}) is {a_area / r_area:.1f}x "
                        f"larger than 'Reject' button ({reject.get('text', '')})"
                    ),
                ))
            elif a_font > r_font * 1.3:
                findings.append(DOMFinding(
                    finding_type="cookie_accept_dominant",
                    category="visual_interference",
                    severity="medium",
                    confidence=0.65,
                    evidence=(
                        f"'Accept' button font ({a_font}px) is larger than "
                        f"'Reject' button font ({r_font}px)"
                    ),
                ))

        return findings

    def _check_popup_modals(self, data: dict) -> list[DOMFinding]:
        """Check for aggressive popup/modal patterns."""
        findings = []
        popups = data.get("popups", [])
        for popup in popups:
            # Full-viewport overlay blocking content
            if popup.get("coversViewport"):
                severity = "high"
                issues = ["covers most of the viewport"]

                if popup.get("hasEmailInput"):
                    issues.append("requests email address")

                if not popup.get("hasCloseButton"):
                    severity = "critical"
                    issues.append("no visible close button")
                elif popup.get("closeButtonTiny"):
                    issues.append("close button is very small")

                findings.append(DOMFinding(
                    finding_type="aggressive_popup",
                    category="forced_continuity",
                    severity=severity,
                    confidence=0.7,
                    evidence=f"Popup/modal detected: {', '.join(issues)}",
                    element_data=popup,
                ))

        return findings

    def _check_subscription_traps(self, data: dict) -> list[DOMFinding]:
        """Check for hidden subscription/auto-renewal traps."""
        findings = []
        traps = data.get("subscriptionTraps", {})

        if traps.get("freeTrialBilling"):
            findings.append(DOMFinding(
                finding_type="free_trial_billing",
                category="sneaking",
                severity="high",
                confidence=0.75,
                evidence=(
                    "Page mentions free trial alongside payment/billing requirements. "
                    "Users may be charged without clear opt-in."
                ),
            ))

        if traps.get("billingInFinePrint") and traps.get("hiddenRecurring"):
            findings.append(DOMFinding(
                finding_type="hidden_recurring_charge",
                category="sneaking",
                severity="high",
                confidence=0.7,
                evidence=(
                    "Recurring billing terms are buried in fine print or legal text, "
                    "not prominently displayed with the pricing."
                ),
            ))

        if traps.get("autoRenew") and not traps.get("cancelAnytime"):
            findings.append(DOMFinding(
                finding_type="auto_renew_no_cancel",
                category="forced_continuity",
                severity="medium",
                confidence=0.6,
                evidence=(
                    "Page mentions auto-renewal but does not clearly state "
                    "that users can cancel at any time."
                ),
            ))

        return findings

        return findings

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
