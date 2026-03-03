"""
Hansa Market Threat Intelligence Source

Historical threat data from Hansa Market (seized 2017).
Read-only OSINT from security research.

Legal: Read-only OSINT only. No marketplace URLs provided.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from veritas.osint.types import OSINTResult, MarketplaceThreatData, DarknetMarketplaceType, ExitRiskLevel
from veritas.osint.sources.base import OSINTSource

logger = logging.getLogger("veritas.osint.sources.darknet_hansa")


class HansaMarketplaceSource(OSINTSource):
    """
    Hansa marketplace threat intelligence source.

    Static historical data from security research.
    Hansa was seized and operated as honeypot in July 2017.
    """

    # Known Hansa onion addresses (historical - no active links)
    KNOWN_ONIONS = {
        # Historical addresses only - not accessible
        "hansamkm.....abc.onion",
    }

    def __init__(self):
        super().__init__(
            name="hansa_marketplace",
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
        Query Hansa threat data for onion addresses.

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

        # Check if this is a known Hansa onion
        if not self._is_known_hansa_onion(onion):
            return None

        # Load threat data
        threat_data = self._load_threat_data(onion)

        return OSINTResult(
            found=True,
            source=self.name,
            data=threat_data.to_dict() if threat_data else None,
            confidence=0.8,
            metadata={
                "marketplace": "Hansa",
                "status": "seized",
                "shutdown_date": "2017-07-20",
                "anon_onion": self.anonymize_onion(onion),
            },
        )

    def _normalize_onion(self, indicator: str) -> str:
        """Normalize onion address to lowercase without protocol."""
        onion = indicator.lower()
        for proto in ("http://", "https://"):
            if onion.startswith(proto):
                onion = onion[len(proto):]
        return onion.rstrip("/")

    def _is_known_hansa_onion(self, onion: str) -> bool:
        """Check if onion address is associated with Hansa."""
        # Known Hansa base patterns from security research
        base = onion.split(".")[0]

        if "hansa" in base or "hansamkt" in base:
            return True

        return False

    def _load_threat_data(self, onion: str) -> Optional[MarketplaceThreatData]:
        """Load threat data for Hansa marketplace."""
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            hansa_data = data.get("marketplaces", {}).get("hansa")
            if not hansa_data:
                return None

            return MarketplaceThreatData(
                marketplace_type=DarknetMarketplaceType.MARKETPLACE,
                product_categories=hansa_data.get("product_categories", []),
                risk_factors=[
                    "Operated as honeypot after AlphaBay seizure",
                    "Vendor credentials harvested by law enforcement",
                    "Buyer information compromised",
                ],
                shutdown_date="2017-07-20",
                seizure_notice=True,
            )
        except Exception as e:
            logger.error(f"Error loading Hansa threat data: {e}")
            return None
