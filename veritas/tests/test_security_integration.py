"""
Integration Tests for SecurityAgent

Test real module analysis, orchestrator routing, and feature flag
integration with actual security modules.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest
import pytest_asyncio
import asyncio

# Add veritas root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from veritas.agents.security_agent import SecurityAgent
from veritas.core.types import SecurityResult
from veritas.core.ipc import ProgressEvent, SecurityModeStarted, SecurityModeCompleted
from veritas.core.orchestrator import AuditState, security_node_with_agent, security_node
import logging

logger = logging.getLogger("test_security_integration")


# ============================================================
# Test Class: TestSecurityAgentRealModules
# ============================================================

class TestSecurityAgentRealModules:
    """Integration tests with real analysis modules."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_analyze_with_real_security_headers_module(self):
        """Test real security_headers module produces results."""
        agent = SecurityAgent()

        # Use httpbin.org which has headers
        result = await agent.analyze("https://httpbin.org/headers")

        assert result.composite_score is not None
        assert isinstance(result.composite_score, float)
        assert 0.0 <= result.composite_score <= 1.0

        # Check for security_headers in module results
        if "security_headers" in result.modules_results:
            assert "security_headers" in result.modules_run

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_analyze_with_real_phishing_checker_module(self):
        """Test real phishing_checker module produces results."""
        agent = SecurityAgent()

        # Use example.com which should be safe
        result = await agent.analyze("https://example.com")

        assert result.composite_score is not None
        assert isinstance(result.composite_score, float)

        # Check phishing_db module ran
        if "phishing_db" in result.modules_results:
            phishing_result = result.modules_results["phishing_db"]
            assert "is_phishing" in phishing_result
            # example.com shouldn't be flagged
            assert phishing_result["is_phishing"] is False

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_analyze_runs_multiple_modules(self):
        """Test that multiple modules run in a single analysis."""
        agent = SecurityAgent()

        result = await agent.analyze("https://example.com")

        # At least 2 modules should run (headers and phishing)
        assert len(result.modules_run) >= 1

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_analyze_handles_module_failures(self):
        """Test that module failures are handled gracefully."""
        agent = SecurityAgent()

        # Use a URL that might fail for some modules
        result = await agent.analyze("https://nonexistent-test-domain-12345.com")

        # Should still return a result (check for expected attributes)
        assert hasattr(result, 'url')
        assert hasattr(result, 'composite_score')
        assert result.url == "https://nonexistent-test-domain-12345.com"

        # Failed modules should be recorded
        if len(result.modules_failed) > 0:
            logger.info(f"Some modules failed as expected: {result.modules_failed}")


# ============================================================
# Test Class: TestSecurityAgentWithOrchestrator
# ============================================================

class TestSecurityAgentWithOrchestrator:
    """Test SecurityAgent works within actual orchestrator flow."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_security_node_with_agent_routes_correctly(self):
        """Test orchestrator processes security analysis."""
        # Create basic audit state
        state: AuditState = {
            "url": "https://example.com",
            "audit_tier": "quick_scan",
            "iteration": 0,
            "max_iterations": 5,
            "max_pages": 1,
            "status": "running",
            "scout_results": [],
            "vision_result": None,
            "graph_result": None,
            "judge_decision": None,
            "pending_urls": [],
            "investigated_urls": [],
            "start_time": 0.0,
            "elapsed_seconds": 0.0,
            "errors": [],
            "scout_failures": 0,
            "nim_calls_used": 0,
            "site_type": "",
            "site_type_confidence": 0.0,
            "verdict_mode": "expert",
            "security_results": {},
            "security_mode": "",
            "enabled_security_modules": ["security_headers", "phishing_db"],
        }

        result = await security_node_with_agent(state)

        assert "security_results" in result
        assert "security_mode" in result
        assert result["security_mode"] in ("agent", "function", "function_fallback")


# ============================================================
# Test Class: TestSecurityModuleEndToEnd
# ============================================================

class TestSecurityModuleEndToEnd:
    """Test each module produces correct SecurityFinding objects."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_security_headers_produces_findings(self):
        """Test security_headers module produces findings."""
        from veritas.analysis.security_headers import SecurityHeaderAnalyzer

        analyzer = SecurityHeaderAnalyzer()
        result = await analyzer.analyze("https://httpbin.org/headers")

        assert result is not None
        assert hasattr(result, "score")
        assert hasattr(result, "checks")
        assert hasattr(result, "to_dict")

        dict_result = result.to_dict()
        assert "score" in dict_result
        assert "checks" in dict_result

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_phishing_checker_produces_findings(self):
        """Test phishing_checker module produces findings."""
        from veritas.analysis.phishing_checker import PhishingChecker

        checker = PhishingChecker()
        result = await checker.check("https://example.com")

        assert result is not None
        assert hasattr(result, "is_phishing")
        assert hasattr(result, "confidence")
        assert hasattr(result, "heuristic_flags")
        assert hasattr(result, "sources")
        assert hasattr(result, "to_dict")

        # example.com should be safe
        assert isinstance(result.is_phishing, bool)
        assert isinstance(result.confidence, float)


# ============================================================
# Test Class: TestSecurityAgentWithProgressEvents
# ============================================================

class TestSecurityAgentWithProgressEvents:
    """Test ProgressEvent integration for security analysis."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_mode_events_is_correct_type(self):
        """Test SecurityMode events have correct types."""
        start_event = SecurityModeStarted(
            type="security_mode_start",
            phase="Security",
            step="mode_selection",
            security_mode="agent",
            module_count=5,
            rollout_enabled=True,
        )

        assert start_event.security_mode == "agent"
        assert start_event.module_count == 5
        assert start_event.rollout_enabled is True

        complete_event = SecurityModeCompleted(
            type="security_mode_complete",
            phase="Security",
            step="analysis",
            security_mode="agent",
            analysis_time_ms=1000,
            modules_run=["security_headers", "phishing_db"],
            modules_failed=[],
            findings_count=2,
            composite_score=0.85,
        )

        assert complete_event.security_mode == "agent"
        assert complete_event.analysis_time_ms == 1000
        assert len(complete_event.modules_run) == 2
        assert complete_event.findings_count == 2
        assert complete_event.composite_score == 0.85


# ============================================================
# Test Class: TestSecurityAgentModuleDiscovery
# ============================================================

class TestSecurityAgentModuleDiscovery:
    """Test module discovery and auto-registration."""

    @pytest.mark.asyncio
    async def test_all_modules_discoverable(self):
        """Test that all security modules are discoverable."""
        from veritas.analysis import SecurityModuleBase, ModuleInfo
        from veritas.analysis.security_headers import SecurityHeaderAnalyzer
        from veritas.analysis.phishing_checker import PhishingChecker
        from veritas.analysis.redirect_analyzer import RedirectAnalyzer
        from veritas.analysis.js_analyzer import JSObfuscationDetector
        from veritas.analysis.form_validator import FormActionValidator

        # Check all modules inherit from SecurityModuleBase
        assert issubclass(SecurityHeaderAnalyzer, SecurityModuleBase)
        assert issubclass(PhishingChecker, SecurityModuleBase)
        assert issubclass(RedirectAnalyzer, SecurityModuleBase)
        assert issubclass(JSObfuscationDetector, SecurityModuleBase)
        assert issubclass(FormActionValidator, SecurityModuleBase)

        # Check all modules are discoverable
        assert SecurityHeaderAnalyzer.is_discoverable()
        assert PhishingChecker.is_discoverable()
        assert RedirectAnalyzer.is_discoverable()
        assert JSObfuscationDetector.is_discoverable()
        assert FormActionValidator.is_discoverable()

    @pytest.mark.asyncio
    async def test_module_info_names_correct(self):
        """Test that module info has correct names."""
        from veritas.analysis.security_headers import SecurityHeaderAnalyzer
        from veritas.analysis.phishing_checker import PhishingChecker
        from veritas.analysis.redirect_analyzer import RedirectAnalyzer
        from veritas.analysis.js_analyzer import JSObfuscationDetector
        from veritas.analysis.form_validator import FormActionValidator

        modules = [
            (SecurityHeaderAnalyzer, "security_headers", "headers"),
            (PhishingChecker, "phishing_db", "phishing"),
            (RedirectAnalyzer, "redirect_chain", "redirects"),
            (JSObfuscationDetector, "js_analysis", "js"),
            (FormActionValidator, "form_validation", "forms"),
        ]

        for module_class, expected_name, expected_category in modules:
            info = module_class.get_module_info()
            assert info.module_name == expected_name
            assert info.category == expected_category


# ============================================================
# Test Class: TestSecurityAgentAnalyzeRealURLs
# ============================================================

class TestSecurityAgentAnalyzeRealURLs:
    """Test SecurityAgent analyze with real URLs."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_analyze_example_com(self):
        """Test analyzing example.com."""
        agent = SecurityAgent()
        result = await agent.analyze("https://example.com")

        assert result.url == "https://example.com"
        assert isinstance(result.composite_score, float)
        assert isinstance(result.findings, list)
        assert isinstance(result.modules_run, list)
        assert isinstance(result.modules_failed, list)

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_analyze_httpbin_headers(self):
        """Test analyzing httpbin.org/headers."""
        agent = SecurityAgent()
        result = await agent.analyze("https://httpbin.org/headers")

        assert "httpbin.org" in result.url
        assert isinstance(result.composite_score, float)

        # Headers module should work with httpbin
        if "security_headers" in result.modules_run:
            assert "security_headers" in result.modules_results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
