"""
OWASP A07: Authentication Failures Module

Detects authentication failures including:
- Weak password policies
- Password autocomplete issues
- Session fixation vulnerabilities
- Unprotected redirect chains
- Missing CAPTCHA on login
- Insecure password recovery

CWE Mappings:
- CWE-522: Insufficiently Protected Credentials (Low)
- CWE-521: Weak Password Requirements (Medium)
- CWE-384: Session Fixation (High)
- CWE-601: URL Redirection to Untrusted Site (High)
- CWE-640: Weak Password Recovery (Medium)
- CWE-795: Use of CAPTCHA Without Rate Limiting (Medium)
"""

import re
from typing import List, Optional

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier


class AuthenticationFailuresModule(SecurityModule):
    """
    OWASP A07: Authentication Failures detection module.

    Analyzes forms, URLs, and page content for authentication-related
    vulnerabilities including weak password policies, session fixation,
    and unprotected redirects.
    """

    # DEEP tier for comprehensive authentication analysis
    _default_tier = SecurityTier.DEEP
    _default_timeout = 15

    @property
    def category_id(self) -> str:
        return "owasp_a07"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze for authentication failures.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers
            dom_meta: Optional DOM metadata from Scout

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # Analyze URL for session fixation indicators
        findings.extend(self._analyze_session_fixation(url))

        # Analyze forms for authentication issues
        if dom_meta:
            findings.extend(self._analyze_auth_forms(dom_meta, url))

        # Analyze page content for authentication issues
        if page_content:
            findings.extend(self._analyze_page_auth(page_content))

        # Analyze headers for authentication headers
        if headers:
            findings.extend(self._analyze_auth_headers(headers))

        return findings

    def _analyze_session_fixation(self, url: str) -> List[SecurityFinding]:
        """Analyze URL for session fixation indicators."""
        findings = []

        # Session fixation: session ID in URL
        session_params = [
            "session_id", "sessionid", "sid", "jsessionid",
            "phpsessid", "phpsess_id", "session", "sessid",
        ]

        if "?" in url:
            query_part = url.split("?")[1].lower()
            param_found = False
            for param in session_params:
                if f"{param}=" in query_part:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="session_id_in_url",
                        severity="high",
                        confidence=0.80,
                        description=f"Session ID parameter found in URL: {param}. Session fixation vulnerability may allow attackers to hijack user sessions.",
                        evidence=f"URL contains: {param}=...",
                        cwe_id="CWE-384",
                        cvss_score=7.5,
                        recommendation="Don't pass session IDs in URLs. Use HttpOnly, Secure cookies. Regenerate session ID after login.",
                        url_finding=True,
                    ))
                    param_found = True
                    break

        return findings

    def _analyze_auth_forms(self, dom_meta: dict, url: str) -> List[SecurityFinding]:
        """Analyze forms for authentication-related vulnerabilities."""
        findings = []

        forms = dom_meta.get("forms", [])

        # Identify login forms
        for form in forms:
            form_action = form.get("action", "").lower()
            form_method = form.get("method", "").upper()
            inputs = form.get("inputs", [])

            # Identify this is likely a login form
            has_password = form.get("has_password", False)
            if not has_password:
                has_password = any(inp.get("type") == "password" for inp in inputs)

            # Check for login-specific indicators
            login_keywords = ["login", "signin", "sign-in", "auth", "authenticate", "log-in"]
            is_login_form = (has_password and
                            any(kw in form_action for kw in login_keywords) or
                            any(kw in url.lower() for kw in login_keywords))

            if is_login_form:
                # Check password field for autocomplete
                password_inputs = [inp for inp in inputs if inp.get("type") == "password"]
                for pwd in password_inputs:
                    autocomplete = pwd.get("autocomplete", "").lower()
                    if autocomplete not in ("off", "new-password"):
                        findings.append(SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="password_autocomplete",
                            severity="low",
                            confidence=0.55,
                            description="Login password field does not have autocomplete disabled. Stored passwords in browser may be a security risk.",
                            evidence=f"Password field autocomplete: {autocomplete or 'not specified'}",
                            cwe_id="CWE-522",
                            cvss_score=2.8,
                            recommendation="Set autocomplete='off' or autocomplete='new-password' on login password fields.",
                        ))

                # Check password constraints
                # Look for validation hints on password input
                password_has_constraints = False
                password_input = password_inputs[0] if password_inputs else {}
                if password_input:
                    # Check for validation attributes
                    has_minlength = password_input.get("minlength")
                    has_pattern = password_input.get("pattern")
                    password_has_constraints = has_minlength or has_pattern

                if not password_has_constraints:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="weak_password_policy",
                        severity="medium",
                        confidence=0.60,
                        description="Login form password field without visible constraint indicators (minlength, pattern). Weak password policies allow easily guessable passwords.",
                        evidence="Password field has no minlength or pattern constraints",
                        cwe_id="CWE-521",
                        cvss_score=5.5,
                        recommendation="Implement strong password policy (minimum 8 characters, mix of character types) with client and server-side validation.",
                    ))

                # Check for CAPTCHA on login
                form_text = (form_action + " " + str(inputs)).lower()
                has_captcha = any(
                    captcha in form_text
                    for captcha in ["recaptcha", "hcaptcha", "captcha", "turnstile", "2fa", "mfa", "g-recaptcha"]
                )

                if not has_captcha:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="login_no_captcha",
                        severity="medium",
                        confidence=0.50,
                        description="Login form detected without visible CAPTCHA. Without CAPTCHA, login forms may be vulnerable to brute force attacks.",
                        evidence="No CAPTCHA indicators found on login form",
                        cwe_id="CWE-795",
                        cvss_score=6.5,
                        recommendation="Implement CAPTCHA or rate limiting on login forms. Enable account lockout after failed attempts.",
                    ))

                # Check for CSRF token protection on login
                has_csrf_token = any(
                    any(keyword in inp.get("name", "").lower() for keyword in ["csrf", "_token", "token"])
                    for inp in inputs
                    if inp.get("type") in ("hidden", "")
                )

                if not has_csrf_token:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="login_missing_csrf_token",
                        severity="medium",
                        confidence=0.65,
                        description="Login form does not have visible CSRF token protection. Login CSRF attacks can force users into unwanted authentication.",
                        evidence="Login form without CSRF token",
                        cwe_id="CWE-352",
                        cvss_score=6.5,
                        recommendation="Implement CSRF tokens for login forms. Use same-site cookie attributes.",
                    ))

            # Check for password recovery forms
            pwd_recovery_keywords = ["recovery", "reset", "forgot", "recover", "change_password", "reset-password"]
            is_pwd_recovery = (has_password and
                               any(kw in form_action for kw in pwd_recovery_keywords) or
                               any(kw in url.lower() for kw in pwd_recovery_keywords))

            if is_pwd_recovery:
                # Check for email-based recovery without secondary verification
                email_input = any(inp.get("type") == "email" for inp in inputs)
                text_inputs = [inp for inp in inputs if inp.get("type") in ("text", "email")]

                # Simple email-only recovery is weak
                if email_input and len(text_inputs) == 1:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="weak_password_recovery",
                        severity="medium",
                        confidence=0.60,
                        description="Password recovery form uses single email verification. Consider adding secondary verification (2FA, security questions, token).",
                        evidence=f"Password recovery form: {form_action or 'unknown'}",
                        cwe_id="CWE-640",
                        cvss_score="5.8",
                        recommendation="Implement multi-factor authentication for password recovery. Add token-based verification with time limits.",
                    ))

            # Check for unprotected redirects (open redirect)
            if form_action and ("http://" in form_action or "https://" in form_action):
                # Check if action is external to the current domain
                parsed_url = url.split("/")[2] if len(url.split("/")) > 2 else ""
                if parsed_url and parsed_url not in form_action:
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="unprotected_redirect",
                        severity="high",
                        confidence=0.70,
                        description=f"Form action points to external domain: {form_action}. Unprotected redirects may allow phishing attacks.",
                        evidence=f"Form action: {form_action}",
                        cwe_id="CWE-601",
                        cvss_score=7.5,
                        recommendation="Validate redirect URLs against a whitelist. Use relative URLs or tokens for redirect protection.",
                    ))

            # Check for forms with GET method that may be vulnerable
            if form_method == "GET" and has_password:
                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="password_form_get_method",
                    severity="medium",
                    confidence=0.75,
                    description="Password submission form uses GET method. Passwords may be logged in URL history and server logs.",
                    evidence=f"Form uses GET method with password field",
                    cwe_id="CWE-598",
                    cvss_score="6.5",
                    recommendation="Use POST method for password forms. Never send passwords in URL parameters.",
                ))

        return findings

    def _analyze_page_auth(self, page_content: str) -> List[SecurityFinding]:
        """Analyze page content for authentication issues."""
        findings = []

        # Check for secret questions in HTML (weak authentication)
        secret_question_patterns = [
            r"""['"]question['"]\s*[:=]\s*['"]""",
            r"""['"]secret_question['"]\s*[:=]""",
            r"""['"]answer['"]\s*[:=]\s*['"]""",
            r"""['"]secret_answer['"]\s*[:=]""",
        ]

        page_lower = page_content.lower()
        has_question = False
        has_answer = False

        for pattern in secret_question_patterns:
            if re.search(pattern, page_lower):
                has_question = True
                break

        answer_pattern = r"""secret_answer['"]\s*[:=]"""
        if re.search(answer_pattern, page_lower):
            has_answer = True

        if has_question and has_answer:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="secret_questions_in_use",
                severity="medium",
                confidence=0.60,
                description="Secret question/answer mechanism detected. Secret questions are a weak form of secondary verification due to social engineering vulnerability.",
                evidence="Secret question/answer fields detected in page content",
                cwe_id="CWE-306",
                cvss_score="5.3",
                recommendation="Replace secret questions with multi-factor authentication (2FA/MFA) or time-based one-time passwords (TOTP).",
            ))

        # Check for hardcoded credentials in comments or code
        hardcoded_patterns = [
            r"""['"]admin['"]\s*[:=]\s*['"]admin['"]""",
            r"""['"]password['"]\s*[:=]\s*['"](?:password|admin|root)[-'"]""",
        ]

        for pattern in hardcoded_patterns:
            matches = re.finditer(pattern, page_content, re.IGNORECASE)
            for match in matches:
                # Check if it's in a comment
                match_start = max(0, match.start() - 20)
                context = page_content[match_start:match.start()]
                if any(comment not in context for comment in ["<!--", "//", "/*", "#"]):
                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="hardcoded_auth_credentials",
                        severity="critical",
                        confidence=0.85,
                        description="Hardcoded credentials found. Hardcoded auth credentials can be extracted by anyone viewing the source.",
                        evidence=f"Pattern: {pattern}",
                        cwe_id="CWE-798",
                        cvss_score=9.8,
                        recommendation="Remove all hardcoded credentials. Use environment variables or secret management services.",
                    ))
                    break

        return findings

    def _analyze_auth_headers(self, headers: dict) -> List[SecurityFinding]:
        """Analyze headers for authentication-related indicators."""
        findings = []

        # Normalize headers to lowercase
        headers_lower = {k.lower(): v for k, v in (headers or {}).items()}

        # Check for WWW-Authenticate header for failed auth attempts
        www_auth = headers_lower.get("www-authenticate", "")
        if www_auth:
            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="www_authenticate_header_found",
                severity="low",
                confidence=0.50,
                description="WWW-Authenticate header found. This indicates authentication is required for this resource.",
                evidence=f"WWW-Authenticate: {www_auth}",
                cwe_id="CWE-287",
                cvss_score=2.1,
                recommendation="Ensure proper authentication flow. 401 responses should include WWW-Authenticate header.",
            ))

        return findings
