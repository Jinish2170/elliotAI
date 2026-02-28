"""
Education site-type scoring strategy.

Prioritizes institutional verification and credential
authenticity assessment for academic content.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class EducationScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for education/academic websites.

    Prioritizes:
    - Graph signals (0.25) - institutional verification and accreditation
    - Metadata (0.25) - credential and certification information
    - Structural analysis (0.20) - course/institution information architecture
    - Visual signals (0.15) - institutional branding consistency
    - Security signals (0.10) - basic security
    - Temporal analysis (0.05) - less important

    Key concerns:
    - Fake certifications and degrees
    - Unverifiable credentials
    - Impersonation of legitimate institutions
    - Diploma mill indicators
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return EDUCATION site type."""
        return ExtendedSiteType.EDUCATION

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Education Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for education context.

        Education specific concerns:
    - Institutional verification and accreditation
        - Credential authenticity
        - Fake certification and diploma mill detection
        - Impersonation of legitimate institutions

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with education-specific logic
        """
        # Base weight adjustments prioritizing graph and metadata
        weight_adjustments = {
            "visual": 0.15,
            "structural": 0.20,
            "temporal": 0.05,
            "graph": 0.25,
            "meta": 0.25,
            "security": 0.10,
        }

        # Severity modifications for education concerns
        severity_modifications = {
            "fake_certifications": "HIGH",
            "unverifiable_credentials": "MEDIUM",
            "diploma_mill": "CRITICAL",
            "institution_impersonation": "CRITICAL",
            "accreditation_fake": "HIGH",
        }

        custom_findings = []

        # Fake certification detection
        if "fake_cert" in context.dark_pattern_types:
            custom_findings.append(("fake_certifications", "HIGH", 30))

        # Unverifiable credentials (low graph and metadata scores)
        if context.graph_score < 50 and context.meta_score < 60:
            custom_findings.append(("unverifiable_credentials", "MEDIUM", 20))

        # Diploma mill indicators
        if "diploma_mill" in context.dark_pattern_types:
            custom_findings.append(("diploma_mill", "CRITICAL", 45))

        # Institution impersonation
        if "impersonation" in context.dark_pattern_types:
            custom_findings.append(("institution_impersonation", "CRITICAL", 45))

        # SSL is important for protecting student data
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "HIGH", 20))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "HIGH", 30) for trigger in critical_triggers]
            )

        # Narrative template
        narrative_template = "Education site"

        if context.graph_score > 75 and context.meta_score > 70:
            narrative_template += ": Institutional verification likely"
        elif context.graph_score >= 50:
            narrative_template += ": Institutional verification partial"
        else:
            narrative_template += ": Institutional verification concerns"

        explanation = (
            "Education evaluation prioritizes graph signals (0.25) for institutional verification "
            "and accreditation status. "
            "Metadata analysis (0.25) checks credential and certification information validity. "
            "Structural analysis (0.20) evaluates course/institution information architecture. "
            "Fake certifications flagged as HIGH (30-point deduction). "
            "Diploma mill indicators are CRITICAL (45-point deduction). "
            "Institution impersonation is CRITICAL (45-point deduction)."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
