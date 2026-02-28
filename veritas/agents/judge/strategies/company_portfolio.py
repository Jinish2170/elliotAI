"""
Company portfolio site-type scoring strategy.

Focuses on entity verification and claim authenticability
through graph analysis of business relationships.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class CompanyPortfolioScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for company portfolio/corporate websites.

    Prioritizes:
    - Graph signals (0.30) - entity verification and business relationships
    - Metadata (0.20) - company information freshness and completeness
    - Structural analysis (0.20) - information architecture
    - Visual signals (0.15) - brand consistency
    - Security signals (0.10) - basic security required
    - Temporal analysis (0.05) - less important

    Key concerns:
    - Mismatched entity information
    - Unverifiable claims and credentials
    - Outdated or missing company information
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return COMPANY_PORTFOLIO site type."""
        return ExtendedSiteType.COMPANY_PORTFOLIO

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Company Portfolio Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for company portfolio context.

        Portfolio specific concerns:
        - Entity verification through business relationships
        - Claim authenticability
        - Company information completeness
        - Professional presentation standards

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with portfolio-specific logic
        """
        # Base weight adjustments prioritizing graph signals
        weight_adjustments = {
            "visual": 0.15,
            "structural": 0.20,
            "temporal": 0.05,
            "graph": 0.30,
            "meta": 0.20,
            "security": 0.10,
        }

        # Severity modifications for portfolio concerns
        severity_modifications = {
            "mismatched_entity": "HIGH",
            "unverifiable_claims": "MEDIUM",
            "outdated_info": "LOW",
            "missing_company_info": "MEDIUM",
        }

        custom_findings = []

        # Entity mismatch detection (via graph analysis)
        if context.graph_score < 50:
            custom_findings.append(("mismatched_entity", "HIGH", 20))

        # Unverifiable claims (low graph and metadata scores)
        if context.graph_score < 60 and context.meta_score < 60:
            custom_findings.append(("unverifiable_claims", "MEDIUM", 15))

        # Missing SSL is less critical but still a concern
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "MEDIUM", 10))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "HIGH", 25) for trigger in critical_triggers]
            )

        # Narrative template
        narrative_template = "Company portfolio site"

        if context.graph_score > 75:
            narrative_template += ": Entity verification confirmed"
        elif context.graph_score > 50:
            narrative_template += ": Entity verification partial"
        else:
            narrative_template += ": Entity verification concerns"

        explanation = (
            "Company portfolio evaluation prioritizes graph signals (0.30) for entity verification "
            "and business relationship validation. "
            "Metadata analysis (0.20) checks company information freshness and completeness. "
            "Structural analysis (0.20) evaluates information architecture and professional presentation. "
            "Entity mismatch detection triggers HIGH severity (20-point deduction). "
            "Unverifiable claims flagged as MEDIUM. "
            "Missing SSL is MEDIUM severity for portfolios (financial sites have higher requirements)."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
