"""
Unit Tests for Security Dataclasses

Test SecurityResult, SecurityFinding, SecurityConfig, and Severity
serialization, validation, and utility methods.
"""

import os
import sys
from pathlib import Path
import pytest
from datetime import datetime, timezone, timedelta

# Add veritas root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from veritas.core.types import SecurityResult, SecurityFinding, Severity, SecurityConfig
import logging

logger = logging.getLogger("test_security_dataclasses")


# ============================================================
# Test Class: TestSecurityResultSerialization
# ============================================================

class TestSecurityResultSerialization:
    """Test SecurityResult serialization and deserialization."""

    def test_to_dict_returns_dict(self):
        """Test to_dict returns a proper dictionary."""
        result = SecurityResult(
            url="https://example.com",
            composite_score=0.85,
        )
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "url" in result_dict
        assert "composite_score" in result_dict

    def test_to_dict_includes_all_fields(self):
        """Test to_dict includes all SecurityResult fields."""
        finding = SecurityFinding.create(
            category="security_headers",
            severity="medium",
            evidence="Test finding",
            source_module="test_module",
        )
        result = SecurityResult(
            url="https://example.com",
            composite_score=0.75,
            findings=[finding],
            modules_results={"test_module": {"score": 0.8}},
            modules_run=["test_module"],
            modules_failed=["failed_module"],
            errors=["Test error"],
            analysis_time_ms=1000,
        )
        result_dict = result.to_dict()

        assert result_dict["url"] == "https://example.com"
        assert result_dict["composite_score"] == 0.75
        assert len(result_dict["findings"]) == 1
        assert "test_module" in result_dict["modules_results"]
        assert "test_module" in result_dict["modules_run"]
        assert "failed_module" in result_dict["modules_failed"]
        assert "Test error" in result_dict["errors"]
        assert result_dict["analysis_time_ms"] == 1000

    def test_from_dict_reconstructs_result(self):
        """Test from_dict reconstructs SecurityResult from dictionary."""
        data = {
            "url": "https://example.com",
            "composite_score": 0.85,
            "findings": [
                {
                    "category": "test",
                    "severity": "MEDIUM",  # Note: from_dict expects uppercase enum value
                    "evidence": "Test finding",
                    "source_module": "test_module",
                    "timestamp": "2026-02-21T00:00:00Z",
                    "confidence": 0.8,
                }
            ],
            "modules_results": {"test": {"score": 0.9}},
            "modules_run": ["test"],
            "modules_failed": [],
            "errors": [],
            "analysis_time_ms": 500,
        }
        result = SecurityResult.from_dict(data)

        assert result.url == "https://example.com"
        assert result.composite_score == 0.85
        assert len(result.findings) == 1
        assert "test" in result.modules_results
        assert "test" in result.modules_run
        assert result.analysis_time_ms == 500

    def test_findings_serializable(self):
        """Test that findings are properly serialized in to_dict."""
        finding = SecurityFinding.create(
            category="phishing",
            severity="high",
            evidence="Suspicious URL pattern",
            source_module="phishing_db",
            confidence=0.9,
        )
        result = SecurityResult(
            url="https://example.com",
            findings=[finding],
        )
        result_dict = result.to_dict()

        assert len(result_dict["findings"]) == 1
        finding_dict = result_dict["findings"][0]
        assert finding_dict["category"] == "phishing"
        assert finding_dict["severity"] == "HIGH"
        assert finding_dict["evidence"] == "Suspicious URL pattern"
        assert finding_dict["source_module"] == "phishing_db"
        assert finding_dict["confidence"] == 0.9

    def test_modules_results_serializable(self):
        """Test that modules_results is properly serialized."""
        result = SecurityResult(
            url="https://example.com",
            modules_results={
                "security_headers": {"score": 0.8, "headers": ["X-Frame-Options"]},
                "phishing_db": {"is_phishing": False, "sources": []},
            },
        )
        result_dict = result.to_dict()

        assert "security_headers" in result_dict["modules_results"]
        assert "phishing_db" in result_dict["modules_results"]
        assert result_dict["modules_results"]["security_headers"]["score"] == 0.8


# ============================================================
# Test Class: TestSecurityFindingStructure
# ============================================================

class TestSecurityFindingStructure:
    """Test SecurityFinding structure and validation."""

    def test_securityfinding_has_all_required_fields(self):
        """Test SecurityFinding has all required fields."""
        now = datetime.now(timezone.utc).isoformat()
        finding = SecurityFinding(
            category="test",
            severity=Severity.MEDIUM,
            evidence="Test evidence",
            source_module="test_module",
            timestamp=now,
            confidence=0.8,
        )

        assert finding.category == "test"
        assert finding.severity == Severity.MEDIUM
        assert finding.evidence == "Test evidence"
        assert finding.source_module == "test_module"
        assert finding.timestamp == now
        assert finding.confidence == 0.8

    def test_severity_enum_values(self):
        """Test Severity enum has all expected values."""
        assert Severity.CRITICAL == "CRITICAL"
        assert Severity.HIGH == "HIGH"
        assert Severity.MEDIUM == "MEDIUM"
        assert Severity.LOW == "LOW"
        assert Severity.INFO == "INFO"

    def test_securityfinding_timestamp_format(self):
        """Test SecurityFinding timestamp is in ISO format."""
        finding = SecurityFinding.create(
            category="test",
            severity="medium",
            evidence="Test",
            source_module="test",
        )
        # Should be parseable as ISO format date
        parsed_time = datetime.fromisoformat(finding.timestamp)
        assert isinstance(parsed_time, datetime)

    def test_securityfinding_invalid_confidence_raises_error(self):
        """Test that invalid confidence raises ValueError."""
        with pytest.raises(ValueError):
            SecurityFinding(
                category="test",
                severity="medium",
                evidence="Test",
                source_module="test",
                timestamp="2026-02-21T00:00:00Z",
                confidence=1.5,  # Invalid: > 1.0
            )

        with pytest.raises(ValueError):
            SecurityFinding(
                category="test",
                severity="medium",
                evidence="Test",
                source_module="test",
                timestamp="2026-02-21T00:00:00Z",
                confidence=-0.1,  # Invalid: < 0.0
            )


# ============================================================
# Test Class: TestSecurityConfigDefaults
# ============================================================

class TestSecurityConfigDefaults:
    """Test SecurityConfig default values and validation."""

    def test_securityconfig_has_default_timeout(self):
        """Test SecurityConfig has default timeout."""
        config = SecurityConfig()
        assert config.timeout == 15

    def test_securityconfig_has_default_retry_count(self):
        """Test SecurityConfig has default retry count."""
        config = SecurityConfig()
        assert config.retry_count == 2

    def test_securityconfig_has_default_fail_fast(self):
        """Test SecurityConfig has default fail_fast."""
        config = SecurityConfig()
        assert config.fail_fast is False

    def test_securityconfig_custom_values(self):
        """Test SecurityConfig with custom values."""
        config = SecurityConfig(
            timeout=30,
            retry_count=5,
            fail_fast=True,
        )
        assert config.timeout == 30
        assert config.retry_count == 5
        assert config.fail_fast is True

    def test_securityconfig_invalid_timeout_raises_error(self):
        """Test that invalid timeout raises ValueError."""
        with pytest.raises(ValueError):
            SecurityConfig(timeout=0)

        with pytest.raises(ValueError):
            SecurityConfig(timeout=-5)

    def test_securityconfig_invalid_retry_count_raises_error(self):
        """Test that invalid retry count raises ValueError."""
        with pytest.raises(ValueError):
            SecurityConfig(retry_count=-1)

    def test_securityconfig_to_dict(self):
        """Test SecurityConfig to_dict method."""
        config = SecurityConfig(timeout=20, retry_count=3, fail_fast=True)
        config_dict = config.to_dict()

        assert config_dict["timeout"] == 20
        assert config_dict["retry_count"] == 3
        assert config_dict["fail_fast"] is True

    def test_securityconfig_from_settings(self):
        """Test SecurityConfig.from_settings creates from global settings."""
        config = SecurityConfig.from_settings()
        assert isinstance(config, SecurityConfig)
        assert config.timeout > 0
        assert config.retry_count >= 0


# ============================================================
# Test Class: TestSecurityResultAggregation
# ============================================================

class TestSecurityResultAggregation:
    """Test SecurityResult aggregation methods."""

    def test_add_finding_appends_to_list(self):
        """Test add_finding appends finding to list."""
        result = SecurityResult(url="https://example.com")
        assert len(result.findings) == 0

        finding1 = SecurityFinding.create(
            category="test1",
            severity="low",
            evidence="Test 1",
            source_module="test",
        )
        result.add_finding(finding1)
        assert len(result.findings) == 1

        finding2 = SecurityFinding.create(
            category="test2",
            severity="medium",
            evidence="Test 2",
            source_module="test",
        )
        result.add_finding(finding2)
        assert len(result.findings) == 2

    def test_add_error_appends_to_list(self):
        """Test add_error appends error to list."""
        result = SecurityResult(url="https://example.com")
        assert len(result.errors) == 0

        result.add_error("Error 1")
        assert len(result.errors) == 1
        assert result.errors[0] == "Error 1"

        result.add_error("Error 2")
        assert len(result.errors) == 2
        assert result.errors[1] == "Error 2"

    def test_total_findings_property(self):
        """Test total_findings property returns count."""
        result = SecurityResult(url="https://example.com")
        assert result.total_findings == 0

        result.add_finding(SecurityFinding.create(
            category="test",
            severity="low",
            evidence="Test",
            source_module="test",
        ))
        assert result.total_findings == 1

        result.add_finding(SecurityFinding.create(
            category="test",
            severity="medium",
            evidence="Test",
            source_module="test",
        ))
        assert result.total_findings == 2

    def test_critical_findings_property(self):
        """Test critical_findings property returns only critical findings."""
        result = SecurityResult(url="https://example.com")

        result.add_finding(SecurityFinding.create(
            category="test",
            severity="critical",
            evidence="Critical issue",
            source_module="test",
        ))
        result.add_finding(SecurityFinding.create(
            category="test",
            severity="high",
            evidence="High issue",
            source_module="test",
        ))
        result.add_finding(SecurityFinding.create(
            category="test",
            severity="medium",
            evidence="Medium issue",
            source_module="test",
        ))

        assert len(result.critical_findings) == 1
        assert result.critical_findings[0].severity == Severity.CRITICAL

    def test_high_findings_property(self):
        """Test high_findings property returns only high findings."""
        result = SecurityResult(url="https://example.com")

        result.add_finding(SecurityFinding.create(
            category="test",
            severity="critical",
            evidence="Critical issue",
            source_module="test",
        ))
        result.add_finding(SecurityFinding.create(
            category="test",
            severity="high",
            evidence="High issue 1",
            source_module="test",
        ))
        result.add_finding(SecurityFinding.create(
            category="test",
            severity="high",
            evidence="High issue 2",
            source_module="test",
        ))

        assert len(result.high_findings) == 2
        for finding in result.high_findings:
            assert finding.severity == Severity.HIGH


# ============================================================
# Test Class: TestSecurityFindingFactory
# ============================================================

class TestSecurityFindingFactory:
    """Test SecurityFinding create factory method."""

    def test_create_with_string_severity(self):
        """Test create with string severity converts to enum."""
        finding = SecurityFinding.create(
            category="test",
            severity="high",
            evidence="Test",
            source_module="test",
        )
        assert finding.severity == Severity.HIGH

    def test_create_with_enum_severity(self):
        """Test create with enum severity keeps as enum."""
        finding = SecurityFinding.create(
            category="test",
            severity=Severity.CRITICAL,
            evidence="Test",
            source_module="test",
        )
        assert finding.severity == Severity.CRITICAL

    def test_create_auto_generates_timestamp(self):
        """Test create auto-generates ISO timestamp."""
        before = datetime.now(timezone.utc)
        finding = SecurityFinding.create(
            category="test",
            severity="medium",
            evidence="Test",
            source_module="test",
        )
        after = datetime.now(timezone.utc)

        parsed_time = datetime.fromisoformat(finding.timestamp)
        assert before <= parsed_time <= after

    def test_create_default_confidence(self):
        """Test create uses default confidence of 1.0."""
        finding = SecurityFinding.create(
            category="test",
            severity="medium",
            evidence="Test",
            source_module="test",
        )
        assert finding.confidence == 1.0


# ============================================================
# Test Class: TestSecurityResultBounds
# ============================================================

class TestSecurityResultBounds:
    """Test SecurityResult boundary validation."""

    def test_composite_score_upper_bound(self):
        """Test composite_score clamped to 1.0 maximum."""
        result = SecurityResult(url="https://example.com")
        assert result.composite_score <= 1.0

    def test_invalid_composite_score_raises_error(self):
        """Test that composite_score > 1.0 raises ValueError."""
        with pytest.raises(ValueError):
            SecurityResult(url="https://example.com", composite_score=1.5)

    def test_invalid_composite_score_lower_bound(self):
        """Test that composite_score < 0.0 raises ValueError."""
        with pytest.raises(ValueError):
            SecurityResult(url="https://example.com", composite_score=-0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
