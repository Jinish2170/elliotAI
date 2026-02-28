"""
SaaS subscription site-type scoring strategy.

Balances feature value against manipulative subscription tactics
and cancellation barriers.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class SaaSSubscriptionScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for SaaS subscription websites.

    Prioritizes:
    - Visual signals (0.20) - dark patterns in pricing/CTAs
    - Security signals (0.20) - account and data security
    - Graph signals (0.20) - company reputation and reviews
    - Structural analysis (0.15) - subscription UX flows
    - Temporal analysis (0.15) - fake expiration/urgency
    - Metadata (0.10) - pricing transparency

    Key concerns:
    - Hidden cancellation mechanisms
    - Roach motel patterns (easy to join, hard to leave)
    - Fake expiration dates and urgency tactics
    - Forced registration for basic features
    - Auto-renewal without clear consent

    Cancellation barriers (hidden_cancel, roach_motel) are CRITICAL.
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return SAAS_SUBSCRIPTION site type."""
        return ExtendedSiteType.SAAS_SUBSCRIPTION

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "SaaS Subscription Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for SaaS subscription context.

        SaaS specific concerns:
        - Hidden cancellation mechanisms
        - Roach motel patterns (easy signup, hard cancel)
        - Expiring offers and fake urgency
        - Forced registration for basic features
        - Pricing obscurity and dark patterns

        Cancellation barriers are treated as CRITICAL violations.

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with SaaS-specific logic
        """
        # Base weight adjustments
        weight_adjustments = {
            "visual": 0.20,
            "structural": 0.15,
            "temporal": 0.15,
            "graph": 0.20,
            "meta": 0.10,
            "security": 0.20,
        }

        # Severity upgrades focused on subscription manipulation
        severity_modifications = {
            "hidden_cancel": "CRITICAL",
            "roach_motel": "CRITICAL",
            "forced_registration": "HIGH",
            "expiring_offer": "HIGH",
            "fake_urgency": "MEDIUM",
            "misleading_pricing": "HIGH",
            "hard_to_cancel": "CRITICAL",
        }

        # Custom findings for SaaS specific threats
        custom_findings = []

        # Cancellation barriers are CRITICAL
        if context.has_dark_patterns:
            if "hidden_cancel" in context.dark_pattern_types:
                custom_findings.append(("hidden_cancel", "CRITICAL", 45))
            if "roach_motel" in context.dark_pattern_types:
                custom_findings.append(("roach_motel", "CRITICAL", 45))
            if "forced_registration" in context.dark_pattern_types:
                custom_findings.append(("forced_registration", "HIGH", 25))
            if "expiring_offer" in context.dark_pattern_types:
                custom_findings.append(("expiring_offer", "HIGH", 20))

        # Fake expiration detection (temporal analysis)
        if "fake_expiration" in context.dark_pattern_types:
            custom_findings.append(("fake_expiration", "MEDIUM", 15))

        # SSL is important for account security
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "HIGH", 20))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "CRITICAL", 40) for trigger in critical_triggers]
            )

        # Narrative template
        has_cancel_barrier = any(
            p in context.dark_pattern_types
            for p in ["hidden_cancel", "roach_motel", "hard_to_cancel"]
        )

        narrative_template = "SaaS subscription site"

        if has_cancel_barrier:
            narrative_template += ": CANCELLATION BARRIERS DETECTED (CRITICAL). "
        else:
            narrative_template += ": Cancellation flow appears accessible. "

        if context.security_score > 75:
            narrative_template += "Strong account security. "
        elif context.security_score >= 50:
            narrative_template += "Basic account security. "
        else:
            narrative_template += "Account security concerns. "

        if len(context.dark_pattern_types) > 0:
            narrative_template += f"Other concerns: {', '.join(set(context.dark_pattern_types) - set(['hidden_cancel', 'roach_motel']))[:2]}"

        explanation = (
            "SaaS subscription evaluation focuses on cancellation barrier detection. "
            "Hidden cancellation (hidden_cancel) and roach motel patterns are CRITICAL (45-point deduction). "
            "Security and visual signals weighted equally (0.20 each) for account safety and pricing transparency. "
            "Graph signals (0.20) verify company reputation and user reviews. "
            "Temporal analysis (0.15) detects fake expiration and fake urgency tactics. "
            "Forced registration and expiring offers flagged as HIGH severity. "
            "Cancel barriers are fundamental violations and trigger maximum penalty."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
