"""
Veritas — Form Action Validator

Runs inside a Playwright page context to validate form security:
  - Cross-domain form action URLs
  - Password/CC fields submitting to foreign domains
  - Missing autocomplete attributes on sensitive fields
  - Known payment processor whitelist
  - Form method (POST vs GET for sensitive data)

Returns per-form validation results with severity ratings.
"""

import logging
import urllib.parse
from dataclasses import dataclass, field

from veritas.analysis import SecurityModuleBase

logger = logging.getLogger("veritas.analysis.form_validator")


@dataclass
class FormValidation:
    """Validation result for a single form."""
    form_index: int
    action_url: str
    method: str = "GET"
    is_cross_domain: bool = False
    has_password_field: bool = False
    has_cc_field: bool = False
    has_email_field: bool = False
    severity: str = "info"          # info / low / medium / high / critical
    flags: list[str] = field(default_factory=list)
    is_safe_processor: bool = False  # True if action points to known payment processor


@dataclass
class FormValidationResult:
    """Overall form validation result."""
    url: str
    forms: list[FormValidation] = field(default_factory=list)
    total_forms: int = 0
    critical_count: int = 0
    score: float = 1.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "total_forms": self.total_forms,
            "critical_count": self.critical_count,
            "score": round(self.score, 3),
            "forms": [
                {
                    "form_index": f.form_index,
                    "action_url": f.action_url[:200],
                    "method": f.method,
                    "is_cross_domain": f.is_cross_domain,
                    "has_password_field": f.has_password_field,
                    "has_cc_field": f.has_cc_field,
                    "severity": f.severity,
                    "flags": f.flags,
                    "is_safe_processor": f.is_safe_processor,
                }
                for f in self.forms
            ],
            "errors": self.errors,
        }


# Known safe payment processor domains
_SAFE_PROCESSORS = {
    "stripe.com", "js.stripe.com", "checkout.stripe.com",
    "paypal.com", "www.paypal.com", "paypalobjects.com",
    "square.com", "squareup.com",
    "braintreegateway.com", "braintree-api.com",
    "adyen.com", "checkout.adyen.com",
    "shopify.com", "checkout.shopify.com",
    "razorpay.com", "api.razorpay.com",
    "2checkout.com", "secure.2checkout.com",
    "authorize.net", "secure.authorize.net",
}


# JavaScript for extracting form data from page
_FORM_EXTRACTION_JS = """
() => {
    const forms = document.querySelectorAll('form');
    return Array.from(forms).map((form, idx) => {
        const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
        const inputTypes = inputs.map(i => ({
            type: (i.getAttribute('type') || 'text').toLowerCase(),
            name: (i.getAttribute('name') || '').toLowerCase(),
            id: (i.getAttribute('id') || '').toLowerCase(),
            autocomplete: (i.getAttribute('autocomplete') || '').toLowerCase(),
            placeholder: (i.getAttribute('placeholder') || '').toLowerCase(),
        }));

        return {
            index: idx,
            action: form.getAttribute('action') || '',
            method: (form.getAttribute('method') || 'GET').toUpperCase(),
            target: form.getAttribute('target') || '',
            enctype: form.getAttribute('enctype') || '',
            inputCount: inputs.length,
            inputs: inputTypes,
        };
    });
}
"""


class FormActionValidator(SecurityModuleBase):
    """Validate form security within a Playwright page."""

    # Module metadata for auto-discovery
    module_name = "form_validation"
    category = "forms"
    requires_page = True  # Needs Playwright Page object

    async def validate(self, page, page_url: str) -> FormValidationResult:
        """
        Extract and validate all forms on the page.

        Args:
            page: Playwright Page object (must be navigated already)
            page_url: The URL of the page (for cross-domain comparison)
        """
        result = FormValidationResult(url=page_url)

        try:
            forms_data = await page.evaluate(_FORM_EXTRACTION_JS)
            result.total_forms = len(forms_data)

            page_domain = self._extract_root_domain(page_url)

            for form_data in forms_data:
                fv = self._validate_form(form_data, page_url, page_domain)
                result.forms.append(fv)

                if fv.severity == "critical":
                    result.critical_count += 1

            # Compute score
            if result.total_forms > 0:
                penalty = 0.0
                for f in result.forms:
                    if f.severity == "critical":
                        penalty += 0.25
                    elif f.severity == "high":
                        penalty += 0.15
                    elif f.severity == "medium":
                        penalty += 0.08
                result.score = max(0.0, 1.0 - penalty)

        except Exception as e:
            logger.error("Form validation failed: %s", e)
            result.errors.append(str(e))

        return result

    def _validate_form(
        self, form_data: dict, page_url: str, page_domain: str
    ) -> FormValidation:
        """Validate a single form."""
        action = form_data.get("action", "") or ""
        method = form_data.get("method", "GET")
        inputs = form_data.get("inputs", [])

        # Resolve relative action URL
        if action and not action.startswith(("http://", "https://", "//")):
            action = urllib.parse.urljoin(page_url, action)
        elif action.startswith("//"):
            action = "https:" + action

        fv = FormValidation(
            form_index=form_data.get("index", 0),
            action_url=action or page_url,
            method=method,
        )

        # Check field types
        for inp in inputs:
            inp_type = inp.get("type", "")
            inp_name = inp.get("name", "")
            inp_id = inp.get("id", "")
            inp_ac = inp.get("autocomplete", "")
            combined = f"{inp_type} {inp_name} {inp_id} {inp_ac}".lower()

            if inp_type == "password" or "password" in combined:
                fv.has_password_field = True
            if any(kw in combined for kw in [
                "card", "credit", "cc-number", "cc-exp", "cc-csc", "cvv", "cvc",
            ]):
                fv.has_cc_field = True
            if inp_type == "email" or "email" in combined:
                fv.has_email_field = True

        # Check cross-domain
        if action:
            action_domain = self._extract_root_domain(action)
            if action_domain and action_domain != page_domain:
                fv.is_cross_domain = True

                # Check if it's a known safe processor
                action_full_domain = urllib.parse.urlparse(action).netloc.lower()
                if any(safe in action_full_domain for safe in _SAFE_PROCESSORS):
                    fv.is_safe_processor = True

        # Determine severity
        if fv.is_cross_domain and not fv.is_safe_processor:
            if fv.has_cc_field:
                fv.severity = "critical"
                fv.flags.append("Credit card data submitted to unknown cross-domain URL")
            elif fv.has_password_field:
                fv.severity = "critical"
                fv.flags.append("Password submitted to unknown cross-domain URL")
            elif fv.has_email_field:
                fv.severity = "high"
                fv.flags.append("Email submitted to cross-domain URL")
            else:
                fv.severity = "medium"
                fv.flags.append("Form submits to cross-domain URL")
        elif fv.is_cross_domain and fv.is_safe_processor:
            fv.severity = "info"
            fv.flags.append("Form submits to known payment processor")

        # Check method
        if method == "GET" and (fv.has_password_field or fv.has_cc_field):
            fv.severity = "high"
            fv.flags.append("Sensitive data sent via GET (visible in URL/logs)")

        # Check for missing autocomplete
        for inp in inputs:
            if inp.get("type") == "password" and not inp.get("autocomplete"):
                fv.flags.append("Password field missing autocomplete attribute")
                break

        # No SSL on page with sensitive form
        if not page_url.startswith("https://") and (fv.has_password_field or fv.has_cc_field):
            fv.severity = "critical"
            fv.flags.append("Sensitive form on non-HTTPS page")

        return fv

    @staticmethod
    def _extract_root_domain(url: str) -> str:
        """Extract registrable domain from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            domain = (parsed.netloc or "").lower().split(":")[0]
            parts = domain.rsplit(".", 2)
            return ".".join(parts[-2:]) if len(parts) >= 2 else domain
        except Exception:
            return ""

    async def analyze(self, url: str, page=None) -> FormValidationResult:
        """
        Analyze forms on a page for security issues (alias for validate).

        Args:
            url: URL of the page
            page: Playwright Page object (navigated) - required for this module

        Returns:
            FormValidationResult with form security analysis
        """
        if page is None:
            result = FormValidationResult(url=url)
            result.errors.append("Form validation requires Playwright Page object")
            result.score = 0.0
            return result

        return await self.validate(page, url)
