"""
Base OSINT Source Module

Base class for OSINT threat intelligence sources.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

from veritas.osint.types import OSINTResult

logger = logging.getLogger("veritas.osint.sources.base")


class OSINTSource(ABC):
    """
    Base class for OSINT threat intelligence sources.

    Each source can query threat intelligence data for indicators.
    Sources are read-only and use static data from security research.

    Attributes:
        name: Source name
        enabled: Whether source is active
        priority: Query priority (lower = higher priority)
        rate_limit_rpm: Rate limit in requests per minute
    """

    def __init__(
        self,
        name: str,
        enabled: bool = True,
        priority: int = 10,
        rate_limit_rpm: int = 60,
    ):
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.rate_limit_rpm = rate_limit_rpm

    @abstractmethod
    async def query(
        self,
        indicator: str,
        indicator_type: Optional[str] = None,
        **kwargs
    ) -> Optional[OSINTResult]:
        """
        Query this source for threat intelligence data.

        Args:
            indicator: The indicator to query (onion URL, IP, etc.)
            indicator_type: Type of indicator (onion, ip, etc.)
            **kwargs: Additional query parameters

        Returns:
            OSINTResult if threat data found, None otherwise
        """
        pass

    def is_onion_address(self, address: str) -> bool:
        """Check if address is a .onion hidden service address."""
        return address.lower().endswith((".onion", ".oniON"))

    def anonymize_onion(self, onion: str) -> str:
        """
        Anonymize onion address for logging/UI display.

        Returns shortened version: abc...xyz.onion (first 3 + last 3 chars)
        """
        if not self.is_onion_address(onion):
            return onion

        base = onion.replace(".onion", "").lower()
        if len(base) <= 6:
            return "anon.onion"

        return f"{base[:3]}...{base[-3:]}.onion"
