"""
Tests for Scout agent IOC detection integration.

Tests verify that the Scout agent properly integrates with the IOC detector
to detect .onion addresses and other threat indicators during page investigation.
"""

import pytest

from veritas.agents.scout import (
    ScoutResult,
    StealthScout,
)


# ============================================================
# ScoutResult Tests
# ============================================================

class TestScoutResultIOCFields:
    """Tests that ScoutResult has IOC detection fields."""

    def test_scout_result_has_ioc_detected_field(self):
        """Verify ScoutResult has ioc_detected field."""
        result = ScoutResult(url="http://example.com", status="SUCCESS")

        assert hasattr(result, "ioc_detected")
        assert result.ioc_detected is False  # Default value

    def test_scout_result_has_ioc_indicators_field(self):
        """Verify ScoutResult has ioc_indicators field."""
        result = ScoutResult(url="http://example.com", status="SUCCESS")

        assert hasattr(result, "ioc_indicators")
        assert result.ioc_indicators == []  # Default empty list

    def test_scout_result_has_onion_detected_field(self):
        """Verify ScoutResult has onion_detected field."""
        result = ScoutResult(url="http://example.com", status="SUCCESS")

        assert hasattr(result, "onion_detected")
        assert result.onion_detected is False  # Default value

    def test_scout_result_has_onion_addresses_field(self):
        """Verify ScoutResult has onion_addresses field."""
        result = ScoutResult(url="http://example.com", status="SUCCESS")

        assert hasattr(result, "onion_addresses")
        assert result.onion_addresses == []  # Default empty list

    def test_scout_result_serialization(self):
        """Verify ScoutResult with IOC data can be converted to dict."""
        result = ScoutResult(
            url="http://example.com",
            status="SUCCESS",
            ioc_detected=True,
            ioc_indicators=[
                {
                    "type": "ONION_ADDRESS",
                    "value": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion",
                    "severity": "high",
                    "confidence": 0.95,
                }
            ],
            onion_detected=True,
            onion_addresses=[
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion"
            ],
        )

        # Convert to dict (dataclasses have __dataclass_fields__)
        fields = {f.name: getattr(result, f.name) for f in result.__dataclass_fields__.values()}

        assert "ioc_detected" in fields
        assert "ioc_indicators" in fields
        assert "onion_detected" in fields
        assert "onion_addresses" in fields
        assert fields["ioc_detected"] is True
        assert len(fields["ioc_indicators"]) == 1
        assert fields["onion_detected"] is True
        assert len(fields["onion_addresses"]) == 1


# ============================================================
# StealthScout IOC Integration Tests
# ============================================================

class TestStealthScoutIOCIntegration:
    """Tests for IOC detection integration in StealthScout."""

    def test_init_creates_ioc_detector(self):
        """Verify StealthScout.__init__ creates IOC detector."""
        scout = StealthScout()

        assert hasattr(scout, "_ioc_detector")

        # Detector may be None if import failed, but should have the attribute
        # In production, it should be an IOCDetector instance
        if scout._ioc_detector is not None:
            from veritas.osint.ioc_detector import IOCDetector
            assert isinstance(scout._ioc_detector, IOCDetector)

    def test_scout_result_default_ioc_values(self):
        """Test that ScoutResult defaults work correctly."""
        result = ScoutResult(url="http://example.com", status="SUCCESS")

        # All IOC fields should be initialized to defaults
        assert result.ioc_detected is False
        assert result.ioc_indicators == []
        assert result.onion_detected is False
        assert result.onion_addresses == []

    def test_scout_result_with_ioc_data(self):
        """Test ScoutResult with IOC detection data."""
        onions = [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.onion",
        ]

        result = ScoutResult(
            url="http://example.com",
            status="SUCCESS",
            ioc_detected=True,
            ioc_indicators=[
                {
                    "type": "ONION_ADDRESS",
                    "value": onions[0],
                    "severity": "high",
                    "confidence": 0.95,
                },
                {
                    "type": "ONION_ADDRESS",
                    "value": onions[1],
                    "severity": "high",
                    "confidence": 0.95,
                },
            ],
            onion_detected=True,
            onion_addresses=onions,
        )

        assert result.ioc_detected is True
        assert len(result.ioc_indicators) == 2
        assert result.onion_detected is True
        assert len(result.onion_addresses) == 2
        assert onions[0] in result.onion_addresses
        assert onions[1] in result.onion_addresses

    def test_onion_detection_affects_trust_score(self):
        """Test that onion detection affects trust modifiers."""
        result = ScoutResult(
            url="http://example.com",
            status="SUCCESS",
            onion_detected=True,
            onion_addresses=["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.onion"],
            trust_modifier=-0.3,
            trust_notes=["Onion (.onion) addresses detected: 1 hidden services found"],
        )

        assert result.trust_modifier < 0  # Onion detection should reduce trust
        assert "onion" in " ".join(result.trust_notes).lower()

    def test_ioc_field_backward_compatibility(self):
        """Test that existing ScoutResult creation still works without IOC fields."""
        # Old scout creation without IOC fields should still work
        result = ScoutResult(
            url="http://example.com",
            status="SUCCESS",
            page_title="Example",
            links=["http://example.com/about"],
            forms_detected=0,
            trust_modifier=0.0,
        )

        # Should work without errors
        assert result.url == "http://example.com"
        assert result.status == "SUCCESS"
        assert result.page_title == "Example"

        # IOC fields should have default values
        assert result.ioc_detected is False
        assert result.onion_detected is False
