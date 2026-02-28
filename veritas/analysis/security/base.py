"""
Security Module Foundation - Base Classes and Data Structures.

Defines the extensible architecture for security modules with tier-based
execution, enabling efficient parallel analysis of 25+ security modules.

Architecture:
    - SecurityModule: Abstract base class for all security modules
    - SecurityFinding: Enhanced finding with CWE ID and CVSS score
    - SecurityTier: Execution tier classification (FAST/MEDIUM/DEEP)

Integration:
    - CVSSCalculator from veritas.cwe.cvss_calculator
    - CWERegistry from veritas.cwe.registry
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from veritas.core.types import SecurityFinding as CoreSecurityFinding, Severity


# ============================================================
# Security Tier Classification
# ============================================================

class SecurityTier(str, Enum):
    """
    Execution tier for security modules with timeout guidelines.

    Tiers enable efficient parallel execution with timeout management:
        - FAST: < 5 seconds (quick header checks, cookie analysis)
        - MEDIUM: < 15 seconds (certificate validation, CSP parsing)
        - DEEP: < 30 seconds (full security analysis, deep inspection)

    Timeout suggestions:
        - FAST modules are for quick, synchronous checks that complete rapidly
        - MEDIUM modules for moderate complexity analysis
        - DEEP modules for comprehensive security audits
    """
    FAST = "FAST"
    MEDIUM = "MEDIUM"
    DEEP = "DEEP"

    @property
    def timeout_suggestion(self) -> int:
        """
        Get suggested timeout in seconds for this tier.

        Returns:
            Timeout in seconds (FAST=5, MEDIUM=15, DEEP=30)
        """
        return self._get_timeout()

    def _get_timeout(self) -> int:
        """Internal timeout mapping."""
        timeouts = {
            SecurityTier.FAST: 5,
            SecurityTier.MEDIUM: 15,
            SecurityTier.DEEP: 30,
        }
        return timeouts.get(self, 10)


# ============================================================
# Enhanced Security Finding
# ============================================================

@dataclass
class SecurityFinding:
    """
    Enhanced security finding with CWE ID and CVSS score.

    Extends core.types.SecurityFinding with additional security metadata
    for professional vulnerability reporting and CWE/CVSS integration.

    Attributes:
        category_id: Module/category identifier (e.g., "owasp_a01", "security_headers", "cookies")
        pattern_type: Specific vulnerability type (e.g., "missing_header", "insecure_cookie")
        severity: Severity level (low, medium, high, critical)
        confidence: Confidence score (0.0-1.0)
        description: Technical description of the finding
        evidence: What was found (actual value or observation)
        cwe_id: CWE identifier (e.g., "CWE-523") - mapped via CWEMapper
        cvss_score: CVSS base score (0.0-10.0) - calculated via CVSSCalculator
        recommendation: Remediation guidance for the finding
        url_finding: Whether this finding is URL-specific (default False)

    Notes:
        - Compatible with core.types.SecurityFinding for serialization
        - cwe_id and cvss_score are added for Phase 9 CWE/CVSS integration
    """
    category_id: str
    pattern_type: str
    severity: str
    confidence: float
    description: str
    evidence: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    recommendation: str = ""
    url_finding: bool = False

    def __post_init__(self):
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

        # Validate cvss_score if provided
        if self.cvss_score is not None and (self.cvss_score < 0.0 or self.cvss_score > 10.0):
            raise ValueError(f"CVSS score must be between 0.0 and 10.0, got {self.cvss_score}")

    def to_dict(self) -> dict:
        """
        Convert to JSON-serializable dictionary.

        Returns:
            Dictionary with all fields
        """
        return {
            "category_id": self.category_id,
            "pattern_type": self.pattern_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "description": self.description,
            "evidence": self.evidence,
            "cwe_id": self.cwe_id,
            "cvss_score": self.cvss_score,
            "recommendation": self.recommendation,
            "url_finding": self.url_finding,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SecurityFinding":
        """
        Create SecurityFinding from JSON-serializable dictionary.

        Args:
            data: Dictionary with SecurityFinding fields

        Returns:
            SecurityFinding instance
        """
        return cls(
            category_id=data["category_id"],
            pattern_type=data["pattern_type"],
            severity=data["severity"],
            confidence=data["confidence"],
            description=data["description"],
            evidence=data["evidence"],
            cwe_id=data.get("cwe_id"),
            cvss_score=data.get("cvss_score"),
            recommendation=data.get("recommendation", ""),
            url_finding=data.get("url_finding", False),
        )

    def to_core_finding(self) -> CoreSecurityFinding:
        """
        Convert to core.types.SecurityFinding for backward compatibility.

        Returns:
            CoreSecurityFinding instance with compatible fields
        """
        return CoreSecurityFinding.create(
            category=self.category_id,
            severity=self.severity,
            evidence=self.evidence,
            source_module=self.category_id,
            confidence=self.confidence,
        )


# ============================================================
# SecurityModule Abstract Base Class
# ============================================================

class SecurityModule(ABC):
    """
    Abstract base class for all security modules.

    Provides tier classification, auto-discovery registration, and async
    analyze() interface for extensible security module architecture.

    All security modules must:
        1. Inherit from SecurityModule
        2. Implement the abstract analyze() method
        3. Set the category_id abstract property
        4. Override timeout and tier properties as needed (optional)

    Usage:
        class MySecurityAnalyzer(SecurityModule):
            @property
            def category_id(self) -> str:
                return "my_security_module"

            async def analyze(self, url: str, page_content: Optional[str] = None,
                            headers: Optional[dict] = None, dom_meta: Optional[dict] = None
                            ) -> List[SecurityFinding]:
                # Security analysis logic here
                return [SecurityFinding(...)]
    """

    # Default timeout in seconds (override per module)
    _default_timeout: int = 10

    # Default tier (override per module)
    _default_tier: SecurityTier = SecurityTier.MEDIUM

    @property
    def timeout(self) -> int:
        """
        Get timeout for this module in seconds.

        Returns:
            Timeout in seconds (override by setting _default_timeout)
        """
        return self._default_timeout

    @property
    def tier(self) -> SecurityTier:
        """
        Get execution tier for this module.

        Returns:
            SecurityTier (override by setting _default_tier)
        """
        return self._default_tier

    @property
    @abstractmethod
    def category_id(self) -> str:
        """
        Get module category identifier.

        Must be overridden by subclasses to provide a unique identifier.

        Returns:
            Category ID string (e.g., "security_headers", "cookies", "csp")
        """
        pass

    @abstractmethod
    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze a URL for security issues.

        Must be overridden by subclasses with module-specific logic.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers dict
            dom_meta: Optional DOM metadata (depth, node counts, etc.)

        Returns:
            List of SecurityFinding objects (empty if no issues found)
        """
        pass

    def to_dict(self) -> dict:
        """
        Convert module to dictionary for progress streaming.

        Returns:
            Dictionary with module metadata
        """
        return {
            "category_id": self.category_id,
            "tier": self.tier.value,
            "timeout": self.timeout,
            "module_name": self.__class__.__name__,
        }

    @classmethod
    def get_module_info(cls) -> dict:
        """
        Get module information for auto-discovery.

        Returns:
            Dictionary with module metadata
        """
        # Try to instantiate to get instance properties
        try:
            instance = cls()
            return {
                "class_name": cls.__name__,
                "category_id": instance.category_id,
                "tier": instance.tier.value,
                "timeout": instance.timeout,
            }
        except Exception:
            # Return class-level info if instantiation fails
            return {
                "class_name": cls.__name__,
                "category_id": cls.__name__.lower(),
                "tier": SecurityTier.MEDIUM.value,
                "timeout": 10,
            }

    @classmethod
    def is_discoverable(cls) -> bool:
        """
        Check if this module should be auto-discovered.

        Override to False for abstract base classes or test modules.

        Returns:
            True if module should be auto-discovered (default True)
        """
        return True


# ============================================================
# Module Registration Registry
# ============================================================

# Registry for discovered security modules
_SECURITY_MODULE_REGISTRY: dict[str, type[SecurityModule]] = {}


def register_security_module(module_class: type[SecurityModule]) -> None:
    """
    Register a security module in the global registry.

    Args:
        module_class: SecurityModule subclass to register
    """
    module_info = module_class.get_module_info()
    _SECURITY_MODULE_REGISTRY[module_info["category_id"]] = module_class


def get_registered_modules() -> List[type[SecurityModule]]:
    """
    Get all registered security modules.

    Returns:
        List of registered SecurityModule classes
    """
    return list(_SECURITY_MODULE_REGISTRY.values())


def clear_module_registry() -> None:
    """Clear the security module registry (useful for testing)."""
    global _SECURITY_MODULE_REGISTRY
    _SECURITY_MODULE_REGISTRY = {}
