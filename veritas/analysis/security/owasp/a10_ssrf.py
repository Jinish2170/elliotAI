"""
OWASP A10: Server-Side Request Forgery (SSRF) Module

Detects SSRF vulnerabilities including:
- URL-based SSRF vectors
- file:// protocol usage
- Internal network indicators
- Cloud metadata endpoint access
- DNS rebinding indicators

CWE Mappings:
- CWE-918: Server-Side Request Forgery (SSRF) (Critical)
- CWE-20: Improper Input Validation (High)
- CWE-200: Information Exposure (Medium)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class SSRFModule(SecurityModule):
    """
    OWASP A10: Server-Side Request Forgery (SSRF) detection module.

    Analyze forms, links, and URLs for SSRF vulnerabilities including
    URL parameters that trigger server-side requests to arbitrary
    resources.
    """

    # MEDIUM tier for SSRF analysis
    _default_tier = SecurityTier.MEDIUM
    _default_timeout = 10

    @property
    def category_id(self) -> str:
        return "owasp_a10"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for Server-Side Request Forgery (SSRF) vulnerabilities.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze URL for SSRF vectors
        findings.extend(self._analyze_url_ssrf(url))

        # Analyze DOM metadata for SSRF-indicating forms
        if dom_meta:
            findings.extend(self._analyze_forms_ssrf(dom_meta, url))

        # Analyze page content for SSRF patterns
        if page_content:
            findings.extend(self._analyze_page_ssrf(page_content))

        return findings

    def _analyze_url_ssrf(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for SSRF vulnerabilities."""
        findings = []

        # SSRF-sensitive parameter names
        ssrf_param_patterns = [
            "url", "target", "destination", "redirect", "forward", "uri",
            "endpoint", "site", "host", "server", "addr", "address", "link",
            "callback", "webhook", "proxy", "fetch", "load", "source",
        ]

        if "?" in url:
            query_part = url.split("?")[1]

            # Parse query parameters
            params = {}
            for param in query_part.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key.lower()] = value[0:100]  # Truncate for analysis

            # Check for SSRF parameters with potentially dangerous values
            for param_pattern in ssrf_param_patterns:
                for param_name, param_value in params.items():
                    if param_pattern in param_name:
                        # Check if value looks like a URL or has SSRF-indicating patterns
                        ssrf_indicators = [
                            ("http://", "HTTP protocol"),
                            ("https://", "HTTPS protocol"),
                            ("file:///", "file:// protocol"),
                            ("file:/etc/", "File path"),
                            ("ftp://", "FTP protocol"),
                            ("localhost", "localhost reference"),
                            ("127.0.0.1", "loopback IP"),
                            ("0.0.0.0", "wildcard IP"),
                            ("192.168.", "private network 192.168.x.x"),
                            ("10.", "private network 10.x.x.x"),
                            ("169.254.169.254", "AWS metadata endpoint"),
                            ("metadata.google.internal", "GCP metadata endpoint"),
                            ("metadata.azure.net", "Azure metadata endpoint"),
                        ]

                        for indicator, description in ssrf_indicators:
                            if indicator.lower() in param_value.lower():
                                # Critical: cloud metadata endpoints
                                if "metadata" in description.lower():
                                    findings.append(SecurityFinding(
                                        category_id=self.category_id,
                                        pattern_type="ssrf_cloud_metadata",
                                        severity="critical",
                                        confidence=0.90,
                                        description=f"Potential SSRF to cloud metadata endpoint: {param_name}={param_value[:30]}... Access to cloud metadata can lead to credential theft.",
                                        evidence=f"Parameter: {param_name} contains: {description}",
                                        cwe_id="CWE-918",
                                        cvss_score=9.8,
                                        recommendation="Strictly validate and whitelist allowed URLs. Block access to internal networks and cloud metadata endpoints.",
                                        url_finding=True,
                                    ))
                                    return findings

                                # High: localhost/internal networks
                                elif any(kw in description.lower() for kw in ["localhost", "loopback", "private", "file://"]):
                                    findings.append(SecurityFinding(
                                        category_id=self.category_id,
                                        pattern_type="ssrf_internal_network",
                                        severity="high",
                                        confidence=0.85,
                                        description=f"Potential SSRF to internal resource: {param_name}={param_value[:30]}... Access to internal networks may expose sensitive services.",
                                        evidence=f"Parameter: {param_name} contains: {description}",
                                        cwe_id="CWE-918",
                                        cvss_score=8.6,
                                        recommendation="Validate and sanitize all URL parameters. Whitelist allowed protocols and domains. Block internal network ranges.",
                                        url_finding=True,
                                    ))
                                    return findings

                                # Medium: generic URL parameter
                                else:
                                    findings.append(SecurityFinding(
                                        category_id=self.category_id,
                                        pattern_type="ssrf_url_parameter",
                                        severity="medium",
                                        confidence=0.70,
                                        description=f"URL parameter detected that may be vulnerable to SSRF: {param_name}. URL parameters that trigger server-side requests can be exploited to scan internal networks.",
                                        evidence=f"Parameter: {param_name}",
                                        cwe_id="CWE-918",
                                        cvss_score=6.5,
                                        recommendation="Validate URL parameters against a whitelist. Restrict protocols to HTTP/HTTPS. Implement network-level restrictions.",
                                        url_finding=True,
                                    ))
                                    return findings

        return findings

    def _analyze_forms_ssrf(self, dom_meta: dict, url: str) -> List[SecurityFinding]:
        """Analyze DOM forms for SSRF vulnerabilities."""
        findings = []

        forms = dom_meta.get("forms", [])

        for form in forms:
            form_action = form.get("action", "")
            form_method = form.get("method", "").upper()
            inputs = form.get("inputs", [])

            # Check form inputs for SSRF parameters
            ssrf_input_names = [
                "url", "target", "destination", "redirect", "uri", "link",
                "endpoint", "webhook", "proxy", "fetch", "image", "avatar",
            ]

            for inp in inputs:
                input_name = inp.get("name", "").lower()
                input_type = inp.get("type", "").lower()

                # Check for SSRF-suspect input names
                for ssrf_pattern in ssrf_input_names:
                    if ssrf_pattern in input_name:
                        # Check if it's in a form that submits (POST/PUT)
                        if form_method in ("POST", "PUT"):
                            findings.append(SecurityFinding(
                                category_id=self.category_id,
                                pattern_type="ssrf_form_input",
                                severity="medium",
                                confidence=0.65,
                                description=f"Form input with SSRF-suspect name: {inp.get('name')}. Form inputs with URL-type names may be vulnerable to SSRF.",
                                evidence=f"Input name: {inp.get('name')} in form: {form_action or 'unknown'}",
                                cwe_id="CWE-918",
                                cvss_score="6.5",
                                recommendation="Validate URL inputs against a whitelist. Restrict to allowed domains/protocols. Block internal network access.",
                            ))
                            return findings

                # Check for URL input type
                if input_type == "url":
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="url_input_type",
                        severity="medium",
                        confidence=0.60,
                        description=f"Form input of type 'url' detected. URL inputs can be SSRF vectors if used for server-side requests.",
                        evidence=f"Input name: {inp.get('name')} (type: url)",
                        cwe_id="CWE-918",
                        cvss_score="5.9",
                        recommendation="Validate all URL inputs. Whitelist allowed domains. DNS rebind and prevent bypass attempts.",
                    ))

        return findings

    def _analyze_page_ssrf(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for SSRF-related patterns."""
        findings = []

        # Check for JavaScript code that makes fetch/XHR requests with user input
        js_patterns = [
            (r"""fetch\s*\(\s*['"]?\s*\w+\['""", "fetch with dynamic parameter", 0.70),
            (r"""fetch\s*\(\s*\w+\s*\+\s*""", "fetch with string concatenation", 0.75),
            (r"""XMLHttpRequest\s*\(\)\s*\.open\s*\(\s*['"]GET['"]\s*,\s*\w+""", "XHR with dynamic parameter", 0.70),
            (r"""axios\.(?:get|post)\s*\(\s*\w+""", "axios with dynamic parameter", 0.70),
            (r"""\.get\s*\(\s*['"]?\s*\w+['"]?\s*\)""", ".get() with dynamic parameter", 0.65),
        ]

        page_lower = page_content.lower()

        for pattern, description, confidence in js_patterns:
            if re.search(pattern, page_content):
                # Check for SSRF-relevant keywords
                context_patterns = [
                    r"(?:url|target|endpoint|uri|link)",
                ]

                # Find matches and check context
                matches = list(re.finditer(pattern, page_content, re.IGNORECASE))
                for match in matches:
                    surrounding = page_content[max(0, match.start() - 100):match.start() + 100]
                    if any(re.search(ctx, surrounding, re.IGNORECASE) for ctx in context_patterns):
                        findings.append(SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="ssrf_in_javascript",
                            severity="medium",
                            confidence=confidence,
                            description=f"JavaScript {description} that may be vulnerable to SSRF. Dynamic requests based on user input can be manipulated.",
                            evidence=f"Pattern: {description}",
                            cwe_id="CWE-918",
                            cvss_score="6.1",
                            recommendation="Validate all user input before using in fetch/XHR requests. Use URL whitelisting and protocol restrictions.",
                        ))
                        return findings

        # Check for file:// protocol references
        file_protocol_pattern = r"""file://(?:/|\\/)"""
        if re.search(file_protocol_pattern, page_content):
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="file_protocol_reference",
                severity="high",
                confidence=0.80,
                description="file:// protocol reference found in page content. This may indicate local file access which can be exploited via SSRF.",
                evidence="file:// protocol found",
                cwe_id="CWE-918",
                cvss_score="7.5",
                recommendation="Remove file:// protocol usage. Restrict external requests to HTTP/HTTPS only. Implement input validation.",
            ))

        # Check for internal network references
        internal_network_patterns = [
            ("192\\.168\\.", "192.168.x.x private network"),
            ("10\\.", "10.x.x.x private network"),
            ("172\\.(1[6-9]|2\\d|3[01])\\.", "172.16-31.x.x private network"),
            ("127\\.0\\.0\\.1", "loopback address"),
            ("localhost", "localhost reference"),
        ]

        for pattern, description in internal_network_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                # Skip if it's clearly in code comments
                matches = list(re.finditer(pattern, page_content))
                for match in matches:
                    match_start = max(0, match.start() - 20)
                    context = page_content[match_start:match.start()]
                    if not any(comment in context for comment in ["<!--", "//", "/*", "#"]):
                        findings.append(SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="internal_network_reference",
                            severity="medium",
                            confidence=0.60,
                            description=f"Internal network reference found: {description}. Internal network references may be SSRF indicators.",
                            evidence=f"Pattern: {description}",
                            cwe_id="CWE-918",
                            cvss_score="5.9",
                            recommendation="Review internal network references. Ensure they're not user-controllable inputs for server-side requests.",
                        ))
                        return findings

        # Check for DNS rebinding patterns (hostname in query or hash)
        dns_rebinding_patterns = [
            r"""hostname\s*=""",
            r"""domain\s*=.*?['"]\.""",
            r"""host\s*=.*?['"]\.""",
        ]

        for pattern in dns_rebinding_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="dns_rebinding_indicator",
                    severity="low",
                    confidence=0.50,
                    description="DNS rebinding-related pattern detected. Dynamic hostname handling can be exploited for SSRF via DNS rebinding attacks.",
                    evidence=f"Pattern: {pattern}",
                    cwe_id="CWE-918",
                    cvss_score="4.3",
                    recommendation="Implement DNS pinning or whitelist-based hostname validation. Use timeout and connection limits.",
                ))
                break

        return findings
