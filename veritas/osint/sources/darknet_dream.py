"""
Dream Market Threat Intelligence Source

Historical threat data from Dream Market (exit scam 2019).
Read-only OSINT from security research.

Legal: Read-only OSINT only. No marketplace URLs provided.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from veritas.osint.types import OSINTResult, MarketplaceThreatData, DarknetMarketplaceType, ExitRiskLevel
from veritas.osint.sources.base import OSINTSource

logger = logging.getLogger("veritas.osint.sources.darknet_dream")


class DreamMarketplaceSource(OSINTSource):
    """
    Dream marketplace threat intelligence source.

    Static historical data from security research.
    Dream exit scammed in March 2019.
    """

    def __init__(self):
        super().__init__(
            name="dream_marketplace",
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
        Query Dream threat data for onion addresses.

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

        # Check if this is a known Dream onion
        if not self._is_known_dream_onion(onion):
            return None

        # Load threat data
        threat_data = self._load_threat_data(onion)

        return OSINTResult(
            found=True,
            source=self.name,
            data=threat_data.to_dict() if threat_data else None,
            confidence=0.7,
            metadata={
                "marketplace": "Dream",
                "status": "exit_scam",
                "shutdown_date": "2019-03-24",
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

    def _is_known_dream_onion(self, onion: str) -> bool:
        """Check if onion address is associated with Dream."""
        base = onion.split(".")[0]

        # Known Dream patterns from security research
        if "dream" in base or "drea7" in base or "drea2" in base:
            return True

        return False

    def _load_threat_data(self, onion: str) -> Optional[MarketplaceThreatData]:
        """Load threat data for Dream marketplace."""
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            dream_data = data.get("marketplaces", {}).get("dream")
            if not dream_data:
                return None

            return MarketplaceThreatData(
                marketplace_type=DarknetMarketplaceType.MARKETPLACE,
                product_categories=dream_data.get("product_categories", []),
                risk_factors=[
                    "Exit scam with partial refunds",
                    "Data theft during shutdown",
                ],
                shutdown_date="2019-03-24",
                exit_scam_status=True,
            )
        except Exception as e:
            logger.error(f"Error loading Dream threat data: {e}")
            return None
