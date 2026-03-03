"""
Financial site-type scoring strategy.

Highest security priority with zero tolerance policy for
authentication and transaction security issues.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class FinancialScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for financial websites (banks, investment, fintech).

    Prioritizes:
    - Security signals (0.30) - HIGHEST priority, zero tolerance
    - Structural analysis (0.25) - authentication flows, transaction UX
    - Graph signals (0.20) - regulatory compliance and reputation
    - Visual signals (0.10) - less critical than security
    - Metadata (0.10) - regulatory/licensing info
    - Temporal analysis (0.05) - less important

    ZERO TOLERANCE POLICY:
    - Missing SSL is CRITICAL (auto-deduct 50 points)
    - Cross-domain financial forms are CRITICAL
    - Form validation failures are HIGH severity
    - Account takeover risks are CRITICAL
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return FINANCIAL site type."""
        return ExtendedSiteType.FINANCIAL

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Financial Scoring Strategy"

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for financial context.

        Financial specific concerns:
        - SSL/TLS security is mandatory
        - Authentication and authorization security
        - Transaction flow security
        - Regulatory compliance indicators
        - Account takeover protection
        - Phishing targeting

        ZERO TOLERANCE policy applied.

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with financial-specific logic
        """
        # Base weight adjustments prioritizing security highest
        weight_adjustments = {
            "visual": 0.10,
            "structural": 0.25,
            "temporal": 0.05,
            "graph": 0.20,
            "meta": 0.10,
            "security": 0.30,
        }

        # Severity upgrades - zero tolerance for financial threats
        severity_modifications = {
            "hidden_cancel": "CRITICAL",
            "roach_motel": "CRITICAL",
            "forced_registration": "CRITICAL",
            "payment_flow_hijack": "CRITICAL",
            "auth_bypass": "CRITICAL",
            "credential_harvesting": "CRITICAL",
            "account_takeover": "CRITICAL",
            "transaction_manipulation": "CRITICAL",
        }

        # Custom findings with zero tolerance policy
        custom_findings = []

        # Zero tolerance: Missing SSL is CRITICAL with 50 point deduction
        if not context.has_ssl:
            custom_findings.append(("missing_ssl_financial", "CRITICAL", 50))

        if context.has_cross_domain_forms:
            custom_findings.append(("cross_domain_financial", "CRITICAL", 40))

        if context.form_validation_score < 50:
            custom_findings.append(("form_validation_failed", "HIGH", 20))

        # Dark patterns in financial context are particularly dangerous
        if context.has_dark_patterns:
            if "hidden_cancel" in context.dark_pattern_types:
                custom_findings.append(("hidden_cancel", "CRITICAL", 40))
            if "roach_motel" in context.dark_pattern_types:
                custom_findings.append(("roach_motel", "CRITICAL", 40))
            if "forced_registration" in context.dark_pattern_types:
                custom_findings.append(("forced_registration", "CRITICAL", 30))

        # Phishing is always critical for financial sites
        if context.has_phishing_hits:
            custom_findings.append(("phishing_financial", "CRITICAL", 50))

        # Detect universal critical triggers
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, "CRITICAL", 50) for trigger in critical_triggers]
            )

        # Narrative template with security-first messaging
        if context.has_ssl and context.security_score > 85:
            security_msg = "Strong security posture detected"
        elif context.has_ssl:
            security_msg = "Basic security present"
        else:
            security_msg = "CRITICAL: Security failures detected"

        narrative_template = f"Financial site: {security_msg}. "

        if context.form_validation_score < 70:
            narrative_template += "Form validation concerns. "

        if len(context.dark_pattern_types) > 0:
            narrative_template += f"Dark patterns detected: {', '.join(context.dark_pattern_types[:2])}"

        explanation = (
            "Financial site evaluation enforces ZERO TOLERANCE policy for security failures. "
            "Missing SSL triggers 50-point automatic deduction (CRITICAL). "
            "Security signals weighted highest (0.30) for authentication/transaction safety. "
            "Cross-domain financial forms and credential harvesting are always flagged as CRITICAL. "
            "Structural analysis (0.25) evaluates authentication flows and transaction UX. "
            "Graph signals (0.20) check regulatory compliance and institutional reputation. "
            "Any dark pattern in financial context triggers CRITICAL severity. "
            "Phishing targeting of financial sites is treated as maximum risk."
        )

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=severity_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
