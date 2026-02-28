"""
OWASP Top 10 Security Modules

This package contains 10 modules covering the OWASP Top 2021 categories:
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable and Outdated Components
- A07: Authentication Failures
- A08: Software and Data Integrity Failures
- A09: Security Logging Failures
- A10: Server-Side Request Forgery (SSRF)

Each module extends SecurityModule base class and provides:
- Category-specific vulnerability detection
- CWE ID mapping via CWEMapper
- CVSS scoring integration
- Tier-based execution (FAST, MEDIUM, DEEP)
"""

from veritas.analysis.security.owasp.a01_broken_access_control import BrokenAccessControlModule
from veritas.analysis.security.owasp.a02_cryptographic_failures import CryptographicFailuresModule
from veritas.analysis.security.owasp.a03_injection import InjectionModule
from veritas.analysis.security.owasp.a04_insecure_design import InsecureDesignModule
from veritas.analysis.security.owasp.a05_security_misconfiguration import SecurityMisconfigurationModule
from veritas.analysis.security.owasp.a06_vulnerable_components import VulnerableComponentsModule
from veritas.analysis.security.owasp.a07_authentication_failures import AuthenticationFailuresModule
from veritas.analysis.security.owasp.a08_data_integrity import DataIntegrityFailuresModule
from veritas.analysis.security.owasp.a09_logging_failures import LoggingFailuresModule
from veritas.analysis.security.owasp.a10_ssrf import SSRFModule

__all__ = [
    "BrokenAccessControlModule",
    "CryptographicFailuresModule",
    "InjectionModule",
    "InsecureDesignModule",
    "SecurityMisconfigurationModule",
    "VulnerableComponentsModule",
    "AuthenticationFailuresModule",
    "DataIntegrityFailuresModule",
    "LoggingFailuresModule",
    "SSRFModule",
]

# Module registry for auto-discovery
OWASP_MODULES = {
    "owasp_a01": BrokenAccessControlModule,
    "owasp_a02": CryptographicFailuresModule,
    "owasp_a03": InjectionModule,
    "owasp_a04": InsecureDesignModule,
    "owasp_a05": SecurityMisconfigurationModule,
    "owasp_a06": VulnerableComponentsModule,
    "owasp_a07": AuthenticationFailuresModule,
    "owasp_a08": DataIntegrityFailuresModule,
    "owasp_a09": LoggingFailuresModule,
    "owasp_a10": SSRFModule,
}


def get_all_owasp_modules():
    """
    Get all OWASP Top 10 security modules.

    Returns:
        Dict mapping category_id strings to module classes
    """
    return OWASP_MODULES.copy()
