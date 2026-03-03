"""
Veritas OSINT Module

Open Source Intelligence gathering capabilities for VERITAS.
Indicators of Compromise (IOC) detection and threat intelligence.
"""

from veritas.osint.ioc_detector import (
    IOCDetector,
    IOCDetectionResult,
    IOCIndicator,
)

from veritas.osint.types import (
    OSINTResult,
    DarknetMarketplaceType,
    ExitRiskLevel,
    VendorReputation,
    MarketplaceThreatData,
    Tor2WebThreatData,
)

# Marketplace threat feed sources
from veritas.osint.sources.darknet_alpha import AlphaBayMarketplaceSource
from veritas.osint.sources.darknet_hansa import HansaMarketplaceSource
from veritas.osint.sources.darknet_empire import EmpireMarketplaceSource
from veritas.osint.sources.darknet_dream import DreamMarketplaceSource
from veritas.osint.sources.darknet_wallstreet import WallStreetMarketplaceSource
from veritas.osint.sources.darknet_tor2web import Tor2WebDeanonSource

__all__ = [
    "IOCDetector",
    "IOCDetectionResult",
    "IOCIndicator",
    "OSINTResult",
    "DarknetMarketplaceType",
    "ExitRiskLevel",
    "VendorReputation",
    "MarketplaceThreatData",
    "Tor2WebThreatData",
    # Marketplace sources
    "AlphaBayMarketplaceSource",
    "HansaMarketplaceSource",
    "EmpireMarketplaceSource",
    "DreamMarketplaceSource",
    "WallStreetMarketplaceSource",
    "Tor2WebDeanonSource",
]
