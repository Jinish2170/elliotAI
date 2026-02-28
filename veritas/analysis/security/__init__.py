"""
Security Analysis Module - Extensible Architecture.

Provides tier-based security module execution with auto-discovery
and CWE/CVSS integration from Phase 9.

Main Exports:
    - SecurityModule: Abstract base class for security modules
    - SecurityFinding: Dataclass with CWE ID and CVSS score
    - SecurityTier: Enum (FAST, MEDIUM, DEEP) with timeout suggestions
    - SecurityHeaderAnalyzerEnhanced: FAST tier TLS/SSL security header analyzer
    - CookieSecurityAnalyzer: FAST tier cookie security analyzer
    - ContentSecurityPolicyAnalyzer: FAST tier CSP analyzer
    - Utility functions: register_security_module(), get_registered_modules()

Usage:
    from veritas.analysis.security import (
        SecurityModule,
        SecurityFinding,
        SecurityTier,
        get_all_security_modules,
        execute_tier,
    )

    class MyAnalyzer(SecurityModule):
        @property
        def category_id(self) -> str:
            return "my_analyzer"

        async def analyze(self, url, page_content=None, headers=None, dom_meta=None):
            # Analysis logic
            return [SecurityFinding(...)]
"""

from .base import (
    SecurityFinding,
    SecurityModule,
    SecurityTier,
    clear_module_registry,
    get_registered_modules,
    register_security_module,
)
from .cookies import CookieSecurityAnalyzer
from .csp import ContentSecurityPolicyAnalyzer
from .tls_ssl import SecurityHeaderAnalyzerEnhanced

__all__ = [
    # Base classes
    "SecurityModule",
    "SecurityFinding",
    "SecurityTier",
    # Module registry
    "register_security_module",
    "get_registered_modules",
    "clear_module_registry",
    # FAST tier modules
    "SecurityHeaderAnalyzerEnhanced",
    "CookieSecurityAnalyzer",
    "ContentSecurityPolicyAnalyzer",
]

