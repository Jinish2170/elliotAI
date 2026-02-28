"""
Scoring strategies for site-type-specific threat assessment.

Uses Strategy Pattern (GoF 1994) for runtime strategy switching.

Usage:
    from veritas.agents.judge.strategies import (
        ExtendedSiteType,
        ScoringContext,
        ScoringAdjustment,
        ScoringStrategy,
        get_strategy,
        get_all_strategies,
        STRATEGY_REGISTRY,
    )
"""

from typing import Optional

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)

# Import all strategies for registry
from veritas.agents.judge.strategies.company_portfolio import CompanyPortfolioScoringStrategy
from veritas.agents.judge.strategies.darknet_suspicious import DarknetSuspiciousScoringStrategy
from veritas.agents.judge.strategies.ecommerce import EcommerceScoringStrategy
from veritas.agents.judge.strategies.education import EducationScoringStrategy
from veritas.agents.judge.strategies.financial import FinancialScoringStrategy
from veritas.agents.judge.strategies.gaming import GamingScoringStrategy
from veritas.agents.judge.strategies.government import GovernmentScoringStrategy
from veritas.agents.judge.strategies.healthcare import HealthcareScoringStrategy
from veritas.agents.judge.strategies.news_blog import NewsBlogScoringStrategy
from veritas.agents.judge.strategies.saas_subscription import SaaSSubscriptionScoringStrategy
from veritas.agents.judge.strategies.social_media import SocialMediaScoringStrategy


# Strategy registry: maps site types to strategy classes
STRATEGY_REGISTRY: dict[ExtendedSiteType, type[ScoringStrategy]] = {
    ExtendedSiteType.ECOMMERCE: EcommerceScoringStrategy,
    ExtendedSiteType.COMPANY_PORTFOLIO: CompanyPortfolioScoringStrategy,
    ExtendedSiteType.FINANCIAL: FinancialScoringStrategy,
    ExtendedSiteType.SAAS_SUBSCRIPTION: SaaSSubscriptionScoringStrategy,
    ExtendedSiteType.NEWS_BLOG: NewsBlogScoringStrategy,
    ExtendedSiteType.SOCIAL_MEDIA: SocialMediaScoringStrategy,
    ExtendedSiteType.EDUCATION: EducationScoringStrategy,
    ExtendedSiteType.HEALTHCARE: HealthcareScoringStrategy,
    ExtendedSiteType.GOVERNMENT: GovernmentScoringStrategy,
    ExtendedSiteType.GAMING: GamingScoringStrategy,
    ExtendedSiteType.DARKNET_SUSPICIOUS: DarknetSuspiciousScoringStrategy,
}


def get_strategy(site_type: ExtendedSiteType) -> Optional[ScoringStrategy]:
    """
    Get an instantiated strategy for the specified site type.

    Args:
        site_type: ExtendedSiteType to get strategy for

    Returns:
        Instantiated ScoringStrategy, or None if site_type not registered
    """
    strategy_class = STRATEGY_REGISTRY.get(site_type)
    if strategy_class:
        return strategy_class()
    return None


def get_all_strategies() -> dict[ExtendedSiteType, ScoringStrategy]:
    """
    Get all instantiated strategies.

    Returns:
        Dict mapping ExtendedSiteType to instantiated ScoringStrategy
    """
    return {
        site_type: strategy_class()
        for site_type, strategy_class in STRATEGY_REGISTRY.items()
    }


__all__ = [
    "ExtendedSiteType",
    "ScoringContext",
    "ScoringAdjustment",
    "ScoringStrategy",
    "STRATEGY_REGISTRY",
    "get_strategy",
    "get_all_strategies",
]

