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

logger = logging.getLogger("veritas.security_agent")


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
    # Module Discovery (Skeleton - Implementation in Plan 02-02)
    # ================================================================

    async def _discover_modules(self) -> dict[str, type]:
        """
        Auto-discover available security modules.

        This method will scan the veritas/security/ directory for modules
        and build a registry of callable analysis functions.

        Returns:
            Dictionary mapping module names to their callables

        Note: Implementation completed in Plan 02-02
        """
        # Placeholder - modules will be discovered in plan 02-02
        logger.debug("_discover_modules called (implementation in plan 02-02)")
        return self._discovered_modules

    # ================================================================
    # Public: Main Analysis Method
    # ================================================================

    async def analyze(self, url: str) -> SecurityResult:
        """
        Analyze a URL for security issues.

        This method runs all enabled security modules (with auto-discovery
        in plan 02-02) and aggregates results into a SecurityResult.

        Args:
            url: URL to analyze

        Returns:
            SecurityResult with findings, scores, and module results

        Note: Full implementation in Plan 02-02. This is a skeleton that
              returns an empty result with score=1.0.
        """
        import time

        start_time = time.time()
        logger.info(
            f"SecurityAgent.analyze called with url={url} | "
            f"USE_SECURITY_AGENT={USE_SECURITY_AGENT}"
        )

        # Create base result
        result = SecurityResult(
            url=url,
            timestamp="",  # Will be set in __post_init__
            composite_score=1.0,  # No modules run yet = neutral score
            modules_results={},
            modules_run=[],  # No modules run yet
            modules_failed=[],
            errors=[],
            analysis_time_ms=0,
        )

        # Placeholder for actual module execution (plan 02-02)
        # This skeleton creates an empty result to verify the interface works

        end_time = time.time()
        result.analysis_time_ms = int((end_time - start_time) * 1000)

        logger.info(
            f"SecurityAgent.analyze complete for {url} | "
            f"modules_run={len(result.modules_run)} | "
            f"findings={result.total_findings} | "
            f"score={result.composite_score:.2f} | "
            f"time={result.analysis_time_ms}ms"
        )

        return result
