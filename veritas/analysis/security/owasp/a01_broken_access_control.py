"""
OWASP A01: Broken Access Control Module

Detects broken access control vulnerabilities including:
- Admin panels without authentication requirements
- IDOR (Insecure Direct Object Reference) patterns
- Path traversal vulnerabilities
- Unrestricted file uploads
- Privilege escalation vectors

CWE Mappings:
- CWE-285: Improper Authorization (Critical)
- CWE-639: Insecure Direct Object Reference (High)
- CWE-22: Path Traversal (High)
- CWE-434: Unrestricted Upload of File (High)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class BrokenAccessControlModule(SecurityModule):
    """
    OWASP A01: Broken Access Control detection module.

    Analyzes DOM metadata for access control vulnerabilities including
    admin panels, IDOR patterns, path traversal indicators, and file upload issues.
    """

    # DEEP tier for comprehensive access control analysis
    _default_tier = SecurityTier.DEEP
    _default_timeout = 20

    @property
    def category_id(self) -> str:
        return "owasp_a01"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for broken access control vulnerabilities.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze URL for IDOR patterns
        findings.extend(self._analyze_idor(url))

        # Analyze URL for path traversal indicators
        findings.extend(self._analyze_path_traversal(url))

        # Analyze DOM metadata for admin panels
        if dom_meta:
            findings.extend(self._analyze_admin_panel(dom_meta))

            # Analyze forms for unrestricted file uploads
            findings.extend(self._analyze_file_upload(dom_meta))

            # Analyze forms for CSRF token protection
            findings.extend(self._analyze_csrf_protection(dom_meta))

        # Analyze page content for access control issues
        if page_content:
            findings.extend(self._analyze_page_content(page_content, url))

        return findings

    def _analyze_idor(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for Insecure Direct Object Reference (IDOR) patterns."""
        findings = []

        # IDOR patterns: sequential IDs in URL path
        idor_patterns = [
            r'/users/\d+',  # /users/123
            r'/user/\d+',   # /user/123
            r'/accounts/\d+',
            r'/account/\d+',
            r'/orders/\d+',
            r'/order/\d+',
            r'/items/\d+',
            r'/item/\d+',
            r'/documents/\d+',
            r'/document/\d+',
            r'/profile/\d+',
            r'/posts/\d+',
            r'/post/\d+',
            r'/messages/\d+',
            r'/message/\d+',
            r'[\?\&]user_id=\d+',  # ?user_id=123
            r'[\?\&]account_id=\d+',
            r'[\?\&]order_id=\d+',
            r'[\?\&]item_id=\d+',
            r'[\?\&]doc_id=\d+',
            r'[\?\&]id=\d+(?:&|$)',  # bare ?id=123
        ]

        url_lower = url.lower()
        for pattern in idor_patterns:
            if re.search(pattern, url):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="idor_pattern",
                    severity="high",
                    confidence=0.85,
                    description="Insecure Direct Object Reference (IDOR) pattern detected in URL. Sequential IDs exposed in URL may allow unauthorized access to user data.",
                    evidence=f"URL matches IDOR pattern: {pattern}",
                    cwe_id="CWE-639",
                    cvss_score=8.1,
                    recommendation="Implement proper access control checks and use UUIDs or random identifiers instead of sequential IDs. Verify user has permission to access the requested resource.",
                ))
                break  # One finding for IDOR is sufficient

        return findings

    def _analyze_path_traversal(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for path traversal indicators."""
        findings = []

        # Path traversal indicators
        traversal_indicators = [
            '../',
            '..\\',
            '%2e%2e',
            '%2e%2e%2f',
            '%2e%2e%5c',
            'path=',
            'file=',
            'dir=',
        ]

        url_lower = url.lower()
        for indicator in traversal_indicators:
            if indicator.lower() in url_lower:
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="path_traversal",
                    severity="high",
                    confidence=0.80,
                    description="Path traversal indicator detected in URL. This could allow attackers to access files outside the intended directory.",
                    evidence=f"URL contains path traversal indicator: {indicator}",
                    cwe_id="CWE-22",
                    cvss_score=7.5,
                    recommendation="Validate and sanitize all user-controlled file paths. Use a whitelist of allowed directories and files. Implement proper path canonicalization.",
                ))
                break  # One finding for path traversal is sufficient

        return findings

    def _analyze_admin_panel(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze DOM metadata for admin panel issues."""
        findings = []

        # Check for admin panel
        admin_panel = dom_meta.get("admin_panel")
        if admin_panel:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="admin_panel_detected",
                severity="critical",
                confidence=0.90,
                description="Admin panel detected on the page. Admin panels should be protected by multi-factor authentication and restricted network access.",
                evidence=f"Admin panel found: {admin_panel.get('path', 'unknown')}",
                cwe_id="CWE-285",
                cvss_score=9.8,
                recommendation="Ensure admin panel requires strong authentication (MFA), IP whitelisting, and role-based access control. Consider moving to a separate admin subdomain.",
            ))

        # Check for IDOR patterns in DOM metadata
        idor_patterns = dom_meta.get("idor_patterns", [])
        if idor_patterns:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="idor_in_dom",
                severity="high",
                confidence=0.75,
                description=f"Insecure Direct Object Reference patterns detected in DOM structure: {len(idor_patterns)} pattern(s) identified.",
                evidence=f"IDOR patterns: {', '.join(idor_patterns[:5])}",
                cwe_id="CWE-639",
                cvss_score=7.5,
                recommendation="Review and fix IDOR vulnerabilities by implementing proper authorization checks on all resource access points. Use UUIDs or random identifiers.",
            ))

        return findings

    def _analyze_file_upload(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze forms for unrestricted file uploads."""
        findings = []

        forms = dom_meta.get("forms", [])
        for form in forms:
            form_action = form.get("action", "")
            form_method = form.get("method", "")

            # Check for file upload forms without proper validation indicators
            has_file_input = any(
                inp.get("type") == "file"
                for inp in form.get("inputs", [])
            )

            if has_file_input:
                # Check for security attributes
                inputs = form.get("inputs", [])
                has_accept_attr = any(inp.get("accept") for inp in inputs if inp.get("type") == "file")

                if not has_accept_attr:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="unrestricted_file_upload",
                        severity="high",
                        confidence=0.70,
                        description="File upload form detected without file type restrictions. This may allow malicious file uploads leading to arbitrary code execution.",
                        evidence=f"File upload form: {form_action or 'unknown action'}",
                        cwe_id="CWE-434",
                        cvss_score=8.6,
                        recommendation="Implement strict file type validation (whitelist allowed extensions), scan uploaded files for malware, and store uploads outside web root with proper isolation.",
                    ))

        return findings

    def _analyze_csrf_protection(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze forms for CSRF token protection."""
        findings = []

        forms = dom_meta.get("forms", [])
        for form in forms:
            form_action = form.get("action", "")
            form_method = form.get("method", "").upper()

            # Only check state-changing forms (POST/PUT/DELETE/PATCH)
            if form_method in ("POST", "PUT", "DELETE", "PATCH"):
                inputs = form.get("inputs", [])
                has_csrf_token = any(
                    any(keyword in inp.get("name", "").lower() for keyword in ["csrf", "_token", "token"])
                    for inp in inputs
                    if inp.get("type") in ("hidden", "")
                )

                if not has_csrf_token:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="missing_csrf_token",
                        severity="high",
                        confidence=0.75,
                        description="State-changing form detected without visible CSRF token protection. This may allow Cross-Site Request Forgery attacks.",
                        evidence=f"Form action: {form_action or 'unknown'} (Method: {form_method})",
                        cwe_id="CWE-352",
                        cvss_score=8.8,
                        recommendation="Implement CSRF tokens in all state-changing forms. Use same-site cookie attributes and validate tokens on the server side.",
                    ))

        return findings

    def _analyze_page_content(self, page_content: str, url: str) -> List[SecurityFinding]:
        """Analyze page content for access control issues."""
        findings = []

        # Check for hardcoded role references or privilege escalation hints
        # e.g., user.role='admin', isAdmin=true in JavaScript

        hardcoded_admin_patterns = [
            r'admin\s*[:=]\s*true',
            r'isAdmin\s*[:=]\s*true',
            r'user\.role\s*[:=]\s*["\']?admin["\']?',
            r'role\s*[:=]\s*["\']?admin["\']?',
            r'is_superuser\s*[:=]\s*true',
            r'is_moderator\s*[:=]\s*true',
        ]

        page_lower = page_content.lower()
        for pattern in hardcoded_admin_patterns:
            if re.search(pattern, page_lower, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="hardcoded_admin_reference",
                    severity="medium",
                    confidence=0.60,
                    description="Hardcoded admin or privilege references found in page content. Client-side admin checks can be bypassed.",
                    evidence=f"Matches pattern: {pattern}",
                    cwe_id="CWE-285",
                    cvss_score=5.5,
                    recommendation="Remove client-side role checks and implement proper server-side authorization. Never trust client-side values for security decisions.",
                ))
                break  # One finding is sufficient

        # Check for exposed user data in page content
        exposed_data_patterns = [
            r'"email"\s*:\s*"[^@]+@[^"]+"',
            r'"password"\s*:',
            r'"user_id"\s*:\s*\d+',
            r'"account_id"\s*:\s*\d+',
        ]

        for pattern in exposed_data_patterns:
            if re.search(pattern, page_content):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="exposed_user_data",
                    severity="medium",
                    confidence=0.50,
                    description="User data potentially exposed in page content. Sensitive user information should not be embedded in client-side code.",
                    evidence=f"Matches pattern: {pattern}",
                    cwe_id="CWE-215",
                    cvss_score=4.3,
                    recommendation="Remove sensitive user data from client-side code. Implement proper API endpoints with authentication to retrieve user-specific data.",
                ))
                break  # One finding is sufficient

        return findings
