"""
TLS/SSL Security Module - FAST Tier.

Analyzes HTTP security headers and TLS/SSL certificate configuration.

Checks:
    - Strict-Transport-Security (HSTS) - CWE-523
    - Content-Security-Policy - CWE-693
    - X-Frame-Options - CWE-1021
    - X-Content-Type-Options - CWE-693

Tier: FAST, timeout: 5 seconds
"""

from typing import List, Optional

from .base import SecurityFinding, SecurityModule, SecurityTier
from ...config.security_rules import (
    calculate_cvss_for_severity,
    get_cwe_for_finding,
    get_severity_for_finding,
)


class SecurityHeaderAnalyzerEnhanced(SecurityModule):
    """
    Enhanced security header analyzer with CWE ID mapping.

    Analyzes HTTP response headers for missing or misconfigured
    security headers and maps findings to CWE IDs.
    """

    # FAST tier module: 5 second timeout
    _default_timeout: int = 5
    _default_tier: SecurityTier = SecurityTier.FAST

    @property
    def category_id(self) -> str:
        """Module category identifier."""
        return "security_headers"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze HTTP response headers for security issues.

        Args:
            url: Target URL
            page_content: Optional HTML content (not used in this module)
            headers: HTTP response headers dict
            dom_meta: Optional DOM metadata (not used in this module)

        Returns:
            List of SecurityFinding objects (empty if no issues)
        """
        findings: List[SecurityFinding] = []

        if not headers:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="no_headers_available",
                    severity="low",
                    confidence=1.0,
                    description="No HTTP headers available for analysis",
                    evidence="Headers dict is None or empty",
                    cwe_id=None,
                    cvss_score=None,
                    recommendation="Ensure HTTP headers are being captured properly.",
                )
            )
            return findings

        # Normalize headers to lowercase (HTTP headers are case-insensitive)
        normalized_headers = {k.lower(): v for k, v in headers.items()}

        # Check HSTS (Strict-Transport-Security)
        self._check_hsts(normalized_headers, findings)

        # Check CSP (Content-Security-Policy)
        self._check_csp(normalized_headers, findings)

        # Check X-Frame-Options
        self._check_x_frame_options(normalized_headers, findings)

        # Check X-Content-Type-Options
        self._check_x_content_type_options(normalized_headers, findings)

        # Check additional security headers (optional)
        self._check_additional_headers(normalized_headers, findings)

        return findings

    def _check_hsts(self, headers: dict, findings: List[SecurityFinding]) -> None:
        """
        Check HSTS header configuration.

        CWE: CWE-523 (Unprotected Transport of Credentials)

        Valid HSTS should have:
        - Strict-Transport-Security header present
        - max-age attribute with value >= 31536000 (1 year)
        """
        hsts_header = headers.get("strict-transport-security", "")

        if not hsts_header:
            # Missing HSTS header
            pattern_type = "missing_hsts"
            severity = get_severity_for_finding(self.category_id, pattern_type, "high")
            cwe_id = get_cwe_for_finding(self.category_id, "security_headers_hsts") or "CWE-523"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.9,
                    description="Strict-Transport-Security (HSTS) header is missing",
                    evidence="No Strict-Transport-Security header found in response",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Add Strict-Transport-Security header with max-age=31536000 (1 year) and includeSubDomains",
                )
            )
        else:
            # Validate HSTS configuration
            self._validate_hsts_config(hsts_header, findings)

    def _validate_hsts_config(self, hsts_value: str, findings: List[SecurityFinding]) -> None:
        """Validate HSTS header value format and duration."""
        # Parse max-age
        max_age = None
        for directive in hsts_value.split(";"):
            directive = directive.strip().lower()
            if directive.startswith("max-age="):
                try:
                    max_age = int(directive.split("=")[1])
                except (ValueError, IndexError):
                    findings.append(
                        SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="hsts_invalid_max_age",
                            severity="medium",
                            confidence=0.7,
                            description="HSTS max-age directive has invalid format",
                            evidence=f"Strict-Transport-Security: {hsts_value}",
                            cwe_id="CWE-523",
                            cvss_score=calculate_cvss_for_severity("medium"),
                            recommendation="Fix HSTS max-age format: max-age=31536000",
                        )
                    )
                    return

        if max_age is None:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="hsts_missing_max_age",
                    severity="medium",
                    confidence=0.9,
                    description="HSTS header missing max-age directive",
                    evidence=f"Strict-Transport-Security: {hsts_value}",
                    cwe_id="CWE-523",
                    cvss_score=calculate_cvss_for_severity("medium"),
                    recommendation="Add max-age=31536000 to HSTS header",
                )
            )
        elif max_age < 31536000:  # Less than 1 year
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="hsts_low_max_age",
                    severity="low",
                    confidence=0.5,
                    description="HSTS max-age is less than recommended 1 year",
                    evidence=f"Strict-Transport-Security: {hsts_value} (max-age={max_age}s)",
                    cwe_id="CWE-523",
                    cvss_score=calculate_cvss_for_severity("low"),
                    recommendation="Increase max-age to at least 31536000 seconds (1 year)",
                )
            )

    def _check_csp(self, headers: dict, findings: List[SecurityFinding]) -> None:
        """
        Check Content-Security-Policy header.

        Note: This module only checks for CSP presence.
        Detailed CSP analysis is handled by the CSP analyzer module.
        """
        csp_header = headers.get("content-security-policy", "")

        if not csp_header:
            # Missing CSP header
            pattern_type = "missing_csp"
            severity = get_severity_for_finding(self.category_id, pattern_type, "high")
            cwe_id = get_cwe_for_finding(self.category_id, "security_headers_csp") or "CWE-693"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.9,
                    description="Content-Security-Policy (CSP) header is missing",
                    evidence="No Content-Security-Policy header found in response",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Add Content-Security-Policy header to prevent XSS and data injection attacks",
                )
            )

    def _check_x_frame_options(self, headers: dict, findings: List[SecurityFinding]) -> None:
        """
        Check X-Frame-Options header for clickjacking protection.

        CWE: CWE-1021 (Permissive Cross-domain Policy)

        Valid values: DENY, SAMEORIGIN
        """
        xfo_header = headers.get("x-frame-options", "")

        if not xfo_header:
            # Missing X-Frame-Options header
            pattern_type = "missing_x_frame_options"
            severity = get_severity_for_finding(self.category_id, pattern_type, "medium")
            cwe_id = get_cwe_for_finding(self.category_id, "security_headers_xfo") or "CWE-1021"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.7,
                    description="X-Frame-Options header is missing",
                    evidence="No X-Frame-Options header found in response",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Add X-Frame-Options: DENY or SAMEORIGIN to prevent clickjacking attacks",
                )
            )
        else:
            # Validate X-Frame-Options value
            xfo_upper = xfo_header.upper().strip()
            if xfo_upper not in ("DENY", "SAMEORIGIN", "ALLOW-FROM"):
                findings.append(
                    SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="weak_x_frame_options",
                        severity="low",
                        confidence=0.5,
                        description="X-Frame-Options has non-standard value",
                        evidence=f"X-Frame-Options: {xfo_header}",
                        cwe_id="CWE-1021",
                        cvss_score=calculate_cvss_for_severity("low"),
                        recommendation='Use X-Frame-Options: DENY or SAMEORIGIN (ALLOW-FROM is deprecated)',
                    )
                )

    def _check_x_content_type_options(self, headers: dict, findings: List[SecurityFinding]) -> None:
        """
        Check X-Content-Type-Options header for MIME sniffing protection.

        CWE: CWE-693 (Protection Mechanism Failure)

        Valid value: nosniff
        """
        xcto_header = headers.get("x-content-type-options", "")

        if not xcto_header:
            # Missing X-Content-Type-Options header
            pattern_type = "missing_x_content_type_options"
            severity = get_severity_for_finding(self.category_id, pattern_type, "medium")
            cwe_id = get_cwe_for_finding(self.category_id, "security_headers_xcto") or "CWE-693"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.6,
                    description="X-Content-Type-Options header is missing",
                    evidence="No X-Content-Type-Options header found in response",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Add X-Content-Type-Options: nosniff to prevent MIME sniffing attacks",
                )
            )
        else:
            # Validate X-Content-Type-Options value
            xcto_lower = xcto_header.lower().strip()
            if xcto_lower != "nosniff":
                findings.append(
                    SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="weak_x_content_type_options",
                        severity="low",
                        confidence=0.4,
                        description="X-Content-Type-Options has unexpected value",
                        evidence=f"X-Content-Type-Options: {xcto_header}",
                        cwe_id="CWE-693",
                        cvss_score=calculate_cvss_for_severity("low"),
                        recommendation='Use X-Content-Type-Options: nosniff',
                    )
                )

    def _check_additional_headers(self, headers: dict, findings: List[SecurityFinding]) -> None:
        """Check additional security headers (informational, low severity)."""
        # Referrer-Policy
        referrer_policy = headers.get("referrer-policy", "")
        if not referrer_policy:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="missing_referrer_policy",
                    severity="low",
                    confidence=0.3,
                    description="Referrer-Policy header is missing",
                    evidence="No Referrer-Policy header found in response",
                    cwe_id=None,
                    cvss_score=None,
                    recommendation="Consider adding Referrer-Policy: strict-origin-when-cross-origin",
                )
            )

        # Permissions-Policy
        permissions_policy = headers.get("permissions-policy", "")
        if not permissions_policy:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="missing_permissions_policy",
                    severity="low",
                    confidence=0.3,
                    description="Permissions-Policy header is missing",
                    evidence="No Permissions-Policy header found in response",
                    cwe_id=None,
                    cvss_score=None,
                    recommendation="Consider adding Permissions-Policy to restrict browser features",
                )
            )
