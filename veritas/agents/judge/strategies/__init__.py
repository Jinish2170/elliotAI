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
        STRATEGY_REGISTRY,
    )
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)

# Strategy registry and functions will be added in Task 6
# STRATEGY_REGISTRY: dict[ExtendedSiteType, ScoringStrategy]
# get_strategy(site_type: ExtendedSiteType) -> Optional[ScoringStrategy]
# get_all_strategies() -> dict[ExtendedSiteType, ScoringStrategy]

__all__ = [
    "ExtendedSiteType",
    "ScoringContext",
    "ScoringAdjustment",
    "ScoringStrategy",
]
