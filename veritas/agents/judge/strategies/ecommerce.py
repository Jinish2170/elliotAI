"""
E-commerce site-type scoring strategy.

Prioritizes visual analysis for dark pattern detection and
security signals for payment form safety.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class EcommerceScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for e-commerce websites.

    Prioritizes:
    - Visual signals (0.25) - dark patterns critical for trust
    - Security signals (0.20) - payment safety paramount
    - Structural analysis (0.15) - form and checkout UX
    - Temporal analysis (0.15) - fake countdowns/scarcity
    - Graph signals (0.20) - seller reputation
    - Metadata (0.05) - product authenticity

    Zero tolerance for payment security issues and dark patterns.
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return ECOMMERCE site type."""
        return ExtendedSiteType.ECOMMERCE

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "E-commerce Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for e-commerce context.

        E-commerce specific concerns:
        - Dark patterns for fake scarcity/urgency
        - Cross-domain payment forms
        - Hidden costs and terms
        - Fake countdown timers
        - Bait-and-switch tactics

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with e-commerce-specific logic
        """
        # Base weight adjustments prioritizing visual and security
        weight_adjustments = {
            "visual": 0.25,
            "security": 0.20,
            "structural": 0.15,
            "temporal": 0.15,
            "graph": 0.20,
            "meta": 0.05,
        }

        # Severity upgrades for common e-commerce dark patterns
        severity_modifications = {
            "hidden_costs": "CRITICAL",
            "fake_scarcity": "CRITICAL",
            "fake_countdown": "CRITICAL",
            "bait_and_switch": "CRITICAL",
            "forced_comparison": "HIGH",
            "manipulative_subscription": "HIGH",
            "trick_question": "MEDIUM",
        }

        # Custom findings for e-commerce specific threats
        custom_findings = []

        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "CRITICAL", 30))

        if context.has_dark_patterns:
            if "fake_scarcity" in context.dark_pattern_types:
                custom_findings.append(("fake_scarcity", "HIGH", None))
            if "fake_countdown" in context.dark_pattern_types:
                custom_findings.append(("fake_countdown", "HIGH", None))
            if "hidden_costs" in context.dark_pattern_types:
                custom_findings.append(("hidden_costs", "HIGH", None))

        if context.has_cross_domain_forms:
            custom_findings.append(("cross_domain_payment", "HIGH", None))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "CRITICAL", 50) for trigger in critical_triggers]
            )

        # Narrative template for summary
        pattern_count = len(context.dark_pattern_types) if context.dark_pattern_types else 0
        narrative_template = f"E-commerce site {pattern_count if pattern_count > 0 else 'no'} dark pattern{'s' if pattern_count != 1 else ''} detected. "

        if context.has_ssl and context.security_score > 75:
            narrative_template += "Secure payment environment. "
        else:
            narrative_template += "Payment security concerns. "

        if pattern_count > 0:
            narrative_template += f"Detected: {', '.join(context.dark_pattern_types[:3])}"

        explanation = (
            "E-commerce trust evaluation prioritizes visual analysis for dark pattern detection "
            "(fake scarcity, countdowns, hidden costs) and security signals for payment form safety. "
            "Temporal analysis detects fake urgency tactics. Cross-domain payment forms are flagged. "
            "Zero tolerance for payment security issues and manipulative dark patterns."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
