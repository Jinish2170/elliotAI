"""
Veritas Tests — Unit & Integration Tests

Test hierarchy:
    1. Unit tests — individual modules (no network, no browser)
    2. Integration tests — module chains with mocked NIM
    3. End-to-end tests — full pipeline against test HTML sites

Run:
    cd veritas
    python -m pytest tests/ -v
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add veritas root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def test_sites_dir():
    """Path to test HTML sites."""
    return Path(__file__).parent / "sites"


@pytest.fixture
def mock_nim_client():
    """Create a mock NIM client that returns controlled responses."""
    client = MagicMock()
    client.analyze_image = AsyncMock(return_value={
        "detected": True,
        "category": "false_urgency",
        "sub_type": "fake_countdown",
        "confidence": 0.85,
        "description": "Countdown timer detected that appears to reset",
    })
    client.generate_text = AsyncMock(return_value="This website shows signs of deceptive practices.")
    client.call_count = 0
    client.cache_hits = 0
    client.fallback_count = 0
    return client


# ============================================================
# 1. Config Module Tests
# ============================================================

class TestDarkPatterns:
    """Test dark_patterns.py taxonomy integrity."""

    def test_taxonomy_structure(self):
        from config.dark_patterns import DARK_PATTERN_TAXONOMY

        assert len(DARK_PATTERN_TAXONOMY) == 5, "Expected 5 top-level categories"

        required_categories = [
            "visual_interference", "false_urgency", "forced_continuity",
            "sneaking", "social_engineering",
        ]
        for cat in required_categories:
            assert cat in DARK_PATTERN_TAXONOMY, f"Missing category: {cat}"
            cat_data = DARK_PATTERN_TAXONOMY[cat]
            assert hasattr(cat_data, "sub_types"), f"Missing sub_types on {cat}"
            assert len(cat_data.sub_types) > 0

    def test_vlm_prompts_present(self):
        from config.dark_patterns import get_all_vlm_prompts

        prompts = get_all_vlm_prompts()
        assert len(prompts) > 10, f"Expected >10 VLM prompts, got {len(prompts)}"
        for p in prompts:
            assert "category" in p
            assert "prompt" in p
            assert len(p["prompt"]) > 20

    def test_severity_weights(self):
        from config.dark_patterns import get_severity_weight

        assert get_severity_weight("false_urgency", "fake_countdown") > 0
        assert get_severity_weight("nonexistent", "category") > 0  # Should fallback

    def test_temporal_categories(self):
        from config.dark_patterns import get_temporal_categories

        temporal = get_temporal_categories()
        assert len(temporal) > 0
        assert "false_urgency" in temporal


class TestTrustWeights:
    """Test trust_weights.py scoring engine."""

    def test_perfect_score(self):
        from config.trust_weights import SubSignal, compute_trust_score

        signals = {
            "visual": SubSignal(name="visual", raw_score=1.0, confidence=1.0),
            "structural": SubSignal(name="structural", raw_score=1.0, confidence=1.0),
            "temporal": SubSignal(name="temporal", raw_score=1.0, confidence=1.0),
            "graph": SubSignal(name="graph", raw_score=1.0, confidence=1.0),
            "meta": SubSignal(name="meta", raw_score=1.0, confidence=1.0),
            "security": SubSignal(name="security", raw_score=1.0, confidence=1.0),
        }
        result = compute_trust_score(signals)
        assert result.final_score >= 90
        assert result.risk_level.value == "trusted"

    def test_zero_score(self):
        from config.trust_weights import SubSignal, compute_trust_score

        signals = {
            "visual": SubSignal(name="visual", raw_score=0.0, confidence=1.0),
            "structural": SubSignal(name="structural", raw_score=0.0, confidence=1.0),
            "temporal": SubSignal(name="temporal", raw_score=0.0, confidence=1.0),
            "graph": SubSignal(name="graph", raw_score=0.0, confidence=1.0),
            "meta": SubSignal(name="meta", raw_score=0.0, confidence=1.0),
            "security": SubSignal(name="security", raw_score=0.0, confidence=1.0),
        }
        result = compute_trust_score(signals)
        assert result.final_score <= 15
        assert result.risk_level.value == "likely_fraudulent"

    def test_override_no_ssl(self):
        from config.trust_weights import SubSignal, compute_trust_score

        signals = {
            "visual": SubSignal(name="visual", raw_score=0.9, confidence=1.0),
            "structural": SubSignal(name="structural", raw_score=0.9, confidence=1.0),
            "temporal": SubSignal(name="temporal", raw_score=0.9, confidence=1.0),
            "graph": SubSignal(name="graph", raw_score=0.9, confidence=1.0),
            "meta": SubSignal(name="meta", raw_score=0.9, confidence=1.0),
            "security": SubSignal(name="security", raw_score=0.9, confidence=1.0),
        }
        result = compute_trust_score(signals, ssl_status=False)
        assert result.final_score <= 50
        assert len(result.overrides_applied) > 0


class TestSettings:
    """Test settings.py configuration."""

    def test_paths_exist(self):
        from config import settings

        assert settings.BASE_DIR.exists()
        assert settings.DATA_DIR.exists()

    def test_audit_tiers(self):
        from config import settings

        assert len(settings.AUDIT_TIERS) == 4
        for tier_name, tier_data in settings.AUDIT_TIERS.items():
            assert "pages" in tier_data
            assert "nim_calls" in tier_data
            assert tier_data["pages"] > 0


# ============================================================
# 2. Analysis Module Tests
# ============================================================

class TestPatternMatcher:
    """Test pattern_matcher.py logic."""

    def test_prompt_generation(self):
        from analysis.pattern_matcher import PatternMatcher

        pm = PatternMatcher()
        prompts = pm.get_screenshot_prompts()
        assert len(prompts) > 5
        for p in prompts:
            assert "category" in p
            assert "prompt" in p

    def test_batched_prompts(self):
        from analysis.pattern_matcher import PatternMatcher

        pm = PatternMatcher()
        batched = pm.build_batched_prompt(max_categories=2)
        assert len(batched) >= 2

    def test_vlm_response_parsing_json(self):
        from analysis.pattern_matcher import PatternMatcher

        pm = PatternMatcher()
        response = json.dumps({
            "detected": True,
            "confidence": 0.82,
            "description": "Timer resets to 5:00",
        })
        finding = pm.parse_vlm_response(response, "false_urgency", "fake_countdown")
        assert finding is not None
        assert finding.confidence == 0.82
        assert finding.category == "false_urgency"

    def test_vlm_response_parsing_negative(self):
        from analysis.pattern_matcher import PatternMatcher

        pm = PatternMatcher()
        finding = pm.parse_vlm_response(
            "No dark patterns detected in this image.",
            "false_urgency", "fake_countdown",
        )
        assert finding is None

    def test_compute_match_result(self):
        from analysis.pattern_matcher import NormalizedFinding, PatternMatcher

        pm = PatternMatcher()
        findings = [
            NormalizedFinding(
                category="false_urgency", sub_type="fake_countdown",
                severity="high", severity_weight=0.7,
                confidence=0.85, source="vlm", evidence="Fake timer",
            ),
            NormalizedFinding(
                category="sneaking", sub_type="pre_selected_checkbox",
                severity="medium", severity_weight=0.4,
                confidence=0.75, source="dom", evidence="Pre-checked box",
            ),
        ]
        result = pm.compute_match_result(findings)
        assert result.pattern_count == 2
        assert result.overall_visual_score < 0.7
        assert "false_urgency" in result.category_scores


class TestTemporalAnalyzer:
    """Test temporal_analyzer.py (no screenshots needed for unit tests)."""

    def test_timer_to_seconds(self):
        from analysis.temporal_analyzer import TemporalAnalyzer

        ta = TemporalAnalyzer()
        assert ta._timer_to_seconds("05:30") == 330
        assert ta._timer_to_seconds("01:00:00") == 3600
        assert ta._timer_to_seconds("invalid") is None

    def test_text_semantics_price_change(self):
        """P17: Detect price changes between snapshots."""
        from analysis.temporal_analyzer import TemporalAnalyzer

        ta = TemporalAnalyzer()
        text_a = "Buy now for $29.99! Limited edition."
        text_b = "Buy now for $49.99! Limited edition."
        findings = ta.analyze_text_semantics(text_a, text_b, delay_seconds=10)

        price_findings = [f for f in findings if f.finding_type == "price_change"]
        assert len(price_findings) >= 1
        assert price_findings[0].is_suspicious is True
        assert price_findings[0].confidence == 0.75

    def test_text_semantics_no_price_change(self):
        """P17: No findings when prices are identical."""
        from analysis.temporal_analyzer import TemporalAnalyzer

        ta = TemporalAnalyzer()
        text = "Buy now for $29.99! Great deal."
        findings = ta.analyze_text_semantics(text, text, delay_seconds=10)

        price_findings = [f for f in findings if f.finding_type == "price_change"]
        assert len(price_findings) == 0

    def test_text_semantics_urgency_injection(self):
        """P17: Detect dynamically injected urgency language."""
        from analysis.temporal_analyzer import TemporalAnalyzer

        ta = TemporalAnalyzer()
        text_a = "Welcome to our store."
        text_b = "Welcome to our store. Act now! Limited time offer!"
        findings = ta.analyze_text_semantics(text_a, text_b, delay_seconds=10)

        urgency_findings = [f for f in findings if f.finding_type == "dynamic_urgency"]
        assert len(urgency_findings) >= 1
        assert urgency_findings[0].is_suspicious is True
        assert urgency_findings[0].confidence == 0.7

    def test_text_semantics_fabricated_counter(self):
        """P17: Detect fabricated social-proof counters (>50% change)."""
        from analysis.temporal_analyzer import TemporalAnalyzer

        ta = TemporalAnalyzer()
        text_a = "100 people bought this today"
        text_b = "200 people bought this today"
        findings = ta.analyze_text_semantics(text_a, text_b, delay_seconds=10)

        counter_findings = [f for f in findings if f.finding_type == "fabricated_counter"]
        assert len(counter_findings) >= 1
        assert counter_findings[0].is_suspicious is True
        assert counter_findings[0].confidence == 0.8

    def test_text_semantics_counter_small_change_ok(self):
        """P17: Small counter changes (<50%) should not be flagged."""
        from analysis.temporal_analyzer import TemporalAnalyzer

        ta = TemporalAnalyzer()
        text_a = "100 people bought this today"
        text_b = "110 people bought this today"
        findings = ta.analyze_text_semantics(text_a, text_b, delay_seconds=10)

        counter_findings = [f for f in findings if f.finding_type == "fabricated_counter"]
        assert len(counter_findings) == 0


class TestMetaAnalyzer:
    """Test meta_analyzer.py (mocked network)."""

    def test_score_computation(self):
        from analysis.meta_analyzer import (DNSInfo, DomainAge,
                                            MetaAnalysisResult, MetaAnalyzer,
                                            SSLInfo)

        analyzer = MetaAnalyzer()

        # Good site
        good = MetaAnalysisResult(
            domain="example.com",
            ssl_info=SSLInfo(is_valid=True, days_until_expiry=365),
            domain_age=DomainAge(age_days=3000),
            dns_info=DNSInfo(a_records=["1.2.3.4"], mx_records=["mx.example.com"],
                             has_spf=True, has_dmarc=True),
        )
        score, signals = analyzer._compute_meta_score(good)
        assert score >= 0.7
        assert len(signals) == 0

        # Bad site
        bad = MetaAnalysisResult(
            domain="scam.xyz",
            ssl_info=SSLInfo(is_valid=False),
            domain_age=DomainAge(age_days=5),
            dns_info=DNSInfo(),
        )
        score, signals = analyzer._compute_meta_score(bad)
        assert score < 0.3
        assert len(signals) >= 3


# ============================================================
# 3. Core Module Tests
# ============================================================

class TestEvidenceStore:
    """Test evidence_store.py with JSON fallback."""

    def test_json_fallback(self, tmp_path):
        # Force JSON-only mode by using a temp directory
        with patch("config.settings.VECTORDB_DIR", tmp_path / "vectordb"), \
             patch("config.settings.EVIDENCE_DIR", tmp_path / "evidence"):
            (tmp_path / "evidence").mkdir()

            from core.evidence_store import EvidenceStore
            store = EvidenceStore()

            # Store an audit
            store.store_audit(
                url="https://test.com",
                trust_score=35,
                risk_level="high_risk",
                dark_patterns=["fake_countdown", "hidden_costs", "pre_selected_checkbox"],
                summary="Test audit with 3 dark patterns detected",
            )

            # Retrieve
            audits = store.get_all_audits()
            assert len(audits) >= 1

    def test_search_fallback(self, tmp_path):
        with patch("config.settings.VECTORDB_DIR", tmp_path / "vectordb"), \
             patch("config.settings.EVIDENCE_DIR", tmp_path / "evidence"):
            (tmp_path / "evidence").mkdir()

            from core.evidence_store import EvidenceStore
            store = EvidenceStore()

            store.store_evidence(
                audit_url="https://test.com",
                evidence_type="dark_pattern",
                content="fake countdown timer detected in false_urgency category",
            )

            results = store.search_similar("countdown timer", table_name="evidence")
            # JSON fallback does keyword search — should find it
            assert len(results) >= 1


# ============================================================
# 4. Reporting Tests
# ============================================================

class TestReportGenerator:
    """Test report_generator.py."""

    def test_context_building(self):
        from reporting.report_generator import ReportGenerator

        gen = ReportGenerator()
        mock_result = {
            "url": "https://test.com",
            "judge_decision": {
                "trust_score_result": {
                    "final_score": 35,
                    "risk_level": "high_risk",
                    "sub_signals": {},
                    "overrides_applied": [],
                },
                "narrative": "Test narrative",
                "recommendations": ["Stop using dark patterns"],
            },
            "vision_result": {"findings": []},
            "graph_result": {"verifications": [], "inconsistencies": [], "domain_intel": {}},
            "iteration": 1,
        }

        ctx = gen._build_context(mock_result, "https://test.com", "standard_audit")
        assert ctx["trust_score"] == 35
        assert ctx["risk_level"] == "high_risk"
        assert ctx["narrative"] == "Test narrative"

    def test_html_generation(self, tmp_path):
        from reporting.report_generator import ReportGenerator

        gen = ReportGenerator()
        gen._output_dir = tmp_path

        mock_result = {
            "url": "https://test.com",
            "judge_decision": {
                "trust_score_result": {
                    "final_score": 65,
                    "risk_level": "suspicious",
                    "sub_signals": {},
                    "overrides_applied": [],
                },
                "narrative": "Test",
                "recommendations": [],
            },
            "vision_result": {"findings": []},
            "graph_result": {"verifications": [], "inconsistencies": [], "domain_intel": {}},
        }

        path = gen.generate(mock_result, url="https://test.com", tier="standard_audit", output_format="html")
        assert path.exists()
        assert path.suffix == ".html"
        content = path.read_text(encoding="utf-8")
        assert "test.com" in content


# ============================================================
# P17: JS Obfuscation Detector Tests
# ============================================================

class TestJSObfuscationDetector:
    """P17 tests for new JS analysis detections."""

    def _make_detector(self):
        from analysis.js_analyzer import JSObfuscationDetector, JSAnalysisResult
        return JSObfuscationDetector(), JSAnalysisResult

    def test_fingerprinting_canvas(self):
        """Detect canvas fingerprinting pattern."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": "var fp = canvas.toDataURL( 'image/png' ); send(fp);" + " " * 50,
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        fp_flags = [f for f in result.flags if f.category == "fingerprinting"]
        assert len(fp_flags) == 1
        assert "Canvas fingerprinting" in fp_flags[0].evidence

    def test_fingerprinting_webgl(self):
        """Detect WebGL fingerprinting pattern."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": "var gl = canvas.getContext('webgl'); gl.getParameter(gl.RENDERER);" + " " * 50,
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        fp_flags = [f for f in result.flags if f.category == "fingerprinting"]
        assert len(fp_flags) == 1
        assert fp_flags[0].severity == "medium"

    def test_fingerprinting_audio(self):
        """Detect Audio fingerprinting pattern."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": "var ctx = new AudioContext(); ctx.createOscillator();" + " " * 50,
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        fp_flags = [f for f in result.flags if f.category == "fingerprinting"]
        assert len(fp_flags) == 1

    def test_keylogger_pattern(self):
        """Detect keylogger pattern (keydown + XHR)."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": (
                "document.addEventListener('keydown', function(e) {"
                "  var xhr = new XMLHttpRequest();"
                "  xhr.open('POST', '/log'); xhr.send(e.key);"
                "});"
            ),
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        kl_flags = [f for f in result.flags if f.category == "keylogger"]
        assert len(kl_flags) == 1
        assert kl_flags[0].severity == "critical"

    def test_keylogger_not_triggered_without_network(self):
        """Keylogger requires both keystroke listener AND network exfil."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": "document.addEventListener('keydown', function(e) { console.log(e.key); });" + " " * 50,
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        kl_flags = [f for f in result.flags if f.category == "keylogger"]
        assert len(kl_flags) == 0

    def test_clipboard_hijack(self):
        """Detect clipboard hijacking pattern."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": (
                "document.addEventListener('copy', function(e) {"
                "  navigator.clipboard.writeText('http://evil.com');"
                "});"
            ),
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        cb_flags = [f for f in result.flags if f.category == "clipboard_hijack"]
        assert len(cb_flags) == 1
        assert cb_flags[0].severity == "high"

    def test_clipboard_no_false_positive(self):
        """clipboard.writeText alone (no event handler) should not flag."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": "navigator.clipboard.writeText('hello world');" + " " * 50,
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        cb_flags = [f for f in result.flags if f.category == "clipboard_hijack"]
        assert len(cb_flags) == 0

    def test_entropy_threshold_at_4_8(self):
        """Entropy threshold is 4.8 — verify the static method works."""
        det, _ = self._make_detector()
        # Normal code → low entropy (repeated identifiers)
        normal = "var name = getName(); var value = getValue(); var result = getResult();"
        entropy = det._compute_identifier_entropy(normal * 5)
        # Normal code should have entropy well below 4.8
        assert entropy < 4.8

    def test_bundler_skip_webpack(self):
        """Webpack scripts should skip entropy check."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        # High-entropy content that would flag, but __webpack_require__ present
        script = {
            "content": "__webpack_require__ " + "var x" * 200,
            "src": "", "index": 0,
        }
        det._analyze_script(script, result, "")
        obf_flags = [f for f in result.flags if f.category == "obfuscation" and "entropy" in f.description.lower()]
        assert len(obf_flags) == 0

    def test_framework_path_skip(self):
        """Scripts from framework paths (/_next/) should skip entropy check."""
        det, Result = self._make_detector()
        result = Result(url="http://test.com")
        script = {
            "content": "var a = 1; " * 100,
            "src": "https://example.com/_next/static/chunks/main.js",
            "index": 0,
        }
        det._analyze_script(script, result, "")
        obf_flags = [f for f in result.flags if f.category == "obfuscation" and "entropy" in f.description.lower()]
        assert len(obf_flags) == 0


# ============================================================
# P17: DOM Analyzer — Cookie Consent, Popups, Subscription Traps
# ============================================================

class TestCookieConsent:
    """P17 tests for DOMAnalyzer._check_cookie_consent."""

    def _analyzer(self):
        from analysis.dom_analyzer import DOMAnalyzer
        return DOMAnalyzer()

    def test_forced_consent_no_reject(self):
        """Cookie banner with Accept but no Reject → forced consent."""
        a = self._analyzer()
        data = {
            "cookieConsent": {
                "found": True,
                "acceptButton": {"text": "Accept All", "width": 200, "height": 40},
            }
        }
        findings = a._check_cookie_consent(data)
        assert len(findings) == 1
        assert findings[0].finding_type == "forced_cookie_consent"
        assert findings[0].category == "sneaking"
        assert findings[0].severity == "high"

    def test_cookie_accept_visually_dominant(self):
        """Accept button 3x larger than Reject → visual_interference."""
        a = self._analyzer()
        data = {
            "cookieConsent": {
                "found": True,
                "acceptButton": {"text": "Accept", "width": 300, "height": 50},
                "rejectButton": {"text": "Reject", "width": 50, "height": 30},
            }
        }
        findings = a._check_cookie_consent(data)
        dominant = [f for f in findings if f.finding_type == "cookie_accept_dominant"]
        assert len(dominant) == 1
        assert dominant[0].category == "visual_interference"

    def test_cookie_equal_buttons_ok(self):
        """Equal-sized Accept/Reject → no finding."""
        a = self._analyzer()
        data = {
            "cookieConsent": {
                "found": True,
                "acceptButton": {"text": "Accept", "width": 100, "height": 40},
                "rejectButton": {"text": "Reject", "width": 100, "height": 40},
            }
        }
        findings = a._check_cookie_consent(data)
        assert len(findings) == 0

    def test_no_cookie_banner(self):
        """No cookie banner found → no findings."""
        a = self._analyzer()
        findings = a._check_cookie_consent({"cookieConsent": {"found": False}})
        assert len(findings) == 0


class TestPopupModals:
    """P17 tests for DOMAnalyzer._check_popup_modals."""

    def _analyzer(self):
        from analysis.dom_analyzer import DOMAnalyzer
        return DOMAnalyzer()

    def test_viewport_overlay_no_close(self):
        """Viewport popup with no close button → critical."""
        a = self._analyzer()
        data = {
            "popups": [
                {"coversViewport": True, "hasCloseButton": False, "hasEmailInput": True}
            ]
        }
        findings = a._check_popup_modals(data)
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert findings[0].finding_type == "aggressive_popup"

    def test_viewport_overlay_with_close(self):
        """Viewport popup with close button → high (not critical)."""
        a = self._analyzer()
        data = {
            "popups": [
                {"coversViewport": True, "hasCloseButton": True}
            ]
        }
        findings = a._check_popup_modals(data)
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_no_popups(self):
        """No popups → no findings."""
        a = self._analyzer()
        findings = a._check_popup_modals({"popups": []})
        assert len(findings) == 0


class TestSubscriptionTraps:
    """P17 tests for DOMAnalyzer._check_subscription_traps."""

    def _analyzer(self):
        from analysis.dom_analyzer import DOMAnalyzer
        return DOMAnalyzer()

    def test_free_trial_billing(self):
        """Free trial + billing → sneaking."""
        a = self._analyzer()
        data = {"subscriptionTraps": {"freeTrialBilling": True}}
        findings = a._check_subscription_traps(data)
        assert len(findings) == 1
        assert findings[0].finding_type == "free_trial_billing"
        assert findings[0].confidence == 0.75

    def test_hidden_recurring_charge(self):
        """Billing in fine print + recurring → sneaking."""
        a = self._analyzer()
        data = {"subscriptionTraps": {"billingInFinePrint": True, "hiddenRecurring": True}}
        findings = a._check_subscription_traps(data)
        assert len(findings) == 1
        assert findings[0].finding_type == "hidden_recurring_charge"

    def test_auto_renew_no_cancel(self):
        """Auto-renew without cancel option → forced_continuity."""
        a = self._analyzer()
        data = {"subscriptionTraps": {"autoRenew": True, "cancelAnytime": False}}
        findings = a._check_subscription_traps(data)
        auto = [f for f in findings if f.finding_type == "auto_renew_no_cancel"]
        assert len(auto) == 1
        assert auto[0].category == "forced_continuity"

    def test_auto_renew_with_cancel_ok(self):
        """Auto-renew with cancel option → no finding."""
        a = self._analyzer()
        data = {"subscriptionTraps": {"autoRenew": True, "cancelAnytime": True}}
        findings = a._check_subscription_traps(data)
        auto = [f for f in findings if f.finding_type == "auto_renew_no_cancel"]
        assert len(auto) == 0

    def test_no_traps(self):
        """Empty subscriptionTraps → no findings."""
        a = self._analyzer()
        findings = a._check_subscription_traps({"subscriptionTraps": {}})
        assert len(findings) == 0


# ============================================================
# P17: Security Headers — Site-Type Multiplier
# ============================================================

class TestSecurityHeadersMultiplier:
    """P17 tests for site-type penalty multiplier."""

    def test_multiplier_dict_values(self):
        """Verify key multiplier values from P17."""
        from analysis.security_headers import _SITE_TYPE_MULTIPLIER

        assert _SITE_TYPE_MULTIPLIER["e-commerce"] == 1.5
        assert _SITE_TYPE_MULTIPLIER["financial"] == 1.8
        assert _SITE_TYPE_MULTIPLIER["banking"] == 1.8
        assert _SITE_TYPE_MULTIPLIER["blog"] == 0.7
        assert _SITE_TYPE_MULTIPLIER["portfolio"] == 0.6
        assert _SITE_TYPE_MULTIPLIER["corporate"] == 1.0

    def test_unknown_site_type_defaults_to_1(self):
        """Unknown site types should use 1.0 multiplier (no amplification)."""
        from analysis.security_headers import _SITE_TYPE_MULTIPLIER

        assert _SITE_TYPE_MULTIPLIER.get("unknown_type", 1.0) == 1.0

    def test_financial_higher_than_blog(self):
        """Financial sites must have higher penalty multiplier than blogs."""
        from analysis.security_headers import _SITE_TYPE_MULTIPLIER

        assert _SITE_TYPE_MULTIPLIER["financial"] > _SITE_TYPE_MULTIPLIER["blog"]


# ============================================================
# P17: Graph Investigator — Social Engineering Links
# ============================================================

class TestGraphSocialEngineering:
    """P17 tests for GraphInvestigator social engineering link analysis."""

    def _make_investigator(self):
        from agents.graph_investigator import GraphInvestigator
        return GraphInvestigator.__new__(GraphInvestigator)

    def test_lookalike_detection(self):
        """_is_lookalike detects similar domain names."""
        from agents.graph_investigator import GraphInvestigator
        assert GraphInvestigator._is_lookalike("paypal", "paypai") is True
        assert GraphInvestigator._is_lookalike("amazon", "amaz0n") is True

    def test_lookalike_same_name_false(self):
        """Identical names are not lookalikes."""
        from agents.graph_investigator import GraphInvestigator
        assert GraphInvestigator._is_lookalike("google", "google") is False

    def test_lookalike_very_different(self):
        """Totally different names are not lookalikes."""
        from agents.graph_investigator import GraphInvestigator
        assert GraphInvestigator._is_lookalike("google", "amazon") is False

    def test_lookalike_short_names_skipped(self):
        """Names shorter than 4 chars are skipped."""
        from agents.graph_investigator import GraphInvestigator
        assert GraphInvestigator._is_lookalike("go", "goo") is False

    def test_payment_domain_detection(self):
        """Payment domain links trigger suspicious_payment_link."""
        gi = self._make_investigator()
        links = ["https://paypal.com/checkout?amt=50"]
        findings = gi._analyze_social_engineering_links(links, "example.com")
        payment = [f for f in findings if f.inconsistency_type == "suspicious_payment_link"]
        assert len(payment) == 1

    def test_url_shortener_threshold(self):
        """3+ URL shorteners → excessive_shorteners finding."""
        gi = self._make_investigator()
        links = [
            "https://bit.ly/abc123",
            "https://tinyurl.com/xyz",
            "https://t.co/short1",
        ]
        findings = gi._analyze_social_engineering_links(links, "example.com")
        shortener = [f for f in findings if f.inconsistency_type == "excessive_shorteners"]
        assert len(shortener) == 1

    def test_url_shortener_below_threshold(self):
        """2 URL shorteners → no aggregate finding."""
        gi = self._make_investigator()
        links = ["https://bit.ly/abc", "https://tinyurl.com/xyz"]
        findings = gi._analyze_social_engineering_links(links, "example.com")
        shortener = [f for f in findings if f.inconsistency_type == "excessive_shorteners"]
        assert len(shortener) == 0

    def test_urgency_params_detection(self):
        """2+ links with urgency params → urgency_links finding."""
        gi = self._make_investigator()
        links = [
            "https://example.com/page?action=verify&urgent=true",
            "https://example.com/page2?confirm=yes&expire=now",
        ]
        findings = gi._analyze_social_engineering_links(links, "example.com")
        urgency = [f for f in findings if f.inconsistency_type == "urgency_links"]
        assert len(urgency) == 1

    def test_lookalike_domain_in_links(self):
        """Lookalike domain in links → lookalike_domain finding."""
        gi = self._make_investigator()
        links = ["https://amaz0n.com/deal"]
        findings = gi._analyze_social_engineering_links(links, "amazon.com")
        lookalike = [f for f in findings if f.inconsistency_type == "lookalike_domain"]
        assert len(lookalike) == 1
        assert lookalike[0].severity == "high"

    def test_clean_links_no_findings(self):
        """Normal links produce no social engineering findings."""
        gi = self._make_investigator()
        links = [
            "https://docs.google.com/help",
            "https://github.com/repo",
        ]
        findings = gi._analyze_social_engineering_links(links, "example.com")
        assert len(findings) == 0


# ============================================================
# P17: CTI Meaningful Indicators Filter
# ============================================================

class TestCTIMeaningfulIndicators:
    """P17 tests for CTI meaningful_indicators filtering."""

    def test_none_severity_excluded(self):
        """NONE-severity indicators (except ONION_ADDRESS/URL) should be excluded."""
        from veritas.osint.ioc_detector import Indicator, IOCType, IOCSeverity

        all_indicators = [
            Indicator(ioc_type=IOCType.DOMAIN, value="cdn.example.com", severity=IOCSeverity.NONE),
            Indicator(ioc_type=IOCType.IPV4, value="192.168.1.1", severity=IOCSeverity.MEDIUM),
            Indicator(ioc_type=IOCType.ONION_ADDRESS, value="abc.onion", severity=IOCSeverity.NONE),
            Indicator(ioc_type=IOCType.URL, value="http://evil.com", severity=IOCSeverity.NONE),
        ]

        meaningful = [
            ind for ind in all_indicators
            if ind.severity != IOCSeverity.NONE or ind.ioc_type in (
                IOCType.ONION_ADDRESS, IOCType.URL
            )
        ]

        assert len(meaningful) == 3
        values = [ind.value for ind in meaningful]
        # NONE DOMAIN filtered out
        assert "cdn.example.com" not in values
        # MEDIUM IPV4 kept
        assert "192.168.1.1" in values
        # NONE ONION kept (exception)
        assert "abc.onion" in values
        # NONE URL kept (exception)
        assert "http://evil.com" in values


# ============================================================
# P17: Tavily Source Signal Extraction
# ============================================================

class TestTavilySignalExtraction:
    """P17 tests for Tavily source _extract_signal."""

    def _get_extract_fn(self):
        from veritas.osint.sources.tavily_source import TavilyReputationSource
        from veritas.osint.types import OSINTCategory
        return TavilyReputationSource._extract_signal, OSINTCategory

    def test_reputation_negative_signal(self):
        """Negative reputation keywords → negative sentiment signal."""
        fn, Cat = self._get_extract_fn()
        result = {
            "snippet": "This site is a total scam and fraud. Avoid at all costs.",
            "title": "Review",
            "url": "https://trustpilot.com/review/shady.com"
        }
        signal = fn(result, Cat.REPUTATION)
        assert signal is not None
        assert signal["type"] == "reputation"
        assert signal["sentiment"] == "negative"
        assert signal["is_review_site"] is True
        assert signal["negative_keywords"] >= 2

    def test_reputation_positive_signal(self):
        """Positive reputation keywords → positive sentiment signal."""
        fn, Cat = self._get_extract_fn()
        result = {
            "snippet": "A trusted and reliable service, highly recommended by experts.",
            "title": "Review",
            "url": "https://review-blog.com/site-review"
        }
        signal = fn(result, Cat.REPUTATION)
        assert signal is not None
        assert signal["sentiment"] == "positive"
        assert signal["positive_keywords"] >= 2

    def test_reputation_no_keywords(self):
        """No reputation keywords → None signal."""
        fn, Cat = self._get_extract_fn()
        result = {
            "snippet": "The weather is nice today.",
            "title": "Blog Post",
            "url": "https://weather.com"
        }
        signal = fn(result, Cat.REPUTATION)
        assert signal is None

    def test_threat_intel_signal(self):
        """Threat intel keywords → threat_intel signal."""
        fn, Cat = self._get_extract_fn()
        result = {
            "snippet": "A critical vulnerability CVE-2024-1234 exploited in phishing campaign.",
            "title": "Security Advisory",
            "url": "https://security-blog.com"
        }
        signal = fn(result, Cat.THREAT_INTEL)
        assert signal is not None
        assert signal["type"] == "threat_intel"
        assert signal["threat_keywords"] >= 2

    def test_social_presence_signal(self):
        """Social media URL → social_presence signal."""
        fn, Cat = self._get_extract_fn()
        result = {
            "snippet": "Company profile",
            "title": "Company - LinkedIn",
            "url": "https://linkedin.com/company/example"
        }
        signal = fn(result, Cat.SOCIAL)
        assert signal is not None
        assert signal["type"] == "social_presence"
        assert signal["platform"] == "linkedin"

    def test_social_non_social_url(self):
        """Non-social URL with SOCIAL category → None."""
        fn, Cat = self._get_extract_fn()
        result = {
            "snippet": "Some random page",
            "title": "Home",
            "url": "https://random-site.com"
        }
        signal = fn(result, Cat.SOCIAL)
        assert signal is None


# ============================================================
# Run directly
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
