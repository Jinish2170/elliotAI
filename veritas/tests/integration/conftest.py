"""
Integration test fixtures for Veritas Phase 13 tests.
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def base_audit_state():
    from veritas.core.orchestrator import AuditState
    return {
        "url": "https://example.com",
        "audit_tier": "standard_audit",
        "iteration": 0,
        "max_iterations": 5,
        "max_pages": 10,
        "status": "running",
        "scout_results": [],
        "vision_result": None,
        "graph_result": None,
        "judge_decision": None,
        "pending_urls": ["https://example.com"],
        "investigated_urls": [],
        "start_time": time.time(),
        "elapsed_seconds": 0.0,
        "errors": [],
        "scout_failures": 0,
        "nim_calls_used": 0,
        "site_type": "company_portfolio",
        "site_type_confidence": 0.5,
        "verdict_mode": "expert",
        "security_results": {},
        "security_mode": "agent",
        "security_summary": {},
        "enabled_security_modules": ["xss_scanner", "sqli_scanner"],
    }


@pytest.fixture
def mock_scout_result_dict():
    return {
        "url": "https://example.com",
        "status": "SUCCESS",
        "screenshots": [],
        "screenshot_timestamps": [],
        "screenshot_labels": [],
        "page_title": "Example",
        "page_metadata": {"description": "Test", "has_ssl": True, "forms": []},
        "links": [],
        "forms_detected": 0,
        "captcha_detected": False,
        "error_message": "",
        "navigation_time_ms": 1000,
        "viewport_used": "desktop",
        "user_agent_used": "test",
        "trust_modifier": 0.0,
        "trust_notes": [],
        "site_type": "company_portfolio",
        "site_type_confidence": 0.5,
        "dom_analysis": {},
        "form_validation": {},
        "ioc_detected": False,
        "ioc_indicators": [],
        "onion_detected": False,
        "onion_addresses": [],
        "page_content": "<html><head><title>Example</title></head><body>Real content</body></html>",
        "response_headers": {"content-type": "text/html; charset=utf-8", "server": "nginx/1.18"},
    }
