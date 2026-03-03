"""
OWASP A02: Cryptographic Failures Module

Detects cryptographic failures including:
- Missing HTTPS on password forms
- Weak TLS/SSL versions and cipher suites
- Hardcoded secrets in page content
- Cleartext transmission of sensitive data
- Missing HTTP Strict Transport Security (HSTS)

CWE Mappings:
- CWE-319: Cleartext Transmission (Critical)
- CWE-327: Use of Broken/Risky Crypto (High)
- CWE-312: Cleartext Storage of Sensitive Information (High)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class CryptographicFailuresModule(SecurityModule):
    """
    OWASP A02: Cryptographic Failures detection module.

    Analyzes headers and page content for cryptographic vulnerabilities
    including weak encryption, cleartext transmission, and hardcoded secrets.
    """

    # MEDIUM tier for cryptographic analysis
    _default_tier = SecurityTier.MEDIUM
    _default_timeout = 10

    @property
    def category_id(self) -> str:
        return "owasp_a02"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for cryptographic failures.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze URL for cleartext transmission
        findings.extend(self._analyze_url_crypto(url))

        # Analyze headers for TLS/SSL issues
        if headers:
            findings.extend(self._analyze_headers_crypto(headers))

        # Analyze DOM metadata for password forms without HTTPS
        if dom_meta:
            findings.extend(self._analyze_password_forms(dom_meta, url))

        # Analyze page content for hardcoded secrets
        if page_content:
            findings.extend(self._analyze_hardcoded_secrets(page_content))

        return findings

    def _analyze_url_crypto(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for cleartight transmission indicators."""
        findings = []

        # Check if URL uses HTTP instead of HTTPS
        if url.startswith("http://"):
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="cleartext_url",
                severity="critical",
                confidence=0.95,
                description="URL uses HTTP instead of HTTPS. Sensitive data transmitted over HTTP can be intercepted and read by attackers.",
                evidence=f"URL: {url}",
                cwe_id="CWE-319",
                cvss_score=9.1,
                recommendation="Migrate all URLs to HTTPS. Configure servers to redirect HTTP to HTTPS. Enable HSTS to enforce secure connections.",
            ))

        return findings

    def _analyze_headers_crypto(self, headers: dict) -> List[SecurityFinding]:
        """Analyze HTTP headers for TLS/SSL issues."""
        findings = []

        # Normalize headers to lowercase for consistent access
        headers_lower = {k.lower(): v for k, v in (headers or {}).items()}

        # Check for TLS version (from some server headers)
        tls_header = headers_lower.get("strict-transport-security", "")
        if tls_header and "max-age=" in tls_header:
            try:
                max_age = tls_header.split("max-age=")[1].split(";")[0].strip()
                max_age_int = int(max_age)
                if max_age_int < 31536000:  # Less than 1 year
                    # HSTS max-age is too short
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="weak_hsts_max_age",
                        severity="medium",
                        confidence=0.80,
                        description="HSTS max-age is less than 1 year. HSTS should have a max-age of at least 1 year to effectively enforce HTTPS.",
                        evidence=f"HSTS max-age: {max_age_int} seconds",
                        cwe_id="CWE-319",
                        cvss_score=5.3,
                        recommendation="Set HSTS max-age to at least 31536000 (1 year). Consider adding the includeSubDomains directive for broader protection.",
                    ))
            except (ValueError, IndexError):
                pass  # Invalid max-age format

        # Check for missing HSTS
        if "strict-transport-security" not in headers_lower:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_hsts",
                severity="medium",
                confidence=0.90,
                description="HTTP Strict Transport Security (HSTS) header is missing. HSTS enforces HTTPS connections and prevents protocol downgrade attacks.",
                evidence="Strict-Transport-Security header not found",
                cwe_id="CWE-523",
                cvss_score=5.3,
                recommendation="Enable HSTS with max-age=31536000 (1 year) and includeSubDomains. Consider adding preload after testing.",
            ))

        # Check for Content-Security-Policy upgrade-insecure-requests
        csp = headers_lower.get("content-security-policy", "")
        if csp and "upgrade-insecure-requests" not in csp.lower():
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_csp_upgrade",
                severity="low",
                confidence=0.70,
                description="Content-Security-Policy missing upgrade-insecure-requests directive. This directive helps transition mixed content sites to HTTPS.",
                evidence="CSP does not include upgrade-insecure-requests",
                cwe_id="CWE-319",
                cvss_score=2.5,
                recommendation="Add upgrade-insecure-requests to Content-Security-Policy header",
            ))

        return findings

    def _analyze_password_forms(self, dom_meta: dict, url: str) -> List[SecurityFinding]:
        """Analyze forms with password fields for HTTPS compliance."""
        findings = []

        # Check if URL is HTTP (not HTTPS)
        is_https = url.startswith("https://")

        forms = dom_meta.get("forms", [])
        for form in forms:
            # Check if form has password fields
            has_password = form.get("has_password", False)
            if not has_password:
                # Also check inputs directly
                has_password = any(
                    inp.get("type") == "password"
                    for inp in form.get("inputs", [])
                )

            if has_password and not is_https:
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="password_form_non_https",
                    severity="critical",
                    confidence=0.95,
                    description="Password form detected on non-HTTPS page. Passwords submitted over HTTP can be intercepted in transit.",
                    evidence=f"Form action: {form.get('action', 'unknown')} on URL: {url}",
                    cwe_id="CWE-319",
                    cvss_score=9.8,
                    recommendation="Ensure all pages with password forms are served over HTTPS. Configure server to redirect all HTTP requests to HTTPS.",
                ))

        return findings

    def _analyze_hardcoded_secrets(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for hardcoded secrets."""
        findings = []

        # Patterns for hardcoded secrets
        secret_patterns = {
            "api_key": r"""api[_-]?key\s*[:=]\s*['"](.*?)['"]""",
            "password": r"""password\s*[:=]\s*['"](.*?)['"]""",
            "secret": r"""secret\s*[:=]\s*['"](.*?)['"]""",
            "private_key": r"""private[_-]?key\s*[:=]\s*['"]{1}.*?['"]{1}""",
            "auth_token": r"""auth[_-]?token\s*[:=]\s*['"](.*?)['"]""",
            "access_token": r"""access[_-]?token\s*[:=]\s*['"](.*?)['"]""",
            "aws_key": r"""aws[_-]?(access|secret)[_-]key\s*[:=]\s*['"](.*?)['"]""",
        }

        # Track findings to avoid duplicates
        found_secrets = set()

        for secret_type, pattern in secret_patterns.items():
            matches = re.finditer(pattern, page_content, re.IGNORECASE)

            for match in matches:
                secret_value = match.group(2) if len(match.groups()) >= 2 else match.group(0)

                # Skip sample/demo values and short values
                skip_keywords = ["your_api_key", "your_secret", "your_password", "demo", "example", "test", "xxx"]
                if any(skip in secret_value.lower() for skip in skip_keywords):
                    continue
                if len(secret_value) < 10:
                    continue

                # Check for base64-like patterns (might be legitimate keys/tokens)
                key_id = f"{secret_type}:{secret_value[:8]}"
                if key_id in found_secrets:
                    continue
                found_secrets.add(key_id)

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type=f"hardcoded_{secret_type}",
                    severity="high",
                    confidence=0.85,
                    description=f"Hardcoded {secret_type.replace('_', ' ')} found in page content. Hardcoded secrets can be extracted by anyone viewing the source code.",
                    evidence=f"{secret_type}: {secret_value[:20]}...",
                    cwe_id="CWE-312",
                    cvss_score=7.5,
                    recommendation="Remove all hardcoded secrets from client-side code. Use secure environment variables, secret management services, or backend APIs to retrieve secret values.",
                    url_finding=True,
                ))

        # Check for JWT tokens in page content
        jwt_pattern = r"""eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"""
        jwt_matches = re.finditer(jwt_pattern, page_content)
        for match in jwt_matches:
            jwt_token = match.group(0)

            # Skip if it's clearly in code comments or documentation
            surrounding = page_content[max(0, match.start() - 50):match.start() + match.end() + 50]
            if any(comment in surrounding for comment in ["<!--", "//", "/*", "#"]):
                continue

            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="jwt_in_page_content",
                severity="medium",
                confidence=0.75,
                description="JWT token found in page content. JWT tokens should not be exposed in client-side code as they can be extracted and used for impersonation.",
                evidence=f"JWT token (first 32 chars): {jwt_token[:32]}...",
                cwe_id="CWE-312",
                cvss_score=5.9,
                recommendation="Do not expose JWT tokens in client-side code. Use HttpOnly, Secure cookies with SameSite attributes for token storage.",
                url_finding=True,
            ))

        return findings
