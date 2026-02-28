"""
Social media site-type scoring strategy.

Focuses on account verification, malicious link detection,
and platform authenticity assessment.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class SocialMediaScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for social media platforms and profiles.

    Prioritizes:
    - Graph signals (0.30) - account verification and network analysis
    - Metadata (0.20) - platform legitimacy and account details
    - Visual signals (0.20) - profile authenticity and content quality
    - Security signals (0.15) - account security and privacy
    - Structural analysis (0.10) - platform infrastructure
    - Temporal analysis (0.05) - less important

    Key concerns:
    - Fake profiles and impersonation
    - Malicious links and phishing within posts
    - Bot activity indicators
    - Platform authenticity and verification
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return SOCIAL_MEDIA site type."""
        return ExtendedSiteType.SOCIAL_MEDIA

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Social Media Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for social media context.

        Social media specific concerns:
        - Profile verification and authenticity
        - Malicious links in posts/messages
        - Bot activity and automation
        - Platform legitimacy

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with social media-specific logic
        """
        # Base weight adjustments prioritizing graph signals
        weight_adjustments = {
            "visual": 0.20,
            "structural": 0.10,
            "temporal": 0.05,
            "graph": 0.30,
            "meta": 0.20,
            "security": 0.15,
        }

        # Severity modifications for social media concerns
        severity_modifications = {
            "fake_profiles": "HIGH",
            "malicious_links": "CRITICAL",
            "bot_activity": "MEDIUM",
            "impersonation": "CRITICAL",
            "spam_patterns": "MEDIUM",
        }

        custom_findings = []

        # Fake profile detection (via graph analysis)
        if context.graph_score < 50:
            custom_findings.append(("fake_profiles", "HIGH", 25))

        # Malicious links detected
        if context.has_phishing_hits:
            custom_findings.append(("malicious_links", "CRITICAL", 40))

        # Impersonation indicators
        if "impersonation" in context.dark_pattern_types:
            custom_findings.append(("impersonation", "CRITICAL", 45))

        # Bot activity (high script count, low temporal coherence)
        if context.script_count > 20 and context.temporal_score < 40:
            custom_findings.append(("bot_activity", "MEDIUM", 15))

        # SSL is important but less critical for profile access
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "MEDIUM", 10))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "HIGH", 25) for trigger in critical_triggers]
            )

        # Narrative template
        narrative_template = "Social media"

        if context.graph_score > 70:
            narrative_template += ": Profile verification probable"
        elif context.graph_score > 50:
            narrative_template += ": Profile verification mixed"
        else:
            narrative_template += ": Profile authenticity concerns"

        explanation = (
            "Social media evaluation prioritizes graph signals (0.30) for account verification "
            "and network analysis to detect fake profiles and impersonation. "
            "Metadata analysis (0.20) verifies platform legitimacy and account details. "
            "Visual signals (0.20) assess profile authenticity and content quality. "
            "Malicious links trigger CRITICAL severity (40-point deduction). "
            "Fake profiles flagged as HIGH (25-point deduction). "
            "Impersonation is CRITICAL (45-point deduction)."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
