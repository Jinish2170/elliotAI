"""
Darknet Analysis Module

TOR-aware security module for detecting darknet vulnerabilities and
hidden service indicators using OSINT marketplace threat feeds.

Read-only OSINT compliance: No live darknet crawling, only
historical threat data analysis.
"""

import logging
from dataclasses import asdict
from dataclasses import dataclass, field
from typing import Optional

from veritas.analysis import ModuleInfo
from veritas.analysis.security.base import SecurityFinding as ModuleSecurityFinding
from veritas.analysis.security.base import SecurityModule, SecurityTier
from veritas.core.types import SecurityFinding as CoreSecurityFinding, Severity
from veritas.osint.types import (
    DarknetMarketplaceType,
    ExitRiskLevel,
    MarketplaceThreatData,
    OSINTResult,
)
from veritas.osint.ioc_detector import IOCDetector, IOCType
from veritas.darknet import OnionDetector, MarketplaceType

logger = logging.getLogger("veritas.analysis.security.darknet")


@dataclass
class DarknetAnalysisResult:
    """Result of darknet security analysis."""
    has_onion_references: bool = False
    onion_urls_detected: list[str] = field(default_factory=list)
    marketplace_threats: list[dict] = field(default_factory=list)
    tor2web_exposure: bool = False
    darknet_risk_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class DarknetAnalyzer(SecurityModule):
    """
    Darknet vulnerability and hidden service analysis module.

    Detects:
    - .onion URL references in page content
    - Marketplace threat intelligence correlations
    - Tor2Web de-anonymization gateway exposure
    - Vendor reputation and exit scam indicators

    Read-only OSINT: Uses historical threat data from security research.
    No live darknet crawling or marketplace access.
    """

    module_name = "darknet_analysis"
    category = "darknet"
    requires_page = False  # Can analyze from URL and OSINT data
    _default_tier: SecurityTier = SecurityTier.MEDIUM

    # Exit scam risk thresholds
    HIGH_EXIT_SCAM_CONFIDENCE = 0.8

    def __init__(self):
        self._ioc_detector = IOCDetector()
        self._onion_detector = OnionDetector()

    @property
    def category_id(self) -> str:
        return self.module_name

    @classmethod
    def get_module_info(cls):
        """Get module metadata for auto-discovery."""
        return ModuleInfo(
            module_name=cls.module_name,
            category=cls.category,
            analyzer_class=cls,
            method_name="analyze_with_details",
            requires_page=cls.requires_page,
        )

    @classmethod
    def is_discoverable(cls) -> bool:
        """Check if module should be auto-discovered."""
        return cls.module_name != "unknown"

    async def analyze_with_details(
        self,
        url: str,
        page=None,
        page_content: Optional[str] = None,
    ) -> DarknetAnalysisResult:
        """
        Analyze URL for darknet-related security issues.

        Args:
            url: Target URL to analyze
            page: Optional Playwright page (not required for this module)

        Returns:
            DarknetAnalysisResult with threat findings
        """
        logger.info(f"Analyzing URL for darknet indicators: {url}")

        result = DarknetAnalysisResult()

        # Step 1: Check for .onion references using the IOC detector's
        # canonical async API. This captures direct .onion URLs as well as
        # references embedded in page content when content is available.
        ioc_result = await self._ioc_detector.detect_content(url=url, content=page_content)
        onion_indicators = [
            indicator
            for indicator in ioc_result.indicators
            if indicator.ioc_type == IOCType.ONION_ADDRESS
        ]
        if onion_indicators:
            result.has_onion_references = True
            result.onion_urls_detected = sorted({indicator.value for indicator in onion_indicators})
            logger.info(f"Found {len(result.onion_urls_detected)} .onion references")

            # Step 1b: Validate .onion addresses with OnionDetector
            validated = [addr for addr in result.onion_urls_detected if self._onion_detector.validate_onion(addr)]
            if validated:
                result.onion_urls_detected = validated
            else:
                result.has_onion_references = False
                logger.debug("All detected onion addresses failed OnionDetector validation")

        # Step 2: Query marketplace threat feeds for onion addresses
        if result.has_onion_references:
            marketplace_results = []
            for onion_addr in result.onion_urls_detected:
                threat_result = await self._check_marketplace_threats(onion_addr)
                if threat_result:
                    marketplace_results.append(threat_result)

            result.marketplace_threats = marketplace_results

            # Calculate darknet risk score based on marketplace intel
            result.darknet_risk_score = self._calculate_risk_score(marketplace_results)

            # Generate recommendations
            result.recommendations = self._generate_recommendations(
                result, marketplace_results
            )

        # Step 3: Check for Tor2Web gateway exposure
        result.tor2web_exposure = await self._check_tor2web_exposure(url)

        if result.tor2web_exposure:
            result.darknet_risk_score = min(result.darknet_risk_score + 0.3, 1.0)

        logger.info(f"Darknet analysis complete: risk_score={result.darknet_risk_score}")
        return result

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> list[ModuleSecurityFinding]:
        """
        Tier-execution entrypoint.

        Returns tier-compatible security findings while preserving the
        richer object result through `analyze_with_details()` for legacy
        and compatibility flows.
        """
        result = await self.analyze_with_details(url, page_content=page_content)
        if not (
            result.has_onion_references
            or result.marketplace_threats
            or result.tor2web_exposure
            or result.darknet_risk_score > 0
        ):
            return []

        severity = "low"
        if result.darknet_risk_score >= 0.7:
            severity = "high"
        elif result.darknet_risk_score >= 0.4:
            severity = "medium"

        pattern_type = "darknet_threat"
        if result.tor2web_exposure:
            pattern_type = "tor2web_exposure"
        elif result.has_onion_references and not result.marketplace_threats:
            pattern_type = "onion_reference"

        evidence_bits = [
            f"risk_score={result.darknet_risk_score:.2f}",
            f"onion_refs={len(result.onion_urls_detected)}",
            f"marketplace_matches={len(result.marketplace_threats)}",
            f"tor2web={result.tor2web_exposure}",
        ]
        recommendation = " ".join(result.recommendations[:2])

        from veritas.config.darknet_rules import get_darknet_cvss_score

        return [
            ModuleSecurityFinding(
                category_id=self.module_name,
                pattern_type=pattern_type,
                severity=severity,
                confidence=max(0.3, min(1.0, result.darknet_risk_score or 0.5)),
                description="Darknet threat indicators detected",
                evidence=", ".join(evidence_bits),
                cwe_id="CWE-200",
                cvss_score=get_darknet_cvss_score(result),
                recommendation=recommendation,
                url_finding=True,
            )
        ]

    async def _check_marketplace_threats(
        self, onion_address: str
    ) -> Optional[dict]:
        """
        Check onion address against marketplace threat feeds.

        Args:
            onion_address: .onion address to check

        Returns:
            Threat data dict if found, None otherwise
        """
        # Try each marketplace source
        from veritas.osint.sources.darknet_alpha import AlphaBayMarketplaceSource
        from veritas.osint.sources.darknet_hansa import HansaMarketplaceSource
        from veritas.osint.sources.darknet_empire import EmpireMarketplaceSource
        from veritas.osint.sources.darknet_dream import DreamMarketplaceSource
        from veritas.osint.sources.darknet_wallstreet import WallStreetMarketplaceSource

        sources = [
            AlphaBayMarketplaceSource(),
            HansaMarketplaceSource(),
            EmpireMarketplaceSource(),
            DreamMarketplaceSource(),
            WallStreetMarketplaceSource(),
        ]

        for source in sources:
            try:
                threat_result = await source.query(onion_address, indicator_type="onion")
                if threat_result and threat_result.found:
                    marketplace_type = self._onion_detector.classify_marketplace(onion_address)
                    return {
                        "marketplace": threat_result.metadata.get("marketplace"),
                        "status": threat_result.metadata.get("status"),
                        "confidence": threat_result.confidence,
                        "threat_data": threat_result.data,
                        "marketplace_type": marketplace_type.value if marketplace_type else MarketplaceType.UNKNOWN.value,
                    }
            except Exception as e:
                logger.debug(f"Source {source.name} error: {e}")
                continue

        return None

    async def _check_tor2web_exposure(self, url: str) -> bool:
        """
        Check if URL uses Tor2Web gateway (de-anonymization risk).

        Args:
            url: URL to check

        Returns:
            True if Tor2Web gateway detected
        """
        from veritas.osint.sources.darknet_tor2web import Tor2WebDeanonSource

        source = Tor2WebDeanonSource()

        # Check if URL itself is a Tor2Web gateway
        result = await source.query(url)
        if result and result.found:
            logger.warning(f"Tor2Web gateway detected in URL: {url}")
            return True

        return False

    def _calculate_risk_score(self, marketplace_results: list[dict]) -> float:
        """
        Calculate darknet risk score from marketplace threat data.

        Args:
            marketplace_results: List of marketplace threat results

        Returns:
            Risk score between 0.0 and 1.0
        """
        if not marketplace_results:
            return 0.0

        # Base score from number of marketplace matches
        base_score = min(len(marketplace_results) * 0.2, 0.6)

        # Add score from exit scam status
        exit_scam_bonus = 0.0
        for result in marketplace_results:
            if result.get("status") in ("exit_scam", "shutdown"):
                confidence = result.get("confidence", 0.5)
                exit_scam_bonus += confidence * 0.4

        return min(base_score + exit_scam_bonus, 1.0)

    def _generate_recommendations(
        self, result: DarknetAnalysisResult, marketplace_results: list[dict]
    ) -> list[str]:
        """
        Generate security recommendations based on findings.

        Args:
            result: Darknet analysis result
            marketplace_results: Marketplace threat results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if result.has_onion_references:
            recommendations.append(
                "Site references .onion hidden services. Verify these references "
                "are for legitimate security research, not illicit marketplace access."
            )

        for threat in marketplace_results:
            marketplace = threat.get("marketplace")
            status = threat.get("status")

            if status == "exit_scam":
                recommendations.append(
                    f"Detected reference to {marketplace} marketplace (EXIT SCAM). "
                    f"Vendor escrow was stolen in 2019-2020. This site may be "
                    f"a mirror or attempting fraudulent association."
                )
            elif status == "shutdown":
                recommendations.append(
                    f"Detected reference to {marketplace} marketplace (SHUTDOWN). "
                    f"Marketplace was seized by law enforcement. This site may be "
                    f"an archive or attempting illicit association."
                )

        if result.tor2web_exposure:
            recommendations.append(
                "Site uses Tor2Web gateway URLs (onion.to, onion.link, etc.). "
                "This compromises TOR anonymity - DNS resolution happens on the "
                "gateway server. Use direct TOR Browser for .onion access."
            )

        if result.darknet_risk_score > 0.7:
            recommendations.append(
                "HIGH RISK: Multiple darknet threat indicators detected. "
                "Site may be attempting to associate with illicit marketplaces "
                "or providing unauthorized darknet access services."
            )

        if not recommendations:
            recommendations.append("No darknet threats detected.")

        return recommendations

    def to_security_finding(
        self, result: DarknetAnalysisResult, url: str
    ) -> CoreSecurityFinding:
        """
        Convert analysis result to SecurityFinding for Judge integration.

        Args:
            result: Darknet analysis result
            url: Analyzed URL

        Returns:
            SecurityFinding for the VERITAS security pipeline
        """
        severity = Severity.UNKNOWN
        if result.darknet_risk_score >= 0.7:
            severity = Severity.HIGH
        elif result.darknet_risk_score >= 0.4:
            severity = Severity.MEDIUM
        elif result.darknet_risk_score > 0:
            severity = Severity.LOW

        # Get CVSS score based on darknet threat patterns
        from veritas.config.darknet_rules import get_darknet_cvss_score
        cvss_score = get_darknet_cvss_score(result)

        return CoreSecurityFinding(
            severity=severity,
            category="darknet",
            rule_id="DARKNET-001",
            title="Darknet Threat Analysis",
            description=(
                f"Darknet analysis of {url}: "
                f"risk_score={result.darknet_risk_score:.2f}"
            ),
            recommendation="\n".join(result.recommendations) if result.recommendations else None,
            cvss_score=cvss_score,
            cwe_id="CWE-200",  # Exposure of sensitive information
            metadata={
                "module": self.module_name,
                "onion_count": len(result.onion_urls_detected),
                "marketplace_matches": len(result.marketplace_threats),
                "tor2web_exposure": result.tor2web_exposure,
            },
        )
