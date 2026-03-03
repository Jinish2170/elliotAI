"""
OWASP A04: Insecure Design Module

Detects insecure design flaws including:
- Mass assignment vulnerabilities
- Business logic flaws (race conditions)
- Missing rate limiting
- Improper data isolation
- Sensitive data in URL parameters

CWE Mappings:
- CWE-915: Improperly Controlled Modification of Object (Medium)
- CWE-352: Cross-Site Request Forgery (High)
- CWE-307: Improper Restriction of Excessive Authentication Attempts (Medium)
- CWE-13: Improper Isolation of Shared Resources (High)
- CWE-598: Information Exposure Through GET Request (High)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class InsecureDesignModule(SecurityModule):
    """
    OWASP A04: Insecure Design detection module.

    Analyzes DOM metadata and forms for design flaws including mass assignment,
    missing rate limiting, business logic vulnerabilities, and data isolation issues.
    """

    # DEEP tier for comprehensive design analysis
    _default_tier = SecurityTier.DEEP
    _default_timeout = 15

    @property
    def category_id(self) -> str:
        return "owasp_a04"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for insecure design vulnerabilities.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze URL for sensitive data in parameters
        findings.extend(self._analyze_sensitive_url_params(url))

        # Analyze headers for rate limiting
        if headers:
            findings.extend(self._analyze_rate_limiting(headers))

        # Analyze DOM metadata and forms
        if dom_meta:
            findings.extend(self._analyze_forms_for_design(dom_meta, url))

        # Analyze page content for design issues
        if page_content:
            findings.extend(self._analyze_page_design(page_content))

        return findings

    def _analyze_sensitive_url_params(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for sensitive data in query parameters."""
        findings = []

        # Pattern: URL contains GET parameters with potentially sensitive data
        sensitive_keywords = [
            "email", "password", "pass", "secret", "token", "api_key",
            "credit_card", "ssn", "social_security", "account", "phone",
            "address", "zip", "postal", "dob", "birthdate", "username",
            "user", "session", "auth", "key", "private",
        ]

        if "?" not in url:
            return findings

        query_part = url.split("?")[1].lower()

        # Check for sensitive parameter names
        sensitive_params = []
        for keyword in sensitive_keywords:
            if f"{keyword}=" in query_part:
                sensitive_params.append(keyword)

        if sensitive_params:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="sensitive_data_in_url",
                severity="high",
                confidence=0.80,
                description=f"Sensitive data parameters found in URL query string: {', '.join(sensitive_params)}. URL parameters are logged and can be exposed via browser history, referrer headers, and server logs.",
                evidence=f"Sensitive parameters: {', '.join(sensitive_params)}",
                cwe_id="CWE-598",
                cvss_score=7.5,
                recommendation="Move sensitive data to POST form body or HTTP headers. Use HTTPS to encrypt transit. Avoid placing sensitive information in URLs.",
                url_finding=True,
            ))

        return findings

    def _analyze_rate_limiting(self, headers: dict) -> List[SecurityFinding]:
        """Analyze headers for rate limiting indicators."""
        findings = []

        # Normalize headers to lowercase
        headers_lower = {k.lower(): v for k, v in (headers or {}).items()}

        # Check for rate limiting headers
        rate_limit_headers = [
            "x-rate-limit",
            "ratelimit-limit",
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "rate-limit-remaining",
        ]

        has_rate_limit = any(h in headers_lower for h in rate_limit_headers)

        # Check for other security headers that might indicate rate limiting
        retry_after = headers_lower.get("retry-after")
        has_retry = retry_after is not None

        if not has_rate_limit and not has_retry:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="missing_rate_limiting",
                severity="medium",
                confidence=0.70,
                description="Rate limiting indicators not found in headers. Without rate limiting, endpoints may be vulnerable to brute force attacks and DoS.",
                evidence="No rate limiting headers detected",
                cwe_id="CWE-307",
                cvss_score=6.5,
                recommendation="Implement rate limiting on authentication-sensitive endpoints. Add rate limit headers or retry-after responses.",
            ))

        return findings

    def _analyze_forms_for_design(self, dom_meta: dict, url: str) -> List[SecurityFinding]:
        """Analyze forms for design vulnerabilities."""
        findings = []

        forms = dom_meta.get("forms", [])

        for form in forms:
            form_action = form.get("action", "")
            form_method = form.get("method", "").upper()
            inputs = form.get("inputs", [])

            # Check for mass assignment: too many fields without CSRF protection
            text_inputs = [inp for inp in inputs if inp.get("type") in ("text", "hidden", "number")]

            if text_inputs and form_method in ("POST", "PUT"):
                has_csrf_token = any(
                    any(keyword in inp.get("name", "").lower() for keyword in ["csrf", "_token", "token"])
                    for inp in inputs
                )

                # Mass assignment: many fields + POST + no CSRF
                if len(text_inputs) > 10 and not has_csrf_token:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="potential_mass_assignment",
                        severity="medium",
                        confidence=0.65,
                        description=f"Form with many fields ({len(text_inputs)}) may be vulnerable to mass assignment. Mass assignment allows attackers to set unexpected fields.",
                        evidence=f"Form action: {form_action or 'unknown'} ({len(text_inputs)} input fields)",
                        cwe_id="CWE-915",
                        cvss_score=5.3,
                        recommendation="Implement whitelist of allowed form fields. Use strong parameter patterns. Add CSRF protection.",
                    ))

                # Business logic: state-changing action without CSRF
                state_changing_keywords = ["transfer", "payment", "submit", "update", "delete", "create", "buy", "sell", "withdraw"]
                if any(keyword in form_action.lower() for keyword in state_changing_keywords) and not has_csrf_token:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="business_logic_missing_csrf",
                        severity="high",
                        confidence=0.75,
                        description=f"State-changing form ({form_action}) without CSRF token. This could allow Cross-Site Request Forgery attacks.",
                        evidence=f"Form action: {form_action} (no CSRF token)",
                        cwe_id="CWE-352",
                        cvss_score=7.5,
                        recommendation="Implement CSRF tokens for all state-changing forms. Use same-site cookie attributes.",
                    ))

            # Check for admin actions in customer URLs
            admin_keywords = ["admin", "admin_", "administrator", "superuser", "root", "sudo", "sudo_"]
            if any(keyword in form_action.lower() for keyword in admin_keywords):
                # Check if this might be a customer-facing page with admin references
                url_lower = url.lower()
                customer_keywords = ["customer", "user", "account", "profile", "dashboard"]
                if any(kw in url_lower for kw in customer_keywords):
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="admin_action_in_customer_context",
                        severity="medium",
                        confidence=0.60,
                        description="Admin action detected in customer-facing context. This could indicate improper data isolation between admin and customer resources.",
                        evidence=f"Form action: {form_action}",
                        cwe_id="CWE-13",
                        cvss_score=5.9,
                        recommendation="Ensure proper RBAC and data isolation. Admin and customer resources should be served from separate endpoints with proper authorization.",
                    ))

            # Check for password field without CAPTCHA
            has_password = form.get("has_password", False)
            if not has_password:
                has_password = any(inp.get("type") == "password" for inp in inputs)

            if has_password:
                # Check for CAPTCHA
                form_text = (form_action + " " + str(inputs)).lower()
                has_captcha = any(
                    captcha in form_text
                    for captcha in ["recaptcha", "hcaptcha", "captcha", "turnstile", "2fa", "mfa"]
                )

                if not has_captcha:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="password_form_no_rate_limit",
                        severity="medium",
                        confidence=0.55,
                        description="Password form detected without visible CAPTCHA. Without rate limiting or CAPTCHA, forms may be vulnerable to brute force attacks.",
                        evidence=f"Form action: {form_action or 'unknown'}",
                        cwe_id="CWE-307",
                        cvss_score=6.5,
                        recommendation="Implement CAPTCHA or strict rate limiting on authentication forms. Enable account lockout after failed attempts.",
                    ))

        return findings

    def _analyze_page_design(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for design-related vulnerabilities."""
        findings = []

        # Pattern: Check for hidden form fields with sensitive names
        hidden_input_pattern = r"""<input[^>]*type\s*=\s*['"]hidden['"][^>]*name\s*=\s*['"](user_|admin_|role_|email_)"""
        hidden_matches = re.findall(hidden_input_pattern, page_content, re.IGNORECASE)

        if hidden_matches:
            sensitive_hidden = [m for m in hidden_matches if m not in ["user_", "admin_"]]  # Filter out generic prefixes
            if sensitive_hidden:
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="sensitive_hidden_input",
                    severity="medium",
                    confidence=0.70,
                    description="Hidden form fields with sensitive names detected. Hidden fields can be modified by users before submission.",
                    evidence=f"Hidden field names: {', '.join(sensitive_hidden[:3])}",
                    cwe_id="CWE-915",
                    cvss_score=5.5,
                    recommendation="Avoid hidden fields for security-critical data. Store sensitive state server-side with session management.",
                ))

        # Pattern: Check for direct database or API calls in client code
        api_call_patterns = [
            r"""fetch\s*\(\s*['"]\s*/api/(user|account|admin)""",
            r"""axios\.(?:get|post|put|delete)\s*\(\s*['"]\s*/api/(user|account|admin)""",
            r"""\.then\s*\(\s*resp\s*=>\s*resp\.(user|email|profile|admin)""",
        ]

        for pattern in api_call_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="client_side_api_calls_to_sensitive_data",
                    severity="medium",
                    confidence=0.60,
                    description="Client-side API calls to sensitive endpoints detected. Ensure proper server-side authorization and input validation.",
                    evidence=f"Pattern: {pattern[:50]}...",
                    cwe_id="CWE-285",
                    cvss_score=5.5,
                    recommendation="Implement proper server-side authorization checks. Validate and sanitize all API requests. Use JWT with proper scopes.",
                ))
                break  # One finding is sufficient

        # Pattern: Check for business logic flows exposed in JavaScript
        business_logic_patterns = [
            r"""if\s*\(.*?role\s*==\s*['"]admin['"]""",
            r"""if\s*\(.*?isAdmin\s*===\s*true""",
            r"""user\.admin\s*===\s*true""",
            r"""user\.role\s*===\s*['"]admin['"]""",
        ]

        client_side_logic_found = False
        for pattern in business_logic_patterns:
            if re.search(pattern, page_content, re.IGNORECASE):
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="client_side_business_logic",
                    severity="medium",
                    confidence=0.65,
                    description="Client-side role or authorization checks detected. Client-side logic can be bypassed; perform authorization checks server-side.",
                    evidence=f"Pattern: {pattern}",
                    cwe_id="CWE-285",
                    cvss_score=6.5,
                    recommendation="Move all authorization logic to server-side. Never trust client-side values for security decisions.",
                ))
                client_side_logic_found = True
                break

        return findings
