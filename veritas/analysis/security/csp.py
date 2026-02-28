"""
Content Security Policy Module - FAST Tier.

Analyzes Content-Security-Policy header for security violations.

Checks:
    - Unsafe-inline in script-src - CWE-829
    - Unsafe-eval in script-src - CWE-95
    - Overly permissive directives (default-src: *) - CWE-693

Tier: FAST, timeout: 5 seconds
"""

from typing import List, Optional

from .base import SecurityFinding, SecurityModule, SecurityTier
from ...config.security_rules import (
    calculate_cvss_for_severity,
    get_cwe_for_finding,
    get_severity_for_finding,
)


class ContentSecurityPolicyAnalyzer(SecurityModule):
    """
    Content Security Policy analyzer with CWE ID mapping.

    Analyzes CSP header for security issues like unsafe-inline,
    unsafe-eval, and overly permissive directives.
    """

    # FAST tier module: 5 second timeout
    _default_timeout: int = 5
    _default_tier: SecurityTier = SecurityTier.FAST

    @property
    def category_id(self) -> str:
        """Module category identifier."""
        return "csp"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze Content-Security-Policy for security violations.

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
            return findings

        # Get CSP header
        csp_header = headers.get("content-security-policy", "")
        if not csp_header:
            # Missing CSP is reported by security_headers module
            return findings

        # Parse CSP directives
        directives = self._parse_csp(csp_header)

        # Check for unsafe-inline in script-src
        self._check_unsafe_inline(directives, findings)

        # Check for unsafe-eval in script-src
        self._check_unsafe_eval(directives, findings)

        # Check for overly permissive directives
        self._check_overly_permissive(directives, findings)

        # Check for weak directives (informational)
        self._check_weak_directives(directives, findings)

        return findings

    def _parse_csp(self, csp_header: str) -> dict:
        """
        Parse CSP header into directives dictionary.

        Args:
            csp_header: Content-Security-Policy header value

        Returns:
            Dict mapping directive names to their values:
            {
                "default-src": ["'self'"],
                "script-src": ["'self'", "'unsafe-inline'"],
                ...
            }
        """
        directives = {}
        parts = csp_header.split(";")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Split directive name from values
            if " " in part:
                directive, values = part.split(" ", 1)
                directive = directive.strip()
                values = [v.strip() for v in values.split()]
                # Merge with existing directive values
                if directive in directives:
                    directives[directive].extend(values)
                else:
                    directives[directive] = values
            else:
                # Directive with no values
                directives[part.strip()] = []

        return directives

    def _check_unsafe_inline(self, directives: dict, findings: List[SecurityFinding]) -> None:
        """
        Check for unsafe-inline in script-src or default-src.

        CWE: CWE-829 (Inclusion of Functionality from Untrusted Control Sphere)

        unsafe-inline allows inline JavaScript which defeats CSP protection.
        """
        # Check script-src first
        script_sources = directives.get("script-src", [])
        if not script_sources:
            # Fall back to default-src
            script_sources = directives.get("default-src", [])

        # Check for unsafe-inline or unsafe-hashes
        unsafe_directives = ["'unsafe-inline'", "'unsafe-hashes'", "unsafe-inline", "unsafe-hashes"]

        for source in script_sources:
            for unsafe in unsafe_directives:
                if source.lower() == unsafe.lower():
                    pattern_type = "unsafe_inline"
                    severity = get_severity_for_finding(self.category_id, pattern_type, "high")
                    cwe_id = get_cwe_for_finding(self.category_id, "csp_inline") or "CWE-829"
                    cvss_score = calculate_cvss_for_severity(severity)

                    findings.append(
                        SecurityFinding(
                            category_id=self.category_id,
                            pattern_type=pattern_type,
                            severity=severity,
                            confidence=0.9,
                            description="Content-Security-Policy allows unsafe-inline in script-src",
                            evidence=f"script-src directive contains '{source}'",
                            cwe_id=cwe_id,
                            cvss_score=cvss_score,
                            recommendation='Remove \'unsafe-inline\' from script-src. Use nonce or hash-based CSP instead.',
                        )
                    )
                    return  # Only report once

    def _check_unsafe_eval(self, directives: dict, findings: List[SecurityFinding]) -> None:
        """
        Check for unsafe-eval in script-src.

        CWE: CWE-95 (Improper Neutralization of Directives in Dynamically
                   Evaluated Code ('Eval Injection'))

        unsafe-eval allows eval() which can lead to code injection attacks.
        """
        # Check script-src first
        script_sources = directives.get("script-src", [])
        if not script_sources:
            # Fall back to default-src
            script_sources = directives.get("default-src", [])

        # Check for unsafe-eval
        if "'unsafe-eval'" in script_sources or "unsafe-eval" in [s.lower() for s in script_sources]:
            pattern_type = "unsafe_eval"
            severity = get_severity_for_finding(self.category_id, pattern_type, "high")
            cwe_id = get_cwe_for_finding(self.category_id, "csp_eval") or "CWE-95"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.9,
                    description="Content-Security-Policy allows unsafe-eval in script-src",
                    evidence="script-src directive contains 'unsafe-eval'",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Remove 'unsafe-eval' from script-src. Avoid using eval() in JavaScript.",
                )
            )

    def _check_overly_permissive(self, directives: dict, findings: List[SecurityFinding]) -> None:
        """
        Check for overly permissive CSP directives.

        CWE: CWE-693 (Protection Mechanism Failure)

        Overly permissive directives like default-src: * weakens CSP.
        """
        # Check for wildcard in default-src
        default_sources = directives.get("default-src", [])
        if "*'" in default_sources or "*" in default_sources or "'*'" in default_sources:
            pattern_type = "overly_permissive"
            severity = get_severity_for_finding(self.category_id, pattern_type, "medium")
            cwe_id = get_cwe_for_finding(self.category_id, "csp_wildcard") or "CWE-693"
            cvss_score = calculate_cvss_for_severity(severity)

            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=pattern_type,
                    severity=severity,
                    confidence=0.8,
                    description="Content-Security-Policy has overly permissive wildcard in default-src",
                    evidence="default-src directive contains '*'",
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    recommendation="Replace wildcard (*) with specific sources in default-src directive",
                )
            )

        # Check for data: URIs in script-src
        script_sources = directives.get("script-src", [])
        if "data:" in script_sources:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="data_uri_in_script_src",
                    severity="medium",
                    confidence=0.7,
                    description="Content-Security-Policy allows data: URIs in script-src",
                    evidence="script-src directive contains 'data:'",
                    cwe_id="CWE-693",
                    cvss_score=calculate_cvss_for_severity("medium"),
                    recommendation="Remove 'data:' from script-src. data: URIs can bypass CSP protections.",
                )
            )

    def _check_weak_directives(self, directives: dict, findings: List[SecurityFinding]) -> None:
        """
        Check for weak CSP directives (informational).

        These are lower severity issues that can be addressed for hardening.
        """
        # Check if script-src is missing (falls back to default-src, which may be weak)
        if "script-src" not in directives and "default-src" in directives:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="missing_script_src",
                    severity="low",
                    confidence=0.5,
                    description="Content-Security-Policy missing explicit script-src directive",
                    evidence="script-src not found, falls back to default-src",
                    cwe_id=None,
                    cvss_score=None,
                    recommendation="Add explicit script-src directive for stronger protection",
                )
            )

        # Check if object-src is missing (default-src allows Flash/etc)
        if "object-src" not in directives and "default-src" in directives:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="missing_object_src",
                    severity="low",
                    confidence=0.4,
                    description="Content-Security-Policy missing explicit object-src directive",
                    evidence="object-src not found, plugins may be allowed",
                    cwe_id=None,
                    cvss_score=None,
                    recommendation="Add object-src 'none' to block vulnerable plugins",
                )
            )

        # Check if frame-ancestors is missing (clickjacking protection)
        if "frame-ancestors" not in directives:
            findings.append(
                SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="missing_frame_ancestors",
                    severity="low",
                    confidence=0.4,
                    description="Content-Security-Policy missing frame-ancestors directive",
                    evidence="frame-ancestors not found, site may be framed",
                    cwe_id=None,
                    cvss_score=None,
                    recommendation="Add frame-ancestors 'none' or 'self' to prevent clickjacking",
                )
            )
