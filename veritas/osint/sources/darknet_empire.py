"""
Empire Market Threat Intelligence Source

Historical threat data from Empire Market (exit scam 2020).
Read-only OSINT from security research.

Legal: Read-only OSINT only. No marketplace URLs provided.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from veritas.osint.types import OSINTResult, MarketplaceThreatData, DarknetMarketplaceType, ExitRiskLevel
from veritas.osint.sources.base import OSINTSource

logger = logging.getLogger("veritas.osint.sources.darknet_empire")


class EmpireMarketplaceSource(OSINTSource):
    """
    Empire marketplace threat intelligence source.

    Static historical data from security research.
    Empire exit scammed in August 2020, stealing millions in BTC/XMR.
    """

    def __init__(self):
        super().__init__(
            name="empire_marketplace",
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
        Query Empire threat data for onion addresses.

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

        # Check if this is a known Empire onion
        if not self._is_known_empire_onion(onion):
            return None

        # Load threat data
        threat_data = self._load_threat_data(onion)

        return OSINTResult(
            found=True,
            source=self.name,
            data=threat_data.to_dict() if threat_data else None,
            confidence=0.9,  # High confidence - definite exit scam
            metadata={
                "marketplace": "Empire",
                "status": "exit_scam",
                "shutdown_date": "2020-08-22",
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

    def _is_known_empire_onion(self, onion: str) -> bool:
        """Check if onion address is associated with Empire."""
        base = onion.split(".")[0]

        # Known Empire patterns from security research
        if "empire" in base or "empmkt" in base or "empiremkt" in base:
            return True

        return False

    def _load_threat_data(self, onion: str) -> Optional[MarketplaceThreatData]:
        """Load threat data for Empire marketplace."""
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            empire_data = data.get("marketplaces", {}).get("empire")
            if not empire_data:
                return None

            return MarketplaceThreatData(
                marketplace_type=DarknetMarketplaceType.MARKETPLACE,
                product_categories=empire_data.get("product_categories", []),
                risk_factors=[
                    "Exit scam - stole millions in BTC and XMR",
                    "Multi-sig wallets compromised",
                    "Vendor funds lost",
                    "Admin forced multisig conversion before exit",
                    "Withdrawal delays before scam",
                    "Admin inactivity/pseudonym changes",
                ],
                shutdown_date="2020-08-22",
                exit_scam_status=True,
            )
        except Exception as e:
            logger.error(f"Error loading Empire threat data: {e}")
            return None
