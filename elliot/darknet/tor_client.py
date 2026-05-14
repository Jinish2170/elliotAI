"""
TOR Client — re-exported from canonical implementation in elliot.core.tor_client.

The canonical TORClient implementation lives in elliot.core.tor_client.
This module re-exports it for backward compatibility.
"""

from elliot.core.tor_client import TORClient

__all__ = ["TORClient"]
