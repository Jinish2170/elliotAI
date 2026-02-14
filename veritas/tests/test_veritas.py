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

        assert len(settings.AUDIT_TIERS) == 3
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
# Run directly
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
