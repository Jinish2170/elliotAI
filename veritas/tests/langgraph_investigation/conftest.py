"""
Veritas LangGraph Investigation — Shared Test Fixtures

Pytest fixtures for LangGraph state machine investigation tests.
Provides mocked dependencies for testing without external API calls or browser automation.
"""

import sys
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add veritas root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# ============================================================
# Mock NIMClient Fixture
# ============================================================

@pytest.fixture
def mock_nim_client():
    """
    Mock NIMClient for testing without API calls.

    Provides:
        - analyze_image: AsyncMock returning cached VLM response
        - generate_text: AsyncMock returning cached text response
        - call_count: Tracking for budget verification
    """
    client = MagicMock()

    # Vision analysis mock (returns structured dark pattern detection)
    async def mock_analyze_image(image_path: str, prompt: str, category_hint: str = ""):
        return {
            "response": '{"patterns": [{"category": "false_urgency", "pattern_type": "fake_timer", "confidence": 0.8}]}',
            "model": "nvidia/neva-22b",
            "fallback_mode": False,
            "cached": False,
        }

    client.analyze_image = AsyncMock(side_effect=mock_analyze_image)

    # Text generation mock (returns reasoning text)
    async def mock_generate_text(prompt: str, system_prompt: str = "", **kwargs):
        return {
            "response": "This analysis indicates low trustworthiness due to detected deceptive patterns.",
            "model": "nvidia/llama-3.2-3b",
            "fallback_mode": False,
            "cached": False,
        }

    client.generate_text = AsyncMock(side_effect=mock_generate_text)

    # Budget tracking
    client.call_count = 0
    client.cache_hits = 0
    client.fallback_count = 0
    client.errors = []

    return client


# ============================================================
# Mock Scout Fixture
# ============================================================

@pytest.fixture
def mock_scout():
    """
    Mock StealthScout for testing without browser automation.

    Provides:
        - __aenter__ / __aexit__: Async context manager support
        - investigate: AsyncMock returning ScoutResult-like dict
    """
    scout = MagicMock()

    # Async context manager
    async def mock_aenter():
        return scout

    async def mock_aexit(*args):
        return None

    scout.__aenter__ = AsyncMock(side_effect=mock_aenter)
    scout.__aexit__ = AsyncMock(side_effect=mock_aexit)

    # Investigation mock (returns successful page capture)
    async def mock_investigate(url: str, **kwargs):
        return {
            "url": url,
            "status": "SUCCESS",
            "screenshots": ["/tmp/test_screenshot_1.jpg", "/tmp/test_screenshot_2.jpg"],
            "screenshot_timestamps": [1630000000.0, 1630000005.0],
            "screenshot_labels": ["t0", "t5"],
            "page_title": "Test Page Title",
            "page_metadata": {
                "title": "Test Page Title",
                "description": "Test description",
                "has_ssl": True,
                "forms_count": 1,
            },
            "links": ["https://example.com/about", "https://example.com/contact"],
            "forms_detected": 1,
            "captcha_detected": False,
            "error_message": "",
            "navigation_time_ms": 1500.0,
            "viewport_used": "desktop",
            "user_agent_used": "Mozilla/5.0 Test Agent",
            "trust_modifier": 0.0,
            "trust_notes": [],
            "site_type": "company_portfolio",
            "site_type_confidence": 0.85,
            "dom_analysis": {},
            "form_validation": {},
        }

    scout.investigate = AsyncMock(side_effect=mock_investigate)

    # navigate_subpage mock (lightweight for additional pages)
    async def mock_navigate_subpage(url: str, **kwargs):
        return {
            "url": url,
            "status": "SUCCESS",
            "screenshots": [f"/tmp/test_{url.replace('/', '_')}_sub.jpg"],
            "screenshot_timestamps": [1630000100.0],
            "screenshot_labels": ["subpage"],
            "page_title": f"Subpage: {url}",
            "page_metadata": {"title": f"Subpage: {url}", "forms_count": 0},
            "links": [],
            "forms_detected": 0,
            "captcha_detected": False,
            "error_message": "",
            "navigation_time_ms": 800.0,
            "viewport_used": "desktop",
            "user_agent_used": "Mozilla/5.0 Test Agent",
            "trust_modifier": 0.0,
            "trust_notes": [],
        }

    scout.navigate_subpage = AsyncMock(side_effect=mock_navigate_subpage)

    return scout


# ============================================================
# Mock Vision Agent Fixture
# ============================================================

@pytest.fixture
def mock_vision_agent():
    """
    Mock VisionAgent for testing without real visual analysis.

    Provides:
        - analyze: AsyncMock returning VisionResult-like dict
    """
    async def mock_analyze(screenshots: list, screenshot_labels: list, url: str = "", **kwargs):
        return {
            "visual_score": 0.45,  # Low score = many dark patterns
            "temporal_score": 0.60,  # Medium score = some temporal issues
            "dark_patterns": [
                {
                    "category": "false_urgency",
                    "sub_type": "fake_countdown",
                    "confidence": 0.85,
                    "severity": "medium",
                    "evidence": "Countdown timer detected on page",
                    "screenshot_path": screenshots[0] if screenshots else "",
                    "model_used": "mocked",
                    "fallback_mode": False,
                    "raw_vlm_response": '{"patterns": [{"type": "countdown"}]}',
                }
            ],
            "temporal_findings": [],
            "screenshots_analyzed": len(screenshots),
            "prompts_sent": 1,
            "nim_calls_made": 1,
            "fallback_used": False,
            "errors": [],
        }

    return AsyncMock(side_effect=mock_analyze)


# ============================================================
# Mock Graph Investigator Fixture
# ============================================================

@pytest.fixture
def mock_graph_investigator():
    """
    Mock GraphInvestigator for testing without real API calls.

    Provides:
        - investigate: AsyncMock returning GraphResult-like dict
    """
    async def mock_investigate(url: str, page_metadata: dict, page_text: str, **kwargs):
        return {
            "graph_score": 0.55,
            "meta_score": 0.50,
            "domain_intel": {
                "domain": "example.com",
                "registrar": "Test Registrar",
                "age_days": 365,
                "ssl_issuer": "Let's Encrypt",
                "is_privacy_protected": False,
            },
            "domain_age_days": 365,
            "has_ssl": True,
            "claims_extracted": [
                {"entity_type": "company", "entity_value": "Example Corp", "source_page": url}
            ],
            "verifications": [
                {
                    "entity_type": "company",
                    "entity_value": "Example Corp",
                    "status": "verified",
                    "evidence_source": "LinkedIn",
                    "evidence_detail": "Company profile found",
                    "confidence": 0.9,
                }
            ],
            "inconsistencies": [],
            "graph": {"nodes": [{"id": "example.com"}], "edges": []},
            "graph_node_count": 1,
            "graph_edge_count": 0,
            "tavily_searches": 2,
            "errors": [],
        }

    return AsyncMock(side_effect=mock_investigate)


# ============================================================
# Mock Judge Agent Fixture
# ============================================================

@pytest.fixture
def mock_judge_agent():
    """
    Mock JudgeAgent for testing without real LLM reasoning.

    Provides:
        - deliberate: AsyncMock returning JudgeDecision-like dict
    """
    async def mock_deliberate(evidence: dict):
        return {
            "action": "RENDER_VERDICT",
            "reason": "Analysis complete based on available evidence",
            "final_score": 52,
            "risk_level": "medium",
            "forensic_narrative": "This website shows signs of deceptive dark patterns, requiring caution.",
            "simple_narrative": "Caution advised: This site uses deceptive tactics.",
            "recommendations": [
                "Proceed with caution when interacting with this site",
                "Avoid providing sensitive information",
            ],
            "simple_recommendations": [
                "Be careful with this site",
                "Don't share personal info",
            ],
            "dark_pattern_summary": [
                "Fake urgency countdown timer detected",
            ],
            "entity_verification_summary": [
                "Company entity verified via LinkedIn",
            ],
            "evidence_timeline": [],
            "investigate_urls": [],
            "trust_score_result": {
                "final_score": 52,
                "risk_level": "medium",
                "pre_override_score": 52,
                "weighted_breakdown": {
                    "visual": 15.0,
                    "temporal": 12.0,
                    "graph": 14.0,
                    "meta": 11.0,
                },
                "overrides_applied": [],
                "sub_signals": [
                    {"name": "visual", "raw_score": 0.45, "confidence": 0.7},
                    {"name": "temporal", "raw_score": 0.60, "confidence": 0.6},
                    {"name": "graph", "raw_score": 0.55, "confidence": 0.7},
                    {"name": "meta", "raw_score": 0.50, "confidence": 0.8},
                ],
                "explanation": "Trust score calculated from weighted analysis of visual, temporal, graph, and metadata signals.",
            },
            "site_type": "company_portfolio",
            "verdict_mode": "expert",
        }

    return AsyncMock(side_effect=mock_deliberate)


# ============================================================
# Audit State Fixture
# ============================================================

@pytest.fixture
def audit_state() -> dict:
    """
    Minimal valid AuditState TypedDict for testing.

    Includes all required fields for the LangGraph state machine.
    """
    return {
        "url": "https://example.com",
        "audit_tier": "standard_audit",
        "iteration": 0,
        "max_iterations": 3,
        "max_pages": 5,
        "status": "running",
        "scout_results": [],
        "vision_result": None,
        "graph_result": None,
        "judge_decision": None,
        "pending_urls": ["https://example.com"],
        "investigated_urls": [],
        "start_time": 1630000000.0,
        "elapsed_seconds": 0.0,
        "errors": [],
        "scout_failures": 0,
        "nim_calls_used": 0,
        # V2 fields
        "site_type": "",
        "site_type_confidence": 0.0,
        "verdict_mode": "expert",
        "security_results": {},
        "security_mode": "",
        "enabled_security_modules": ["security_headers", "phishing_db"],
    }


# ============================================================
# Mock Security Modules Fixtures
# ============================================================

@pytest.fixture
def mock_security_headers_result():
    """Mock security headers analysis result."""
    return {
        "score": 0.75,
        "headers": {
            "strict-transport-security": "max-age=31536000; includeSubDomains",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
        },
        "missing": ["content-security-policy", "x-xss-protection"],
        "warnings": [],
    }


@pytest.fixture
def mock_phishing_result():
    """Mock phishing check result."""
    return {
        "is_phishing": False,
        "confidence": 0.95,
        "heuristic_flags": [],
        "sources": [],
        "score": 0.95,
    }
