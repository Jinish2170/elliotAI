"""
Veritas Darknet Module

Provides TOR client functionality for darknet (.onion) URL auditing.

Legal/Privacy Compliance:
- Read-only OSINT only
- No transaction or purchase capability
- User agent headers set appropriately
- No logging of user-provided .onion URLs
"""

from .tor_client import TORClient

__all__ = ["TORClient"]
