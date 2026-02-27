"""IOC (Indicator of Compromise) detection for cyber threat intelligence.

Extracts and classifies indicators from text, HTML, and metadata including
URLs, domains, IP addresses, email addresses, and file hashes.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class IOCType(str, Enum):
    """Type of indicator of compromise."""
    URL = "url"
    DOMAIN = "domain"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    EMAIL = "email"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    FILENAME = "filename"


@dataclass
class Indicator:
    """Single indicator of compromise with metadata.

    Attributes:
        ioc_type: Type of the indicator (IOCType enum)
        value: The actual indicator value (e.g., "192.168.1.1", "malicious.exe")
        confidence: Confidence score in range 0.0-1.0
        context: Additional context about where/when this was found
        source: Source of this indicator (e.g., URL, filename)
    """
    ioc_type: IOCType
    value: str
    confidence: float
    context: str = ""
    source: str = ""

    def __hash__(self) -> int:
        """Hash based on (ioc_type, value) pair for deduplication."""
        return hash((self.ioc_type, self.value))

    def __eq__(self, other: object) -> bool:
        """Equality based on (ioc_type, value) pair."""
        if not isinstance(other, Indicator):
            return False
        return (self.ioc_type, self.value) == (other.ioc_type, other.value)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "ioc_type": self.ioc_type.value,
            "value": self.value,
            "confidence": self.confidence,
            "context": self.context,
            "source": self.source,
        }


class IOCDetector:
    """Detector for IOCs in text, HTML, and metadata."""

    # Common false positives to exclude
    FALSE_POSITIVES = {
        "example.com", "test.com", "localhost", "127.0.0.1", "0.0.0.0",
        "example.org", "test.org", "example.net", "test.net",
        "www.example.com", "mail.example.com", "ftp.example.com",
    }

    # Suspicious TLDs often used in malicious domains
    SUSPICIOUS_TLDS = {".xyz", ".top", ".tk", ".ml", ".cf", ".gq", ".cc", ".pw"}

    # Baseline confidence scores by IOC type
    BASELINE_CONFIDENCE = {
        IOCType.DOMAIN: 0.6,
        IOCType.IPV4: 0.7,
        IOCType.IPV6: 0.6,
        IOCType.URL: 0.8,
        IOCType.EMAIL: 0.5,
        IOCType.MD5: 0.9,
        IOCType.SHA1: 0.9,
        IOCType.SHA256: 0.95,
        IOCType.FILENAME: 0.3,
    }

    # Regex patterns for each IOC type
    PATTERNS: Dict[IOCType, List[str]] = {
        IOCType.DOMAIN: [
            r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',
        ],
        IOCType.IPV4: [
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        ],
        IOCType.IPV6: [
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            r'\b::(?:[0-9a-fA-F]{1,4}:){0,7}[0-9a-fA-F]{1,4}\b',
        ],
        IOCType.URL: [
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            r'ftp://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
        ],
        IOCType.EMAIL: [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        IOCType.MD5: [
            r'\b[a-fA-F0-9]{32}\b',
        ],
        IOCType.SHA1: [
            r'\b[a-fA-F0-9]{40}\b',
        ],
        IOCType.SHA256: [
            r'\b[a-fA-F0-9]{64}\b',
        ],
        IOCType.FILENAME: [
            r'\b[\w\-,\s@]+\.(?:exe|dll|bat|cmd|ps1|vbs|js|jar|msi|scr|com|pif)\b',
        ],
    }

    def __init__(self) -> None:
        """Initialize the IOC detector."""
        # Compile all patterns for better performance
        self._compiled_patterns: Dict[IOCType, List[re.Pattern]] = {}
        for ioc_type, patterns in self.PATTERNS.items():
            self._compiled_patterns[ioc_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def extract_from_text(self, text: str, source: str = "") -> List[Indicator]:
        """Extract IOCs from plain text.

        Args:
            text: Text content to analyze
            source: Source identifier for context

        Returns:
            List of unique indicators found in the text
        """
        if not text:
            return []

        indicators = []
        for ioc_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    value = match.group(0)
                    if self._is_valid_ioc(ioc_type, value):
                        confidence = self._calculate_confidence(ioc_type, value)
                        indicators.append(Indicator(
                            ioc_type=ioc_type,
                            value=value,
                            confidence=confidence,
                            source=source,
                        ))

        # Deduplicate by IOC type and value
        return list(dict.fromkeys(indicators))

    def extract_from_html(self, html: str) -> List[Indicator]:
        """Extract IOCs from HTML content.

        Args:
            html: HTML content to parse

        Returns:
            List of unique indicators found in HTML
        """
        if not html:
            return []

        indicators = []

        # Extract URLs from href attributes
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        for match in href_pattern.finditer(html):
            url = match.group(1)
            if self._is_valid_ioc(IOCType.URL, url):
                confidence = self._calculate_confidence(IOCType.URL, url)
                indicators.append(Indicator(
                    ioc_type=IOCType.URL,
                    value=url,
                    confidence=confidence,
                    context="href attribute",
                    source="html",
                ))

        # Extract URLs from src attributes
        src_pattern = re.compile(r'src=["\']([^"\']+)["\']', re.IGNORECASE)
        for match in src_pattern.finditer(html):
            url = match.group(1)
            if self._is_valid_ioc(IOCType.URL, url):
                confidence = self._calculate_confidence(IOCType.URL, url)
                indicators.append(Indicator(
                    ioc_type=IOCType.URL,
                    value=url,
                    confidence=confidence,
                    context="src attribute",
                    source="html",
                ))

        # Also extract from text content of HTML
        text_indicators = self.extract_from_text(html, "html")
        indicators.extend(text_indicators)

        # Deduplicate
        return list(dict.fromkeys(indicators))

    def extract_from_metadata(self, metadata: Dict) -> List[Indicator]:
        """Extract IOCs from page metadata.

        Args:
            metadata: Dictionary containing page metadata

        Returns:
            List of unique indicators found in metadata
        """
        indicators = []

        # Check for external links
        if "external_links" in metadata:
            for link in metadata["external_links"]:
                if self._is_valid_ioc(IOCType.URL, link):
                    confidence = self._calculate_confidence(IOCType.URL, link)
                    indicators.append(Indicator(
                        ioc_type=IOCType.URL,
                        value=link,
                        confidence=confidence,
                        context="external link",
                        source="metadata",
                    ))

        # Check for script sources
        if "scripts" in metadata:
            for script in metadata["scripts"]:
                if isinstance(script, dict) and "src" in script:
                    src = script["src"]
                    if self._is_valid_ioc(IOCType.URL, src):
                        confidence = self._calculate_confidence(IOCType.URL, src)
                        indicators.append(Indicator(
                            ioc_type=IOCType.URL,
                            value=src,
                            confidence=confidence,
                            context="script source",
                            source="metadata",
                        ))

        # Also scan other metadata values for IOCs
        for key, value in metadata.items():
            if isinstance(value, str):
                text_indicators = self.extract_from_text(
                    value, f"metadata.{key}"
                )
                indicators.extend(text_indicators)

        return list(dict.fromkeys(indicators))

    def _is_valid_ioc(self, ioc_type: IOCType, value: str) -> bool:
        """Validate an IOC to filter false positives.

        Args:
            ioc_type: Type of indicator
            value: Indicator value to validate

        Returns:
            True if the IOC appears valid, False if likely false positive
        """
        # Exclude common false positives across all types
        if value.lower() in self.FALSE_POSITIVES:
            return False

        # IPv4 specific validation - ensure octets in valid range
        if ioc_type == IOCType.IPV4:
            octets = value.split('.')
            if len(octets) != 4:
                return False
            for octet in octets:
                try:
                    if not (0 <= int(octet) <= 255):
                        return False
                except ValueError:
                    return False

        # Exclude private/reserved IPv4 ranges for external threat intel
        if ioc_type == IOCType.IPV4:
            if value.startswith('10.') or value.startswith('192.168.') or \
               value.startswith('172.') or value.startswith('127.'):
                return False

        # Domain validation
        if ioc_type == IOCType.DOMAIN:
            # Must have at least a TLD
            if '.' not in value or value.startswith('.'):
                return False
            # Check for common test words
            lower_value = value.lower()
            if 'example' in lower_value or 'test' in lower_value:
                return False

        # URL validation
        if ioc_type == IOCType.URL:
            # Must have a protocol
            if not value.startswith(('http://', 'https://', 'ftp://')):
                return False

        # Email validation - exclude common service emails
        if ioc_type == IOCType.EMAIL:
            lower_value = value.lower()
            if any(service in lower_value for service in ['noreply@', 'no-reply@', 'support@', 'info@']):
                return False

        return True

    def _calculate_confidence(self, ioc_type: IOCType, value: str) -> float:
        """Calculate confidence score for an IOC.

        Args:
            ioc_type: Type of indicator
            value: Indicator value

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Start with baseline confidence for the type
        confidence = self.BASELINE_CONFIDENCE.get(ioc_type, 0.5)

        # HTTPS bonus for URLs
        if ioc_type == IOCType.URL and value.startswith('https://'):
            confidence = min(confidence + 0.1, 1.0)

        # Penalty for suspicious TLDs (often used in malicious domains)
        if ioc_type in (IOCType.DOMAIN, IOCType.URL):
            for tld in self.SUSPICIOUS_TLDS:
                if value.lower().endswith(tld):
                    confidence = max(confidence - 0.2, 0.0)
                    break

        # Bonus for specific file extensions known to be malicious
        if ioc_type == IOCType.FILENAME:
            lower_value = value.lower()
            if lower_value.endswith(('.scr', '.pif', '.bat', '.cmd')):
                confidence = min(confidence + 0.3, 1.0)
            elif lower_value.endswith(('.dll', '.vbs')):
                confidence = min(confidence + 0.2, 1.0)

        # Ensure confidence stays in valid range
        return max(0.0, min(confidence, 1.0))

    def classify_threat_level(
        self, indicator: Indicator, osint_context: Optional[Dict] = None
    ) -> str:
        """Classify threat level for a specific indicator.

        Args:
            indicator: IOC to classify
            osint_context: Optional OSINT context (reputation, threat intel, etc.)

        Returns:
            Threat level: "critical", "high", "medium", "low", or "none"
        """
        # Start with confidence-based classification
        confidence = indicator.confidence

        # Adjust based on OSINT context if available
        if osint_context:
            # Check if IOC is flagged in threat intel
            if "threat_intel" in osint_context:
                threat_data = osint_context["threat_intel"]
                if threat_data.get("is_malicious", False):
                    return "critical"
                if threat_data.get("suspicious_activity"):
                    return "high"

            # Check reputation score
            if "reputation" in osint_context:
                rep_score = osint_context["reputation"].get("score", 100)
                if rep_score < 20:  # Very low reputation
                    return "critical"
                elif rep_score < 40:  # Low reputation
                    return "high"
                elif rep_score < 60:  # Medium reputation
                    confidence = max(confidence - 0.1, 0.0)

        # Final classification based on adjusted confidence
        if confidence >= 0.7:
            return "critical"
        elif confidence >= 0.5:
            return "high"
        elif confidence >= 0.3:
            return "medium"
        elif confidence >= 0.1:
            return "low"
        else:
            return "none"
