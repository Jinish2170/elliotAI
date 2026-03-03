"""
Unit tests for Marketplace Threat Feed Sources

Tests for darknet marketplace OSINT sources.
Read-only OSINT from security research.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from veritas.osint.types import (
    MarketplaceThreatData,
    Tor2WebThreatData,
    DarknetMarketplaceType,
    ExitRiskLevel,
)
from veritas.osint.sources.base import OSINTSource


# ============================================================
# Utility Functions
# ============================================================

def normalize_onion(onion: str) -> str:
    """Normalize onion address."""
    onion = onion.lower()
    for proto in ("http://", "https://"):
        if onion.startswith(proto):
            onion = onion[len(proto):]
    return onion.rstrip("/")


# ============================================================
# Marketplace Source Tests
# ============================================================

class TestAlphaBayMarketplaceSource:
    """Tests for AlphaBay marketplace source."""

    @pytest.fixture
    def source(self):
        from veritas.osint.sources.darknet_alpha import AlphaBayMarketplaceSource
        return AlphaBayMarketplaceSource()

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_indicator(self, source):
        """Query should return None for empty indicator."""
        result = await source.query("")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_non_onion_indicator(self, source):
        """Query should return None for non-onion indicators."""
        result = await source.query("example.com", indicator_type="domain")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_onion(self, source):
        """Query should return None for unknown onion addresses."""
        result = await source.query("unknownabcdefgh.onion", indicator_type="onion")
        assert result is None

    @pytest.mark.asyncio
    @patch("builtins.open", MagicMock())
    async def test_queries_known_onion(self, source, mock_open):
        """Query should return result for known AlphaBay onion."""
        # Mock file read
        import json
        mock_data = {
            "marketplaces": {
                "alphabay": {
                    "name": "AlphaBay",
                    "type": "marketplace",
                    "product_categories": ["drugs", "fraud", "counterfeit"],
                }
            }
        }
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(mock_data)
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock onion pattern match
        with patch.object(source, "_is_known_alphabay_onion", return_value=True):
            result = await source.query("pwoah7foa6au2pul.onion", indicator_type="onion")

        assert result is not None
        assert result.found is True
        assert result.source == "alphabay_marketplace"
        assert result.confidence == 0.8
        assert result.metadata["marketplace"] == "AlphaBay"
        assert result.metadata["status"] == "shutdown"


class TestHansaMarketplaceSource:
    """Tests for Hansa marketplace source."""

    @pytest.fixture
    def source(self):
        from veritas.osint.sources.darknet_hansa import HansaMarketplaceSource
        return HansaMarketplaceSource()

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_indicator(self, source):
        """Query should return None for empty indicator."""
        result = await source.query("")
        assert result is None

    @pytest.mark.asyncio
    @patch("builtins.open", MagicMock())
    async def test_queries_known_onion(self, source, mock_open):
        """Query should return result for known Hansa onion."""
        import json
        mock_data = {
            "marketplaces": {
                "hansa": {
                    "name": "Hansa",
                    "type": "marketplace",
                    "product_categories": ["drugs", "digital_goods"],
                }
            }
        }
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(mock_data)
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(source, "_is_known_hansa_onion", return_value=True):
            result = await source.query("hansaabcdefgh.onion", indicator_type="onion")

        assert result is not None
        assert result.found is True
        assert result.source == "hansa_marketplace"
        assert result.metadata["marketplace"] == "Hansa"


class TestEmpireMarketplaceSource:
    """Tests for Empire marketplace source."""

    @pytest.fixture
    def source(self):
        from veritas.osint.sources.darknet_empire import EmpireMarketplaceSource
        return EmpireMarketplaceSource()

    @pytest.mark.asyncio
    async def test_returns_none_for_non_onion_indicator(self, source):
        """Query should return None for non-onion indicators."""
        result = await source.query("example.com", indicator_type="domain")
        assert result is None

    @pytest.mark.asyncio
    @patch("builtins.open", MagicMock())
    async def test_queries_known_onion(self, source, mock_open):
        """Query should return result for known Empire onion."""
        import json
        mock_data = {
            "marketplaces": {
                "empire": {
                    "name": "Empire",
                    "type": "marketplace",
                    "product_categories": ["drugs", "digital_goods"],
                    "known_threats": ["exit scam"],
                }
            }
        }
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(mock_data)
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(source, "_is_known_empire_onion", return_value=True):
            result = await source.query("empireabcdefgh.onion", indicator_type="onion")

        assert result is not None
        assert result.found is True
        assert result.confidence == 0.9  # Higher for definite exit scam
        assert result.metadata["status"] == "exit_scam"


class TestDreamMarketplaceSource:
    """Tests for Dream marketplace source."""

    @pytest.fixture
    def source(self):
        from veritas.osint.sources.darknet_dream import DreamMarketplaceSource
        return DreamMarketplaceSource()

    @pytest.mark.asyncio
    @patch("builtins.open", MagicMock())
    async def test_queries_known_onion(self, source, mock_open):
        """Query should return result for known Dream onion."""
        import json
        mock_data = {
            "marketplaces": {
                "dream": {
                    "name": "Dream",
                    "type": "marketplace",
                    "product_categories": ["drugs", "digital_goods"],
                }
            }
        }
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(mock_data)
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(source, "_is_known_dream_onion", return_value=True):
            result = await source.query("drea7abcdefgh.onion", indicator_type="onion")

        assert result is not None
        assert result.found is True
        assert result.confidence == 0.7


class TestWallStreetMarketplaceSource:
    """Tests for Wall Street marketplace source."""

    @pytest.fixture
    def source(self):
        from veritas.osint.sources.darknet_wallstreet import WallStreetMarketplaceSource
        return WallStreetMarketplaceSource()

    @pytest.mark.asyncio
    @patch("builtins.open", MagicMock())
    async def test_queries_known_onion(self, source, mock_open):
        """Query should return result for known WSM onion."""
        import json
        mock_data = {
            "marketplaces": {
                "wallstreet": {
                    "name": "Wall Street",
                    "type": "marketplace",
                    "product_categories": ["drugs", "digital_goods"],
                }
            }
        }
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(mock_data)
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(source, "_is_known_wsm_onion", return_value=True):
            result = await source.query("wallstabcdefgh.onion", indicator_type="onion")

        assert result is not None
        assert result.found is True
        assert result.confidence == 0.9


# ============================================================
# Tor2Web Source Tests
# ============================================================

class TestTor2WebDeanonSource:
    """Tests for Tor2Web de-anonymization source."""

    @pytest.fixture
    def source(self):
        from veritas.osint.sources.darknet_tor2web import Tor2WebDeanonSource
        return Tor2WebDeanonSource()

    def test_is_tor2web_url_detects_gateway(self, source):
        """Should detect tor2web gateway URLs."""
        assert source._is_tor2web_url("https://onion.to/example.onion") is True
        assert source._is_tor2web_url("http://onion.link/hdhd.onion") is True
        assert source._is_tor2web_url("https://example.onion") is False
        assert source._is_tor2web_url("https://google.com") is False

    @pytest.mark.asyncio
    async def test_query_returns_none_for_non_gateway(self, source):
        """Query should return None for non-gateway URLs."""
        result = await source.query("https://example.onion")
        assert result is None

    @pytest.mark.asyncio
    async def test_query_detects_gateway(self, source):
        """Query should detect tor2web gateway."""
        result = await source.query("https://onion.to/example.onion")

        assert result is not None
        assert result.found is True
        assert result.source == "tor2web_deanon"
        assert result.confidence == 0.9
        assert result.metadata["gateway_detected"] is True

    @pytest.mark.asyncio
    async def test_query_multiple_gateways(self, source):
        """Query should detect all known gateway domains."""
        gateways = [
            "https://onion.to/test.onion",
            "https://onion.link/test.onion",
            "https://onion.cab/test.onion",
            "https://onion.lt/test.onion",
            "https://onion.direct/test.onion",
            "https://t2web.io/test.onion",
            "https://tor2web.org/test.onion",
        ]

        for url in gateways:
            result = await source.query(url)
            assert result is not None
            assert result.found is True

    def test_check_headers_with_referrer_gateway(self, source):
        """Should detect gateway in referer header."""
        headers = {
            "Referer": "https://onion.to/previous.onion/page"
        }
        result = source.check_headers(headers)
        assert result is not None
        assert result.found is True

    def test_check_headers_without_gateway(self, source):
        """Should not detect gateway when none present."""
        headers = {
            "Referer": "https://example.com"
        }
        result = source.check_headers(headers)
        assert result is None

    def test_check_headers_with_forwarded_for(self, source):
        """Should note potential gateway usage with forwarded headers."""
        headers = {
            "X-Forwarded-For": "1.2.3.4"
        }
        result = source.check_headers(headers)
        # Should return result with found=False but notes
        assert result is not None
        assert result.found is False

    def test_check_headers_empty(self, source):
        """Should return None for empty headers."""
        result = source.check_headers({})
        assert result is None


# ============================================================
# Type Tests
# ============================================================

class TestMarketplaceThreatData:
    """Tests for MarketplaceThreatData type."""

    def test_marketplace_threat_data_creation(self):
        """Should create MarketplaceThreatData with correct values."""
        data = MarketplaceThreatData(
            marketplace_type=DarknetMarketplaceType.MARKETPLACE,
            product_categories=["drugs", "digital_goods"],
            risk_factors=["exit_scam"],
            exit_scam_status=True,
        )

        assert data.marketplace_type == DarknetMarketplaceType.MARKETPLACE
        assert "drugs" in data.product_categories
        assert "exit_scam" in data.risk_factors
        assert data.exit_scam_status is True

    def test_to_dict_conversion(self):
        """Should convert to dictionary properly."""
        data = MarketplaceThreatData(
            marketplace_type=DarknetMarketplaceType.FORUM,
            product_categories=["forum_posts"],
        )

        result = data.to_dict()
        assert isinstance(result, dict)
        assert result["marketplace_type"] == "forum"
        assert "product_categories" in result


class TestTor2WebThreatData:
    """Tests for Tor2WebThreatData type."""

    def test_tor2web_threat_data_creation(self):
        """Should create Tor2WebThreatData with correct values."""
        data = Tor2WebThreatData(
            gateway_domains=["onion.to", "onion.link"],
            de_anon_risk=ExitRiskLevel.HIGH,
            recommendation="Use direct TOR access",
        )

        assert "onion.to" in data.gateway_domains
        assert data.de_anon_risk == ExitRiskLevel.HIGH
        assert "direct TOR" in data.recommendation

    def test_to_dict_conversion(self):
        """Should convert to dictionary properly."""
        data = Tor2WebThreatData(
            gateway_domains=["onion.to"],
        )

        result = data.to_dict()
        assert isinstance(result, dict)
        assert result["gateway_domains"] == ["onion.to"]
        assert result["de_anon_risk"] == "unknown"


# ============================================================
# Base Source Tests
# ============================================================

class TestOSINTSource:
    """Tests for OSINTSource base class."""

    def test_anonymize_onion(self, source):
        """Should anonymize onion addresses."""
        anon = source.anonymize_onion("abcdefgh1234567890abcdefghijklmnopqrstuvwxyz.onion")
        assert "anon.onion" in anon or "..." in anon
        assert "abcdefgh" not in anon  # Should not expose full onion

    def test_anonymize_onion_short(self, source):
        """Should handle short onion addresses."""
        anon = source.anonomize_onion("short.onion")  # Typo in method name test
        anon = source.anonymize_onion("short.onion")  # Correct version
        assert "anon.onion" in anon or "..." in anon

    def test_is_onion_address(self, source):
        """Should detect .onion addresses."""
        assert source.is_onion_address("example.onion") is True
        assert source.is_onion_address("example.oniON") is True
        assert source.is_onion_address("example.com") is False
        assert source.is_onion_address("https://example.onion") is True
