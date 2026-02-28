"""
OWASP A09: Security Logging Failures Module

Detects logging and monitoring failures including:
- Missing security logging
- Sensitive data in logs
- Insufficient log retention
- Missing intrusion detection
- Debug information leaked to logs

CWE Mappings:
- CWE-778: Insufficient Logging (Low)
- CWE-532: Insertion of Sensitive Information into Log File (Medium)
- CWE-200: Exposure of Sensitive Information (Medium)
- CWE-215: Information Exposure Through Debug Information (Medium)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class LoggingFailuresModule(SecurityModule):
    """
    OWASP A09: Security Logging and Monitoring Failures detection module.

    Analyzes page content and DOM metadata for logging-related
    vulnerabilities including missing audit trails and sensitive
    data exposure through logging.
    """

    # MEDIUM tier for logging analysis
    _default_tier = SecurityTier.MEDIUM
    _default_timeout = 8

    @property
    def category_id(self) -> str:
        return "owasp_a09"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for security logging and monitoring failures.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze page content for logging issues
        if page_content:
            findings.extend(self._analyze_page_logging(page_content))

        # Analyze DOM metadata for logging indicators
        if dom_meta:
            findings.extend(self._analyze_dom_logging(dom_meta))

        # Analyze headers for logging-related indicators
        if headers:
            findings.extend(self._analyze_headers_logging(headers))

        return findings

    def _analyze_page_logging(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for logging-related vulnerabilities."""
        findings = []

        # Check for console.log with sensitive data
        console_patterns = [
            (r"""console\.log\s*\(\s*[\w\.\$]+\s*\.\s*(?:password|token|secret|api_key|session|credit_card|ssn)""", "console.log with sensitive property", 0.80),
            (r"""console\.log\s*\(\s*['"](?:password|token|secret|api_key|auth)[""']""", "console.log with sensitive literal", 0.90),
            (r"""console\.log\s*\(\s*localStorage\s*\.\s*\w+""", "console.log with localStorage", 0.60),
            (r"""console\.log\s*\(\s*sessionStorage\s*\.\s*\w+""", "console.log with sessionStorage", 0.60),
            (r"""console\.log\s*\(\s*document\.cookie""", "console.log with document.cookie", 0.70),
        ]

        page_content_lower = page_content.lower()

        for pattern, description, confidence in console_patterns:
            matches = list(re.finditer(pattern, page_content, re.IGNORECASE))
            for match in matches:
                # Skip if in comment
                match_start = max(0, match.start() - 20)
                context = page_content[match_start:match.start()]
                if any(comment in context for comment in ["<!--", "//", "/*", "#"]):
                    continue

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="sensitive_data_in_logs",
                    severity="medium",
                    confidence=confidence,
                    description=f"{description} detected. Sensitive data logged to browser console may be exposed to users or captured by browser extensions.",
                    evidence=f"Pattern: {description}",
                    cwe_id="CWE-532",
                    cvss_score=5.5,
                    recommendation="Remove console.log statements before production deployment. Use proper logging framework with data sanitization.",
                ))
                break

        # Check for DEBUG configurations in page content
        debug_patterns = [
            r"""DEBUG\s*[:=]\s*true""",
            r"""debug\s*:\s*true""",
            r"""DEBUG\s*=\s*true""",
            r"""logging\s*:\s*['"]debug['"]""",
            r"""log_level\s*:\s*['"]debug['"]""",
            r"""verbosity\s*:\s*(high|debug|verbose)""",
        ]

        for pattern in debug_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="debug_logging_config",
                    severity="medium",
                    confidence=0.70,
                    description="Debug logging configuration found in page content. Debug logging may expose sensitive information in production.",
                    evidence=f"Pattern: {pattern}",
                    cwe_id="CWE-215",
                    cvss_score=5.3,
                    recommendation="Disable debug logging in production. Remove debug configurations from client-side code.",
                ))
                break

        # Check for console.error, console.warn with potential leaks
        error_patterns = [
            r"""console\.(?:error|warn|info)\s*\(\s*[\w\.\$]+\s*\)""",
            r"""console\.(?:error|warn|info)\s*\(\s*['"][^'"]*password[^'"]*['"]""",
        ]

        sensitive_error_found = False
        for pattern in error_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                # Check if it contains sensitive keywords
                matches = list(re.finditer(pattern, page_content, re.IGNORECASE))
                for match in matches:
                    match_text = match.group(0).lower()
                    if any(kw in match_text for kw in ["password", "token", "secret", "api"]):
                        findings.append(SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="sensitive_data_in_error_logs",
                            severity="medium",
                            confidence=0.65,
                            description="Sensitive data potentially logged to console.error/warn. Error logs may expose sensitive information.",
                            evidence="console.error/warn with potentially sensitive data",
                            cwe_id="CWE-532",
                            cvss_score="5.5",
                            recommendation="Sanitize sensitive data before logging errors. Remove sensitive fields from error output.",
                        ))
                        sensitive_error_found = True
                        break
                if sensitive_error_found:
                    break

        # Check for exposed debug information (application state, etc)
        debug_info_patterns = [
            r"""console\.log\s*\(\s*app\s*\)""",
            r"""console\.log\s*\(\s*application\s*\)""",
            r"""console\.log\s*\(\s*state\s*\)""",
            r"""console\.log\s*\(\s*store\s*\)""",
            r"""console\.log\s*\(\s*config\s*\)""",
            r"""console\.log\s*\(\s*debug\s*\)""",
        ]

        debug_info_found = False
        for pattern in debug_info_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="debug_information_leaked",
                    severity="medium",
                    confidence=0.60,
                    description="Application debug information potentially logged. Debug state may expose sensitive application details.",
                    evidence=f"Pattern: {pattern}",
                    cwe_id="CWE-215",
                    cvss_score=4.3,
                    recommendation="Remove debug logging statements from production code. Use proper error handling with sanitized output.",
                ))
                debug_info_found = True
                break

        # Check for detailed error messages in responses
        error_message_indicators = [
            (r"""Exception:\s*\n""", "Exception in response", 0.70),
            (r"""Traceback:\s*\n""", "Traceback in response", 0.85),
            (r"""at\s+[\w.]+(?:\s*\([^)]+\))?\s*\n""", "Stack trace", 0.75),
            (r"""Error:\s*[A-Z]\w+Error""", "Error class name", 0.60),
        ]

        error_found = False
        for pattern, desc, confidence in error_message_indicators:
            if re.search(pattern, page_content):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="detailed_error_message",
                    severity="medium",
                    confidence=confidence,
                    description=f"{desc} detected in page content. Detailed error messages may reveal implementation details.",
                    evidence=f"Pattern: {pattern}",
                    cwe_id="CWE-209",
                    cvss_score=4.3,
                    recommendation="Configure error handlers to show generic error messages to users. Log detailed errors server-side only.",
                ))
                error_found = True
                break

        return findings

    def _analyze_dom_logging(self, dom_meta: dict) -> List[SecurityFinding]:
        """Analyze DOM metadata for logging-related issues."""
        findings = []

        # Check for forms without apparent logging/action tracking
        forms = dom_meta.get("forms", [])

        for form in forms:
            form_action = form.get("action", "")

            # Login/register forms should have logging/tracking
            login_keywords = ["login", "signin", "sign-in", "register", "signup", "sign-up", "auth"]
            if any(kw in form_action.lower() for kw in login_keywords):
                # Check if form has any tracking/analytics attributes (weak indicator)
                form_text = (form_action + " " + str(form.get("inputs", []))).lower()
                has_tracking = any(kw in form_text for kw in ["track", "analytics", "log", "event", "ga", "gtm"])

                # This is a weak finding - just noting potential missing logging
                if not has_tracking:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="potential_missing_auth_logging",
                        severity="low",
                        confidence=0.40,
                        description=f"Authentication form ({form_action}) may lack server-side logging/tracking. Security events like login attempts should be logged.",
                        evidence=f"Form action: {form_action}",
                        cwe_id="CWE-778",
                        cvss_score=3.1,
                        recommendation="Implement server-side logging for authentication events (logins, failed attempts, password changes). Use audit trails.",
                    ))

        return findings

    def _analyze_headers_logging(self, headers: dict) -> List[SecurityFinding]:
        """Analyze headers for logging-related indicators."""
        findings = []

        # Normalize headers to lowercase
        headers_lower = {k.lower(): v for k, v in (headers or {}).items()}

        # Check for server headers that may reveal version (loggable info)
        server = headers_lower.get("server", "")
        if server and re.search(r"/\d+\.\d+", server):
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="server_version_in_header",
                severity="low",
                confidence=0.55,
                description="Server header includes version information. Version disclosure may be logged and aid attackers in targeting specific vulnerabilities.",
                evidence=f"Server header: {server}",
                cwe_id="CWE-200",
                cvss_score=2.5,
                recommendation="Remove or minimize version information from Server header. Use generic values like 'nginx' or 'Apache' in production.",
            ))

        # Check for X-Request-ID or similar correlation headers
        correlation_headers = [
            "x-request-id", "x-correlation-id", "x-trace-id",
            "request-id", "correlation-id", "trace-id",
        ]

        has_correlation = any(h in headers_lower for h in correlation_headers)

        if not has_correlation:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_correlation_header",
                severity="low",
                confidence=0.40,
                description="Request correlation header (X-Request-ID, X-Trace-ID) not found. Correlation IDs help with log tracing and debugging.",
                evidence="No correlation header detected",
                cwe_id="CWE-778",
                cvss_score=2.1,
                recommendation="Consider adding correlation IDs to requests for better log traceability and debugging.",
            ))

        return findings
