"""
Veritas IOCDetector — Indicators of Compromise Detector

Detects security indicators and threat intelligence across analyzed content:
- ONION_ADDRESS: Tor hidden service (.onion) URLs
- IP_ADDRESS: Suspicious IP addresses
- HASH: Malware file hashes
- DOMAIN: Suspicious domain names

Integration with Scout: Automatically called during URL investigation to flag
content related to darknet/tor services.

Patterns from:
- graph_investigator.py → OSINT pattern detection
- tor_client.py → Onion URL detection

Usage:
    detector = IOCDetector()
    result = detector.detect(url, content, links)
    for indicator in result.indicators:
        print(f"{indicator.type}: {indicator.value}")
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger("veritas.osint.ioc_detector")


# ============================================================
# IOC Indicator Types
# ============================================================

class IOCType(Enum):
    """Types of Indicators of Compromise."""

    ONION_ADDRESS = "ONION_ADDRESS"      # Tor .onion hidden services
    IP_ADDRESS = "IP_ADDRESS"            # IP addresses
    HASH = "HASH"                        # File hashes (MD5, SHA1, SHA256)
    DOMAIN = "DOMAIN"                    # Domain names
    URL = "URL"                          # Full URLs
    EMAIL = "EMAIL"                      # Email addresses
    PHONE = "PHONE"                      # Phone numbers


class IOCSeverity(Enum):
    """Risk severity levels for IOCs."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# Data Classes
# ============================================================

@dataclass
class IOCIndicator:
    """
    A detected Indicator of Compromise.

    Attributes:
        type: Type of indicator (ONION_ADDRESS, IP, etc.)
        value: The detected value
        severity: Risk severity level
        confidence: Detection confidence (0.0-1.0)
        context: Additional context (source, location, etc.)
        raw_match: The raw text that matched the pattern
        start_pos: Position in source where match was found
        end_pos: End position of match
    """

    type: IOCType
    value: str
    severity: IOCSeverity = IOCSeverity.LOW
    confidence: float = 0.5
    context: dict = field(default_factory=dict)
    raw_match: str = ""
    start_pos: int = 0
    end_pos: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "value": self.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "context": self.context,
            "raw_match": self.raw_match,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
        }


@dataclass
class IOCDetectionResult:
    """
    Result of IOC detection across analyzed content.

    Attributes:
        found: True if any indicators were detected
        indicators: List of detected indicators
        ioc_counts: Counts by IOC type
        highest_severity: Highest severity level detected
        onion_detected: True if any onion addresses found (convenience flag)
        onion_count: Number of onion addresses detected
        ip_detected: True if any IP addresses found
        hash_detected: True if any hashes found
    """

    found: bool = False
    indicators: list[IOCIndicator] = field(default_factory=list)
    ioc_counts: dict[str, int] = field(default_factory=dict)
    highest_severity: IOCSeverity = IOCSeverity.LOW
    onion_detected: bool = False
    onion_count: int = 0
    ip_detected: bool = False
    hash_detected: bool = False

    def add_indicator(self, indicator: IOCIndicator) -> None:
        """Add an indicator and update statistics."""
        self.indicators.append(indicator)
        self.found = True

        # Update counts
        ioc_type = indicator.type.value
        self.ioc_counts[ioc_type] = self.ioc_counts.get(ioc_type, 0) + 1

        # Update highest severity
        severity_order = {
            IOCSeverity.LOW: 0,
            IOCSeverity.MEDIUM: 1,
            IOCSeverity.HIGH: 2,
            IOCSeverity.CRITICAL: 3,
        }
        if severity_order[indicator.severity] > severity_order[self.highest_severity]:
            self.highest_severity = indicator.severity

        # Update convenience flags
        if indicator.type == IOCType.ONION_ADDRESS:
            self.onion_detected = True
            self.onion_count += 1
        elif indicator.type == IOCType.IP_ADDRESS:
            self.ip_detected = True
        elif indicator.type == IOCType.HASH:
            self.hash_detected = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "found": self.found,
            "indicators": [ind.to_dict() for ind in self.indicators],
            "ioc_counts": self.ioc_counts,
            "highest_severity": self.highest_severity.value,
            "onion_detected": self.onion_detected,
            "onion_count": self.onion_count,
            "ip_detected": self.ip_detected,
            "hash_detected": self.hash_detected,
        }


# ============================================================
# IOC Detection Patterns
# ============================================================

class IOCPatterns:
    """Regex patterns for detecting IOCs."""

    # V3 onion addresses (56 chars base32 + .onion)
    # No word boundary at start to catch in URLs and HTML attributes
    ONION_V3 = re.compile(
        r'(?<![a-zA-Z0-9-])[a-z2-7]{56}\.onion(?![a-zA-Z0-9-])',
        re.IGNORECASE
    )

    # V2 onion addresses (16 chars base32 + .onion) - deprecated but checked
    ONION_V2 = re.compile(
        r'(?<![a-zA-Z0-9-])[a-z2-7]{16}\.onion(?![a-zA-Z0-9-])',
        re.IGNORECASE
    )

    # IPv4 addresses
    IPV4 = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )

    # IPv6 addresses (simplified)
    IPV6 = re.compile(
        r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    )

    # MD5 hash (32 hex chars)
    HASH_MD5 = re.compile(
        r'\b[a-fA-F0-9]{32}\b'
    )

    # SHA1 hash (40 hex chars)
    HASH_SHA1 = re.compile(
        r'\b[a-fA-F0-9]{40}\b'
    )

    # SHA256 hash (64 hex chars)
    SHA256 = re.compile(
        r'\b[a-fA-F0-9]{64}\b'
    )

    # SHA512 hash (128 hex chars)
    SHA512 = re.compile(
        r'\b[a-fA-F0-9]{128}\b'
    )

    # Email addresses
    EMAIL = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )

    # Phone numbers (international format)
    PHONE = re.compile(
        r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b'
    )


# ============================================================
# IOC Detector
# ============================================================

class IOCDetector:
    """
    Indicators of Compromise detector for web content analysis.

    Detects security-related indicators across URLs, page content,
    and link collections. Automatically flags darknet-related content.

    Usage:
        detector = IOCDetector()

        # Detect in a single URL
        result = detector.detect_url("http://example7f...56.onion")

        # Detect in page content
        result = await detector.detect_content(
            url="http://example.com",
            content="<html>...",
            links=["http://hidden.onion", "http://normal.com"]
        )
    """

    def __init__(self):
        self.patterns = IOCPatterns()

    def detect_url(self, url: str) -> IOCIndicator | None:
        """
        Detect IOC in a URL.

        Primarily focused on .onion address detection for darknet sites.

        Args:
            url: URL to analyze

        Returns:
            IOCIndicator if an indicator is found, None otherwise
        """
        url_lower = url.lower()

        # Check for onion address
        if self._is_onion_url(url):
            domain = self._extract_onion_address(url)
            return IOCIndicator(
                type=IOCType.ONION_ADDRESS,
                value=domain,
                severity=IOCSeverity.HIGH,
                confidence=0.95,
                context={"source": "url", "full_url": url},
                raw_match=domain,
            )

        # Check for suspicious IP addresses in URL
        parsed = urlparse(url)
        if parsed.netloc:
            # Check if netloc is an IP address
            if self.patterns.IPV4.match(parsed.netloc):
                return IOCIndicator(
                    type=IOCType.IP_ADDRESS,
                    value=parsed.netloc,
                    severity=IOCSeverity.MEDIUM,
                    confidence=0.7,
                    context={"source": "url"},
                )

        return None

    async def detect_content(
        self,
        url: str,
        content: str | None = None,
        links: list[str] | None = None,
    ) -> IOCDetectionResult:
        """
        Detect IOCs across content and links.

        Analyzes HTML content, page text, and extracted links for
        indicators of compromise. Results include onion addresses,
        IP addresses, hashes, and other security indicators.

        Args:
            url: Primary URL being analyzed
            content: HTML or text content to analyze
            links: List of URLs extracted from the page

        Returns:
            IOCDetectionResult with all detected indicators
        """
        result = IOCDetectionResult()

        # Detect in primary URL
        url_ioc = self.detect_url(url)
        if url_ioc:
            result.add_indicator(url_ioc)

        # Detect in content
        if content:
            content_result = self._scan_content(content, context_source="content")
            for indicator in content_result.indicators:
                result.add_indicator(indicator)

        # Detect in links
        if links:
            for link in links:
                link_ioc = self.detect_url(link)
                if link_ioc:
                    result.add_indicator(link_ioc)

        # Detect in links content (for inline links)
        if links and content:
            # Scan content for embedded links/text
            for link in links:
                if link in content:
                    start = content.find(link)
                    if start >= 0:
                        # Check if this link is an onion address
                        if self._is_onion_url(link):
                            domain = self._extract_onion_address(link)
                            result.add_indicator(
                                IOCIndicator(
                                    type=IOCType.ONION_ADDRESS,
                                    value=domain,
                                    severity=IOCSeverity.HIGH,
                                    confidence=0.9,
                                    context={
                                        "source": "link_in_content",
                                        "full_url": link,
                                        "url": url,
                                    },
                                    raw_match=link,
                                    start_pos=start,
                                    end_pos=start + len(link),
                                )
                            )

        logger.debug(
            f"IOC detection complete: {len(result.indicators)} indicators "
            f"(onions: {result.onion_count}, ips: {result.ip_detected})"
        )

        return result

    def _scan_content(
        self,
        content: str,
        context_source: str = "content",
    ) -> IOCDetectionResult:
        """
        Scan content for IOCs using regex patterns.

        Args:
            content: Text content to scan
            context_source: Where the content came from

        Returns:
            IOCDetectionResult with detected indicators
        """
        result = IOCDetectionResult()

        # Scan for onion V3 addresses
        for match in self.patterns.ONION_V3.finditer(content):
            result.add_indicator(
                IOCIndicator(
                    type=IOCType.ONION_ADDRESS,
                    value=match.group(),
                    severity=IOCSeverity.HIGH,
                    confidence=0.95,
                    context={"source": context_source},
                    raw_match=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        # Scan for onion V2 addresses (lower confidence - deprecated)
        for match in self.patterns.ONION_V2.finditer(content):
            result.add_indicator(
                IOCIndicator(
                    type=IOCType.ONION_ADDRESS,
                    value=match.group(),
                    severity=IOCSeverity.MEDIUM,  # Lower severity for V2
                    confidence=0.7,  # Lower confidence - V2 deprecated
                    context={
                        "source": context_source,
                        "version": "v2",
                        "notes": "onion v2 addresses are deprecated",
                    },
                    raw_match=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        # Scan for IPv4 addresses
        for match in self.patterns.IPV4.finditer(content):
            result.add_indicator(
                IOCIndicator(
                    type=IOCType.IP_ADDRESS,
                    value=match.group(),
                    severity=IOCSeverity.MEDIUM,
                    confidence=0.6,
                    context={"source": context_source},
                    raw_match=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        # Scan for MD5 hashes
        for match in self.patterns.HASH_MD5.finditer(content):
            result.add_indicator(
                IOCIndicator(
                    type=IOCType.HASH,
                    value=match.group(),
                    severity=IOCSeverity.MEDIUM,
                    confidence=0.6,
                    context={"source": context_source, "hash_type": "MD5"},
                    raw_match=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        # Scan for SHA1 hashes
        for match in self.patterns.HASH_SHA1.finditer(content):
            result.add_indicator(
                IOCIndicator(
                    type=IOCType.HASH,
                    value=match.group(),
                    severity=IOCSeverity.MEDIUM,
                    confidence=0.6,
                    context={"source": context_source, "hash_type": "SHA1"},
                    raw_match=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        # Scan for SHA256 hashes
        for match in self.patterns.SHA256.finditer(content):
            result.add_indicator(
                IOCIndicator(
                    type=IOCType.HASH,
                    value=match.group(),
                    severity=IOCSeverity.HIGH,
                    confidence=0.7,
                    context={"source": context_source, "hash_type": "SHA256"},
                    raw_match=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        # Scan for SHA512 hashes
        for match in self.patterns.SHA512.finditer(content):
            result.add_indicator(
                IOCIndicator(
                    type=IOCType.HASH,
                    value=match.group(),
                    severity=IOCSeverity.HIGH,
                    confidence=0.7,
                    context={"source": context_source, "hash_type": "SHA512"},
                    raw_match=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

        return result

    def _is_onion_url(self, url: str) -> bool:
        """Check if a URL is a .onion address."""
        parsed = urlparse(url)
        # Use hostname which automatically strips the port, fallback to netloc
        host = (parsed.hostname or parsed.netloc).lower()
        return host.endswith(".onion")

    def _extract_onion_address(self, url: str) -> str:
        """Extract the onion address from a URL."""
        parsed = urlparse(url)
        host = (parsed.netloc or parsed.path.split("/")[0]).lower()

        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]

        # Validate it's an address, not just ends with .onion
        # Return if it matches pattern OR if it ends with .onion
        if self.patterns.ONION_V3.match(host):
            return host
        elif self.patterns.ONION_V2.match(host):
            return host
        elif host.endswith(".onion"):
            return host

        return host


# ============================================================
# Convenience Functions
# ============================================================

async def detect_onion_addresses(
    url: str,
    content: str | None = None,
    links: list[str] | None = None,
) -> list[str]:
    """
    Convenience function to extract .onion addresses from content.

    Args:
        url: Primary URL
        content: HTML text content
        links: Extracted links

    Returns:
        List of .onion addresses found
    """
    detector = IOCDetector()
    result = await detector.detect_content(url, content, links)

    onion_addresses = [
        ind.value
        for ind in result.indicators
        if ind.type == IOCType.ONION_ADDRESS
    ]

    return list(set(onion_addresses))  # Deduplicate


def is_onion_url(url: str) -> bool:
    """
    Check if a URL is a .onion address.

    Convenience wrapper for static checking.

    Args:
        url: URL to check

    Returns:
        True if URL is .onion, False otherwise
    """
    detector = IOCDetector()
    return detector._is_onion_url(url)
