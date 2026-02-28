"""
OWASP A03: Injection Module

Detects injection vulnerabilities including:
- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- Command Injection
- LDAP Injection
- Template Injection
- NoSQL Injection

CWE Mappings:
- CWE-89: SQL Injection (Critical)
- CWE-79: Cross-Site Scripting (XSS) (High)
- CWE-78: Command Injection (Critical)
- CWE-90: LDAP Injection (Medium)
- CWE-94: Code Injection (High)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class InjectionModule(SecurityModule):
    """
    OWASP A03: Injection detection module.

    Analyzes DOM metadata and page content for injection vulnerabilities
    including SQL injection, XSS, command injection, and template injection.
    """

    # MEDIUM tier for injection analysis
    _default_tier = SecurityTier.MEDIUM
    _default_timeout = 10

    @property
    def category_id(self) -> str:
        return "owasp_a03"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for injection vulnerabilities.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze URL for injection vectors
        findings.extend(self._analyze_url_injections(url))

        # Analyze DOM metadata for form and script injection points
        if dom_meta:
            findings.extend(self._analyze_dom_injections(dom_meta))

        # Analyze page content for XSS vectors
        if page_content:
            findings.extend(self._analyze_page_injections(page_content))

        # Analyze headers for injection protection
        if headers:
            findings.extend(self._analyze_headers_injection_protection(headers))

        return findings

    def _analyze_url_injections(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for injection vectors in query parameters."""
        findings = []

        # Extract query parameters
        if "?" not in url:
            return findings

        query_part = url.split("?")[1]

        # SQL Injection patterns
        sqli_patterns = [
            r"['\"]\s*(?:or|and)\s+\d+\s*=\s*\d+",  # ' OR 1=1, " AND 5=5
            r"['\"]\s*[;,\-]\s*",  # Quotes with special chars
            r"(?:union\s+select|select\s+.*\s+from)",  # UNION SELECT queries
            r"(?:drop\s+table|truncate\s+table)",  # DROP/TRUNCATE statements
            r"(?:;|&&|\|)\s*(?:drop|delete|update|insert)",  # Multiple statements
            r"(?:exec|execute)\s*\(",  # EXECUTE()
        ]

        for pattern in sqli_patterns:
            if re.search(pattern, query_part, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="sql_injection",
                    severity="critical",
                    confidence=0.85,
                    description="SQL injection pattern detected in URL query parameters. This could allow attackers to execute arbitrary SQL commands.",
                    evidence=f"URL contains SQLi pattern: {pattern}",
                    cwe_id="CWE-89",
                    cvss_score=9.8,
                    recommendation="Use parameterized queries/prepared statements. Validate and sanitize all user input. Implement server-side input validation.",
                    url_finding=True,
                ))
                break  # One SQLi finding is sufficient

        # Command injection patterns
        cmd_injection_patterns = [
            r"[;|&`]",  # Shell command separators
            r"\$\(.*?\)",  # Command substitution $()
            r"`(?:.*?)`",  # Backtick execution
            r"\|\s*\w+",  # Pipe with command
            r"&&\s*\w+",  # AND with command
            r"(?:system|exec|popen|passthru)\s*\(",  # Command functions
        ]

        # Skip URL-encoded values (legitimate)
        for pattern in cmd_injection_patterns:
            if re.search(pattern, query_part) and not self._is_url_safe(query_part):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="command_injection",
                    severity="critical",
                    confidence=0.80,
                    description="Command injection pattern detected in URL query parameters. This could allow attackers to execute arbitrary system commands.",
                    evidence=f"URL contains command injection pattern: {pattern}",
                    cwe_id="CWE-78",
                    cvss_score=9.8,
                    recommendation="Never execute shell commands with user input. Use language-native APIs instead of shell commands. Validate and escape all user input.",
                    url_finding=True,
                ))
                break  # One command injection finding is sufficient

        # LDAP injection patterns
        ldap_patterns = [
            r"\(\s*\*\s*\)",  # (*)
            r"\(\s*(?:uid|cn|dn)\s*=\s*\*",  # (uid=*)
            r"[*&|~]",  # LDAP operators
            r"(?:\(|\))",  # Parentheses (LDAP query syntax)
        ]

        url_lower = query_part.lower()
        for pattern in ldap_patterns:
            if re.search(pattern, query_part) and any(kw in url_lower for kw in ["login", "auth", "ldap", "directory"]):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="ldap_injection",
                    severity="medium",
                    confidence=0.60,
                    description="LDAP injection pattern detected in URL. This could allow attackers to manipulate LDAP queries.",
                    evidence=f"URL contains LDAP pattern: {pattern}",
                    cwe_id="CWE-90",
                    cvss_score=6.5,
                    recommendation="Use LDAP escape functions for all user input. Implement whitelist validation for LDAP query parameters. Consider using prepared statements.",
                    url_finding=True,
                ))
                break

        # Template injection (SSTI) patterns
        template_patterns = [
            r"\{\{.*?\}\}",  # Jinja2, Django
            r"\{%.*?%\}",  # Jinja2 statements
            r"\{\$.*?\}",  # Smarty
            r"\$\s*\(.*?\)",  # Velocity
            r"<#.*?>",  # FreeMarker
        ]

        for pattern in template_patterns:
            if re.search(pattern, query_part):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="template_injection",
                    severity="high",
                    confidence=0.70,
                    description="Template injection pattern detected in URL. This could allow attackers to inject template engine code.",
                    evidence=f"URL contains template pattern: {pattern}",
                    cwe_id="CWE-94",
                    cvss_score=8.6,
                    recommendation="Disable template rendering for user input. Sanitize and validate all template parameters. Use context-aware escaping.",
                    url_finding=True,
                ))
                break

        return findings

    def _analyze_dom_injections(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze DOM metadata for injection vectors in forms and scripts."""
        findings = []

        # Analyze forms for injection points
        forms = dom_meta.get("forms", [])
        for form in forms:
            form_action = form.get("action", "")

            # Check for forms with method="GET" that could be used for XSS
            form_method = form.get("method", "").upper()
            if form_method == "GET":
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="get_form_xss",
                    severity="medium",
                    confidence=0.60,
                    description="Form with method=GET detected. GET requests may be susceptible to reflected XSS if parameters are not properly escaped.",
                    evidence=f"Form action: {form_action or 'unknown'} (Method: GET)",
                    cwe_id="CWE-79",
                    cvss_score=6.1,
                    recommendation="Use POST for state-changing operations. Implement server-side input validation and output encoding for reflected parameters.",
                ))

            # Check for text inputs without maxlength or pattern
            inputs = form.get("inputs", [])
            text_inputs = [inp for inp in inputs if inp.get("type") in ("text", "textarea", "search", "url")]

            for inp in text_inputs:
                name = inp.get("name", "")
                if not name or name.lower() in ("search", "q", "query"):
                    continue  # Skip search inputs typically safe

                has_maxlength = inp.get("maxlength")
                has_pattern = inp.get("pattern")

                if not has_maxlength and not has_pattern:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="unvalidated_input_field",
                        severity="low",
                        confidence=0.50,
                        description="Text input field without maxlength or pattern attribute detected. Unbounded input fields may increase injection risk.",
                        evidence=f"Field name: {name or 'unnamed'}",
                        cwe_id="CWE-20",
                        cvss_score=3.1,
                        recommendation="Add maxlength and pattern attributes to input fields. Implement server-side input validation.",
                    ))

        # Analyze scripts for dangerous patterns
        scripts = dom_meta.get("scripts", [])
        for script in scripts:
            script_content = script.get("content", "").lower()

            # Check for dangerous JavaScript patterns
            dangerous_js_patterns = [
                ("innerHTML assignment", r"innerHTML\s*=", 0.75, "high"),
                ("eval() usage", r"eval\s*\(", 0.85, "high"),
                ("document.write()", r"document\.write\s*\(", 0.70, "medium"),
                ("setTimeout with string", r"setTimeout\s*\(\s*['\"]", 0.60, "medium"),
                ("setInterval with string", r"setInterval\s*\(\s*['\"]", 0.60, "medium"),
                ("Function constructor", r"new\s+Function\s*\(", 0.80, "high"),
            ]

            for pattern_name, pattern, confidence, severity in dangerous_js_patterns:
                if re.search(pattern, script_content):
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type=f"dangerous_js_{pattern_name.replace(' ', '_')}",
                        severity=severity,
                        confidence=confidence,
                        description=f"{pattern_name} detected in inline JavaScript. This pattern can lead to DOM-based XSS vulnerabilities if user input is not properly sanitized.",
                        evidence=f"Script contains {pattern_name}",
                        cwe_id="CWE-79",
                        cvss_score=7.5 if severity == "high" else 5.9,
                        recommendation="Avoid dangerous patterns like innerHTML, eval() with user input. Use textContent, createElement, and safe alternatives. Implement input sanitization.",
                    ))

        return findings

    def _analyze_page_injections(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for XSS vectors."""
        findings = []

        # Check for reflected XSS vectors in page content
        # Look for scripts that insert query parameters directly into HTML

        # Pattern: script reading URL query and inserting into DOM
        url_reflection_patterns = [
            r"(?:document\.URL|window\.location\.(?:search|href)|location\.(?:search|href))",
        ]

        page_lower = page_content.lower()
        for pattern in url_reflection_patterns:
            if re.search(pattern, page_lower):
                # Check if the value is being used dangerously (innerHTML, etc)
                dangerous_usage = r"innerHTML|eval|document\.write|\$\(\s*['\"]"
                if re.search(dangerous_usage, page_lower[page_lower.find(pattern):page_lower.find(pattern) + 500]):
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="reflected_xss",
                        severity="high",
                        confidence=0.75,
                        description="Potential reflected XSS vulnerability detected. Page reads URL parameters and may insert them into DOM without sanitization.",
                        evidence=f"URL parameter access pattern: {pattern}",
                        cwe_id="CWE-79",
                        cvss_score=7.5,
                        recommendation="Validate and encode all URL parameters before rendering. Use safe DOM APIs like textContent or escape HTML entities.",
                        url_finding=True,
                    ))
                    break

        # Check for inline event handlers (XSS vectors)
        inline_event_handlers = r"""on\w+\s*=\s*["']"""
        inline_handler_matches = re.finditer(inline_event_handlers, page_content.lower())
        handler_count = sum(1 for _ in inline_handler_matches)

        if handler_count > 5:  # More than 5 inline handlers is suspicious
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="excessive_inline_event_handlers",
                severity="medium",
                confidence=0.65,
                description=f"Excessive inline event handlers detected ({handler_count} found). Inline event handlers can be XSS vectors if they process user input.",
                evidence=f"Inline event handlers found: {handler_count}",
                cwe_id="CWE-79",
                cvss_score=5.4,
                recommendation="Replace inline event handlers (onclick, onload, etc) with event listeners attached in JavaScript. Use CSP with unsafe-inline disabled.",
            ))

        return findings

    def _analyze_headers_injection_protection(self, headers: dict) -> List[SecurityFinding]:
        """Analyze headers for injection protection headers."""
        findings = []

        # Normalize headers to lowercase
        headers_lower = {k.lower(): v for k, v in (headers or {}).items()}

        # Check for missing Content Security Policy (XSS protection)
        if "content-security-policy" not in headers_lower:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_csp",
                severity="high",
                confidence=0.85,
                description="Content Security Policy (CSP) header is missing. CSP helps prevent XSS and injection attacks by restricting script sources.",
                evidence="Content-Security-Policy header not found",
                cwe_id="CWE-693",
                cvss_score=6.8,
                recommendation="Implement Content-Security-Policy header with appropriate directive restrictions (script-src, object-src, default-src",
            ))

        # Check for X-Content-Type-Options (MIME sniffing protection)
        if "x-content-type-options" not in headers_lower:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_xcto",
                severity="low",
                confidence=0.75,
                description="X-Content-Type-Options header is missing. This header prevents MIME-type sniffing which can mitigate some XSS attacks.",
                evidence="X-Content-Type-Options header not found",
                cwe_id="CWE-693",
                cvss_score=3.7,
                recommendation="Set X-Content-Type-Options: nosniff to prevent MIME-type sniffing.",
            ))

        # Check for X-XSS-Protection (legacy but still useful)
        if "x-xss-protection" not in headers_lower:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_xxssp",
                severity="low",
                confidence=0.60,
                description="X-XSS-Protection header is missing. This legacy header provides XSS filtering in some browsers (though CSP is preferred).",
                evidence="X-XSS-Protection header not found",
                cwe_id="CWE-79",
                cvss_score=2.1,
                recommendation="Set X-XSS-Protection: 1; mode=block for legacy browser protection, but prioritize CSP.",
            ))

        return findings

    def _is_url_safe(self, query_part: str) -> bool:
        """Check if URL uses safe URL encoding (percent-encoding)."""
        # Heuristic: if URL uses percent-encoding extensively, it might be safe
        percent_count = query_part.count("%")
        total_length = len(query_part)
        return percent_count / max(total_length, 1) > 0.3
