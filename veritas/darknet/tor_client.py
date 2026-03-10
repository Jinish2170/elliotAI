"""
TOR Client — re-exported from canonical implementation in veritas.core.tor_client.

The canonical TORClient implementation lives in veritas.core.tor_client.
This module re-exports it for backward compatibility.
"""

from veritas.core.tor_client import TORClient

__all__ = ["TORClient"]
