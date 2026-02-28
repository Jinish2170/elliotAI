"""
Healthcare site-type scoring strategy.

Highest priority on medical credentialing and patient data protection.
Any health claim triggers minimum HIGH severity.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class HealthcareScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for healthcare websites (clinics, hospitals, telehealth).

    Prioritizes:
    - Graph signals (0.35) - medical credentialing and licensing verification
    - Metadata (0.20) - healthcare provider information
    - Structural analysis (0.20) - medical content and service information
    - Security signals (0.10) - HIPAA-level patient data protection
    - Visual signals (0.10) - professional medical presentation
    - Temporal analysis (0.05) - less important

    Key concerns:
    - Unverified medical claims
    - Missing medical credentials
    - Patient data security violations
    - Fake healthcare providers

    ANY health claim is minimum HIGH severity.
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return HEALTHCARE site type."""
        return ExtendedSiteType.HEALTHCARE

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Healthcare Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for healthcare context.

        Healthcare specific concerns:
        - Medical credentialing and licensing
        - Patient data security (HIPAA requirements)
        - Unverified medical claims
        - Fake healthcare providers

        All health claims trigger minimum HIGH severity.

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with healthcare-specific logic
        """
        # Base weight adjustments prioritizing graph signals
        weight_adjustments = {
            "visual": 0.10,
            "structural": 0.20,
            "temporal": 0.05,
            "graph": 0.35,
            "meta": 0.20,
            "security": 0.10,
        }

        # Severity modifications - ANY health claim -> HIGH minimum
        severity_modifications = {
            "unverified_medical_claims": "HIGH",
            "missing_credentials": "HIGH",
            "missing_medical_license": "CRITICAL",
            "fake_provider": "CRITICAL",
            "data_security_violation": "CRITICAL",
            "medical_misinformation": "HIGH",
        }

        custom_findings = []

        # MISSING SSL for healthcare is CRITICAL
        if not context.has_ssl:
            custom_findings.append(("missing_ssl_healthcare", "CRITICAL", 40))

        # Unverified medical claims
        if context.graph_score < 60 or context.meta_score < 60:
            custom_findings.append(("unverified_medical_claims", "HIGH", 30))

        # Missing medical credentials
        if "missing_credentials" in context.dark_pattern_types:
            custom_findings.append(("missing_credentials", "HIGH", 35))

        # Fake healthcare provider
        if "fake_provider" in context.dark_pattern_types:
            custom_findings.append(("fake_provider", "CRITICAL", 50))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "CRITICAL", 45) for trigger in critical_triggers]
            )

        # Narrative template
        narrative_template = "Healthcare site"

        if context.has_ssl and context.security_score > 75:
            narrative_template += ": Patient data security adequate"
        else:
            narrative_template += ": Patient data security CONCERNS"

        if context.graph_score > 75:
            narrative_template += ", medical credentialing verified"
        else:
            narrative_template += ", medical credentialing verification needed"

        explanation = (
            "Healthcare evaluation prioritizes graph signals (0.35) for medical credentialing "
            "and licensing verification. "
            "Metadata analysis (0.20) checks healthcare provider information completeness. "
            "Missing SSL for healthcare is CRITICAL (40-point deduction) due to HIPAA requirements. "
            "Unverified medical claims flagged as HIGH (30-point deduction). "
            "ANY health claim triggers minimum HIGH severity to protect patient safety. "
            "Fake healthcare providers are CRITICAL (50-point deduction)."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
