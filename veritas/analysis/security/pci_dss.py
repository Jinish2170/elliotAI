"""
PCI DSS Compliance Module - Payment Card Industry Data Security Standard 3.2.1

Checks for PCI DSS compliance violations in web applications:
    - Req 3.3: Mask PAN (Primary Account Number) when displayed
    - Req 3.4: Encrypt PAN when stored at rest
    - Req 4.1: Encrypt transmission of cardholder data over open networks
    - Req 6.5.1: SQL injection protection
    - Req 8.2: Strong authentication requirements

This module only reports findings when payment-related forms are detected.
"""

import logging
import re
from typing import List, Optional, Dict, Any

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier
from veritas.cwe.cvss_calculator import cvss_calculate_score, PRESET_METRICS
from veritas.cwe.registry import map_finding_to_cwe

logger = logging.getLogger("veritas.analysis.security.pci_dss")


# PCI DSS Requirements and CWE Mappings
_PCI_DSS_REQUIREMENTS = {
    "3.3": {
        "name": "Mask PAN when displayed",
        "cwe_id": "CWE-359",
        "description": "Primary Account Number (credit card) displayed without masking"
    },
    "3.4": {
        "name": "Encrypt PAN at rest",
        "cwe_id": "CWE-311",
        "description": "Forms collecting full credit card numbers without encryption indicator"
    },
    "4.1": {
        "name": "Encrypt transmission over open networks",
        "cwe_id": "CWE-319",
        "description": "Payment forms submitted over HTTP (not HTTPS)"
    },
    "6.5.1": {
        "name": "SQL injection protection",
        "cwe_id": "CWE-89",
        "description": "Payment-related forms without input validation indicators"
    },
    "8.2": {
        "name": "Strong authentication",
        "cwe_id": "CWE-521",
        "description": "Payment flows with weak password requirements"
    }
}


class PCIDSSComplianceModule(SecurityModule):
    """
    PCI DSS 3.2.1 compliance security module.

    Analyzes web pages for PCI DSS compliance violations, focusing on:
        - Credit card number exposure (unmasked display)
        - Unencrypted credit card storage indicators
        - HTTP transmission of payment data
        - SQL injection risks in payment forms
        - Weak authentication in payment flows

    Only reports findings when payment-related forms are detected to avoid
    false positives on non-payment pages.

    Tier: MEDIUM (timeout: 12 seconds)
    Category: pci_dss
    """

    _default_timeout: int = 12
    _default_tier: SecurityTier = SecurityTier.MEDIUM

    @property
    def category_id(self) -> str:
        """Module category identifier."""
        return "pci_dss"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze a URL for PCI DSS compliance violations.

        Args:
            url: Target URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers dict
            dom_meta: Optional DOM metadata (forms, page_content, etc.)

        Returns:
            List of SecurityFinding objects (empty if no issues found)
        """
        findings = []

        try:
            # Normalize headers to lowercase for HTTP RFC 7230 compliance
            normalized_headers = {
                k.lower(): v for k, v in (headers or {}).items()
            } if headers else {}

            # Check if payment-related forms are present
            has_payment_forms = self._detect_payment_forms(dom_meta)

            if not has_payment_forms:
                # No payment forms detected, return empty findings
                logger.debug("No payment forms detected, skipping PCI DSS checks")
                return findings

            # Check PCI DSS Requirement 3.3: Mask PAN when displayed
            findings.extend(self._check_req_3_3(url, page_content, has_payment_forms))

            # Check PCI DSS Requirement 3.4: Encrypt PAN at rest
            findings.extend(self._check_req_3_4(dom_meta))

            # Check PCI DSS Requirement 4.1: Encrypt transmission over open networks
            findings.extend(self._check_req_4_1(url, dom_meta))

            # Check PCI DSS Requirement 6.5.1: SQL injection protection
            findings.extend(self._check_req_6_5_1(dom_meta))

            # Check PCI DSS Requirement 8.2: Strong authentication
            findings.extend(self._check_req_8_2(dom_meta))

        except Exception as e:
            logger.error(f"PCI DSS analysis failed for {url}: {e}", exc_info=True)

        return findings

    def _detect_payment_forms(self, dom_meta: Optional[dict]) -> bool:
        """
        Detect if payment-related forms are present on the page.

        Args:
            dom_meta: Optional DOM metadata containing form information

        Returns:
            True if payment-related forms detected, False otherwise
        """
        if not dom_meta:
            return False

        # Check forms in dom_meta
        forms = dom_meta.get("forms", [])
        page_content = dom_meta.get("page_content", "")

        # Payment-related keywords
        payment_keywords = [
            "creditcard", "credit_card", "cc-number", "ccnumber", "card number",
            "card_number", "cardnumber", "cc-exp", "ccexp", "card expiration",
            "card-exp", "cvv", "cvc", "security code", "card_verification",
            "card-verification", "paymentmethod", "payment_method", "cardtype"
        ]

        # Check form attributes
        for form in forms:
            action = form.get("action", "").lower()
            # Check form action for payment-related URLs
            if any(kw in action for kw in payment_keywords):
                return True

            # Check form inputs
            inputs = form.get("inputs", [])
            for inp in inputs:
                name = inp.get("name", "").lower()
                inp_id = inp.get("id", "").lower()
                placeholder = inp.get("placeholder", "").lower()
                autocomplete = inp.get("autocomplete", "").lower()

                # Combine all input attributes for keyword search
                input_text = f"{name} {inp_id} {placeholder} {autocomplete}"

                if any(kw in input_text for kw in payment_keywords):
                    return True

        # Also check page content for payment-related text
        page_lower = page_content.lower() if page_content else ""
        payment_text_patterns = [
            "credit card", "card number", "cardholder", "payment information",
            "billing information", "checkout", "pay now"
        ]
        if any(pattern in page_lower for pattern in payment_text_patterns):
            # Still need form confirmation to avoid false positives
            if forms:
                return True

        return False

    def _check_req_3_3(
        self,
        url: str,
        page_content: Optional[str],
        has_payment_forms: bool,
    ) -> List[SecurityFinding]:
        """
        PCI DSS Requirement 3.3: Mask PAN when displayed.

        Search for unmasked credit card numbers in page content.
        Masked format: **** **** **** 1234 or XXXX XXXX XXXX 1234

        Args:
            url: Target URL
            page_content: HTML page content
            has_payment_forms: Whether payment forms were detected

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        if not page_content:
            return findings

        # Credit card patterns (16 digits, with or without spaces/dashes)
        # This includes: 1234567812345678, 1234-5678-1234-5678, 1234 5678 1234 5678
        cc_patterns = [
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Full 16-digit card
            r'\b\d{16}\b',  # 16 consecutive digits
        ]

        # Masked patterns to exclude (**** **** **** 1234, XXXX XXXX XXXX 1234)
        masked_patterns = [
            r'[*]{4}[- ]?[*]{4}[- ]?[*]{4}[- ]?\d{4}',
            r'[X]{4}[- ]?[X]{4}[- ]?[X]{4}[- ]?\d{4}',
        ]

        for cc_pattern in cc_patterns:
            matches = re.finditer(cc_pattern, page_content)
            for match in matches:
                matched_number = match.group()

                # Check if it's already masked
                is_masked = any(
                    re.search(masked, matched_number)
                    for masked in masked_patterns
                )

                if is_masked:
                    continue

                # Check if this looks like a real credit card (Luhn check would be more accurate)
                # For now, use confidence based on payment forms presence
                confidence = 0.70 if has_payment_forms else 0.40

                # Calculate CVSS score for this severity
                cvss_score = cvss_calculate_score(PRESET_METRICS["high_risk"])

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="pan_exposed_unmasked",
                    severity="high",
                    confidence=confidence,
                    description=f"{_PCI_DSS_REQUIREMENTS['3.3']['description']}",
                    evidence=f"Potential unmasked PAN detected: {matched_number[:8]}... on {url}",
                    cwe_id=_PCI_DSS_REQUIREMENTS["3.3"]["cwe_id"],
                    cvss_score=cvss_score,
                    recommendation="Display only the last 4 digits of credit card numbers (e.g., **** **** **** 1234)"
                ))

                # Only report one finding per requirement to avoid flooding
                if findings:
                    break

        return findings

    def _check_req_3_4(self, dom_meta: Optional[dict]) -> List[SecurityFinding]:
        """
        PCI DSS Requirement 3.4: Encrypt PAN at rest.

        Check for forms asking for full credit card numbers without encryption indicators.

        Args:
            dom_meta: Optional DOM metadata

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        if not dom_meta:
            return findings

        forms = dom_meta.get("forms", [])

        for form in forms:
            inputs = form.get("inputs", [])

            for inp in inputs:
                inp_type = inp.get("type", "")
                name = inp.get("name", "").lower()
                inp_id = inp.get("id", "").lower()
                placeholder = inp.get("placeholder", "").lower()

                # Look for full credit card number inputs
                credit_card_names = [
                    "cc", "card", "creditcard", "credit_card", "cardnumber",
                    "card_number", "ccnumber", "cc-number", "creditcardnumber"
                ]

                is_cc_input = any(cc_name in name or cc_name in inp_id or cc_name in placeholder
                                  for cc_name in credit_card_names)

                if is_cc_input:
                    # Check for encryption indicators (data-encrypt, aria-label mentioning encryption)
                    data_encrypt = inp.get("data-encrypt", "")
                    aria_label = inp.get("aria-label", "").lower()
                    aria_description = inp.get("aria-describedby", "")

                    has_encryption_indicator = (
                        "encrypt" in data_encrypt.lower() or
                        "encrypt" in aria_label or
                        "encrypt" in aria_description or
                        "secure" in aria_label
                    )

                    if not has_encryption_indicator:
                        # Calculate CVSS score
                        cvss_score = cvss_calculate_score(PRESET_METRICS["high_risk"])

                        findings.append(SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="pan_stored_unencrypted",
                            severity="high",
                            confidence=0.60,
                            description=f"{_PCI_DSS_REQUIREMENTS['3.4']['description']}",
                            evidence=f"Credit card input '{name or inp_id}' without encryption indicator",
                            cwe_id=_PCI_DSS_REQUIREMENTS["3.4"]["cwe_id"],
                            cvss_score=cvss_score,
                            recommendation="Add data-encrypt='true' attribute or clear aria-label indicating encryption at rest"
                        ))

                        # Only report one finding per form
                        break

            if findings:
                break

        return findings

    def _check_req_4_1(self, url: str, dom_meta: Optional[dict]) -> List[SecurityFinding]:
        """
        PCI DSS Requirement 4.1: Encrypt transmission over open networks.

        Check for payment forms submitted over HTTP (not HTTPS).

        Args:
            url: Target URL
            dom_meta: Optional DOM metadata

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        if not dom_meta:
            return findings

        forms = dom_meta.get("forms", [])

        # Check if the page itself is HTTP
        is_http = not url.startswith("https://")

        for form in forms:
            action = form.get("action", "")

            if not action:
                # Form submits to same page as form
                if is_http:
                    cvss_score = cvss_calculate_score(PRESET_METRICS["critical_web"])

                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="payment_over_http",
                        severity="critical",
                        confidence=0.90,
                        description=f"{_PCI_DSS_REQUIREMENTS['4.1']['description']}",
                        evidence=f"Payment form on HTTP page: {url}",
                        cwe_id=_PCI_DSS_REQUIREMENTS["4.1"]["cwe_id"],
                        cvss_score=cvss_score,
                        recommendation="Serve all payment-related pages over HTTPS with a valid TLS certificate"
                    ))
                    break
                continue

            # Check if form action is HTTP (not HTTPS)
            if action.startswith("http://") and not action.startswith("https://"):
                cvss_score = cvss_calculate_score(PRESET_METRICS["critical_web"])

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="payment_over_http",
                    severity="critical",
                    confidence=0.90,
                    description=f"{_PCI_DSS_REQUIREMENTS['4.1']['description']}",
                    evidence=f"Payment form submits to HTTP endpoint: {action}",
                    cwe_id=_PCI_DSS_REQUIREMENTS["4.1"]["cwe_id"],
                    cvss_score=cvss_score,
                    recommendation="Ensure all payment form actions use HTTPS: "
                                 f"{action.replace('http://', 'https://', 1)}"
                ))
                break

            if findings:
                break

        return findings

    def _check_req_6_5_1(self, dom_meta: Optional[dict]) -> List[SecurityFinding]:
        """
        PCI DSS Requirement 6.5.1: SQL injection protection.

        Check for payment-related forms without input validation indicators.

        Args:
            dom_meta: Optional DOM metadata

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        if not dom_meta:
            return findings

        forms = dom_meta.get("forms", [])

        for form in forms:
            inputs = form.get("inputs", [])
            payment_inputs = []

            # Identify payment-related inputs
            for inp in inputs:
                inn_type = inp.get("type", "")
                name = inp.get("name", "").lower()
                inp_id = inp.get("id", "").lower()
                placeholder = inp.get("placeholder", "").lower()

                credit_card_names = [
                    "cc", "card", "creditcard", "credit_card", "cardnumber",
                    "card_number", "ccnumber", "cvv", "cvc", "expiration"
                ]

                if any(cc_name in name or cc_name in inp_id or cc_name in placeholder
                       for cc_name in credit_card_names):
                    payment_inputs.append(inp)

            if not payment_inputs:
                continue

            # Check for input validation indicators
            has_validation = False
            for inp in payment_inputs:
                # Check for pattern attribute (regex validation)
                if inp.get("pattern"):
                    has_validation = True
                    break

                # Check for maxlength attribute
                if inp.get("maxlength"):
                    has_validation = True
                    break

                # Check for type="number" or type="tel" (numeric inputs)
                if inp.get("type") in ["number", "tel"]:
                    has_validation = True
                    break

            if not has_validation:
                # Lower confidence as this requires OWASP A03 for confirmation
                cvss_score = cvss_calculate_score(PRESET_METRICS["critical_web"])

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="sql_injection_risk_payment",
                    severity="critical",
                    confidence=0.50,
                    description=f"{_PCI_DSS_REQUIREMENTS['6.5.1']['description']}",
                    evidence=f"Payment form found with inputs lacking validation indicators "
                             f"(pattern, maxlength, numeric type)",
                    cwe_id=_PCI_DSS_REQUIREMENTS["6.5.1"]["cwe_id"],
                    cvss_score=cvss_score,
                    recommendation="Add input validation (pattern attribute, maxlength) "
                                 "and server-side parameterized queries; confirm with OWASP A03 scan"
                ))
                break

        return findings

    def _check_req_8_2(self, dom_meta: Optional[dict]) -> List[SecurityFinding]:
        """
        PCI DSS Requirement 8.2: Strong authentication.

        Check for payment flows with weak password requirements.

        Args:
            dom_meta: Optional DOM metadata

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        if not dom_meta:
            return findings

        forms = dom_meta.get("forms", [])

        for form in forms:
            inputs = form.get("inputs", [])

            # Find password fields
            password_inputs = [
                inp for inp in inputs
                if inp.get("type", "") == "password" or
                   "password" in inp.get("name", "").lower() or
                   "password" in inp.get("id", "").lower()
            ]

            if not password_inputs:
                continue

            # Check password requirements
            for pwd_input in password_inputs:
                name = pwd_input.get("name", "")
                inp_id = pwd_input.get("id", "")

                # Check for strength indicators
                has_minlength = pwd_input.get("minlength")
                has_pattern = pwd_input.get("pattern")
                autocomplete = pwd_input.get("autocomplete", "")

                # Check if autocomplete is set to new-password or current-password
                has_autocomplete = autocomplete in ["new-password", "current-password"]

                # Weak password detection
                is_weak = not (has_minlength or has_pattern or has_autocomplete)

                if is_weak:
                    cvss_score = cvss_calculate_score(PRESET_METRICS["high_risk"])

                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="weak_auth_payment",
                        severity="medium",
                        confidence=0.60,
                        description=f"{_PCI_DSS_REQUIREMENTS['8.2']['description']}",
                        evidence=f"Password field '{name or inp_id}' lacks strength requirements "
                                 f"(no minlength, pattern, or autocomplete='new-password')",
                        cwe_id=_PCI_DSS_REQUIREMENTS["8.2"]["cwe_id"],
                        cvss_score=cvss_score,
                        recommendation="Add minlength='8', pattern attribute for complexity, "
                                     "and autocomplete='new-password' for new passwords"
                    ))
                    break

            if findings:
                break

        return findings
