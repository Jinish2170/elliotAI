"""
OSINT Types Module

Data classes and enums for VERITAS Open Source Intelligence.

Legal Compliance:
- Read-only OSINT only
- Data from public research and security blogs
- No live darknet crawling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


# ============================================================
# Darknet Marketplace Types
# ============================================================

class DarknetMarketplaceType(str, Enum):
    """Darknet site marketplace type classification."""

    MARKETPLACE = "marketplace"
    FORUM = "forum"
    EXCHANGE = "exchange"
    UNKNOWN = "unknown"


class ExitRiskLevel(str, Enum):
    """Exit scam risk level for darknet marketplaces."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class VendorReputation:
    """
    Vendor reputation data for darknet threat intelligence.

    Historical data from security research only - not for live trading.

    Attributes:
        vendor_id: Vendor identifier (hashed for privacy)
        reputation_score: Normalized score 0.0-1.0
        transactions_count: Historical transaction count
        feedback_count: Number of feedback entries
        scam_flags: Known scam or fraud indicators
        exit_risk: Exit scam risk level
        last_activity: Last known activity timestamp
    """

    vendor_id: str
    reputation_score: float
    transactions_count: int
    feedback_count: int
    scam_flags: List[str] = field(default_factory=list)
    exit_risk: ExitRiskLevel = ExitRiskLevel.UNKNOWN
    last_activity: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "vendor_id": self.vendor_id,
            "reputation_score": self.reputation_score,
            "transactions_count": self.transactions_count,
            "feedback_count": self.feedback_count,
            "scam_flags": self.scam_flags,
            "exit_risk": self.exit_risk.value,
            "last_activity": self.last_activity,
        }


@dataclass
class MarketplaceThreatData:
    """
    Threat intelligence data for darknet marketplaces.

    Static threat feeds from research/security blogs only.
    No marketplace URLs provided to users.

    Attributes:
        marketplace_type: Type of marketplace
        vendor_reputations: Known vendor reputation data
        product_categories: Known product categories
        risk_factors: Additional risk indicators
        exit_scam_status: Whether marketplace exit scammed
        shutdown_date: Known shutdown date (if applicable)
    """

    marketplace_type: DarknetMarketplaceType
    vendor_reputations: List[VendorReputation] = field(default_factory=list)
    product_categories: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    exit_scam_status: bool = False
    shutdown_date: Optional[str] = None
    seizure_notice: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "marketplace_type": self.marketplace_type.value,
            "vendor_reputations": [v.to_dict() for v in self.vendor_reputations],
            "product_categories": self.product_categories,
            "risk_factors": self.risk_factors,
            "exit_scam_status": self.exit_scam_status,
            "shutdown_date": self.shutdown_date,
            "seizure_notice": self.seizure_notice,
        }


@dataclass
class Tor2WebThreatData:
    """
    Tor2Web gateway de-anonymization threat data.

    Tor2Web gateways allow clearnet access to .onion sites,
    potentially compromising user anonymity.

    Attributes:
        gateway_domains: Known Tor2Web gateway domains
        de_anon_risk: Risk level of de-anonymization
        referrer_leaks: Whether referrer headers leak onion URLs
        recommendation: Recommended action
    """

    gateway_domains: List[str] = field(default_factory=list)
    de_anon_risk: ExitRiskLevel = ExitRiskLevel.UNKNOWN
    referrer_leaks: bool = True
    recommendation: str = "Avoid accessing .onion sites through clearnet gateways"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "gateway_domains": self.gateway_domains,
            "de_anon_risk": self.de_anon_risk.value,
            "referrer_leaks": self.referrer_leaks,
            "recommendation": self.recommendation,
        }


# ============================================================
# OSINT Result Types
# ============================================================

@dataclass
class OSINTResult:
    """
    Generic OSINT query result.

    Attributes:
        found: Whether a result was found
        source: Source name
        data: Result data (can be MarketplaceThreatData, Tor2WebThreatData, etc.)
        confidence: Detection confidence 0.0-1.0
        metadata: Additional metadata
    """

    found: bool
    source: str
    data: Optional[dict] = None
    confidence: float = 0.5
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "found": self.found,
            "source": self.source,
            "data": self.data,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }
