"""
Government site-type scoring strategy.

Highest emphasis on official verification with zero tolerance
for fake government indicators.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class GovernmentScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for government websites.

    Prioritizes:
    - Graph signals (0.40) - official verification and domain legitimacy
    - Metadata (0.25) - official agency information and contact details
    - Visual signals (0.10) - official branding and seals
    - Structural analysis (0.15) - official documentation structure
    - Security signals (0.05) - government sites expected to be secure
    - Temporal analysis (0.05) - less important

    Key concerns:
    - Fake government domains (e.g., .gov spoofed)
    - Missing government domain suffix
    - Spoofed official sites
    - Impersonation of government agencies

    ANY fake government indicator -> CRITICAL severity.
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return GOVERNMENT site type."""
        return ExtendedSiteType.GOVERNMENT

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Government Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for government context.

        Government specific concerns:
        - Official domain verification (.gov, .gov.<country>)
        - Fake government indicators and impersonation
        - Official agency and contact information
        - Spoofed official websites

        ANY fake government indicator is CRITICAL.

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with government-specific logic
        """
        # Base weight adjustments prioritizing graph signals
        weight_adjustments = {
            "visual": 0.10,
            "structural": 0.15,
            "temporal": 0.05,
            "graph": 0.40,
            "meta": 0.25,
            "security": 0.05,
        }

        # Severity modifications - ANY fake government indicator -> CRITICAL
        severity_modifications = {
            "fake_gov_domain": "CRITICAL",
            "missing_gov_suffix": "HIGH",
            "spoofed_official_site": "CRITICAL",
            "impersonation_agency": "CRITICAL",
            "fake_official_seals": "CRITICAL",
            "misleading_official_language": "HIGH",
        }

        custom_findings = []

        # Check for .gov domain (or other government TLDs)
        has_gov_domain = any(
            tld in context.url.lower()
            for tld in [".gov", ".gov.uk", ".gov.au", ".gov.ca", ".gov.in"]
        )

        if not has_gov_domain:
            custom_findings.append(("missing_gov_suffix", "HIGH", 25))
        else:
            # If has .gov but graph score is low, might be spoofed
            if context.graph_score < 50:
                custom_findings.append(("spoofed_official_site", "CRITICAL", 50))

        # Fake government domain indicators
        if "fake_gov" in context.dark_pattern_types:
            custom_findings.append(("fake_gov_domain", "CRITICAL", 50))

        # Agency impersonation
        if "impersonation" in context.dark_pattern_types:
            custom_findings.append(("impersonation_agency", "CRITICAL", 50))

        # Fake official seals
        if "fake_seals" in context.dark_pattern_types:
            custom_findings.append(("fake_official_seals", "CRITICAL", 45))

        # SSL is expected for government sites
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", "HIGH", 15))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "CRITICAL", 50) for trigger in critical_triggers]
            )

        # Narrative template
        narrative_template = "Government site"

        if has_gov_domain and context.graph_score > 70:
            narrative_template += ": Official verification likely"
        elif has_gov_domain:
            narrative_template += ": .gov domain present but verification uncertain"
        else:
            narrative_template += ": Missing .gov domain (HIGH risk)"

        explanation = (
            "Government evaluation prioritizes graph signals (0.40) for official verification "
            "and domain legitimacy assessment. "
            "Metadata analysis (0.25) verifies official agency information and contact details. "
            "Missing .gov domain suffix triggers HIGH severity (25-point deduction). "
            "ANY fake government indicator is CRITICAL (50-point maximum deduction). "
            "Fake government domains, spoofed official sites, and agency impersonation "
            "are treated as maximum trust violations. "
            "Fake official seals flagged as CRITICAL (45-point deduction)."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
