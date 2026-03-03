"""
Cookies Security Module - FAST Tier.

Analyzes HTTP cookies for security attributes and flags.

Checks:
    - Missing Secure flag for HTTPS cookies - CWE-614
    - Missing HttpOnly flag - CWE-1004
    - Missing SameSite attribute - CWE-942
    - SameSite=None without Secure - CWE-942

Tier: FAST, timeout: 5 seconds
"""

from typing import List, Optional

from .base import SecurityFinding, SecurityModule, SecurityTier
from ...config.security_rules import (
    calculate_cvss_for_severity,
    get_cwe_for_finding,
    get_severity_for_finding,
)


class CookieSecurityAnalyzer(SecurityModule):
    """
    Cookie security analyzer with CWE ID mapping.

    Analyzes Set-Cookie headers for missing or misconfigured
    security attributes and maps findings to CWE IDs.
    """

    # FAST tier module: 5 second timeout
    _default_timeout: int = 5
    _default_tier: SecurityTier = SecurityTier.FAST

    @property
    def category_id(self) -> str:
        """Module category identifier."""
        return "cookies"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze HTTP cookies for security issues.

        Args:
            url: Target URL (used to determine HTTPS vs HTTP)
            page_content: Optional HTML content (not used in this module)
            headers: HTTP response headers dict with Set-Cookie values
            dom_meta: Optional DOM metadata (not used in this module)

        Returns:
            List of SecurityFinding objects (empty if no issues)
        """
        findings: List[SecurityFinding] = []

        if not headers:
            return findings

        # Normalize headers to lowercase (HTTP headers are case-insensitive)
        normalized_headers = {k.lower(): v for k, v in headers.items()}

        # Check if URL is HTTPS
        is_https = url.lower().startswith("https://")

        # Find all Set-Cookie headers
        set_cookie_headers = []
        for key, value in normalized_headers.items():
            if key == "set-cookie":
                if isinstance(value, list):
                    set_cookie_headers.extend(value)
                else:
                    set_cookie_headers.append(str(value))

        if not set_cookie_headers:
            return findings

        # Analyze each cookie
        for i, cookie_header in enumerate(set_cookie_headers):
            self._analyze_cookie(cookie_header, is_https, i, findings)

        return findings

    def _analyze_cookie(
        self,
        cookie_header: str,
        is_https: bool,
        cookie_index: int,
        findings: List[SecurityFinding],
    ) -> None:
        """
        Analyze a single cookie header for security issues.

        Args:
            cookie_header: Set-Cookie header value
            is_https: Whether the connection is HTTPS
            cookie_index: Index of the cookie for evidence tracking
            findings: List to append findings to
        """
        # Extract cookie name and attributes
        parts = cookie_header.split(";")
        cookie_name_value = parts[0].strip()
        cookie_name = cookie_name_value.split("=")[0].strip() if "=" in cookie_name_value else "unknown"

        # Parse attributes
        has_secure = False
        has_httponly = False
        samesite_value = None

        for i in range(1, len(parts)):
            attr = parts[i].strip().lower()
            if attr == "secure":
                has_secure = True
            elif attr == "httponly":
                has_httponly = True
            elif attr.startswith("samesite="):
                samesite_value = attr.split("=")[1].strip().lower()

        # Check Secure flag (only relevant for HTTPS)
        if is_https and not has_secure:
            pattern_type = "missing_secure"
            severity = get_severity_for_finding(self.category_id, pattern_type, "high")
            cwe_id = get_cwe_for_finding(self.category_id, "cookies_secure") or "CWE-614"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.9,
                    description=f"Cookie '{cookie_name}' missing Secure flag on HTTPS connection",
                    evidence=f"Cookie #{cookie_index} ({cookie_name}): {cookie_header}",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Add Secure flag to cookie to prevent transmission over HTTP",
                )
            )

        # Check HttpOnly flag (prevents XSS cookie theft)
        if not has_httponly:
            pattern_type = "missing_httponly"
            severity = get_severity_for_finding(self.category_id, pattern_type, "medium")
            cwe_id = get_cwe_for_finding(self.category_id, "cookies_httponly") or "CWE-1004"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.8,
                    description=f"Cookie '{cookie_name}' missing HttpOnly flag",
                    evidence=f"Cookie #{cookie_index} ({cookie_name}): {cookie_header}",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Add HttpOnly flag to cookie to prevent JavaScript access (XSS protection)",
                )
            )

        # Check SameSite attribute (CSRF protection)
        if samesite_value is None:
            pattern_type = "missing_samesite"
            severity = get_severity_for_finding(self.category_id, pattern_type, "low")
            cwe_id = get_cwe_for_finding(self.category_id, "cookies_samesite") or "CWE-942"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.7,
                    description=f"Cookie '{cookie_name}' missing SameSite attribute",
                    evidence=f"Cookie #{cookie_index} ({cookie_name}): {cookie_header}",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Add SameSite=Lax or SameSite=Strict to cookie for CSRF protection",
                )
            )
        elif samesite_value == "none" and not has_secure:
            # SameSite=None must have Secure flag
            pattern_type = "samesite_none_without_secure"
            severity = get_severity_for_finding(self.category_id, pattern_type, "medium")
            cwe_id = get_cwe_for_finding(self.category_id, "cookies_samesite_none") or "CWE-942"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.9,
                    description=f"Cookie '{cookie_name}' has SameSite=None without Secure flag",
                    evidence=f"Cookie #{cookie_index} ({cookie_name}): {cookie_header}",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="SameSite=None requires Secure flag. Add Secure to the cookie.",
                )
            )

    def _parse_cookie_attributes(self, cookie_header: str) -> dict:
        """
        Parse cookie attributes from Set-Cookie header.

        Args:
            cookie_header: Set-Cookie header value

        Returns:
            Dict with cookie attributes:
            {
                "name": cookie_name,
                "has_secure": bool,
                "has_httponly": bool,
                "samesite": str or None,
                "has_path": bool,
                "has_domain": bool,
                "has_expires": bool,
            }
        """
        parts = cookie_header.split(";")
        cookie_name_value = parts[0].strip()
        cookie_name = cookie_name_value.split("=")[0].strip() if "=" in cookie_name_value else "unknown"

        attributes = {
            "name": cookie_name,
            "has_secure": False,
            "has_httponly": False,
            "samesite": None,
            "has_path": False,
            "has_domain": False,
            "has_expires": False,
        }

        for i in range(1, len(parts)):
            attr = parts[i].strip().lower()
            if attr == "secure":
                attributes["has_secure"] = True
            elif attr == "httponly":
                attributes["has_httponly"] = True
            elif attr.startswith("samesite="):
                attributes["samesite"] = attr.split("=")[1].strip()
            elif attr.startswith("path="):
                attributes["has_path"] = True
            elif attr.startswith("domain="):
                attributes["has_domain"] = True
            elif attr.startswith("expires="):
                attributes["has_expires"] = True
            elif attr.startswith("max-age="):
                attributes["has_expires"] = True

        return attributes
