"""
Integration tests: Tier workflow configurations.
Verifies all AUDIT_TIERS have correct behavioral budgets.
"""
import pytest
from veritas.config import settings
from veritas.core.nodes.security import _get_security_modules_for_tier


class TestTierConfigs:
    def test_all_tiers_have_behavioral_budgets(self):
        for name, cfg in settings.AUDIT_TIERS.items():
            assert "max_verifications" in cfg, f"{name} missing max_verifications"
            assert "enable_tavily" in cfg, f"{name} missing enable_tavily"
            assert "vision_passes" in cfg, f"{name} missing vision_passes"

    def test_quick_scan_is_fast_and_shallow(self):
        cfg = settings.AUDIT_TIERS["quick_scan"]
        assert cfg["max_verifications"] <= 5
        assert cfg["vision_passes"] <= 2
        assert cfg["pages"] <= 2
        assert cfg["target_duration_s"] <= 300

    def test_deep_forensic_is_thorough(self):
        cfg = settings.AUDIT_TIERS["deep_forensic"]
        assert cfg["max_verifications"] >= 15
        assert cfg["enable_tavily"] is True
        assert cfg["vision_passes"] >= 5

    def test_darknet_has_tor_and_darknet(self):
        cfg = settings.AUDIT_TIERS["darknet_investigation"]
        assert cfg.get("enable_tor") is True
        assert cfg.get("enable_darknet") is True

    @pytest.mark.parametrize("tier,expected_has_darknet", [
        ("quick_scan", False),
        ("standard_audit", False),
        ("deep_forensic", False),
        ("darknet_investigation", True),
    ])
    def test_tier_security_modules(self, tier, expected_has_darknet):
        modules = _get_security_modules_for_tier(tier)
        has_darknet = "darknet_correlation" in modules
        assert has_darknet == expected_has_darknet, (
            f"{tier}: expected darknet={expected_has_darknet}, got {has_darknet}"
        )

    def test_vision_passes_per_tier(self):
        assert (
            settings.AUDIT_TIERS["quick_scan"]["vision_passes"]
            < settings.AUDIT_TIERS["standard_audit"]["vision_passes"]
        )
        assert (
            settings.AUDIT_TIERS["standard_audit"]["vision_passes"]
            <= settings.AUDIT_TIERS["deep_forensic"]["vision_passes"]
        )
