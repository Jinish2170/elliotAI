"""
Security Analysis Module - Extensible Architecture.

Provides tier-based security module execution with auto-discovery
and CWE/CVSS integration from Phase 9.

Main Exports:
    - SecurityModule: Abstract base class for security modules
    - SecurityFinding: Dataclass with CWE ID and CVSS score
    - SecurityTier: Enum (FAST, MEDIUM, DEEP) with timeout suggestions
    - register_security_module(): Module registration
    - get_registered_modules(): Get all registered modules

Usage:
    from veritas.analysis.security import (
        SecurityModule,
        SecurityFinding,
        SecurityTier,
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

__all__ = [
    "SecurityModule",
    "SecurityFinding",
    "SecurityTier",
    "register_security_module",
    "get_registered_modules",
    "clear_module_registry",
]
