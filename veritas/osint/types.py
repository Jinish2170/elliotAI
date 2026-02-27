"""Data types and enums for OSINT sources.

Defines standardized data structures, enums, and configuration
objects used across all OSINT source implementations.
"""

from dataclasses import dataclass
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
    source: str
    category: OSINTCategory
    query_type: str
    query_value: str
    status: SourceStatus
    data: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    cached_at: Optional[datetime] = None
    error_message: Optional[str] = None

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
