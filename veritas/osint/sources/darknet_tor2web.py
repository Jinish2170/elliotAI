"""
Tor2Web De-anonymization Threat Source

Detects Tor2Web gateway URLs that compromise TOR anonymity.
Read-only OSINT from security research.

Legal: Read-only OSINT only. Security research data.
"""

import logging
from typing import Optional

from veritas.osint.types import OSINTResult, Tor2WebThreatData, ExitRiskLevel
from veritas.osint.sources.base import OSINTSource

logger = logging.getLogger("veritas.osint.sources.darknet_tor2web")


class Tor2WebDeanonSource(OSINTSource):
    """
    Tor2Web gateway de-anonymization threat source.

    Detects clearnet gateways that expose .onion URLs,
    potentially compromising user anonymity.
    """

    # Known Tor2Web gateway domains
    GATEWAY_DOMAINS = {
        "onion.to",
        "onion.link",
        "onion.cab",
        "onion.lt",
        "onion.direct",
        "t2web.io",
        "tor2web.org",
        "check.torproject.org",  # Legitimate but indicates gateway usage
    }

    def __init__(self):
        super().__init__(
            name="tor2web_deanon",
            enabled=True,
            priority=2,
            rate_limit_rpm=999,
        )

    async def query(
        self,
        indicator: str,
        indicator_type: Optional[str] = None,
        **kwargs
    ) -> Optional[OSINTResult]:
        """
        Query for Tor2Web gateway indicators.

        Args:
            indicator: URL to check for Tor2Web gateway domain
            indicator_type: Type of indicator
            **kwargs: Additional parameters

        Returns:
            OSINTResult if Tor2Web gateway detected, None otherwise
        """
        if not self.enabled:
            return None

        if not indicator:
            return None

        # Check if this URL uses a Tor2Web gateway
        if not self._is_tor2web_url(indicator):
            return None

        # Build threat data
        threat_data = self._build_threat_data(indicator)

        return OSINTResult(
            found=True,
            source=self.name,
            data=threat_data.to_dict(),
            confidence=0.9,
            metadata={
                "gateway_detected": True,
                "anonymity_breach": "high",
                "rec": "Use direct TOR access for .onion URLs",
            },
        )

    def _is_tor2web_url(self, url: str) -> bool:
        """Check if URL uses a known Tor2Web gateway."""
        url_lower = url.lower()

        for domain in self.GATEWAY_DOMAINS:
            if f".{domain}/" in url_lower or url_lower.startswith(f"{domain}/"):
                return True

        return False

    def _build_threat_data(self, url: str) -> Tor2WebThreatData:
        """Build Tor2Web threat data."""
        # Identify which gateway was used
        detected_gateway = None
        for domain in self.GATEWAY_DOMAINS:
            if f".{domain}/" in url.lower() or url.lower().startswith(f"{domain}/"):
                detected_gateway = domain
                break

        return Tor2WebThreatData(
            gateway_domains=[detected_gateway] if detected_gateway else [],
            de_anon_risk=ExitRiskLevel.HIGH,
            referrer_leaks=True,
            recommendation=(
                "Direct access to .onion URLs through clearnet gateways "
                "compromises TOR anonymity. Use TOR Browser with direct "
                ".onion URLs instead."
            ),
        )

    def check_headers(
        self,
        headers: dict,
    ) -> Optional[OSINTResult]:
        """
        Check HTTP headers for Tor2Web exposure indicators.

        Args:
            headers: HTTP response headers

        Returns:
            OSINTResult if Tor2Web indicators found, None otherwise
        """
        if not headers:
            return None

        # Check for suspicious headers
        referrer = headers.get("Referer", headers.get("Referrer", ""))
        x_forwarded_for = headers.get("X-Forwarded-For", "")
        via = headers.get("Via", "")

        if self._is_tor2web_url(referrer):
            return OSINTResult(
                found=True,
                source=self.name,
                data={
                    "threat_type": "referrer_header_exposure",
                    "referrer": referrer[:50] + "..." if len(referrer) > 50 else referrer,
                    "de_anon_risk": "high",
                },
                confidence=0.8,
            )

        if x_forwarded_for or via:
            # Could indicate gateway usage
            return OSINTResult(
                found=False,
                source=self.name,
                data={
                    "threat_type": "potential_gateway_usage",
                    "note": "Forward headers detected - verify gateway usage",
                },
                confidence=0.4,
            )

        return None
