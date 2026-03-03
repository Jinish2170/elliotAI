"""Cyber Threat Intelligence (CTI-lite) module for threat analysis.

Integrates IOC detection and MITRE ATT&CK mapping to provide
comprehensive threat intelligence for analyzed URLs.
"""

from typing import Any, Dict, List, Optional

from .attack_patterns import AttackPatternMapper
from .ioc_detector import IOCDetector, Indicator


class CThreatIntelligence:
    """Main CTI module integrating IOC detection and ATT&CK mapping.

    Provides comprehensive threat analysis including indicator extraction,
    technique mapping, and threat attribution suggestions.
    """

    def __init__(self) -> None:
        """Initialize the CTI module."""
        self.ioc_detector = IOCDetector()
        self.attack_mapper = AttackPatternMapper()

    async def analyze_threats(
        self,
        url: str,
        page_html: str,
        page_text: str,
        page_metadata: Dict[str, Any],
        osint_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze threats in a web page comprehensively.

        Args:
            url: Target URL being analyzed
            page_html: HTML content of the page
            page_text: Plain text content of the page
            page_metadata: Metadata dictionary about the page
            osint_results: Optional OSINT results for context

        Returns:
            Dict containing: target_url, indicators, mitre_techniques,
            attribution, threat_level, confidence
        """
        if osint_results is None:
            osint_results = {}

        # Extract IOCs from various sources
        text_indicators = self.ioc_detector.extract_from_text(page_text, url)
        html_indicators = self.ioc_detector.extract_from_html(page_html)
        metadata_indicators = self.ioc_detector.extract_from_metadata(page_metadata)

        # Combine and deduplicate indicators
        all_indicators = list(set(text_indicators + html_indicators + metadata_indicators))

        # Classify threat level for each indicator
        indicators_list = []
        threat_level_map = {}
        for indicator in all_indicators:
            threat_level = self.ioc_detector.classify_threat_level(
                indicator, osint_results
            )
            threat_level_map[indicator] = threat_level
            indicators_list.append(indicator.to_dict() | {"threat_level": threat_level})

        # Extract site features from metadata
        site_features = self._extract_site_features(page_metadata)

        # Map indicators to MITRE ATT&CK techniques (use original Indicator objects)
        mitre_techniques = self.attack_mapper.map_indicators_to_techniques(
            all_indicators,
            site_features,
        )

        # Generate attribution suggestion
        attribution = self.attack_mapper.generate_attribution_suggestion(
            mitre_techniques
        )

        # Calculate overall threat level and confidence
        threat_level, confidence = self._calculate_overall_threat({
            "indicators": indicators_list,
            "techniques": mitre_techniques,
            "attribution": attribution,
        })

        return {
            "target_url": url,
            "indicators": indicators_list,
            "mitre_techniques": mitre_techniques,
            "attribution": attribution,
            "threat_level": threat_level,
            "confidence": confidence,
        }

    def _extract_site_features(
        self, page_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract relevant site features for technique mapping.

        Args:
            page_metadata: Dictionary containing page metadata

        Returns:
            Dict of extracted features for use in technique matching
        """
        features = {}

        # Extract dark patterns from metadata
        if "dark_patterns" in page_metadata:
            patterns = page_metadata["dark_patterns"]
            if isinstance(patterns, list):
                features["dark_patterns"] = patterns
            elif isinstance(patterns, dict):
                features.update({
                    f"dark_pattern_{k}": v for k, v in patterns.items()
                })

        # Identify urgency patterns
        urgency_indicators = [
            "urgent", "immediate", "act now", "limited time", "expires soon",
            "don't wait", "hurry", "last chance", "today only",
        ]

        content_text = page_metadata.get("content_text", "").lower()
        urgency_found = [
            indicator for indicator in urgency_indicators
            if indicator in content_text
        ]

        if urgency_found:
            features["urgency_patterns"] = urgency_found

        # Check for credential harvesting forms
        forms = page_metadata.get("forms", [])
        if forms:
            credential_fields = []
            for form in forms:
                if isinstance(form, dict):
                    fields = form.get("fields", [])
                    for field in fields:
                        field_name = field.lower() if isinstance(field, str) else str(field).lower()
                        if any(keyword in field_name for keyword in ["password", "pass", "login", "credential"]):
                            credential_fields.append(field_name)
                            break

            if credential_fields:
                features["credential_harvesting"] = True
                features["credential_fields"] = credential_fields

        # Extract page title for context
        if "page_title" in page_metadata:
            features["page_title"] = page_metadata["page_title"]

        # Extract description or meta content
        if "description" in page_metadata:
            features["description"] = page_metadata["description"]

        return features

    def _calculate_overall_threat(self, cti_result: Dict[str, Any]) -> tuple:
        """Calculate overall threat level and confidence score.

        Args:
            cti_result: Dict containing indicators, techniques, attribution

        Returns:
            Tuple of (threat_level: str, confidence_score: float)
        """
        indicators = cti_result.get("indicators", [])
        techniques = cti_result.get("techniques", [])
        attribution = cti_result.get("attribution", {})

        # Factor 1: MITRE techniques (40% weight)
        tech_confidence = attribution.get("confidence", 0.0)
        tech_count = len(techniques)
        tech_score = tech_confidence * (1.0 + tech_count * 0.1)  # More techniques = higher threat
        tech_score = min(tech_score, 1.0)  # Cap at 1.0

        # Factor 2: High-threat IOCs (35% weight)
        high_threat_iocs = sum(
            1 for ind in indicators
            if ind.get("threat_level") in ("critical", "high")
        )
        ioc_ratio = high_threat_iocs / len(indicators) if indicators else 0.0
        ioc_score = ioc_ratio * 1.5  # Weight high-threat IOCs more heavily
        ioc_score = min(ioc_score, 1.0)

        # Factor 3: Attribution confidence (25% weight)
        attr_confidence = attribution.get("confidence", 0.0)
        # Bonus for specific attribution (not "Unknown")
        if attribution.get("threat_actor") != "Unknown" and attr_confidence > 0.5:
            attr_score = min(attr_confidence + 0.2, 1.0)
        else:
            attr_score = attr_confidence

        # Weighted calculation
        confidence_score = (
            tech_score * 0.4 +
            ioc_score * 0.35 +
            attr_score * 0.25
        )

        # Determine threat level based on confidence score
        if confidence_score >= 0.7:
            threat_level = "critical"
        elif confidence_score >= 0.5:
            threat_level = "high"
        elif confidence_score >= 0.3:
            threat_level = "medium"
        elif confidence_score >= 0.1:
            threat_level = "low"
        else:
            threat_level = "none"

        return threat_level, round(confidence_score, 2)
