"""Data types and enums for OSINT sources.

Defines standardized data structures, enums, and configuration
objects used across all OSINT source implementations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceStatus(str, Enum):
    """Status of OSINT source query execution."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class OSINTCategory(str, Enum):
    """Category of OSINT intelligence source."""
    DNS = "dns"
    WHOIS = "whois"
    SSL = "ssl"
    THREAT_INTEL = "threat_intel"
    REPUTATION = "reputation"
    SOCIAL = "social"


@dataclass
class OSINTResult:
    """Result from an OSINT source query.

    Attributes:
        source: Name of the OSINT source (e.g., "dns", "whois", "ssl")
        category: Category of the intelligence (OSINTCategory enum)
        query_type: Type of query performed (e.g., "A", "MX", "certificate")
        query_value: Value queried (e.g., domain, hostname, IP)
        status: Execution status (SourceStatus enum)
        data: Fetched intelligence data (dict or list)
        confidence_score: Confidence score in range 0.0-1.0
        cached_at: Timestamp when result was cached (None if not cached)
        error_message: Error message if status is ERROR
    """
    source: str = ""
    category: OSINTCategory = OSINTCategory.THREAT_INTEL
    query_type: str = "lookup"
    query_value: str = ""
    status: SourceStatus = SourceStatus.SUCCESS
    data: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    cached_at: Optional[datetime] = None
    error_message: Optional[str] = None

    found: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None

    def __post_init__(self):
        if self.found is not None:
            self.status = SourceStatus.SUCCESS if self.found else SourceStatus.ERROR
        else:
            self.found = (self.status == SourceStatus.SUCCESS)

        if self.confidence is not None and self.confidence_score == 0.0:
            self.confidence_score = self.confidence
        elif self.confidence_score != 0.0:
            self.confidence = self.confidence_score

        if self.metadata is not None and self.data is None:
            self.data = self.metadata
        elif self.data is not None:
            self.metadata = self.data

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "category": self.category.value,
            "query_type": self.query_type,
            "query_value": self.query_value,
            "status": self.status.value,
            "data": self.data,
            "confidence_score": self.confidence_score,
            "cached_at": self.cached_at.isoformat() if self.cached_at else None,
            "error_message": self.error_message,
        }


@dataclass
class SourceConfig:
    """Configuration for an OSINT source.

    Attributes:
        enabled: Whether the source is enabled
        priority: Source priority (1=CRITICAL, 2=IMPORTANT, 3=SUPPLEMENTARY)
        requires_api_key: Whether source requires API key
        rate_limit_rpm: Requests per minute rate limit
        rate_limit_rph: Requests per hour rate limit
        api_key: API key (not used for core free sources)
    """
    enabled: bool = True
    priority: int = 2  # Default: IMPORTANT
    requires_api_key: bool = False
    rate_limit_rpm: Optional[int] = None
    rate_limit_rph: Optional[int] = None
    api_key: Optional[str] = None


# ============================================================
# Darknet / Threat Intelligence Types
# ============================================================

class DarknetMarketplaceType(str, Enum):
    """Type of darknet marketplace or forum."""
    MARKETPLACE = "marketplace"
    FORUM = "forum"
    EXCHANGE = "exchange"
    HACKING = "hacking"
    CARDING = "carding"
    DRUGS = "drugs"
    WEAPONS = "weapons"
    UNKNOWN = "unknown"


class ExitRiskLevel(str, Enum):
    """Risk level classification for a darknet exit or exposure."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class MarketplaceThreatData:
    """Intelligence data about a darknet marketplace threat.

    Attributes:
        marketplace_name: Human-readable name of the marketplace
        marketplace_type: Type of marketplace (DarknetMarketplaceType)
        onion_address: .onion address of the marketplace
        threat_level: Severity level of the threat (ExitRiskLevel)
        confidence: Confidence score in range 0.0-1.0
        description: Human-readable description of the threat
        indicators: List of IOC indicators associated with threat
        source: OSINT source that discovered this threat
    """
    marketplace_name: str = ""
    marketplace_type: DarknetMarketplaceType = DarknetMarketplaceType.UNKNOWN
    onion_address: str = ""
    threat_level: ExitRiskLevel = ExitRiskLevel.NONE
    confidence: float = 0.0
    description: str = ""
    indicators: List[str] = field(default_factory=list)
    source: str = ""
    product_categories: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    exit_scam_status: bool = False
    shutdown_date: str = ""

    def __post_init__(self):
        if self.indicators is None:
            self.indicators = []
        if self.product_categories is None:
            self.product_categories = []
        if self.risk_factors is None:
            self.risk_factors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "marketplace_name": self.marketplace_name,
            "marketplace_type": self.marketplace_type.value,
            "onion_address": self.onion_address,
            "threat_level": self.threat_level.value,
            "confidence": self.confidence,
            "description": self.description,
            "indicators": self.indicators,
            "source": self.source,
            "product_categories": self.product_categories,
            "risk_factors": self.risk_factors,
            "exit_scam_status": self.exit_scam_status,
        }


@dataclass
class Tor2WebThreatData:
    """Intelligence data about a Tor2Web gateway exposure.
    
    Attributes:
        gateway_domains: List of gateway domains used
        de_anon_risk: Severity level of the de-anonymization risk
        recommendation: Recommended action to remediate
    """
    gateway_domains: List[str] = field(default_factory=list)
    de_anon_risk: ExitRiskLevel = ExitRiskLevel.UNKNOWN
    recommendation: str = ""
    referrer_leaks: bool = False

    def __post_init__(self):
        if self.gateway_domains is None:
            self.gateway_domains = []
            
        # For test compat: if de_anon_risk is not passed and UNKNOWN is missing
        if getattr(self, "de_anon_risk", None) == "unknown":
            self.de_anon_risk = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "gateway_domains": self.gateway_domains,
            "de_anon_risk": self.de_anon_risk.value if hasattr(self.de_anon_risk, 'value') else str(self.de_anon_risk),
            "recommendation": self.recommendation,
            "referrer_leaks": self.referrer_leaks,
        }

