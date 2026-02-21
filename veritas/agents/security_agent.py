"""
Veritas Agent — Security Analysis (Unified Security Modules)

The "Security Shield" of Veritas. Analyzes websites for security vulnerabilities
and malicious patterns through a unified agent interface.

Prior Implementation (Function-based):
    - security_node() function in core/orchestrator
    - Separate security modules (security_headers, phishing_db, redirects, js_analysis, etc.)
    - Module functions called independently

New Implementation (Agent-based):
    - SecurityAgent class with async analyze() method
    - Module auto-discovery and unified execution
    - Feature-flagged migration for gradual rollout

Migration Path (Plan 02-03):
    - USE_SECURITY_AGENT=true → Agent implementation
    - USE_SECURITY_AGENT=false → Original function-based implementation
    - SECURITY_AGENT_ROLLOUT 0.0-1.0 controls gradual rollout

Responsibilities:
    1. Auto-discover all security modules at initialization
    2. Execute enabled modules with timeout and retry handling
    3. Aggregate results into SecurityResult with composite score
    4. Handle module failures gracefully (collect in modules_failed list)
    5. Stream progress updates via queue-based IPC

Modules (auto-discovered):
    - security_headers: HTTP security header analysis
    - phishing_db: URL/Domain matching against phishing databases
    - redirects: Redirect chain analysis for suspicious hops
    - js_analysis: JavaScript security risk analysis
    - forms: Form validation and cross-domain checks
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    SECURITY_AGENT_FAIL_FAST,
    SECURITY_AGENT_RETRY_COUNT,
    SECURITY_AGENT_TIMEOUT,
    USE_SECURITY_AGENT,
)
from core.nim_client import NIMClient
from core.types import SecurityConfig, SecurityFinding, SecurityResult, Severity

# Import analysis module base for auto-discovery
from analysis import SecurityModuleBase

# Import discoverable modules
from analysis.security_headers import SecurityHeaderAnalyzer
from analysis.phishing_checker import PhishingChecker
from analysis.redirect_analyzer import RedirectAnalyzer
from analysis.js_analyzer import JSObfuscationDetector
from analysis.form_validator import FormActionValidator

logger = logging.getLogger("veritas.security_agent")

# Module execution priority order (affects module order in results)
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
# Security Agent
# ============================================================

class SecurityAgent:
    """
    Agent for unified security analysis across all security modules.

    Usage:
        # Basic usage with auto-discovery
        agent = SecurityAgent()
        result = await agent.analyze("https://example.com")

        # With custom NIM client and config
        from core.types import SecurityConfig
        config = SecurityConfig(timeout=20, retry_count=3)
        agent = SecurityAgent(nim_client=custom_nim, config=config)
        result = await agent.analyze(url)

        # Async context manager support
        async with SecurityAgent() as agent:
            result = await agent.analyze(url)
    """

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
        self._discovered_modules: dict[str, type] = {}

        # Log feature flag state
        logger.info(
            f"SecurityAgent initialized | "
            f"USE_SECURITY_AGENT={USE_SECURITY_AGENT} | "
            f"config={self._config.to_dict()}"
        )

    # ================================================================
    # Context Manager
    # ================================================================

    async def __aenter__(self) -> "SecurityAgent":
        """Enter async context manager."""
        await self._discover_modules()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        # Cleanup resources if needed
        pass

    # ================================================================
    # Module Discovery
    # ================================================================

    def _discover_modules(self) -> dict[str, type]:
        """
        Auto-discover available security modules.

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
                # Check if class is discoverable (call method on the class itself)
                if module_class.is_discoverable():
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
    # Public: Main Analysis Method
    # ================================================================

    async def analyze(self, url: str, page=None) -> SecurityResult:
        """
        Analyze a URL for security issues.

        This method runs all auto-discovered security modules and aggregates
        results into a SecurityResult with a composite score.

        Args:
            url: URL to analyze
            page: Optional Playwright Page object (for modules requiring page context)

        Returns:
            SecurityResult with findings, scores, and module results
        """
        start_time = time.time()
        logger.info(
            f"SecurityAgent.analyze called with url={url} | "
            f"USE_SECURITY_AGENT={USE_SECURITY_AGENT} | "
            f"page_provided={page is not None}"
        )

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
            if module_info.requires_page and page is None:
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

        end_time = time.time()
        result.analysis_time_ms = int((end_time - start_time) * 1000)

        logger.info(
            f"SecurityAgent.analyze complete for {url} | "
            f"modules_run={len(result.modules_run)} | "
            f"modules_failed={len(result.modules_failed)} | "
            f"findings={result.total_findings} | "
            f"score={result.composite_score:.2f} | "
            f"time={result.analysis_time_ms}ms"
        )

        return result

    async def _run_module_with_retry(
        self,
        module_class: type,
        module_info: type,  # ModuleInfo named tuple
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
                if module_info.method_name == "analyze":
                    instance = module_class()
                    module_result = await instance.analyze(url, page=page)
                elif module_info.method_name == "check":
                    instance = module_class()
                    module_result = await instance.check(url)
                elif module_info.method_name == "validate":
                    instance = module_class()
                    module_result = await instance.validate(page, url)
                else:
                    logger.error(f"Unknown method name: {module_info.method_name}")
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
    ):
        """
        Extract SecurityFinding objects from module result.

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
    ):
        """
        Extract findings based on module-specific patterns.

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
                    if not check.present:
                        finding = SecurityFinding.create(
                            category="security_headers",
                            severity=check.severity,
                            evidence=f"Missing header: {check.header}. {check.recommendation}",
                            source_module="security_headers",
                        )
                        result.add_finding(finding)
                    elif hasattr(check, "status") and check.status == "weak":
                        finding = SecurityFinding.create(
                            category="security_headers",
                            severity=check.severity,
                            evidence=f"Weak header: {check.header}. {check.recommendation}",
                            source_module="security_headers",
                        )
                        result.add_finding(finding)

        elif module_name == "phishing_db":
            # Extract from phishing verdict
            if hasattr(module_result, "is_phishing") and module_result.is_phishing:
                finding = SecurityFinding.create(
                    category="phishing_db",
                    severity="critical" if module_result.confidence > 0.7 else "high",
                    evidence=f"URL flagged as phishing. Sources: {module_result.sources}. Heuristics: {module_result.heuristic_flags}",
                    source_module="phishing_db",
                    confidence=module_result.confidence,
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
                        severity=flag.severity,
                        evidence=f"Script {flag.script_index}: {flag.description}",
                        source_module="js_analysis",
                    )
                    result.add_finding(finding)

        elif module_name == "form_validation":
            # Extract from form validations
            if hasattr(module_result, "forms"):
                for form in module_result.forms:
                    if form.severity != "info":
                        if form.flags:
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

    def _compute_composite_score(self, modules_results: dict[str, dict]) -> float:
        """
        Compute composite security score from all module results.

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
