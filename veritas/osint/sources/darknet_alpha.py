"""
AlphaBay Marketplace Threat Intelligence Source

Historical threat data from AlphaBay (shutdown 2017).
Read-only OSINT from security research.

Legal: Read-only OSINT only. No marketplace URLs provided.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from veritas.osint.types import OSINTResult, MarketplaceThreatData, DarknetMarketplaceType, ExitRiskLevel
from veritas.osint.sources.base import OSINTSource

logger = logging.getLogger("veritas.osint.sources.darknet_alpha")


class AlphaBayMarketplaceSource(OSINTSource):
    """
    AlphaBay marketplace threat intelligence source.

    Static historical data from security research.
    AlphaBay was seized by law enforcement in July 2017.
    """

    # Known AlphaBay onion addresses (historical - no active links)
    KNOWN_ONIONS = {
        # Historical addresses only - not accessible
        "pwoah7foa6au2pul.onion",
        "alpaba2h22v4.onion",
    }

    def __init__(self):
        super().__init__(
            name="alphabay_marketplace",
            enabled=True,
            priority=3,
            rate_limit_rpm=999,
        )
        self._data_path = Path(__file__).parent.parent.parent / "data" / "marketplace_threat_feeds.json"
        self._cache = {}

    async def query(
        self,
        indicator: str,
        indicator_type: Optional[str] = None,
        **kwargs
    ) -> Optional[OSINTResult]:
        """
        Query AlphaBay threat data for onion addresses.

        Args:
            indicator: Onion address to query
            indicator_type: Must be "onion" or "darknet"
            **kwargs: Additional parameters

        Returns:
            OSINTResult with threat data if onion is known, None otherwise
        """
        if not self.enabled:
            return None

        if not indicator_type or indicator_type not in ("onion", "darknet", "onion_address"):
            return None

        onion = self._normalize_onion(indicator)

        # Check if this is a known AlphaBay onion
        if not self._is_known_alphabay_onion(onion):
            return None

        # Load threat data
        threat_data = self._load_threat_data(onion)

        return OSINTResult(
            found=True,
            source=self.name,
            data=threat_data.to_dict() if threat_data else None,
            confidence=0.8,
            metadata={
                "marketplace": "AlphaBay",
                "status": "shutdown",
                "shutdown_date": "2017-07-05",
                "anon_onion": self.anonymize_onion(onion),
            },
        )

    def _normalize_onion(self, indicator: str) -> str:
        """Normalize onion address to lowercase without protocol."""
        onion = indicator.lower()
        # Remove protocol if present
        for proto in ("http://", "https://"):
            if onion.startswith(proto):
                onion = onion[len(proto):]
        # Remove trailing slash
        onion = onion.rstrip("/")
        return onion

    def _is_known_alphabay_onion(self, onion: str) -> bool:
        """Check if onion address is associated with AlphaBay."""
        # Direct matches
        if onion in self.KNOWN_ONIONS:
            return True
        # Domain match
        base = onion.split(".")[0]

        # Known AlphaBay base patterns (historical research data)
        # These are patterns from security research, not active URLs
        if base.startswith("pwoah7foa6au2pul"):
            return True
        if base.startswith("alpaba"):
            return True

        return False

    def _load_threat_data(self, onion: str) -> Optional[MarketplaceThreatData]:
        """Load threat data for AlphaBay marketplace."""
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            alphabay_data = data.get("marketplaces", {}).get("alphabay")
            if not alphabay_data:
                return None

            return MarketplaceThreatData(
                marketplace_type=DarknetMarketplaceType.MARKETPLACE,
                product_categories=alphabay_data.get("product_categories", []),
                risk_factors=[
                    "Law enforcement seizure - user data compromised",
                    "Admin arrested by DEA",
                    "PGP keys compromised",
                ],
                shutdown_date="2017-07-05",
                seizure_notice=True,
            )
        except Exception as e:
            logger.error(f"Error loading AlphaBay threat data: {e}")
            return None
