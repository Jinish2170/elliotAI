"""
Veritas Darknet Module

Provides TOR client and onion detection functionality for darknet (.onion) URL auditing.

Legal/Privacy Compliance:
- Read-only OSINT only
- No transaction or purchase capability
- User agent headers set appropriately
- No logging of user-provided .onion URLs
"""

from .tor_client import TORClient
from .onion_detector import OnionDetector, MarketplaceType

__all__ = ["TORClient", "OnionDetector", "MarketplaceType"]
