"""
Veritas Agent — Security Analysis (Unified Security Modules with Tier Execution)

The "Security Shield" of Veritas. Analyzes websites for security vulnerabilities
and malicious patterns through tier-based parallel execution of security modules.

New Architecture (Tier-based Execution):
    - FAST tier: < 5 seconds (parallel execution via asyncio.gather)
    - MEDIUM tier: < 15 seconds (parallel execution via asyncio.gather)
    - DEEP tier: < 30 seconds (sequential execution for thorough analysis)
    - CVSS scoring integration via Phase 9 CVSSCalculator
    - Darknet threat correlation via Phase 8 CTI/OSINT components

Previous Implementation (Function-based - Maintained for backward compatibility):
    - security_node() function in core/orchestrator
    - Separate security modules (security_headers, phishing_db, redirects, js_analysis, etc.)
    - Module functions called independently

Migration Path:
    - use_tier_execution=True → New tier-based execution (recommended)
    - use_tier_execution=False → Original function-based implementation (default)
    - SECURITY_USE_TIER_EXECUTION environment variable controls orchestrator behavior

Responsibilities:
    1. Auto-discover all security modules (via get_all_security_modules)
    2. Group modules by execution tier (FAST/MEDIUM/DEEP)
    3. Execute tiers with appropriate timeout strategies
    4. Calculate CVSS scores for findings (via CVSSCalculator)
    5. Correlate darknet threat intelligence (via CThreatIntelligence)
    6. Aggregate results into SecurityResult with execution metrics
    7. Handle module failures gracefully

Modules (auto-discovered via SecurityModule architecture):
    - security_headers: HTTP security header analysis
    - cookies: Cookie security analysis (secure, httponly, samesite)
    - redirects: Redirect chain analysis for suspicious hops
    - forms: Form validation and cross-domain checks
    - owasp_a01: Broken Access Control detection
    - owasp_a02: Cryptographic Failures detection
    - owasp_a03: Injection vulnerabilities (SQLi, XSS, command injection)
    - owasp_a04: Insecure Design detection
    - owasp_a05: Security Misconfiguration detection
    - owasp_a06: Vulnerable and Outdated Components detection
    - owasp_a07: Identification and Authentication Failures detection
    - owasp_a08: Software and Data Integrity Failures detection
    - owasp_a09: Security Logging and Monitoring Failures detection
    - owasp_a10: Server-Side Request Forgery (SSRF) detection
    - pci_dss: PCI DSS compliance checks
    - gdpr: GDPR compliance checks
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

SYS_PATH = str(Path(__file__).resolve().parent.parent)
if SYS_PATH not in os.sys.path:
    os.sys.path.insert(0, SYS_PATH)

from config.settings import (
    SECURITY_AGENT_FAIL_FAST,
    SECURITY_AGENT_RETRY_COUNT,
    SECURITY_AGENT_TIMEOUT,
    USE_SECURITY_AGENT,
)
from core.nim_client import NIMClient
from core.types import SecurityConfig, SecurityFinding, SecurityResult, Severity

# Tier execution utilities
try:
    from analysis.security.utils import get_all_security_modules, group_modules_by_tier, execute_tier
    from analysis.security.base import SecurityModule, SecurityTier, SecurityFinding as SecurityModuleFinding
    TIER_AVAILABLE = True
except ImportError:
    TIER_AVAILABLE = False

# CVSS and CWE integration from Phase 9
try:
    from cwe.cvss_calculator import cvss_calculate_score, PRESET_METRICS, CVSSMetrics
    from cwe.registry import map_finding_to_cwe
    CVSS_AVAILABLE = True
except ImportError:
    CVSS_AVAILABLE = False

# Darknet threat intel from Phase 8 (CTI integration)
try:
    from osint.cti import CThreatIntelligence
    DARKNET_AVAILABLE = True
except ImportError:
    DARKNET_AVAILABLE = False

# Legacy imports for backward compatibility
from analysis.security_headers import SecurityHeaderAnalyzer
from analysis.phishing_checker import PhishingChecker
from analysis.redirect_analyzer import RedirectAnalyzer
from analysis.js_analyzer import JSObfuscationDetector
from analysis.form_validator import FormActionValidator

logger = logging.getLogger("veritas.security_agent")

# ============================================================
# Module execution priority order (affects module order in results)
# ============================================================
_MODULE_PRIORITY = [
    "security_headers",
    "phishing_db",
    "redirect_chain",
    "js_analysis",
    "form_validation",
]

# Composite score weights for each module
# Weights should sum to 1.0 (or be normalized)
_MODULE_WEIGHTS = {
    "security_headers": 0.20,
    "phishing_db": 0.30,  # Heavier penalty for phishing
    "redirect_chain": 0.15,
    "js_analysis": 0.20,
    "form_validation": 0.15,
}


# ============================================================
# Security Agent with Tier-Based Execution
# ============================================================

class SecurityAgent:
    """
    Agent for unified security analysis with tier-based parallel execution.

    Supports two execution modes:
        1. Tier-based execution (recommended): FAST parallel → MEDIUM parallel → DEEP sequential
        2. Function-based execution (legacy): Original sequential module analysis

    Usage:
        #-tier-based execution (recommended)
        agent = SecurityAgent()
        result = await agent.analyze(
            url="https://example.com",
            page_content="<html>...</html>",
            headers={"content-type": "text/html"},
            dom_meta={"depth": 1, "node_count": 100},
            use_tier_execution=True
        )

        # function-based execution (legacy)
        result = await agent.analyze(url, use_tier_execution=False)

        # With custom NIM client and config
        from core.types import SecurityConfig
        config = SecurityConfig(timeout=20, retry_count=3)
        agent = SecurityAgent(nim_client=custom_nim, config=config)

        # Async context manager support
        async with SecurityAgent() as agent:
            result = await agent.analyze(url, use_tier_execution=True)
    """

    # Feature flags
    use_tier_execution: bool = False  # Set to True to enable tier execution
    enable_cvss: bool = True          # Enable CVSS scoring
    enable_darknet: bool = True       # Enable darknet threat correlation

    # Class-level cache for modules by tier (initialized in __init__)
    _modules_by_tier: Dict = {}

    def __init__(
        self,
        nim_client: Optional[NIMClient] = None,
        config: Optional[SecurityConfig] = None,
    ):
        """
        Initialize SecurityAgent.

        Args:
            nim_client: Optional NIMClient instance for LLM-based analysis
            config: Optional SecurityConfig for timeout/retry behavior
        """
        self._nim = nim_client or NIMClient()
        self._config = config or SecurityConfig(
            timeout=SECURITY_AGENT_TIMEOUT,
            retry_count=SECURITY_AGENT_RETRY_COUNT,
            fail_fast=SECURITY_AGENT_FAIL_FAST,
        )
        self._discovered_modules: Dict[str, type] = {}

        # Check availability of tier execution dependencies
        if not TIER_AVAILABLE:
            logger.warning("Tier Execution not available: security.utils or security.base not found")
            self.use_tier_execution = False

        if not CVSS_AVAILABLE:
            logger.warning("CVSS scoring not available: cvss_calculator or registry not found")
            self.enable_cvss = False

        if not DARKNET_AVAILABLE:
            logger.warning("Darknet correlation not available: cti module not found")
            self.enable_darknet = False

        # Log feature flag state
        logger.info(
            f"SecurityAgent initialized | "
            f"USE_SECURITY_AGENT={USE_SECURITY_AGENT} | "
            f"use_tier_execution={self.use_tier_execution} | "
            f"enable_cvss={self.enable_cvss} | "
            f"enable_darknet={self.enable_darknet} | "
            f"config={self._config.to_dict()}"
        )

    # ================================================================
    # Context Manager
    # ================================================================

    async def __aenter__(self) -> "SecurityAgent":
        """Enter async context manager."""
        if self.use_tier_execution:
            self._load_modules()
        else:
            self._discover_modules()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        # Cleanup resources if needed
        pass

    # ================================================================
    # Mode Selection
    # ================================================================

    @classmethod
    def is_enabled(cls, url: str = "") -> bool:
        """Check if SecurityAgent should be used for this URL.

        Wraps settings.should_use_security_agent() with convenient
        class method access.

        Args:
            url: Target URL (if empty, simple random selection)

        Returns:
            bool: True if SecurityAgent should be used, False for function mode
        """
        from config.settings import should_use_security_agent
        return should_use_security_agent(url)

    @staticmethod
    def get_env_mode() -> str:
        """Return the configured mode: 'agent', 'function', or 'auto'.

        Reads USE_SECURITY_AGENT environment variable and returns:
        - "true" → "agent"
        - "false" → "function"
        - "auto" or unknown → "auto"

        Returns:
            str: Mode identifier
        """
        mode = os.getenv("USE_SECURITY_AGENT", "true").lower()
        if mode == "false":
            return "function"
        if mode == "true":
            return "agent"
        return "auto"

    async def initialize(self) -> None:
        """Initialize the agent (discover modules, set up resources).

        Can be called explicitly before analyze() or will be
        called automatically by analyze() if not already done.
        """
        logger.info("Initializing SecurityAgent...")
        if self.use_tier_execution:
            self._load_modules()
            logger.info(f"SecurityAgent initialized with tier execution | "
                       f"FAST={len(self._modules_by_tier[SecurityTier.FAST])}, "
                       f"MEDIUM={len(self._modules_by_tier[SecurityTier.MEDIUM])}, "
                       f"DEEP={len(self._modules_by_tier[SecurityTier.DEEP])}")
        else:
            self._discover_modules()
            logger.info(f"SecurityAgent initialized with {len(self._discovered_modules)} modules")

    # ================================================================
    # Module Discovery (Legacy)
    # ================================================================

    def _discover_modules(self) -> Dict[str, type]:
        """
        Auto-discover available security modules (legacy function-based).

        Scans imported security module classes and builds a registry
        based on module class.is_discoverable().

        Returns:
            Dictionary mapping module names to analyzer classes
        """
        modules = {}

        # List of discoverable modules (hardcoded for reliability)
        module_classes = [
            SecurityHeaderAnalyzer,
            PhishingChecker,
            RedirectAnalyzer,
            JSObfuscationDetector,
            FormActionValidator,
        ]

        for module_class in module_classes:
            try:
                # Check if class is discoverable
                if hasattr(module_class, 'is_discoverable') and module_class.is_discoverable():
                    module_info = module_class.get_module_info()
                    modules[module_info.module_name] = module_class
                    logger.debug(
                        f"Discovered module: {module_info.module_name} "
                        f"(category={module_info.category}, "
                        f"method={module_info.method_name}, "
                        f"requires_page={module_info.requires_page})"
                    )
            except Exception as e:
                logger.warning(f"Failed to discover module {module_class.__name__}: {e}")

        self._discovered_modules = modules
        logger.info(f"SecurityAgent discovered {len(modules)} modules: {list(modules.keys())}")

        return modules

    # ================================================================
    # Tier-Based Module Loading
    # ================================================================

    def _load_modules(self) -> None:
        """
        Load and group all security modules by execution tier.

        Calls get_all_security_modules() from analysis.security.utils
        and groups by tier using group_modules_by_tier().

        Caches results in _modules_by_tier class variable.
        """
        if not TIER_AVAILABLE:
            logger.warning("Cannot load tier modules: security.utils not available")
            return

        # Discover all security modules
        modules = get_all_security_modules()

        # Group by tier
        self._modules_by_tier = group_modules_by_tier(modules)

        total_modules = sum(len(tier_modules) for tier_modules in self._modules_by_tier.values())
        logger.info(
            f"Loaded {total_modules} security modules across tiers: "
            f"FAST={len(self._modules_by_tier[SecurityTier.FAST])}, "
            f"MEDIUM={len(self._modules_by_tier[SecurityTier.MEDIUM])}, "
            f"DEEP={len(self._modules_by_tier[SecurityTier.DEEP])}"
        )

    # ================================================================
    # Public: Main Analysis Method
    # ================================================================

    async def analyze(
        self,
        url: str,
        page_content: Optional[str] = None,
        headers: Optional[dict] = None,
        dom_meta: Optional[dict] = None,
        page=None,  # Optional Playwright Page object for backward compatibility
        use_tier_execution: Optional[bool] = None,
    ) -> SecurityResult:
        """
        Analyze a URL for security issues.

        Supports two execution modes:
            - Tier-based execution (FAST → MEDIUM → DEEP) with parallel execution
            - Function-based execution (legacy sequential module analysis)

        Args:
            url: URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers dict
            dom_meta: Optional DOM metadata (depth, node counts, etc.)
            page: Optional Playwright Page object (for modules requiring page context)
            use_tier_execution: If True, use tier execution; if False, use legacy mode
                               Defaults to self.use_tier_execution

        Returns:
            SecurityResult with findings, scores, and execution metrics
        """
        # Use parameter or class default
        tier_mode = use_tier_execution if use_tier_execution is not None else self.use_tier_execution

        start_time = time.time()
        logger.info(
            f"SecurityAgent.analyze called with url={url} | "
            f"use_tier_execution={tier_mode} | "
            f"USE_SECURITY_AGENT={USE_SECURITY_AGENT} | "
            f"page_provided={page is not None}"
        )

        if tier_mode:
            result = await self._analyze_tier_mode(url, page_content, headers, dom_meta)
        else:
            result = await self._analyze_legacy_mode(url, page)

        # Calculate execution time
        result.analysis_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"SecurityAgent.analysis complete for {url} | "
            f"modules_run={len(result.modules_run)} | "
            f"modules_failed={len(result.modules_failed)} | "
            f"findings={result.total_findings} | "
            f"score={result.composite_score:.2f} | "
            f"time={result.analysis_time_ms}ms"
        )

        return result

    # ================================================================
    # Tier-Based Analysis Mode
    # ================================================================

    async def _analyze_tier_mode(
        self,
        url: str,
        page_content: Optional[str],
        headers: Optional[dict],
        dom_meta: Optional[dict],
    ) -> SecurityResult:
        """
        Analyze URL using tier-based execution.

        Execution pattern:
            - FAST tier: Parallel execution (<5 seconds)
            - MEDIUM tier: Parallel execution (<15 seconds)
            - DEEP tier: Sequential execution (<30 seconds)

        Args:
            url: URL to analyze
            page_content: Optional HTML page content
            headers: Optional HTTP response headers dict
            dom_meta: Optional DOM metadata

        Returns:
            SecurityResult with findings and execution metrics
        """
        # Load modules if not already loaded
        if not any(self._modules_by_tier.values()):
            self._load_modules()

        # Create base result
        result = SecurityResult(
            url=url,
            timestamp="",  # Will be set in __post_init__
            composite_score=1.0,  # Will be computed from findings
            modules_results={},
            modules_run=[],
            modules_failed=[],
            errors=[],
            analysis_time_ms=0,
        )

        all_findings: List[SecurityModuleFinding] = []
        modules_executed = 0
        modules_failed = 0

        # Helper to convert SecurityModuleFinding to SecurityFinding
        def convert_findings(module_findings: List[SecurityModuleFinding], module_name: str) -> List[SecurityFinding]:
            converted = []
            for mf in module_findings:
                try:
                    sf = SecurityFinding.create(
                        category=mf.category_id,
                        severity=mf.severity,
                        evidence=mf.evidence,
                        source_module=module_name,
                        confidence=mf.confidence,
                        cwe_id=mf.cwe_id,
                        cvss_score=mf.cvss_score,
                        recommendation=mf.recommendation,
                        url_finding=mf.url_finding,
                    )
                    converted.append(sf)
                except Exception as e:
                    logger.warning(f"Failed to convert finding: {e}")
            return converted

        # Execute FAST tier (parallel)
        fast_modules = self._modules_by_tier[SecurityTier.FAST]
        if fast_modules:
            logger.info(f"Executing FAST tier with {len(fast_modules)} modules (parallel, <5s)")
            try:
                async with asyncio.timeout(SecurityTier.FAST.timeout_suggestion):
                    fast_findings = await execute_tier(fast_modules, url, page_content, headers, dom_meta)
                    all_findings.extend(fast_findings)
                    result.modules_run.extend([m.__name__ for m in fast_modules])
                    modules_executed += len(fast_modules)
                    logger.info(f"FAST tier complete: {len(fast_findings)} findings")
            except (TimeoutError, Exception) as e:
                logger.error(f"FAST tier execution failed: {e}")
                result.errors.append(f"FAST tier error: {e}")
                modules_failed += len(fast_modules)
                result.modules_failed.extend([m.__name__ for m in fast_modules])

        # Execute MEDIUM tier (parallel)
        medium_modules = self._modules_by_tier[SecurityTier.MEDIUM]
        if medium_modules and (not self._config.fail_fast or modules_failed == 0):
            logger.info(f"Executing MEDIUM tier with {len(medium_modules)} modules (parallel, <15s)")
            try:
                async with asyncio.timeout(SecurityTier.MEDIUM.timeout_suggestion):
                    medium_findings = await execute_tier(medium_modules, url, page_content, headers, dom_meta)
                    all_findings.extend(medium_findings)
                    result.modules_run.extend([m.__name__ for m in medium_modules])
                    modules_executed += len(medium_modules)
                    logger.info(f"MEDIUM tier complete: {len(medium_findings)} findings")
            except (TimeoutError, Exception) as e:
                logger.error(f"MEDIUM tier execution failed: {e}")
                result.errors.append(f"MEDIUM tier error: {e}")
                modules_failed += len(medium_modules)
                result.modules_failed.extend([m.__name__ for m in medium_modules])

        # Execute DEEP tier (sequential)
        deep_modules = self._modules_by_tier[SecurityTier.DEEP]
        if deep_modules and (not self._config.fail_fast or modules_failed == 0):
            logger.info(f"Executing DEEP tier with {len(deep_modules)} modules (sequential, <30s)")
            for module_class in deep_modules:
                try:
                    instance = module_class()
                    timeout = instance.timeout
                    async with asyncio.timeout(timeout):
                        module_findings = await instance.analyze(url, page_content, headers, dom_meta)
                    all_findings.extend(module_findings)
                    result.modules_run.append(module_class.__name__)
                    modules_executed += 1
                    logger.debug(f"DEEP module {module_class.__name__} complete: {len(module_findings)} findings")
                except (TimeoutError, Exception) as e:
                    logger.error(f"DEEP module {module_class.__name__} failed: {e}")
                    result.errors.append(f"{module_class.__name__}: {e}")
                    modules_failed += 1
                    result.modules_failed.append(module_class.__name__)
            logger.info(f"DEEP tier complete: {len(deep_modules)} modules executed")

        # Convert findings to core types
        result.findings = convert_findings(all_findings, "security_modules")

        # Update execution metrics
        result.modules_executed = modules_executed

        # Apply CVSS scoring if enabled
        if self.enable_cvss and CVSS_AVAILABLE:
            result.findings = await self._calculate_cvss_scores(result.findings)

        # Apply darknet threat correlation if enabled
        if self.enable_darknet and DARKNET_AVAILABLE:
            result.findings, darknet_intel = await self._correlate_darknet_threats(url, result.findings)
            result.darknet_correlation = darknet_intel

        # Compute composite score
        result.composite_score = self._compute_composite_score_from_findings(result.findings)

        return result

    # ================================================================
    # Legacy Analysis Mode (Backward Compatibility)
    # ================================================================

    async def _analyze_legacy_mode(
        self,
        url: str,
        page,
    ) -> SecurityResult:
        """
        Analyze URL using legacy function-based execution.

        Maintains backward compatibility with existing code that uses
        the direct module analyzer approach.

        Args:
            url: URL to analyze
            page: Optional Playwright Page object

        Returns:
            SecurityResult with findings and execution metrics
        """
        # Discover modules if not already done
        if not self._discovered_modules:
            self._discover_modules()

        # Create base result
        result = SecurityResult(
            url=url,
            timestamp="",  # Will be set in __post_init__
            composite_score=1.0,  # Will be computed from modules
            modules_results={},
            modules_run=[],
            modules_failed=[],
            errors=[],
            analysis_time_ms=0,
        )

        # Execute modules in priority order
        for module_name in _MODULE_PRIORITY:
            if module_name not in self._discovered_modules:
                logger.debug(f"Module {module_name} not discovered, skipping")
                continue

            module_class = self._discovered_modules[module_name]
            module_info = module_class.get_module_info()

            # Check if module requires page
            if hasattr(module_info, 'requires_page') and module_info.requires_page and page is None:
                logger.warning(
                    f"Module {module_name} requires Playwright Page object, skipping"
                )
                result.errors.append(
                    f"Module {module_name} skipped (requires Playwright Page but not provided)"
                )
                continue

            # Execute module with retry logic
            module_result = await self._run_module_with_retry(
                module_class, module_info, url, page
            )

            if module_result is not None:
                # Convert module result to dict and store
                result.modules_results[module_name] = self._convert_module_result(
                    module_result
                )
                result.modules_run.append(module_name)

                # Extract findings from module result
                self._extract_findings(result, module_result, module_name, url)
            else:
                result.modules_failed.append(module_name)

            # Check fail_fast flag
            if self._config.fail_fast and result.modules_failed:
                logger.warning("Fail-fast enabled, stopping analysis after module failure")
                break

        # Compute composite score
        result.composite_score = self._compute_composite_score(result.modules_results)

        return result

    # ================================================================
    # CVSS Scoring
    # ================================================================

    async def _calculate_cvss_scores(self, findings: List[SecurityFinding]) -> List[SecurityFinding]:
        """
        Calculate CVSS scores for security findings.

        For each finding:
            - If finding.cwe_id is None, find it via map_finding_to_cwe()
            - If finding.cvss_score is None, calculate it via cvss_calculator()

        Args:
            findings: List of SecurityFinding objects

        Returns:
            Updated list of SecurityFinding objects with CVSS scores
        """
        updated_findings = []

        for finding in findings:
            try:
                # Map to CWE if not already set
                if finding.cwe_id is None:
                    cwe_entry = map_finding_to_cwe(
                        finding_category=finding.category,
                        severity=finding.severity.value
                    )
                    if cwe_entry:
                        finding.cwe_id = cwe_entry.cwe_id
                        # Add recommendation
                        if not finding.recommendation:
                            finding.recommendation = f"See {cwe_entry.url} for remediation guidance."

                # Calculate CVSS score if not already set
                if finding.cvss_score is None and finding.cwe_id:
                    # Use preset metrics based on severity
                    severity_str = finding.severity.value.lower()
                    if severity_str in PRESET_METRICS:
                        metrics = PRESET_METRICS[severity_str]
                        finding.cvss_score = cvss_calculate_score(metrics)
                        logger.debug(
                            f"CVSS score calculated: {finding.cvss_score} "
                            f"for {finding.category} (severity={severity_str})"
                        )

                updated_findings.append(finding)

            except Exception as e:
                logger.warning(f"Failed to calculate CVSS score for finding: {e}")
                updated_findings.append(finding)

        return updated_findings

    # ================================================================
    # Darknet Threat Correlation
    # ================================================================

    async def _correlate_darknet_threats(
        self,
        url: str,
        findings: List[SecurityFinding],
    ) -> tuple[List[SecurityFinding], Optional[dict]]:
        """
        Correlate security findings with darknet threat intelligence.

        Uses CThreatIntelligence from Phase 8 to analyze darknet exposure.
        If darknet exposure detected (threat_level="high" or "critical"):

        For specific finding types (owasp_a03, owasp_a07, owasp_a10):
            - Elevate severity: medium → high, high → critical
            - Boost finding.confidence by 1.5x (max 1.0)
            - Append evidence with darknet correlation annotation
            - Add "darknet_correlation": true to finding metadata

        Args:
            url: URL being analyzed
            findings: List of SecurityFinding objects

        Returns:
            Tuple of (updated_findings, darknet_intel_dict)
        """
        darknet_intel_data = None

        try:
            # Initialize CTI module
            cti = CThreatIntelligence()

            # Extract basic page info for CTI analysis
            # Note: In production, this would include actual page content
            page_html = ""
            page_text = ""
            page_metadata = {
                "target_url": url,
                "security_findings": [f.to_dict() for f in findings],
            }

            # Analyze threats
            cti_result = await cti.analyze_threats(
                url=url,
                page_html=page_html,
                page_text=page_text,
                page_metadata=page_metadata,
                osint_results={},  # Could be enhanced with OSINT data
            )

            darknet_intel_data = cti_result
            threat_level = cti_result.get("threat_level", "none")
            confidence = cti_result.get("confidence", 0.0)

            logger.info(
                f"Darknet threat correlation: threat_level={threat_level}, "
                f"confidence={confidence:.2f}"
            )

            # If high or critical threat level, elevate relevant findings
            if threat_level in ("high", "critical"):
                updated_findings = []
                darknet_affected_categories = [
                    "owasp_a03",  # Injection
                    "owasp_a07",  # Auth
                    "owasp_a10",  # SSRF
                ]

                for finding in findings:
                    # Check if this finding type should be affected
                    should_elevate = finding.category in darknet_affected_categories

                    if should_elevate:
                        # Elevate severity
                        severity_mapping = {
                            Severity.MEDIUM: Severity.HIGH,
                            Severity.HIGH: Severity.CRITICAL,
                        }
                        current_severity = finding.severity
                        if current_severity in severity_mapping:
                            finding.severity = severity_mapping[current_severity]
                            finding.evidence += (
                                f" | [DARKNET CORRELATION: Elevated due to "
                                f"threat feed exposure (level={threat_level}, confidence={confidence:.0%})]"
                            )

                            # Boost confidence (max 1.0)
                            finding.confidence = min(finding.confidence * 1.5, 1.0)

                            logger.info(
                                f"Elevated finding {finding.category} from {current_severity.value} "
                                f"to {finding.severity.value} due to darknet correlation"
                            )

                    updated_findings.append(finding)

                return updated_findings, cti_result

        except Exception as e:
            logger.warning(f"Darknet threat correlation failed: {e}")

        return findings, darknet_intel_data

    # ================================================================
    # Legacy Methods (For Backward Compatibility)
    # ================================================================

    async def _run_module_with_retry(
        self,
        module_class: type,
        module_info: type,
        url: str,
        page,
    ):
        """
        Run a security module with retry logic.

        Args:
            module_class: The module analyzer class
            module_info: ModuleInfo with metadata
            url: URL to analyze
            page: Optional Playwright Page object

        Returns:
            Module result or None if all retries fail
        """
        last_error = None

        for attempt in range(self._config.retry_count + 1):
            try:
                start_time = time.time()

                # Call the module's analysis method
                if hasattr(module_info, 'method_name'):
                    method_name = module_info.method_name
                else:
                    method_name = "analyze"  # Default fallback

                if method_name == "analyze":
                    instance = module_class()
                    method = getattr(instance, 'analyze', None)
                    if method:
                        module_result = await method(url) if asyncio.iscoroutinefunction(method) else method(url)
                    else:
                        module_result = None
                elif method_name == "check":
                    instance = module_class()
                    module_result = await instance.check(url)
                elif method_name == "validate":
                    instance = module_class()
                    module_result = await instance.validate(page, url)
                else:
                    logger.error(f"Unknown method name: {method_name}")
                    return None

                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.debug(
                    f"Module {module_info.module_name} completed in {elapsed_ms}ms "
                    f"(attempt {attempt + 1}/{self._config.retry_count + 1})"
                )

                return module_result

            except asyncio.TimeoutError:
                last_error = "Timeout"
                logger.warning(
                    f"Module {module_info.module_name} timed out "
                    f"(attempt {attempt + 1}/{self._config.retry_count + 1})"
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Module {module_info.module_name} failed: {e} "
                    f"(attempt {attempt + 1}/{self._config.retry_count + 1})"
                )

            # If not last attempt, wait before retry
            if attempt < self._config.retry_count:
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

        logger.error(
            f"Module {module_info.module_name} failed after {self._config.retry_count + 1} attempts: {last_error}"
        )
        return None

    def _convert_module_result(self, module_result) -> dict:
        """
        Convert module result to JSON-serializable dict.

        Args:
            module_result: Result object from module (with to_dict() method)

        Returns:
            Dictionary representation of the result
        """
        if hasattr(module_result, "to_dict"):
            return module_result.to_dict()
        else:
            # Fallback for modules without to_dict()
            return {
                "raw_result": str(module_result),
                "has_score": hasattr(module_result, "score"),
                "score": getattr(module_result, "score", 0.0),
            }

    def _extract_findings(
        self, result: SecurityResult, module_result, module_name: str, url: str
    ) -> None:
        """
        Extract SecurityFinding objects from module result (legacy).

        Args:
            result: SecurityResult to add findings to
            module_result: Result object from module
            module_name: Name of the module
            url: URL being analyzed
        """
        findings_extracted = 0

        # 1. Check for explicit findings list in result
        if hasattr(module_result, "findings") and isinstance(module_result.findings, list):
            for module_finding in module_result.findings:
                try:
                    # Convert module finding to SecurityFinding
                    finding = SecurityFinding.create(
                        category=module_name,
                        severity=getattr(module_finding, "severity", "medium"),
                        evidence=getattr(module_finding, "evidence", str(module_finding)),
                        source_module=module_name,
                    )
                    result.add_finding(finding)
                    findings_extracted += 1
                except Exception as e:
                    logger.debug(f"Failed to convert finding: {e}")

        # 2. Extract findings from specific module patterns
        if findings_extracted == 0:
            self._extract_findings_by_module_type(result, module_result, module_name, url)

        logger.debug(f"Extracted {findings_extracted} findings from {module_name}")

    def _extract_findings_by_module_type(
        self, result: SecurityResult, module_result, module_name: str, url: str
    ) -> None:
        """
        Extract findings based on module-specific patterns (legacy).

        Args:
            result: SecurityResult to add findings to
            module_result: Result object from module
            module_name: Name of the module
            url: URL being analyzed
        """
        if module_name == "security_headers":
            # Extract from header checks
            if hasattr(module_result, "checks"):
                for check in module_result.checks:
                    if hasattr(check, 'present') and not check.present:
                        finding = SecurityFinding.create(
                            category="security_headers",
                            severity=getattr(check, 'severity', "medium"),
                            evidence=f"Missing header: {check.header}. {getattr(check, 'recommendation', '')}",
                            source_module="security_headers",
                        )
                        result.add_finding(finding)
                    elif hasattr(check, 'status') and check.status == "weak":
                        finding = SecurityFinding.create(
                            category="security_headers",
                            severity=getattr(check, 'severity', "medium"),
                            evidence=f"Weak header: {check.header}. {getattr(check, 'recommendation', '')}",
                            source_module="security_headers",
                        )
                        result.add_finding(finding)

        elif module_name == "phishing_db":
            # Extract from phishing verdict
            if hasattr(module_result, "is_phishing") and module_result.is_phishing:
                finding = SecurityFinding.create(
                    category="phishing_db",
                    severity="critical" if module_result.confidence > 0.7 else "high",
                    evidence=f"URL flagged as phishing. Sources: {getattr(module_result, 'sources', [])}. Heuristics: {getattr(module_result, 'heuristic_flags', [])}",
                    source_module="phishing_db",
                    confidence=getattr(module_result, 'confidence', 1.0),
                )
                result.add_finding(finding)

        elif module_name == "redirect_chain":
            # Extract from redirect flags
            if hasattr(module_result, "suspicion_flags") and module_result.suspicion_flags:
                for flag in module_result.suspicion_flags:
                    # Determine severity based on flag type
                    if "downgrade" in flag.lower():
                        severity = "critical"
                    elif "excessive" in flag.lower():
                        severity = "medium"
                    elif "tracking" in flag.lower():
                        severity = "low"
                    else:
                        severity = "medium"

                    finding = SecurityFinding.create(
                        category="redirect_chain",
                        severity=severity,
                        evidence=f"Redirect issue: {flag}",
                        source_module="redirect_chain",
                    )
                    result.add_finding(finding)

        elif module_name == "js_analysis":
            # Extract from JS flags
            if hasattr(module_result, "flags"):
                for flag in module_result.flags:
                    finding = SecurityFinding.create(
                        category="js_analysis",
                        severity=getattr(flag, 'severity', "medium"),
                        evidence=f"Script {flag.script_index}: {getattr(flag, 'description', str(flag))}",
                        source_module="js_analysis",
                    )
                    result.add_finding(finding)

        elif module_name == "form_validation":
            # Extract from form validations
            if hasattr(module_result, "forms"):
                for form in module_result.forms:
                    if hasattr(form, 'severity') and form.severity != "info":
                        if hasattr(form, 'flags') and form.flags:
                            evidence = "; ".join(form.flags)
                        else:
                            evidence = f"Form {form.form_index}: {form.action_url}"
                        finding = SecurityFinding.create(
                            category="form_validation",
                            severity=form.severity,
                            evidence=evidence,
                            source_module="form_validation",
                        )
                        result.add_finding(finding)

    # ================================================================
    # Score Computation
    # ================================================================

    def _compute_composite_score(self, modules_results: Dict[str, dict]) -> float:
        """
        Compute composite security score from all module results (legacy).

        Args:
            modules_results: Dict of module_name -> result_dict

        Returns:
            Composite score in range [0.0, 1.0]
        """
        score = 1.0
        total_weight = 0.0

        for module_name, module_dict in modules_results.items():
            weight = _MODULE_WEIGHTS.get(module_name, 0.0)
            if weight == 0.0:
                continue

            module_score = module_dict.get("score", 0.0)
            total_weight += weight

            # Phishing module: score is probability of NOT phishing
            # If is_phishing=True, score should be 0.0
            if module_name == "phishing_db":
                is_phishing = module_dict.get("is_phishing", False)
                if is_phishing:
                    module_score = 0.0
                else:
                    module_score = 1.0

            # Weighted penalization: lower module_score means higher penalty
            penalty = weight * (1.0 - module_score)
            score = max(0.0, score - penalty)

        # If no modules were run, return neutral score
        if total_weight == 0.0:
            return 1.0

        return score

    def _compute_composite_score_from_findings(self, findings: List[SecurityFinding]) -> float:
        """
        Compute composite security score from findings.

        Based on severity and confidence of findings:
            - Critical findings: severe penalty (0.25 * confidence)
            - High findings: moderate penalty (0.15 * confidence)
            - Medium findings: mild penalty (0.08 * confidence)
            - Low findings: minimal penalty (0.03 * confidence)
            - Info findings: no penalty

        Args:
            findings: List of SecurityFinding objects

        Returns:
            Composite score in range [0.0, 1.0]
        """
        score = 1.0

        for finding in findings:
            severity_penalty = {
                Severity.CRITICAL: 0.25,
                Severity.HIGH: 0.15,
                Severity.MEDIUM: 0.08,
                Severity.LOW: 0.03,
                Severity.INFO: 0.0,
            }
            penalty = severity_penalty.get(finding.severity, 0.0) * finding.confidence
            score = max(0.0, score - penalty)

        return score
