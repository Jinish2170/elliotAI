"""
Veritas Analysis Layer

Analysis modules provide specialized processing logic:
- dom_analyzer:      Structural DOM analysis (Phase 2)
- temporal_analyzer: Screenshot diff logic (Phase 3)
- meta_analyzer:     WHOIS + SSL + DNS enrichment (Phase 3)
- pattern_matcher:   VLM prompt builder from taxonomy (Phase 2)

Security Analysis Modules (auto-discovered by SecurityAgent):
- security_headers:      HTTP security header analysis
- phishing_checker:      URL/Domain phishing database checks
- redirect_analyzer:     Redirect chain analysis
- js_analyzer:           JavaScript obfuscation & malware detection
- form_validator:        Form action and cross-domain security validation
"""

from abc import ABC, abstractmethod
from typing import Any, NamedTuple


# ============================================================
# Security Module Base Class
# ============================================================

class ModuleInfo(NamedTuple):
    """Information about a discovered security module."""
    module_name: str
    category: str
    analyzer_class: type
    method_name: str  # e.g., "analyze", "check", "validate"
    requires_page: bool  # True if module needs Playwright Page object


class SecurityModuleBase(ABC):
    """
    Abstract base class for security analysis modules.

    All security modules should inherit from this class to enable
    auto-discovery by SecurityAgent.

    Required attributes:
        module_name: str - Unique identifier for the module (e.g., "security_headers")
        category: str - Module category (e.g., "headers", "phishing", "redirects", "js", "forms")

    Required methods (one must be implemented):
        async analyze(url: str, page=None) -> result - Primary analysis method
        OR async check(url: str) -> result - Phishing-style check method
        OR async validate(page, page_url: str) -> result - Form-style validation method

    Example:
        class MyModule(SecurityModuleBase):
            module_name = "my_module"
            category = "custom"

            async def analyze(self, url: str, page=None) -> MyResult:
                # Implementation here
                pass
    """

    # Module metadata (to be overridden by subclasses)
    module_name: str = "unknown"
    category: str = "unknown"

    # Default is False, set to True if module needs Playwright Page
    requires_page: bool = False

    @classmethod
    def get_module_info(cls) -> ModuleInfo:
        """
        Get module information for auto-discovery.

        Returns:
            ModuleInfo with module metadata and method details
        """
        # Detect the primary analysis method
        method_name = None
        if hasattr(cls, "analyze"):
            # Prefer analyze() as primary method
            method_name = "analyze"
        elif hasattr(cls, "check"):
            method_name = "check"
        elif hasattr(cls, "validate"):
            method_name = "validate"

        return ModuleInfo(
            module_name=cls.module_name,
            category=cls.category,
            analyzer_class=cls,
            method_name=method_name or "analyze",
            requires_page=cls.requires_page,
        )

    @classmethod
    def is_discoverable(cls) -> bool:
        """
        Check if this module class should be auto-discovered.

        Modules are discoverable if:
        1. They have a valid module_name (not "unknown")
        2. They have a recognized method name (analyze, check, validate)
        3. Class name ends with "Analyzer", "Checker", or "Detector"

        Returns:
            True if the module should be auto-discovered
        """
        # Check for valid module name
        if cls.module_name == "unknown":
            return False

        # Check method exists
        method_name = cls.get_module_info().method_name
        if not hasattr(cls, method_name):
            return False

        # Check naming convention
        class_name = cls.__name__
        return any(class_name.endswith(suffix) for suffix in ("Analyzer", "Checker", "Detector", "Validator"))


# Import all security modules for auto-registration
# These imports allow SecurityAgent to discover modules via inheritance scan
try:
    from .security_headers import SecurityHeaderAnalyzer
    from .phishing_checker import PhishingChecker
    from .redirect_analyzer import RedirectAnalyzer
    from .js_analyzer import JSObfuscationDetector
    from .form_validator import FormActionValidator
except ImportError as e:
    # Modules may not be fully available during import
    import logging
    logging.getLogger("veritas.analysis").warning(f"Failed to import security modules: {e}")
