"""
Gaming site-type scoring strategy.

Balanced approach with focus on loot box manipulation
and pay-to-win pattern detection.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class GamingScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for gaming websites and platforms.

    Prioritizes:
    - Balanced weights across all signals:
    - Visual signals (0.20) - UI fairness, dark pattern detection
    - Security signals (0.20) - account and payment security
    - Graph signals (0.15) - platform reputation and reviews
    - Metadata (0.20) - game information and pricing transparency
    - Structural analysis (0.15) - game/platform infrastructure
    - Temporal analysis (0.10) - fake events and time-limited offers

    Key concerns:
    - Loot box manipulation and RNG unfairness
    - Fake rewards and impossible prizes
    - Pay-to-win mechanics that break game balance
    - Account security and cheating detection
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return GAMING site type."""
        return ExtendedSiteType.GAMING

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Gaming Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for gaming context.

        Gaming specific concerns:
        - Loot box manipulation and unfair RNG
        - Fake rewards and impossible prizes
        - Pay-to-win mechanics
        - Account security and cheating

        Pay-to-win patterns flagged as MEDIUM severity.

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with gaming-specific logic
        """
        # Base weight adjustments - balanced approach
        weight_adjustments = {
            "visual": 0.20,
            "structural": 0.15,
            "temporal": 0.10,
            "graph": 0.15,
            "meta": 0.20,
            "security": 0.20,
        }

        # Severity modifications for gaming concerns
        severity_modifications = {
            "loot_box_manipulation": "HIGH",
            "fake_rewards": "MEDIUM",
            "impossible_prizes": "HIGH",
            "pay_to_win": "MEDIUM",
            "account_theft": "CRITICAL",
            "cheating_detected": "MEDIUM",
            "fake_events": "MEDIUM",
        }

        custom_findings = []

        # Loot box manipulation
        if "loot_box" in context.dark_pattern_types:
            custom_findings.append(("loot_box_manipulation", "HIGH", 25))

        # Fake rewards and impossible prizes
        if "fake_rewards" in context.dark_pattern_types:
            custom_findings.append(("fake_rewards", "MEDIUM", 15))

        # Pay-to-win patterns
        if "pay_to_win" in context.dark_pattern_types:
            custom_findings.append(("pay_to_win", "MEDIUM", 15))

        # Account theft/security concerns
        if "account_theft" in context.dark_pattern_types:
            custom_findings.append(("account_theft", "CRITICAL", 40))

        # High JS risk could indicate cheating scripts
        if context.js_risk_score > 70:
            custom_findings.append(("cheating_detected", "MEDIUM", 15))

        # SSL important for account/payment security
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "MEDIUM", 15))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "HIGH", 25) for trigger in critical_triggers]
            )

        # Narrative template
        narrative_template = "Gaming site"

        if context.security_score > 70:
            narrative_template += ": Account security adequate"
        else:
            narrative_template += ": Account security concerns"

        if len(context.dark_pattern_types) > 0:
            narrative_template += f", concerns: {', '.join(context.dark_pattern_types[:2])}"

        explanation = (
            "Gaming evaluation uses balanced weights across all signals. "
            "Visual and security signals each weighted 0.20 for UI fairness and account safety. "
            "Metadata (0.20) checks game information and pricing transparency. "
            "Loot box manipulation flagged as HIGH (25-point deduction). "
            "Pay-to-win patterns flagged as MEDIUM (15-point deduction). "
            "Account theft is CRITICAL (40-point deduction). "
            "Cheating detection based on high JavaScript risk scores."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
