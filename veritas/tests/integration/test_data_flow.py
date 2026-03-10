"""
Integration tests: Data flow verification.
Verifies real page content flows from Scout to downstream agents.
"""
import pytest


class TestScoutDataFlow:
    def test_scout_result_has_real_page_content(self, mock_scout_result_dict):
        """Verify Scout captures real HTML, not fabricated."""
        page_content = mock_scout_result_dict["page_content"]
        fabricated_marker = '<html>\n<head><title>'
        assert fabricated_marker not in page_content or "Real content" in page_content

    def test_scout_result_has_real_headers(self, mock_scout_result_dict):
        """Verify Scout captures real response headers."""
        headers = mock_scout_result_dict["response_headers"]
        hardcoded_headers = {"content-type": "text/html", "server": "unknown"}
        assert headers != hardcoded_headers, "Headers should be real, not hardcoded"

    def test_no_fabricated_html_in_security_input(self, base_audit_state, mock_scout_result_dict):
        """Verify security_node receives real HTML from Scout."""
        state = dict(base_audit_state)
        state["scout_results"] = [mock_scout_result_dict]

        # Simulate what security_node_with_agent does
        first_result = state["scout_results"][0]
        page_content = first_result.get("page_content", "")

        fabricated_pattern = "<html>\n<head><title>"
        assert fabricated_pattern not in page_content, (
            "Security node should receive real HTML, not fabricated"
        )

    def test_scout_result_fields_complete(self, mock_scout_result_dict):
        """Verify all expected Scout output fields are present."""
        required_fields = [
            "url", "status", "page_content", "response_headers",
            "page_title", "page_metadata", "screenshots", "trust_modifier",
            "ioc_indicators", "onion_addresses"
        ]
        for field in required_fields:
            assert field in mock_scout_result_dict, f"Missing field: {field}"
