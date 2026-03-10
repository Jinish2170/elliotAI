"""
Veritas — Security Node

Security analysis node for the audit graph.
Moved from veritas.core.orchestrator as part of Phase 13-04 refactoring.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from veritas.config import settings

if TYPE_CHECKING:
    from veritas.core.orchestrator import AuditState

logger = logging.getLogger("veritas.orchestrator")


def _get_security_modules_for_tier(tier: str) -> list[str]:
    """Return the security modules to enable based on audit tier."""
    base = ["security_headers", "phishing_db"]
    if tier == "quick_scan":
        return base
    standard = base + ["redirect_chain", "js_analysis", "form_validation", "cookies"]
    if tier == "standard_audit":
        return standard
    deep = standard + [
        "owasp_a01", "owasp_a02", "owasp_a03", "owasp_a04", "owasp_a05",
        "owasp_a06", "owasp_a07", "owasp_a08", "owasp_a09", "owasp_a10",
        "pci_dss", "gdpr",
    ]
    if tier == "deep_forensic":
        return deep
    # darknet_investigation: everything + darknet modules
    return deep + ["darknet_correlation", "threat_intel"]


async def security_node_with_agent(state: AuditState) -> dict:
    """
    SECURITY node with feature-flagged agent routing (Plan 02-03, 10-04).

    Routes to SecurityAgent class or security_node function based on:
    1. USE_SECURITY_AGENT environment variable
    2. SECURITY_AGENT_ROLLOUT percentage (0.0-1.0)
    3. Consistent hash-based rollout for same URLs

    Implements auto-fallback: if SecurityAgent raises exception,
    falls back to security_node function.

    Phase 10-04 enhancements:
    - Supports tier-based execution with SECURITY_USE_TIER_EXECUTION flag
    - Passes page_content, headers, dom_meta from Scout results to SecurityAgent
    - Returns tier execution metrics (modules_executed, darknet_correlation)

    Modes:
        - "agent_tier": Use SecurityAgent with tier-based execution
        - "agent_legacy": Use SecurityAgent with legacy function-based execution
        - "function": Use security_node function directly
        - "function_fallback": SecurityAgent failed, fell back to function

    Returns:
        dict: {"security_results": {...}, "security_mode": str}
    """
    url = state.get("url", "")
    enabled = state.get("enabled_security_modules", [])
    errors = state.get("errors", [])
    results = {}
    security_mode = "agent"  # Default
    security_summary = {}

    if not enabled:
        enabled = getattr(settings, 'ENABLED_SECURITY_MODULES', ["security_headers", "phishing_db"])

    # Feature flag check: determine which implementation to use
    use_agent = settings.should_use_security_agent(url)
    rollout_pct = settings.get_security_agent_rollout()

    # Phase 10-04: Feature flag for tier execution
    use_tier_execution = bool(getattr(settings, "SECURITY_USE_TIER_EXECUTION", True))

    # Tier-aware: skip DEEP security modules on quick scans
    audit_tier = state.get("audit_tier", "standard_audit")
    if audit_tier == "quick_scan":
        # Quick scan: only FAST tier security modules
        use_tier_execution = True  # Force tier mode for granular control

    # Extract Scout data for tier-based analysis
    scout_results = state.get("scout_results", [])
    page_content = None
    headers = None
    dom_meta = None

    if scout_results:
        first_result = scout_results[0]
        # Use real page_content and response_headers captured by Scout (Plan 13-01)
        page_content = first_result.get("page_content", "")
        headers = first_result.get("response_headers", {})

        # Extract DOM analysis from Scout
        dom_analysis = first_result.get("dom_analysis", {})
        if dom_analysis:
            dom_meta = {
                "depth": dom_analysis.get("depth", 0),
                "node_count": dom_analysis.get("node_count", 0),
                "forms_count": dom_analysis.get("forms_count", 0),
                "scripts_count": dom_analysis.get("scripts_count", 0),
                "links_count": dom_analysis.get("links_count", 0),
            }

    # Emit security mode start event
    SecurityModeStarted_event = None
    if hasattr(state, '_progress_queue') or 'progress_queue' in state.get('_internal', {}):
        # Access progress queue if available (via internal state or orchestrator)
        pass

    if use_agent:
        security_mode = "agent_tier" if use_tier_execution else "agent_legacy"
        logger.info(
            f"Security node: USING AGENT MODE ({security_mode}) for {url} | "
            f"rollout={rollout_pct:.0%} | tier_execution={use_tier_execution}"
        )
        try:
            # Try SecurityAgent implementation
            from veritas.agents.security_agent import SecurityAgent

            # Initialize SecurityAgent with module discovery
            agent = SecurityAgent()
            await agent.initialize()

            # Run analysis with new signature for tier execution
            result = None
            result = await agent.analyze(
                url=url,
                page_content=page_content,
                headers=headers,
                dom_meta=dom_meta,
                use_tier_execution=use_tier_execution
            )

            results = dict(result.modules_results)
            security_summary = {
                "composite_score": result.composite_score,
                "findings": [f.to_dict() if hasattr(f, 'to_dict') else f for f in result.findings],
                "total_findings": result.total_findings,
                "modules_run": result.modules_run,
                "modules_failed": result.modules_failed,
                "modules_executed": getattr(result, 'modules_executed', len(result.modules_run)),
                "analysis_time_ms": result.analysis_time_ms,
                "modules_results": result.modules_results,
                "errors": result.errors,
                # Phase 10-04 tier execution fields
                "tier_execution": use_tier_execution,
                "darknet_correlation": result.darknet_correlation,
            }

            logger.info(
                f"SecurityAgent complete | mode={security_mode} | score={result.composite_score:.2f} | "
                f"findings={result.total_findings} | modules_executed={getattr(result, 'modules_executed', len(result.modules_run))} | "
                f"time={result.analysis_time_ms}ms"
            )

        except Exception as e:
            # Auto-fallback: SecurityAgent failed
            logger.error(f"SecurityAgent failed, falling back to security_node: {e}", exc_info=True)
            security_mode = "function_fallback"

            # Call original security_node function
            update = await security_node(state)
            results = update.get("security_results", {})
            security_summary = update.get("security_summary", {})
            security_summary["fallback_reason"] = str(e)

            return {
                "security_results": results,
                "security_mode": security_mode,
                "security_summary": security_summary,
            }
    else:
        security_mode = "function"
        logger.info(f"Security node: USING FUNCTION MODE for {url} | rollout={rollout_pct:.0%}")

    # Use function mode (either by choice or fallback already handled)
    if security_mode == "function":
        update = await security_node(state)
        results = update.get("security_results", {})
        security_summary = update.get("security_summary", {})

    logger.info(f"Security node complete: mode={security_mode} | url={url}")
    security_summary["security_mode"] = security_mode
    return {
        "security_results": results,
        "security_mode": security_mode,
        "security_summary": security_summary,
    }


async def security_node(state: AuditState) -> dict:
    """
    SECURITY node: Run enabled security analysis modules.
    Runs between Scout and Vision (while we have the URL).
    """
    url = state.get("url", "")
    enabled = state.get("enabled_security_modules", [])
    errors = state.get("errors", [])
    results = {}

    if not enabled:
        # Use defaults from settings
        enabled = getattr(settings, 'ENABLED_SECURITY_MODULES', ["security_headers", "phishing_db"])

    logger.info(f"Security node: running {enabled} modules for {url}")

    # 1. Security Headers
    if "security_headers" in enabled:
        try:
            from veritas.analysis.security_headers import SecurityHeaderAnalyzer
            analyzer = SecurityHeaderAnalyzer()
            res = await analyzer.analyze(url)
            results["security_headers"] = res.to_dict()
            logger.info(f"Security headers score: {res.score:.2f}")
        except Exception as e:
            logger.warning(f"Security headers analysis failed: {e}")
            results["security_headers"] = {"error": str(e)}

    # 2. Phishing Check
    if "phishing_db" in enabled:
        try:
            from veritas.analysis.phishing_checker import PhishingChecker
            checker = PhishingChecker()
            res = await checker.check(url)
            results["phishing_db"] = res.to_dict()
            logger.info(
                f"Phishing check: is_phishing={res.is_phishing}, "
                f"heuristic_flags={len(res.heuristic_flags)}, sources={len(res.sources)}"
            )
        except Exception as e:
            logger.warning(f"Phishing check failed: {e}")
            results["phishing_db"] = {"error": str(e)}

    # 3. Redirect Analysis
    if "redirect_chain" in enabled:
        try:
            from veritas.analysis.redirect_analyzer import RedirectAnalyzer
            analyzer = RedirectAnalyzer()
            res = await analyzer.analyze(url)
            results["redirect_chain"] = res.to_dict()
            logger.info(
                f"Redirect analysis: {res.total_hops} hops, suspicious={bool(res.suspicion_flags)}"
            )
        except Exception as e:
            logger.warning(f"Redirect analysis failed: {e}")
            results["redirect_chain"] = {"error": str(e)}

    # 4. JS Obfuscation Detection (lightweight heuristic from scout data)
    if "js_analysis" in enabled:
        try:
            primary = (state.get("scout_results") or [{}])[0]
            meta = primary.get("page_metadata", {})
            scripts_count = meta.get("scripts_count", 0)
            ext_scripts = meta.get("external_scripts", [])
            results["js_analysis"] = {
                "scripts_count": scripts_count,
                "external_scripts_count": len(ext_scripts) if isinstance(ext_scripts, list) else 0,
                "risk_score": 0.3 if scripts_count > 30 else 0.0,
                "note": "Full JS analysis runs in Scout's Playwright session",
            }
        except Exception as e:
            results["js_analysis"] = {"error": str(e)}

    # 5. Form Validation summary (already computed in scout)
    if "form_validation" in enabled:
        try:
            primary = (state.get("scout_results") or [{}])[0]
            fv = primary.get("form_validation", {})
            results["form_validation"] = fv if fv else {"note": "No form validation data"}
        except Exception as e:
            results["form_validation"] = {"error": str(e)}

    # 6. Darknet Correlation (for darknet_investigation tier)
    if "darknet_correlation" in enabled:
        try:
            from veritas.analysis.security.darknet import DarknetAnalyzer
            analyzer = DarknetAnalyzer()
            # Get page_content from scout results if available
            scout_results_list = state.get("scout_results", [])
            page_content_for_darknet = None
            if scout_results_list:
                page_content_for_darknet = scout_results_list[0].get("page_content", None)
            # Use analyze_with_details() for full result dict
            res = await analyzer.analyze_with_details(url, page_content=page_content_for_darknet)
            results["darknet_correlation"] = res.to_dict()
        except Exception as e:
            results["darknet_correlation"] = {"error": str(e)}

    modules_run = list(results.keys())
    modules_failed = [
        module_name for module_name, module_result in results.items()
        if isinstance(module_result, dict) and module_result.get("error")
    ]
    security_summary = {
        "composite_score": 1.0,
        "findings": [],
        "total_findings": 0,
        "modules_run": modules_run,
        "modules_failed": modules_failed,
        "modules_executed": len(modules_run),
        "analysis_time_ms": 0,
        "errors": [results[m]["error"] for m in modules_failed],
        "tier_execution": False,
        "darknet_correlation": None,
    }
    return {"security_results": results, "security_summary": security_summary}
