"""
OWASP A05: Security Misconfiguration Module

Detects security misconfigurations including:
- Debug mode enabled
- default credentials exposed
- Stack traces in error messages
- Directory listing enabled
- CORS misconfigurations
- Exposed configuration files

CWE Mappings:
- CWE-489: Active Debug Code (High)
- CWE-798: Use of Hard-coded Credentials (Critical)
- CWE-209: Error Message Revealing Info (Medium)
- CWE-538: Insertion of Sensitive Information into Externally-Accessible File or Directory (Medium)
- CWE-942: Permissive Cross-domain Policy (Medium)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class SecurityMisconfigurationModule(SecurityModule):
    """
    OWASP A05: Security Misconfiguration detection module.

    Analyzes headers, page content, and DOM metadata for security
    misconfiguration vulnerabilities including debug mode, default
    credentials, error messages, and CORS issues.
    """

    # MEDIUM tier for configuration analysis
    _default_tier = SecurityTier.MEDIUM
    _default_timeout = 8

    @property
    def category_id(self) -> str:
        return "owasp_a05"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for security misconfigurations.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze URL for debug mode indicators
        findings.extend(self._analyze_url_debug(url))

        # Analyze headers for misconfigurations
        if headers:
            findings.extend(self._analyze_headers_misconfig(headers))

        # Analyze page content for misconfigurations
        if page_content:
            findings.extend(self._analyze_page_misconfig(page_content))

        # Analyze DOM metadata for issues
        if dom_meta:
            findings.extend(self._analyze_dom_misconfig(dom_meta))

        return findings

    def _analyze_url_debug(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for debug mode indicators."""
        findings = []

        debug_indicators = [
            "debug=true",
            "debug=1",
            "dev=true",
            "dev=1",
            "test=true",
            "test=1",
            "verbose=true",
            "verbosity=",
        ]

        url_lower = url.lower()
        for indicator in debug_indicators:
            if indicator in url_lower:
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="debug_mode_in_url",
                    severity="high",
                    confidence=0.85,
                    description=f"Debug mode indicator found in URL: {indicator}. Debug mode may expose sensitive information.",
                    evidence=f"URL contains: {indicator}",
                    cwe_id="CWE-489",
                    cvss_score=7.5,
                    recommendation="Disable debug mode in production. Use separate deployment configuration for debug settings.",
                    url_finding=True,
                ))
                break

        return findings

    def _analyze_headers_misconfig(self, headers: dict) -> List[SecurityFinding]:
        """Analyze headers for security misconfigurations."""
        findings = []

        # Normalize headers to lowercase
        headers_lower = {k.lower(): v for k, v in (headers or {}).items()}

        # Check for CORS misconfiguration
        cors_headers = {
            "access-control-allow-origin": headers_lower.get("access-control-allow-origin", ""),
            "access-control-allow-credentials": headers_lower.get("access-control-allow-credentials", ""),
        }

        if cors_headers["access-control-allow-origin"]:
            origin = cors_headers["access-control-allow-origin"].lower()

            # Check for wildcard CORS with credentials
            # This is risky: wildcard origin with credentials allows any site to make authenticated requests
            if origin == "*" and cors_headers["access-control-allow-credentials"] == "true":
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="cors_wildcard_with_credentials",
                    severity="medium",
                    confidence=0.85,
                    description="CORS misconfiguration: wildcard origin (Access-Control-Allow-Origin: *) with credentials enabled. This allows any site to make authenticated requests.",
                    evidence="Access-Control-Allow-Origin: * with Access-Control-Allow-Credentials: true",
                    cwe_id="CWE-942",
                    cvss_score=6.5,
                    recommendation="Do not use wildcard origin with credentials. Specify allowed origins explicitly. Remove Access-Control-Allow-Credentials if not needed.",
                ))
            # Wildcard origin without credentials is less severe
            elif origin == "*":
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="cors_wildcard_origin",
                    severity="low",
                    confidence=0.60,
                    description="CORS uses wildcard origin (Access-Control-Allow-Origin: *). This allows any site to make requests, though without credentials.",
                    evidence="Access-Control-Allow-Origin: *",
                    cwe_id="CWE-942",
                    cvss_score=3.7,
                    recommendation="Consider restricting CORS to specific origins rather than wildcard. Only use wildcard if the API is truly public.",
                ))

        # Check for server header revealing version info
        server_header = headers_lower.get("server", "")
        if server_header:
            # Check for version numbers (common patterns: /1.0.0, v1.2.3, 1.5)
            version_patterns = [
                r"/\d+\.\d+(\.\d+)?",  # e.g., nginx/1.18.0
                r"\s\d+\.\d+(\.\d+)?\s",  # e.g., Apache 2.4.41
                r"\bv\d+\.\d+",  # e.g., v1.2.3
            ]

            for pattern in version_patterns:
                if re.search(pattern, server_header, re.IGNORECASE):
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="server_header_version",
                        severity="low",
                        confidence=0.70,
                        description="Server header reveals version information. Version disclosure can help attackers target specific vulnerabilities.",
                        evidence=f"Server header: {server_header}",
                        cwe_id="CWE-200",
                        cvss_score=2.5,
                        recommendation="Remove or minimize version information from Server header. Use generic values like 'nginx' or 'Apache'.",
                    ))
                    break

        # Check for X-Powered-By header
        powered_by = headers_lower.get("x-powered-by", "")
        if powered_by:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="powered_by_header",
                severity="low",
                confidence=0.60,
                description="X-Powered-By header reveals framework information. Framework disclosure can help attackers target specific vulnerabilities.",
                evidence=f"X-Powered-By: {powered_by}",
                cwe_id="CWE-200",
                cvss_score=2.1,
                recommendation="Remove X-Powered-By header in production.",
            ))

        return findings

    def _analyze_page_misconfig(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for security misconfigurations."""
        findings = []

        # Check for debug/error messages
        debug_patterns = [
            r"debug\s*:\s*true",
            r"debug\s*=\s*true",
            r"console\.log\s*\(\s*debug",
            r"console\.log\s*\(\s*DEBUG",
            r"show_debug\s*=\s*true",
            r"enable_debug",
        ]

        page_lower = page_content.lower()
        for pattern in debug_patterns:
            if re.search(pattern, page_lower, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="debug_in_page_content",
                    severity="high",
                    confidence=0.75,
                    description="Debug-related code found in page content. Debug information can expose sensitive system details.",
                    evidence=f"Pattern: {pattern}",
                    cwe_id="CWE-489",
                    cvss_score=7.5,
                    recommendation="Remove debug code from production. Use different deployment configurations for debug logging.",
                ))
                break

        # Check for stack traces
        stack_trace_indicators = [
            r"Traceback",
            r"Stack trace",
            r"at\s+[\w.]+\((?:file\s+)?[^\)]+\)",
            r"Exception\s+in\s+thread",
            r"Error:\s*\n",
            r"Error:",
        ]

        for indicator in stack_trace_indicators:
            if re.search(indicator, page_content, re.IGNORECASE):
                # Exclude benign cases like user-facing error messages
                # Stack traces typically have multiple lines with code references
                if "at " in page_content or "Traceback" in page_content:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="stack_trace_exposed",
                        severity="medium",
                        confidence=0.70,
                        description="Stack trace or detailed error message detected. Error messages may reveal sensitive implementation details.",
                        evidence="Stack trace indicators found in page content",
                        cwe_id="CWE-209",
                        cvss_score=5.3,
                        recommendation="Configure error handlers to show generic error messages. Log detailed errors server-side only.",
                    ))
                    break

        # Check for default credentials
        default_credential_patterns = [
            (r"""['"]admin['"]\s*[:=]\s*['"]admin['"]""", "admin/admin default credential"),
            (r"""['"]password['"]\s*[:=]\s*['"](?:password|123456|admin)['"]""", "default password"),
            (r"""['"]root['"]\s*[:=]\s*['"](?:password|123456|root)['"]""", "root default credential"),
            (r"""['"]username['"]\s*[:=]\s*['"]admin['"]""", "default username"),
            (r"""['"]key['"]\s*[:=]\s*['"](?:secret|password|api)['"]""", "default API key"),
        ]

        for pattern, description in default_credential_patterns:
            matches = re.finditer(pattern, page_content, re.IGNORECASE)
            for match in matches:
                # Skip comments
                match_start = max(0, match.start() - 20)
                context = page_content[match_start:match.start()]
                if any(comment in context for comment in ["<!--", "//", "/*", "#"]):
                    continue

                # Skip demo/sample code
                if "demo" in context.lower() or "example" in context.lower():
                    continue

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="default_credential",
                    severity="critical",
                    confidence=0.85,
                    description=f"Default credential pattern detected: {description}. Default credentials can be used by attackers to gain unauthorized access.",
                    evidence=f"Pattern: {description}",
                    cwe_id="CWE-798",
                    cvss_score=9.8,
                    recommendation="Remove all default credentials. Force password reset on first login. Never ship with default credentials.",
                ))

        # Check for directory listing (index of)
        if "index of" in page_lower and ("parent directory" in page_lower or "name last modified size" in page_lower):
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="directory_listing_enabled",
                severity="medium",
                confidence=0.85,
                description="Directory listing appears to be enabled. Directory listing exposes file structures and may reveal sensitive files.",
                evidence="Directory listing page detected",
                cwe_id="CWE-538",
                cvss_score=5.3,
                recommendation="Disable directory listing in web server configuration. Use index files or implement access control.",
            ))

        # Check for configuration file references
        config_file_patterns = [
            r"\.(env|config|ini|conf|yaml|yml|json)\b",
            r"wp-config\.php",
            r"web\.config",
            r"application\.yml",
        ]

        # Only look for these in HTML comments (not just references)
        html_comments = re.findall(r"<!--(.*?)-->", page_content, re.DOTALL | re.IGNORECASE)
        for comment in html_comments:
            for pattern in config_file_patterns:
                if re.search(pattern, comment, re.IGNORECASE):
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="config_file_in_comment",
                        severity="low",
                        confidence=0.60,
                        description="Configuration file name found in HTML comments. This may reveal architecture details.",
                        evidence=f"Pattern: {pattern} in HTML comment",
                        cwe_id="CWE-200",
                        cvss_score=3.1,
                        recommendation="Remove all comments from production HTML. Remove inline comments that reveal architecture details.",
                    ))

        return findings

    def _analyze_dom_misconfig(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze DOM metadata for misconfigurations."""
        findings = []

        # Check for forms with autocomplete enabled on password fields
        forms = dom_meta.get("forms", [])
        for form in forms:
            password_inputs = [inp for inp in form.get("inputs", []) if inp.get("type") == "password"]

            for pwd in password_inputs:
                # Check if autocomplete is explicitly enabled (or not disabled)
                autocomplete = pwd.get("autocomplete", "").lower()
                if autocomplete not in ("off", "new-password"):
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="password_autocomplete_enabled",
                        severity="low",
                        confidence=0.55,
                        description="Password field does not have autocomplete disabled. Saved passwords in browser may be a security risk on shared computers.",
                        evidence=f"Password field autocomplete: {autocomplete or 'not specified'}",
                        cwe_id="CWE-522",
                        cvss_score=2.8,
                        recommendation="Set autocomplete='off' or autocomplete='new-password' on password fields for sensitive applications.",
                    ))

        return findings
