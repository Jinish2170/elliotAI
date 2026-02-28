"""
Darknet/suspicious site-type scoring strategy.

PARANOIA MODE: All findings minimum HIGH severity with severity_upgrade.
Critical red flags trigger CRITICAL severity.
Maximally suspicious approach with 0.30 security weight.
"""

from veritas.agents.judge.strategies.base import (
    ExtendedSiteType,
    ScoringAdjustment,
    ScoringContext,
    ScoringStrategy,
)


class DarknetSuspiciousScoringStrategy(ScoringStrategy):
    """
    Scoring strategy for darknet and highly suspicious websites.

    PARANOIA MODE: All findings are minimum HIGH severity with automatic
    severity_upgrade by 1 level (INFO->LOW, LOW->MEDIUM, MEDIUM->HIGH, HIGH->CRITICAL).

    Prioritizes:
    - Security signals (0.30) - highest priority for suspicious sites
    - Graph signals (0.30) - network analysis and reputation
    - Visual signals (0.15) - darknet interface detection
    - Metadata (0.10) - minimal trust in metadata
    - Structural analysis (0.10) - infrastructure analysis
    - Temporal analysis (0.05) - less important

    Key concerns:
    - Onion links and darknet access points
    - BTC/crypto-only payment (no traceability)
    - Escrow warnings and trust issues
    - Any darknet pattern is minimum HIGH severity

    PARANOIA MODE: severity_upgrade by 1 level for ALL findings.
    """

    @property
    def site_type(self) -> ExtendedSiteType:
        """Return DARKNET_SUSPICIOUS site type."""
        return ExtendedSiteType.DARKNET_SUSPICIOUS

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "Darknet Suspicious Scoring Strategy"

    def _severity_upgrade(self, severity: str) -> str:
        """
        PARANOIA MODE: Upgrade severity by 1 level.

        Args:
            severity: Original severity string

        Returns:
            Upgraded severity string
        """
        upgrade_map = {
            "info": "LOW",
            "INFO": "LOW",
            "low": "MEDIUM",
            "LOW": "MEDIUM",
            "medium": "HIGH",
            "MEDIUM": "HIGH",
            "high": "CRITICAL",
            "HIGH": "CRITICAL",
            "critical": "CRITICAL",
            "CRITICAL": "CRITICAL",
        }
        return upgrade_map.get(severity, severity)

    def calculate_adjustments(self, context: ScoringContext) -> ScoringAdjustment:
        """
        Calculate scoring adjustments for darknet/suspicious context.

        Darknet specific concerns:
        - Onion links and darknet access points
        - BTC/crypto-only payment (no traceability)
        - Escrow warnings and marketplace trust issues
        - Illegal content indicators

        PARANOIA MODE: All findings minimum HIGH severity with auto-upgrade.

        Args:
            context: ScoringContext with available evidence

        Returns:
            ScoringAdjustment with darknet/specific logic
        """
        # Base weight adjustments - maximum security focus
        weight_adjustments = {
            "visual": 0.15,
            "structural": 0.10,
            "temporal": 0.05,
            "graph": 0.30,
            "meta": 0.10,
            "security": 0.30,
        }

        # Severity modifications - PARANOIA MODE
        severity_modifications = {
            "onion_links": "CRITICAL",
            "btc_only_payment": "HIGH",  # Will upgrade to CRITICAL
            "escrow_warnings": "HIGH",  # Will upgrade to CRITICAL
            "marketplace_trust": "HIGH",
            "illegal_content": "CRITICAL",
            "malware_distribution": "CRITICAL",
            "illegal_services": "CRITICAL",
        }

        custom_findings = []

        # Onion links are CRITICAL for darknet
        if "onion" in context.url.lower() or "onion" in context.dark_pattern_types:
            custom_findings.append(("onion_links", "CRITICAL", 50))

        # BTC/crypto-only payment (upgraded to CRITICAL)
        if "btc_only" in context.dark_pattern_types or "crypto_only" in context.dark_pattern_types:
            custom_findings.append(("btc_only_payment", self._severity_upgrade("HIGH"), 45))

        # Escrow warnings (upgraded to CRITICAL)
        if "escrow_warning" in context.dark_pattern_types:
            custom_findings.append(("escrow_warnings", self._severity_upgrade("HIGH"), 40))

        # Missing SSL is expected but still a red flag for darknet
        if not context.has_ssl:
            custom_findings.append(("missing_ssl", self._severity_upgrade("MEDIUM"), 25))

        # ANY darknet pattern triggers MINIMUM HIGH severity (PARANOIA MODE)
        if context.has_dark_patterns:
            for pattern in context.dark_pattern_types:
                # Each pattern gets upgraded severity
                severity = self._severity_upgrade("HIGH")
                custom_findings.append((f"darknet_pattern_{pattern}", severity, 30))

        # Phishing in darknet context is CRITICAL
        if context.has_phishing_hits:
            custom_findings.append(("phishing_darknet", "CRITICAL", 50))

        # High JS risk is very suspicious for darknet
        if context.js_risk_score > 60:
            custom_findings.append(("suspicious_js", self._severity_upgrade("MEDIUM"), 25))

        # Detect universal critical triggers (upgraded)
        critical_triggers = self._detect_critical_triggers(context)
        if critical_triggers:
            custom_findings.extend(
                [(trigger, self._severity_upgrade("HIGH"), 50) for trigger in critical_triggers]
            )

        # Narrative template - PARANOIA MODE language
        narrative_template = "⚠️ DARKNET/SUSPICIOUS SITE DETECTED ⚠️ "

        if "onion" in str(context.url) or "onion" in str(context.dark_pattern_types):
            narrative_template += "Onion links confirmed. "

        if context.has_phishing_hits:
            narrative_template += "Phishing indicators detected. "

        warning_count = sum(1 for f in custom_findings if "CRITICAL" in f[1])
        narrative_template += f"{warning_count} critical red flags detected."

        explanation = (
            "PARANOIA MODE: Darknet evaluation suspects maximum potential harm. "
            "Security and graph signals each weighted 0.30 for maximum threat detection. "
            "ANY darknet pattern is minimum HIGH severity with auto-upgrade by 1 level "
            "(MEDIUM->HIGH, HIGH->CRITICAL). "
            "Onion links flagged as CRITICAL (50-point deduction). "
            "BTC/crypto-only payment upgraded to CRITICAL (45-point deduction). "
            "Escrow warnings upgraded to CRITICAL (40-point deduction). "
            "Every darknet pattern triggers 30-point deduction with upgraded severity. "
            "Zero trust in darknet environment - all findings suspect maximum threat."
        )

        # Apply severity upgrade to all severity_modifications
        upgraded_modifications = {
            k: self._severity_upgrade(v) for k, v in severity_modifications.items()
        }

        return ScoringAdjustment(
            weight_adjustments=weight_adjustments,
            severity_modifications=upgraded_modifications,
            custom_findings=custom_findings,
            narrative_template=narrative_template,
            explanation=explanation,
        )
