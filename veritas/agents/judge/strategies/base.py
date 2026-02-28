"""
Strategy pattern base classes for site-type-specific scoring.

Provides abstract base class and data structures for implementing
site-type-specific threat scoring strategies.

Uses Strategy Pattern (GoF 1994) for runtime strategy switching.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ExtendedSiteType(str, Enum):
    """
    Extended site type enumeration for strategy routing.

    Extends existing SiteType with additional types for specialized scoring.
    """

    ECOMMERCE = "ecommerce"
    COMPANY_PORTFOLIO = "company_portfolio"
    FINANCIAL = "financial"
    SAAS_SUBSCRIPTION = "saas_subscription"
    NEWS_BLOG = "news_blog"
    SOCIAL_MEDIA = "social_media"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    GOVERNMENT = "government"
    GAMING = "gaming"
    DARKNET_SUSPICIOUS = "darknet_suspicious"


@dataclass(frozen=True)
class ScoringContext:
    """
    Context containing all available evidence for scoring.

    Wraps findings from Scout, Vision, Graph, Security agents for strategy evaluation.

    Attributes:
        url: Target URL being evaluated
        site_type: Detected site type
        site_type_confidence: Confidence in site type detection (0.0-1.0)
        visual_score: Vision agent score (0-100)
        structural_score: Structural analysis score (0-100)
        temporal_score: Temporal analysis score (0-100)
        graph_score: Graph investigator score (0-100)
        meta_score: Metadata analysis score (0-100)
        security_score: Security assessment score (0-100)
        has_ssl: Whether HTTPS is enabled
        domain_age_days: Domain age in days (if available)
        has_dark_patterns: Whether dark patterns detected
        dark_pattern_types: List of dark pattern types detected
        has_phishing_hits: Whether phishing services flagged this URL
        js_risk_score: JavaScript risk score (0-100)
        form_validation_score: Form validation score (0-100)
        has_cross_domain_forms: Whether cross-domain forms detected
        dom_depth: DOM depth of the page
        script_count: Number of scripts on page
        has_lazy_load: Whether lazy loading detected
        screenshot_count: Number of screenshots captured
    """

    # Site information
    url: str
    site_type: ExtendedSiteType
    site_type_confidence: float = 0.5

    # Evidence scores (0-100)
    visual_score: float = 50.0
    structural_score: float = 50.0
    temporal_score: float = 50.0
    graph_score: float = 50.0
    meta_score: float = 50.0
    security_score: float = 50.0

    # Security indicators
    has_ssl: bool = False
    domain_age_days: int | None = None
    has_dark_patterns: bool = False
    dark_pattern_types: list[str] = tuple()  # Use tuple for frozen dataclass
    has_phishing_hits: bool = False

    # Risk scores
    js_risk_score: float = 0.0
    form_validation_score: float = 0.0
    has_cross_domain_forms: bool = False

    # Page complexity
    dom_depth: int = 0
    script_count: int = 0
    has_lazy_load: bool = False
    screenshot_count: int = 1


@dataclass(frozen=True)
class ScoringAdjustment:
    """
    Scoring adjustments made by site-type strategy.

    Provides weights, severity modifications, and narrative context.

    Attributes:
        weight_adjustments: Dict mapping signal names to adjusted weights (sum <= 1.0)
        severity_modifications: Dict mapping finding names to severity levels
        custom_findings: List of custom findings as tuples (name, severity, auto_deduct)
        narrative_template: Template string for summary narrative
        explanation: Human-readable explanation of the adjustments
    """

    weight_adjustments: dict[str, float]
    severity_modifications: dict[str, str] = tuple()  # Use tuple for frozen
    custom_findings: list[tuple[str, str, int | None]] = tuple()
    narrative_template: str = ""
    explanation: str = ""


class ScoringStrategy(ABC):
    """
    Abstract base class for site-type-specific scoring strategies.

    Implements Strategy Pattern (GoF 1994) for runtime strategy switching.

    Subclasses must implement:
    - site_type property: Return the ExtendedSiteType this strategy handles
    - name property: Return human-readable strategy name
    - calculate_adjustments(): Return ScoringAdjustment for the context

    Protected methods:
    - _detect_critical_triggers(): Detect universal critical triggers
    """

    @property
    @abstractmethod
    def site_type(self) -> ExtendedSiteType:
        """Return the site type this strategy handles."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return human-readable strategy name."""
        pass

    @abstractmethod
    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments based on the context.

        Args:
            context: ScoringContext with all available evidence

        Returns:
            ScoringAdjustment with weights, severity mods, and narrative
        """
        pass

    def _detect_critical_triggers(self, context: ScoringContext) -> list[str]:
        """
        Detect universal critical triggers applicable to all site types.

        Universal triggers:
        - Missing SSL for financial/SaaS sites
        - Phishing hits from external services
        - High JavaScript risk score (> 80)

        Args:
            context: ScoringContext with available evidence

        Returns:
            List of critical trigger descriptions
        """
        triggers = []

        # Missing SSL is critical for sensitive site types
        if not context.has_ssl:
            if context.site_type in (
                ExtendedSiteType.FINANCIAL,
                ExtendedSiteType.SAAS_SUBSCRIPTION,
                ExtendedSiteType.HEALTHCARE,
                ExtendedSiteType.GOVERNMENT,
            ):
                triggers.append(f"Missing SSL on {context.site_type.value} site")

        # Phishing hits are always critical
        if context.has_phishing_hits:
            triggers.append("Phishing service detection")

        # High JS risk score is concerning
        if context.js_risk_score > 80:
            triggers.append(f"High JavaScript risk ({context.js_risk_score})")

        return triggers
