"""
GDPR Compliance Module - General Data Protection Regulation (Articles 7, 17, 25, 32, 35)

Checks for GDPR compliance violations in web applications:
    - Art. 7: Consent requirements (freely given, specific, informed, unambiguous)
    - Art. 17: Right to erasure (data deletion mechanism)
    - Art. 25: Privacy by design and by default (no pre-checked consent)
    - Art. 32: Security of processing (encryption, access controls, security headers)
    - Art. 35: Data Protection Impact Assessment (DPIA) for high-risk processing

This module only reports findings when data collection is detected.
"""

import logging
import re
from typing import List, Optional, Dict, Any

from veritas.analysis.security.base import SecurityModule, SecurityFinding, SecurityTier
from veritas.cwe.cvss_calculator import cvss_calculate_score, PRESET_METRICS
from veritas.cwe.registry import map_finding_to_cwe

logger = logging.getLogger("veritas.analysis.security.gdpr")


# GDPR Articles and CWE Mappings
_GDPR_ARTICLES = {
    "7": {
        "name": "Consent requirements",
        "cwe_id": "CWE-359",
        "description": "Data collection without explicit consent mechanism"
    },
    "17": {
        "name": "Right to erasure",
        "cwe_id": "CWE-200",
        "description": "No data deletion/account deletion mechanism visible"
    },
    "25": {
        "name": "Privacy by design and by default",
        "cwe_id": "CWE-359",
        "description": "Pre-checked consent checkboxes (not privacy by default)"
    },
    "32": {
        "name": "Security of processing",
        "cwe_id": "CWE-319",
        "description": "Missing security headers for data protection"
    },
    "35": {
        "name": "Data Protection Impact Assessment (DPIA)",
        "cwe_id": "CWE-200",
        "description": "High-risk data processing without DPIA indicators"
    }
}


class GDPRComplianceModule(SecurityModule):
    """
    GDPR Articles 7, 17, 25, 32, 35 compliance security module.

    Analyzes web pages for GDPR compliance violations, focusing on:
        - Data collection without explicit consent (Art. 7)
        - Missing right to erasure mechanism (Art. 17)
        - Pre-checked consent options (Art. 25 - privacy by default)
        - Insufficient security headers (Art. 32)
        - High-risk processing without DPIA (Art. 35)

    Only reports findings when data collection is detected to avoid
    false positives on pages that don't collect personal data.

    Tier: MEDIUM (timeout: 12 seconds)
    Category: gdpr
    """

    _default_timeout: int = 12
    _default_tier: SecurityTier = SecurityTier.MEDIUM

    @property
    def category_id(self) -> str:
        """Module category identifier."""
        return "gdpr"

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
    ) -> List[SecurityFinding]:
        """
        Analyze a URL for GDPR compliance violations.

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

            # Check if data collection is present
            has_data_collection = self._detect_data_collection(dom_meta, page_content)

            if not has_data_collection:
                # No data collection detected, return empty findings
                logger.debug("No data collection detected, skipping GDPR checks")
                return findings

            # Check GDPR Art. 7: Consent requirements
            findings.extend(self._check_article_7(dom_meta))

            # Check GDPR Art. 17: Right to erasure
            findings.extend(self._check_article_17(dom_meta, url))

            # Check GDPR Art. 25: Privacy by design and by default (pre-checked consent)
            findings.extend(self._check_article_25(dom_meta))

            # Check GDPR Art. 32: Security of processing
            findings.extend(self._check_article_32(normalized_headers, url))

            # Check GDPR Art. 35: Data Protection Impact Assessment (DPIA)
            findings.extend(self._check_article_35(dom_meta, page_content, url))

        except Exception as e:
            logger.error(f"GDPR analysis failed for {url}: {e}", exc_info=True)

        return findings

    def _detect_data_collection(
        self,
        dom_meta: Optional[dict],
        page_content: Optional[str]
    ) -> bool:
        """
        Detect if data collection is present on the page.

        Args:
            dom_meta: Optional DOM metadata
            page_content: Optional HTML page content

        Returns:
            True if data collection detected, False otherwise
        """
        if not dom_meta:
            return False

        forms = dom_meta.get("forms", [])

        # Check for data collection in forms
        data_collection_fields = [
            "email", "name", "first_name", "lastname", "last_name", "full_name",
            "phone", "mobile", "telephone", "address", "zip", "postal",
            "date_of_birth", "dob", "birthdate", "birth_date",
            "username", "user_name", "password"
        ]

        for form in forms:
            inputs = form.get("inputs", [])

            for inp in inputs:
                name = inp.get("name", "").lower()
                inp_id = inp.get("id", "").lower()
                placeholder = inp.get("placeholder", "").lower()
                inp_type = inp.get("type", "")

                # Check for personal data fields
                if any(field in name or field in inp_id or field in placeholder
                       for field in data_collection_fields):
                    return True

                # Check for email input type
                if inp_type == "email":
                    return True

        # Also check page content for registration/signup indicators
        if page_content:
            page_lower = page_content.lower()
            collection_indicators = [
                "sign up", "signup", "register", "create account",
                "subscribe", "newsletter", "join us"
            ]
            if any(indicator in page_lower for indicator in collection_indicators):
                if forms:  # Only if there are forms present
                    return True

        return False

    def _check_article_7(self, dom_meta: Optional[dict]) -> List[SecurityFinding]:
        """
        GDPR Article 7: Consent requirements.

        Check for data collection forms without explicit consent checkbox.

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

            # Check if form collects personal data
            has_personal_data = False
            data_collection_fields = ["email", "name", "phone", "address"]

            for inp in inputs:
                name = inp.get("name", "").lower()
                inp_id = inp.get("id", "").lower()
                if any(field in name or field in inp_id for field in data_collection_fields):
                    has_personal_data = True
                    break

            if not has_personal_data:
                continue

            # Check for consent checkbox
            has_consent_checkbox = False
            has_required_consent = False

            for inp in inputs:
                inp_type = inp.get("type", "")
                name = inp.get("name", "").lower()

                if inp_type == "checkbox":
                    consent_keywords = ["consent", "agree", "accept", "terms", "policy", "privacy"]
                    if any(kw in name for kw in consent_keywords):
                        has_consent_checkbox = True
                        if inp.get("required") or inp.get("required") == "":
                            has_required_consent = True
                        break

            if not has_consent_checkbox:
                cvss_score = cvss_calculate_score(PRESET_METRICS["high_risk"])

                findings.append(SecurityFinding(
                    category_id=self.category_id,
                    pattern_type="gdpr_article7_no_consent",
                    severity="medium",
                    confidence=0.70,
                    description=f"{_GDPR_ARTICLES['7']['description']}",
                    evidence="Data collection forms detected without explicit consent checkbox",
                    cwe_id=_GDPR_ARTICLES["7"]["cwe_id"],
                    cvss_score=cvss_score,
                    recommendation="Add required consent checkbox with clear disclosure of data processing "
                                 "under GDPR Art. 7 (freely given, specific, informed, unambiguous)"
                ))
                break

        return findings

    def _check_article_17(self, dom_meta: Optional[dict], url: str) -> List[SecurityFinding]:
        """
        GDPR Article 17: Right to erasure (Right to be Forgotten).

        Check for missing data deletion/account deletion mechanism.

        Args:
            dom_meta: Optional DOM metadata
            url: Target URL

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        if not dom_meta:
            return findings

        forms = dom_meta.get("forms", [])
        page_content = dom_meta.get("page_content", "")

        # Check if user account-related forms present
        has_account_forms = False
        account_indicators = ["login", "signin", "register", "signup", "account"]

        for form in forms:
            action = form.get("action", "").lower()
            if any(indicator in action for indicator in account_indicators):
                has_account_forms = True
                break

        if not has_account_forms:
            # Check forms for account-related inputs
            for form in forms:
                inputs = form.get("inputs", [])
                for inp in inputs:
                    name = inp.get("name", "").lower()
                    inp_id = inp.get("id", "").lower()
                    if any(indicator in name or indicator in inp_id for indicator in account_indicators):
                        has_account_forms = True
                        break
                if has_account_forms:
                    break

        if not has_account_forms:
            return findings

        # Check for deletion mechanism
        page_lower = page_content.lower() if page_content else ""
        deletion_keywords = [
            "delete account", "delete my account", "account deletion",
            "close account", "deactivate account", "remove account",
            "data deletion", "delete data", "right to be forgotten",
            "right to erasure", "data export"
        ]

        has_deletion_mechanism = any(
            keyword in page_lower for keyword in deletion_keywords
        )

        if not has_deletion_mechanism:
            cvss_score = cvss_calculate_score(PRESET_METRICS["low_risk"])

            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="gdpr_article17_no_deletion",
                severity="low",
                confidence=0.50,
                description=f"{_GDPR_ARTICLES['17']['description']}",
                evidence="User account forms present but no data deletion/account deletion mechanism found",
                cwe_id=_GDPR_ARTICLES["17"]["cwe_id"],
                cvss_score=cvss_score,
                recommendation="Provide data deletion request mechanism (Right to be Forgotten) per GDPR Art. 17, "
                             "including account deletion options and data export functionality"
            ))

        return findings

    def _check_article_25(self, dom_meta: Optional[dict]) -> List[SecurityFinding]:
        """
        GDPR Article 25: Privacy by design and by default.

        Check for pre-checked consent checkboxes.

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
                inn_type = inp.get("type", "")
                name = inp.get("name", "").lower()

                if inn_type == "checkbox":
                    # Check if checkbox is pre-checked
                    is_checked = inp.get("checked") in [True, "checked", ""]

                    # Only flag consent/marketing checkboxes, not benign ones
                    consent_keywords = [
                        "consent", "agree", "accept", "terms", "policy",
                        "newsletter", "marketing", "subscribe", "updates",
                        "email", "notify", "promotions", "offers"
                    ]

                    if is_checked and any(kw in name for kw in consent_keywords):
                        cvss_score = cvss_calculate_score(PRESET_METRICS["high_risk"])

                        findings.append(SecurityFinding(
                            category_id=self.category_id,
                            pattern_type="gdpr_article25_prechecked_consent",
                            severity="medium",
                            confidence=0.80,
                            description=f"{_GDPR_ARTICLES['25']['description']}",
                            evidence=f"Pre-checked consent option detected: '{name}' (not privacy by default)",
                            cwe_id=_GDPR_ARTICLES["25"]["cwe_id"],
                            cvss_score=cvss_score,
                            recommendation="Uncheck consent options by default, require explicit user opt-in "
                                         "per GDPR Art. 25 privacy by design and by default principle"
                        ))

                        # Only report one finding per form
                        break

            if findings:
                break

        return findings

    def _check_article_32(self, headers: Dict[str, Any], url: str) -> List[SecurityFinding]:
        """
        GDPR Article 32: Security of processing.

        Check for missing critical security headers.

        Args:
            headers: Normalized HTTP headers dict (lowercase keys)
            url: Target URL

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        if not headers:
            cvss_score = cvss_calculate_score(PRESET_METRICS["medium_risk"])

            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="gdpr_article32_no_headers",
                severity="medium",
                confidence=0.60,
                description=f"{_GDPR_ARTICLES['32']['description']}",
                evidence=f"No HTTP headers available to verify security implementation on {url}",
                cwe_id=_GDPR_ARTICLES["32"]["cwe_id"],
                cvss_score=cvss_score,
                recommendation="Implement security headers (HSTS, CSP, X-Frame-Options) for data in transit protection"
            ))
            return findings

        # Check for critical security headers
        missing_headers = []

        # Strict-Transport-Security (HSTS)
        if "strict-transport-security" not in headers:
            missing_headers.append("Strict-Transport-Security")

        # Content-Security-Policy (CSP)
        if "content-security-policy" not in headers:
            missing_headers.append("Content-Security-Policy")

        # X-Frame-Options (clickjacking protection)
        if "x-frame-options" not in headers:
            missing_headers.append("X-Frame-Options")

        # Only report if multiple critical headers missing
        if len(missing_headers) >= 2:
            cvss_score = cvss_calculate_score(PRESET_METRICS["medium_risk"])

            findings.append(SecurityFinding(
                category_id=self.category_id,
                pattern_type="gdpr_article32_insufficient_security",
                severity="medium",
                confidence=0.60,
                description=f"{_GDPR_ARTICLES['32']['description']}",
                evidence=f"Data collection present but critical security headers missing: "
                         f"{', '.join(missing_headers)}",
                cwe_id=_GDPR_ARTICLES["32"]["cwe_id"],
                cvss_score=cvss_score,
                recommendation="Implement HTTPS with HSTS, Content-Security-Policy, and X-Frame-Options "
                             "for data in transit protection per GDPR Art. 32 security of processing"
            ))

        return findings

    def _check_article_35(
        self,
        dom_meta: Optional[dict],
        page_content: Optional[str],
        url: str
    ) -> List[SecurityFinding]:
        """
        GDPR Article 35: Data Protection Impact Assessment (DPIA).

        Check for high-risk data processing without DPIA indicators.

        Args:
            dom_meta: Optional DOM metadata
            page_content: Optional HTML page content
            url: Target URL

        Returns:
            List of SecurityFinding objects
        """
        findings = []

        # High-risk data processing keywords
        high_risk_keywords = [
            "health", "medical", "financial", "credit", "biometric",
            "criminal", "religion", "race", "ethnicity", "political",
            "genetic", "fingerprint", "iris", "face recognition"
        ]

        if page_content:
            page_lower = page_content.lower()

            # Check for high-risk data processing
            has_high_risk_processing = any(
                keyword in page_lower for keyword in high_risk_keywords
            )

            if has_high_risk_processing:
                # Check for privacy policy/DPIA indicators
                privacy_policy_keywords = [
                    "privacy policy", "privacy statement",
                    "data protection impact assessment", "dpia",
                    "privacy impact assessment", "pia"
                ]

                has_privacy_policy = any(
                    keyword in page_lower for keyword in privacy_policy_keywords
                )

                if not has_privacy_policy:
                    cvss_score = cvss_calculate_score(PRESET_METRICS["medium_risk"])

                    findings.append(SecurityFinding(
                        category_id=self.category_id,
                        pattern_type="gdpr_article35_no_dpia",
                        severity="medium",
                        confidence=0.50,
                        description=f"{_GDPR_ARTICLES['35']['description']}",
                        evidence="High-risk data processing detected without DPIA/privacy policy indicator",
                        cwe_id=_GDPR_ARTICLES["35"]["cwe_id"],
                        cvss_score=cvss_score,
                        recommendation="Conduct Data Protection Impact Assessment (DPIA) for high-risk "
                                     "processing per GDPR Art. 35, and publish privacy policy "
                                     "explaining data processing activities"
                    ))

        return findings
