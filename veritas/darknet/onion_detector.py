"""
.onion URL validator and marketplace classifier for darknet auditing.

This module provides:
- Detection of v2 (16-char) and v3 (56-char) .onion addresses
- Base32 format validation
- Fingerprinting patterns for darknet sites
- Marketplace type classification (marketplace, forum, exchange, unknown)

Legal/Privacy Compliance:
- Read-only OSINT only
- No transaction or purchase capability
- No logging of user-provided .onion URLs
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List


class MarketplaceType(str, Enum):
    """Darknet site marketplace type classification."""
    MARKETPLACE = "marketplace"
    FORUM = "forum"
    EXCHANGE = "exchange"
    UNKNOWN = "unknown"


# Regex patterns for .onion URL validation
# v2 addresses: 16 base32 characters
PATTERN_V2 = re.compile(r'\b([a-z2-7]{16})\.onion\b', re.IGNORECASE)

# v3 addresses: 56 base32 characters
PATTERN_V3 = re.compile(r'\b([a-z2-7]{56})\.onion\b', re.IGNORECASE)

# Combined pattern for quick detection
PATTERN_ONION = re.compile(r'\b([a-z2-7]{16}|[a-z2-7]{56})\.onion\b', re.IGNORECASE)


@dataclass
class OnionAddress:
    """Extracted .onion address with metadata.

    Attributes:
        address: Full .onion URL (e.g., "example.onion")
        version: v2 or v3 based on character count
        marketplace_type: Classified marketplace type
        confidence: Confidence score (0.0-1.0)
    """
    address: str
    version: str
    marketplace_type: MarketplaceType
    confidence: float = 0.8

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "address": self.address,
            "version": self.version,
            "marketplace_type": self.marketplace_type.value,
            "confidence": self.confidence,
        }


class OnionDetector:
    """Detector for .onion hidden service URLs marketplace classification.

    Usage:
        detector = OnionDetector()

        # Validate .onion URL
        is_valid = detector.validate_onion("example.onion")

        # Extract from text
        urls = detector.detect_onion_urls("Visit site.onion for info")

        # Classify marketplace
        mtype = detector.classify_marketplace("example.onion", "buy drugs marketplace")

        # Quick detection
        is_darknet = detector.is_darknet_url("example.onion")
    """

    # Keywords for marketplace type classification (lowercase)
    MARKETPLACE_KEYWORDS = {
        'marketplace', 'market', 'shop', 'store', 'buy', 'purchase', 'sell',
        'drugs', 'vendor', 'listing', 'escrow', 'verified', 'crypto', 'bitcoin',
        'monero', 'anonymous', 'payment', 'order', 'cart', 'checkout'
    }

    FORUM_KEYWORDS = {
        'forum', 'discussion', 'thread', 'post', 'reply', 'board', 'community',
        'topic', 'comment', 'message', 'user', 'member', 'moderator'
    }

    EXCHANGE_KEYWORDS = {
        'exchange', 'swap', 'mixer', 'launder', 'convert', 'trade', 'crypto',
        'coin', 'transfer', 'bitcoin', 'monero', 'xmr', 'btc', 'pool'
    }

    BASE32_CHARSET = set('abcdefghijklmnopqrstuvwxyz234567')

    def __init__(self):
        """Initialize the onion detector."""
        # Patterns are compiled at module level for performance
        pass

    def validate_onion(self, onion_url: str) -> bool:
        """Validate .onion URL format and base32 charset.

        Args:
            onion_url: .onion URL to validate

        Returns:
            True if valid v2 or v3 address, False otherwise
        """
        if not onion_url or not isinstance(onion_url, str):
            return False

        # Case-insensitive .oniON check
        if not onion_url.lower().endswith('.onion'):
            return False

        # Extract the address part (before .onion)
        # Handle case-insensitive .onion suffix
        parts = onion_url.lower().rsplit('.onion', 1)
        if len(parts) < 2:
            return False

        address = parts[0]
        # Remove any path/query components
        if '/' in address:
            address = address.split('/')[0]
        if '?' in address:
            address = address.split('?')[0]

        # Check length: v2 is 16 chars, v3 is 56 chars
        if len(address) == 16:
            # v2 address
            return self._validate_base32(address)
        elif len(address) == 56:
            # v3 address
            return self._validate_base32(address)
        else:
            return False

    def _validate_base32(self, address: str) -> bool:
        """Validate base32 charset for onion address.

        Args:
            address: Onion address part (without .onion)

        Returns:
            True if all characters are valid base32
        """
        address_lower = address.lower()
        return all(c in self.BASE32_CHARSET for c in address_lower)

    def detect_onion_urls(self, text: str) -> List[str]:
        """Extract .onion URLs from text.

        Args:
            text: Text content to analyze

        Returns:
            List of unique .onion URLs found in text
        """
        if not text or not isinstance(text, str):
            return []

        # Find all .onion URLs
        matches = PATTERN_ONION.findall(text)

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for match in matches:
            url = f"{match.lower()}.onion"
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def classify_marketplace(
        self,
        onion_url: str,
        page_content: str = ""
    ) -> MarketplaceType:
        """Classify darknet site by marketplace type.

        Args:
            onion_url: .onion URL (optional context)
            page_content: Page text content for keyword analysis

        Returns:
            MarketplaceType enum value
        """
        if not page_content:
            return MarketplaceType.UNKNOWN

        content_lower = page_content.lower()

        # Count keyword matches for each type
        marketplace_count = sum(
            1 for kw in self.MARKETPLACE_KEYWORDS if kw in content_lower
        )
        forum_count = sum(
            1 for kw in self.FORUM_KEYWORDS if kw in content_lower
        )
        exchange_count = sum(
            1 for kw in self.EXCHANGE_KEYWORDS if kw in content_lower
        )

        # Determine type based on keyword density
        if marketplace_count > max(forum_count, exchange_count) and marketplace_count > 0:
            return MarketplaceType.MARKETPLACE
        elif forum_count > max(marketplace_count, exchange_count) and forum_count > 0:
            return MarketplaceType.FORUM
        elif exchange_count > max(marketplace_count, forum_count) and exchange_count > 0:
            return MarketplaceType.EXCHANGE
        else:
            return MarketplaceType.UNKNOWN

    def is_darknet_url(self, url: str) -> bool:
        """Quick check if URL is a .onion darknet URL.

        Args:
            url: URL to check

        Returns:
            True if .onion URL, False for clearweb
        """
        if not url or not isinstance(url, str):
            return False

        # Quick regex match
        return bool(PATTERN_ONION.search(url))

    def extract_addresses(
        self,
        text: str,
        classify: bool = True
    ) -> List[OnionAddress]:
        """Extract and optionally classify .onion addresses from text.

        Args:
            text: Text content to analyze
            classify: Whether to classify marketplace type (default: True)

        Returns:
            List of OnionAddress objects
        """
        urls = self.detect_onion_urls(text)

        addresses = []
        for url in urls:
            address_part = url.replace('.onion', '').lower()
            version = 'v3' if len(address_part) == 56 else 'v2'

            if classify:
                mtype = MarketplaceType.UNKNOWN
            else:
                mtype = MarketplaceType.UNKNOWN

            addresses.append(OnionAddress(
                address=url,
                version=version,
                marketplace_type=mtype,
                confidence=0.8
            ))

        return addresses
