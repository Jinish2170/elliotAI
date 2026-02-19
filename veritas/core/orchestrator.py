"""
Veritas Core — LangGraph Orchestrator

The state machine that wires Scout, Vision, Graph, and Judge agents
into a cyclic reasoning loop with budget controls and termination conditions.

State Machine:
    START → SCOUT → VISION → GRAPH → JUDGE → REPORT (or → SCOUT for more investigation)
    Any node → ABORT on unrecoverable failure → PARTIAL_REPORT → END

Budget Controls:
    - max_iterations: Hard cap on reasoning cycles
    - max_pages: Hard cap on total pages scouted
    - nim_call_budget: Soft cap tracked via NIMClient.call_count

LangGraph Integration:
    Uses LangGraph's StateGraph with TypedDict state to manage the audit
    lifecycle. The graph is compiled once and invoked per audit.
"""

import asyncio
import json as _json
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.graph_investigator import GraphInvestigator, GraphResult
from agents.judge import AuditEvidence, JudgeAgent, JudgeDecision
from agents.scout import ScoutResult, StealthScout
from agents.vision import VisionAgent, VisionResult
from config import settings
from config.trust_weights import TrustScoreResult
from core.nim_client import NIMClient

logger = logging.getLogger("veritas.orchestrator")


# ============================================================
# Audit State (the shared state flowing through the graph)
# ============================================================

class AuditState(TypedDict):
    """
    Shared state passed between all nodes in the LangGraph.
    LangGraph requires TypedDict for state management.
    """
    # Input
    url: str
    audit_tier: str                      # "quick_scan", "standard_audit", "deep_forensic"

    # Iteration tracking
    iteration: int
    max_iterations: int
    max_pages: int
    status: str                          # "running", "completed", "aborted"

    # Collected evidence
    scout_results: list[dict]            # Serialized ScoutResult dicts
    vision_result: Optional[dict]        # Serialized VisionResult dict
    graph_result: Optional[dict]         # Serialized GraphResult dict

    # Judge decision
    judge_decision: Optional[dict]       # Serialized JudgeDecision dict

    # URLs to investigate
    pending_urls: list[str]              # URLs queued for Scout investigation
    investigated_urls: list[str]         # URLs already visited

    # Timing
    start_time: float
    elapsed_seconds: float

    # Error tracking
    errors: list[str]
    scout_failures: int                  # Consecutive scout failures (for retry → abort logic)

    # NIM budget
    nim_calls_used: int

    # --- V2 fields ---
    site_type: str                       # Detected website type from Scout
    site_type_confidence: float
    verdict_mode: str                    # "simple" | "expert"
    security_results: dict               # Results from security modules
    enabled_security_modules: list[str]  # Which security modules to run


# ============================================================
# Node Functions
# ============================================================

async def scout_node(state: AuditState) -> dict:
    """
    SCOUT node: Navigate the next URL and capture evidence.
    Processes one URL per invocation from pending_urls.
    """
    pending = state.get("pending_urls", [])
    investigated = state.get("investigated_urls", [])
    scout_results = state.get("scout_results", [])
    scout_failures = state.get("scout_failures", 0)
    errors = state.get("errors", [])

    if not pending:
        logger.warning("Scout node invoked with no pending URLs")
        return {"status": "running", "errors": errors + ["Scout: no pending URLs"]}

    url = pending[0]
    remaining = pending[1:]

    logger.info(f"Scout investigating: {url}")

    try:
        async with StealthScout() as scout:
            # First URL gets full temporal investigation
            if len(investigated) == 0:
                result = await scout.investigate(url)
            else:
                result = await scout.navigate_subpage(url)

        # Serialize ScoutResult for state storage
        result_dict = {
            "url": result.url,
            "status": result.status,
            "screenshots": result.screenshots,
            "screenshot_timestamps": result.screenshot_timestamps,
            "screenshot_labels": result.screenshot_labels,
            "page_title": result.page_title,
            "page_metadata": result.page_metadata,
            "links": result.links,
            "forms_detected": result.forms_detected,
            "captcha_detected": result.captcha_detected,
            "error_message": result.error_message,
            "navigation_time_ms": result.navigation_time_ms,
            "viewport_used": result.viewport_used,
            "user_agent_used": result.user_agent_used,
            "trust_modifier": result.trust_modifier,
            "trust_notes": result.trust_notes,
            # V2 fields
            "site_type": getattr(result, 'site_type', ''),
            "site_type_confidence": getattr(result, 'site_type_confidence', 0.0),
            "dom_analysis": getattr(result, 'dom_analysis', {}),
            "form_validation": getattr(result, 'form_validation', {}),
        }

        new_scout_results = scout_results + [result_dict]
        new_investigated = investigated + [url]

        # Extract site_type from primary (first) scout result
        update = {
            "scout_results": new_scout_results,
            "pending_urls": remaining,
            "investigated_urls": new_investigated,
        }
        if len(scout_results) == 0:  # First result: set site_type
            update["site_type"] = getattr(result, 'site_type', '')
            update["site_type_confidence"] = getattr(result, 'site_type_confidence', 0.0)

        if result.status == "SUCCESS":
            logger.info(f"Scout SUCCESS: {url} | screenshots={len(result.screenshots)}")
            update["scout_failures"] = 0
            update["iteration"] = state.get("iteration", 0)
            return update
        elif result.status == "CAPTCHA_BLOCKED":
            logger.info(f"Scout CAPTCHA_BLOCKED: {url}")
            update["scout_failures"] = 0
            return update
        else:
            logger.warning(f"Scout failed: {url} | status={result.status} | error={result.error_message}")
            update["scout_failures"] = scout_failures + 1
            update["errors"] = errors + [f"Scout failed on {url}: {result.error_message}"]
            return update

    except Exception as e:
        logger.error(f"Scout exception on {url}: {e}", exc_info=True)
        return {
            "pending_urls": remaining,
            "investigated_urls": investigated + [url],
            "scout_failures": scout_failures + 1,
            "errors": errors + [f"Scout exception: {str(e)}"],
        }


async def vision_node(state: AuditState) -> dict:
    """
    VISION node: Analyze all screenshots from Scout results.
    """
    scout_results = state.get("scout_results", [])
    errors = state.get("errors", [])

    if not scout_results:
        return {"errors": errors + ["Vision: no scout results to analyze"]}

    # Collect all screenshots and labels from all scout results
    all_screenshots = []
    all_labels = []
    for sr in scout_results:
        all_screenshots.extend(sr.get("screenshots", []))
        all_labels.extend(sr.get("screenshot_labels", []))

    if not all_screenshots:
        logger.warning("Vision node: no screenshots available")
        return {
            "vision_result": {
                "visual_score": 0.5,
                "temporal_score": 0.5,
                "dark_patterns": [],
                "temporal_findings": [],
                "screenshots_analyzed": 0,
                "fallback_used": False,
                "errors": ["No screenshots available"],
            }
        }

    logger.info(f"Vision analyzing {len(all_screenshots)} screenshots")

    try:
        nim = NIMClient()
        agent = VisionAgent(nim_client=nim)

        result = await agent.analyze(
            screenshots=all_screenshots,
            screenshot_labels=all_labels,
            url=state.get("url", ""),
            site_type=state.get("site_type", ""),
        )

        # Serialize VisionResult
        vision_dict = {
            "visual_score": result.visual_score,
            "temporal_score": result.temporal_score,
            "findings": [
                {
                    "category": p.category_id,
                    "sub_type": p.pattern_type,
                    "confidence": p.confidence,
                    "severity": p.severity,
                    "evidence": p.evidence,
                    "screenshot_path": p.screenshot_path,
                    "model_used": p.model_used,
                    "fallback_mode": p.fallback_mode,
                    "raw_vlm_response": p.raw_vlm_response,
                }
                for p in result.dark_patterns
            ],
            "temporal_findings": [
                {
                    "finding_type": tf.finding_type,
                    "value_at_t0": tf.value_at_t0,
                    "value_at_t_delay": tf.value_at_t_delay,
                    "delta_seconds": tf.delta_seconds,
                    "is_suspicious": tf.is_suspicious,
                    "explanation": tf.explanation,
                    "confidence": tf.confidence,
                }
                for tf in result.temporal_findings
            ],
            "screenshots_analyzed": result.screenshots_analyzed,
            "prompts_sent": result.prompts_sent,
            "nim_calls_made": result.nim_calls_made,
            "fallback_used": result.fallback_used,
            "errors": result.errors,
        }

        return {
            "vision_result": vision_dict,
            "nim_calls_used": state.get("nim_calls_used", 0) + result.nim_calls_made,
        }

    except Exception as e:
        logger.error(f"Vision node exception: {e}", exc_info=True)
        return {
            "errors": errors + [f"Vision exception: {str(e)}"],
            "vision_result": {
                "visual_score": 0.5,
                "temporal_score": 0.5,
                "dark_patterns": [],
                "temporal_findings": [],
                "screenshots_analyzed": 0,
                "fallback_used": True,
                "errors": [str(e)],
            },
        }


async def graph_node(state: AuditState) -> dict:
    """
    GRAPH node: Run entity verification and build knowledge graph.
    """
    scout_results = state.get("scout_results", [])
    errors = state.get("errors", [])
    url = state.get("url", "")

    if not scout_results:
        return {"errors": errors + ["Graph: no scout results"]}

    # Gather metadata from the primary scout result
    primary = scout_results[0]
    metadata = primary.get("page_metadata", {})

    # Gather page text from all scout results (titles + descriptions)
    page_texts = []
    for sr in scout_results:
        if sr.get("page_title"):
            page_texts.append(sr["page_title"])
        meta = sr.get("page_metadata", {})
        if meta.get("description"):
            page_texts.append(meta["description"])
    page_text = "\n".join(page_texts)

    # External links
    external_links = primary.get("links", [])

    logger.info(f"Graph investigating {url} | text_length={len(page_text)}")

    try:
        nim = NIMClient()
        agent = GraphInvestigator(nim_client=nim)
        graph_timeout_s = max(10, int(getattr(settings, "GRAPH_PHASE_TIMEOUT_S", 90)))

        try:
            async with asyncio.timeout(graph_timeout_s):
                result = await agent.investigate(
                    url=url,
                    page_metadata=metadata,
                    page_text=page_text,
                    external_links=external_links,
                    site_type=state.get("site_type", ""),
                    form_validation=primary.get("form_validation"),
                )
        except TimeoutError:
            timeout_msg = f"Graph phase timeout after {graph_timeout_s}s"
            logger.error(timeout_msg)
            fallback_graph = {
                "graph_score": 0.5,
                "meta_score": 0.5,
                "meta_analysis": {},
                "ip_geolocation": {},
                "domain_age_days": -1,
                "has_ssl": False,
                "claims_extracted": [],
                "verifications": [],
                "inconsistencies": [],
                "graph_data": {"nodes": [], "edges": []},
                "graph_node_count": 0,
                "graph_edge_count": 0,
                "domain_intel": None,
                "tavily_searches": 0,
                "errors": [timeout_msg],
            }
            return {
                "graph_result": fallback_graph,
                "errors": errors + [timeout_msg],
            }

        # Serialize GraphResult (graph is exported separately)
        graph_dict = {
            "graph_score": result.graph_score,
            "meta_score": result.meta_score,
            "meta_analysis": getattr(result, 'meta_analysis', {}),
            "ip_geolocation": getattr(result, 'ip_geolocation', {}),
            "domain_age_days": result.domain_age_days,
            "has_ssl": result.has_ssl,
            "claims_extracted": [
                {"entity_type": c.entity_type, "entity_value": c.entity_value, "source_page": c.source_page}
                for c in result.claims_extracted
            ],
            "verifications": [
                {
                    "entity_type": v.claim.entity_type,
                    "entity_value": v.claim.entity_value,
                    "status": v.status,
                    "evidence_source": v.evidence_source,
                    "evidence_detail": v.evidence_detail,
                    "confidence": v.confidence,
                }
                for v in result.verifications
            ],
            "inconsistencies": [
                {
                    "claim_text": inc.claim_text,
                    "evidence_text": inc.evidence_text,
                    "inconsistency_type": inc.inconsistency_type,
                    "severity": inc.severity,
                    "confidence": inc.confidence,
                    "explanation": inc.explanation,
                }
                for inc in result.inconsistencies
            ],
            "graph_data": agent.export_graph_data(result.graph) if result.graph else {"nodes": [], "edges": []},
            "graph_node_count": result.graph_node_count,
            "graph_edge_count": result.graph_edge_count,
            "domain_intel": {
                "domain": result.domain_intel.domain if result.domain_intel else "",
                "registrar": result.domain_intel.registrar if result.domain_intel else "",
                "age_days": result.domain_intel.age_days if result.domain_intel else -1,
                "ssl_issuer": result.domain_intel.ssl_issuer if result.domain_intel else "",
                "is_privacy_protected": result.domain_intel.is_privacy_protected if result.domain_intel else False,
            } if result.domain_intel else None,
            "tavily_searches": result.tavily_searches,
            "errors": result.errors,
        }

        return {
            "graph_result": graph_dict,
            "nim_calls_used": state.get("nim_calls_used", 0) + result.tavily_searches,
        }

    except Exception as e:
        logger.error(f"Graph node exception: {e}", exc_info=True)
        return {
            "errors": errors + [f"Graph exception: {str(e)}"],
            "graph_result": {
                "graph_score": 0.5,
                "meta_score": 0.5,
                "domain_age_days": -1,
                "has_ssl": False,
                "claims_extracted": [],
                "verifications": [],
                "inconsistencies": [],
                "graph_data": {"nodes": [], "edges": []},
                "errors": [str(e)],
            },
        }


async def judge_node(state: AuditState) -> dict:
    """
    JUDGE node: Synthesize all evidence into a verdict or request more investigation.
    """
    url = state.get("url", "")
    iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", settings.MAX_ITERATIONS)

    # Reconstruct ScoutResult objects from serialized dicts
    scout_results = []
    for sr_dict in state.get("scout_results", []):
        scout_results.append(ScoutResult(**{
            k: v for k, v in sr_dict.items()
            if k in ScoutResult.__dataclass_fields__
        }))

    # Reconstruct VisionResult from serialized dict
    vision_result = None
    vr_dict = state.get("vision_result")
    if vr_dict:
        from agents.vision import DarkPatternFinding, TemporalFinding
        dark_patterns = []
        for p in vr_dict.get("findings", []):
            dark_patterns.append(DarkPatternFinding(
                category_id=p.get("category", p.get("category_id", "")),
                pattern_type=p.get("sub_type", p.get("pattern_type", "")),
                confidence=p.get("confidence", 0),
                severity=p.get("severity", "medium"),
                evidence=p.get("evidence", ""),
                screenshot_path=p.get("screenshot_path", ""),
                raw_vlm_response=p.get("raw_vlm_response", ""),
                model_used=p.get("model_used", ""),
                fallback_mode=p.get("fallback_mode", False),
            ))
        temporal_findings = []
        for tf in vr_dict.get("temporal_findings", []):
            temporal_findings.append(TemporalFinding(
                finding_type=tf.get("finding_type", ""),
                value_at_t0=tf.get("value_at_t0", ""),
                value_at_t_delay=tf.get("value_at_t_delay", ""),
                delta_seconds=tf.get("delta_seconds", 0),
                is_suspicious=tf.get("is_suspicious", False),
                explanation=tf.get("explanation", ""),
                confidence=tf.get("confidence", 0),
            ))
        vision_result = VisionResult(
            visual_score=vr_dict.get("visual_score", 0.5),
            temporal_score=vr_dict.get("temporal_score", 0.5),
            dark_patterns=dark_patterns,
            temporal_findings=temporal_findings,
            screenshots_analyzed=vr_dict.get("screenshots_analyzed", 0),
            prompts_sent=vr_dict.get("prompts_sent", 0),
            nim_calls_made=vr_dict.get("nim_calls_made", 0),
            fallback_used=vr_dict.get("fallback_used", False),
            errors=vr_dict.get("errors", []),
        )

    # Reconstruct GraphResult from serialized dict
    graph_result = None
    gr_dict = state.get("graph_result")
    if gr_dict:
        from agents.graph_investigator import (DomainIntel, EntityClaim,
                                               GraphInconsistency,
                                               VerificationResult)
        claims = [EntityClaim(**c) for c in gr_dict.get("claims_extracted", [])]
        verifications = [
            VerificationResult(
                claim=EntityClaim(
                    entity_type=v["entity_type"],
                    entity_value=v["entity_value"],
                    source_page=url,
                ),
                status=v["status"],
                evidence_source=v.get("evidence_source", ""),
                evidence_detail=v.get("evidence_detail", ""),
                confidence=v.get("confidence", 0.5),
            )
            for v in gr_dict.get("verifications", [])
        ]
        inconsistencies = [
            GraphInconsistency(**inc)
            for inc in gr_dict.get("inconsistencies", [])
        ]

        di_dict = gr_dict.get("domain_intel")
        domain_intel = DomainIntel(
            domain=di_dict.get("domain", ""),
            registrar=di_dict.get("registrar", ""),
            age_days=di_dict.get("age_days", -1),
            ssl_issuer=di_dict.get("ssl_issuer", ""),
            is_privacy_protected=di_dict.get("is_privacy_protected", False),
        ) if di_dict else None

        graph_result = GraphResult(
            domain_intel=domain_intel,
            claims_extracted=claims,
            verifications=verifications,
            inconsistencies=inconsistencies,
            graph_score=gr_dict.get("graph_score", 0.5),
            meta_score=gr_dict.get("meta_score", 0.5),
            graph_node_count=gr_dict.get("graph_node_count", 0),
            graph_edge_count=gr_dict.get("graph_edge_count", 0),
            tavily_searches=gr_dict.get("tavily_searches", 0),
            errors=gr_dict.get("errors", []),
        )

    # Build evidence bundle
    evidence = AuditEvidence(
        url=url,
        scout_results=scout_results,
        vision_result=vision_result,
        graph_result=graph_result,
        iteration=iteration,
        max_iterations=max_iterations,
        site_type=state.get("site_type", ""),
        site_type_confidence=state.get("site_type_confidence", 0.0),
        verdict_mode=state.get("verdict_mode", "expert"),
        security_results=state.get("security_results", {}),
    )

    logger.info(f"Judge deliberating | iteration={iteration}/{max_iterations}")

    try:
        nim = NIMClient()
        judge = JudgeAgent(nim_client=nim)
        decision = await judge.deliberate(evidence)

        if decision.action == "REQUEST_MORE_INVESTIGATION":
            logger.info(f"Judge: need more investigation → {decision.investigate_urls}")
            return {
                "iteration": iteration,
                "pending_urls": decision.investigate_urls,
                "judge_decision": {
                    "action": decision.action,
                    "reason": decision.reason,
                    "investigate_urls": decision.investigate_urls,
                },
            }
        else:
            # RENDER_VERDICT
            logger.info(
                f"Judge verdict: {decision.final_score}/100 "
                f"({decision.risk_level.value if decision.risk_level else 'unknown'})"
            )

            judge_dict = {
                "action": decision.action,
                "reason": decision.reason,
                "narrative": decision.forensic_narrative,
                "simple_narrative": getattr(decision, 'simple_narrative', ''),
                "recommendations": decision.recommendations,
                "simple_recommendations": getattr(decision, 'simple_recommendations', []),
                "dark_pattern_summary": decision.dark_pattern_summary,
                "entity_verification_summary": decision.entity_verification_summary,
                "evidence_timeline": decision.evidence_timeline,
                "site_type": getattr(decision, 'site_type', ''),
                "verdict_mode": getattr(decision, 'verdict_mode', 'expert'),
            }

            if decision.trust_score_result:
                tsr = decision.trust_score_result
                judge_dict["trust_score_result"] = {
                    "final_score": tsr.final_score,
                    "risk_level": tsr.risk_level.value,
                    "pre_override_score": tsr.pre_override_score,
                    "weighted_breakdown": tsr.weighted_breakdown,
                    "overrides_applied": [r.name for r in tsr.overrides_applied],
                    "sub_signals": {
                        s.name: {
                            "raw_score": s.raw_score,
                            "confidence": s.confidence,
                            "weighted_value": tsr.weighted_breakdown.get(s.name, 0),
                        }
                        for s in tsr.sub_signals
                    },
                    "explanation": tsr.explanation,
                }

            return {
                "iteration": iteration,
                "judge_decision": judge_dict,
                "status": "completed",
                "elapsed_seconds": time.time() - state.get("start_time", time.time()),
            }

    except Exception as e:
        logger.error(f"Judge exception: {e}", exc_info=True)
        return {
            "iteration": iteration,
            "errors": state.get("errors", []) + [f"Judge exception: {str(e)}"],
            "status": "aborted",
            "judge_decision": {
                "action": "RENDER_VERDICT",
                "reason": f"Judge failed: {str(e)}",
                "error": str(e),
            },
        }


# ============================================================
# Security Node
# ============================================================

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
            from analysis.security_headers import SecurityHeaderAnalyzer
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
            from analysis.phishing_checker import PhishingChecker
            checker = PhishingChecker()
            res = await checker.check(url)
            results["phishing"] = res.to_dict()
            logger.info(
                f"Phishing check: is_phishing={res.is_phishing}, "
                f"heuristic_flags={len(res.heuristic_flags)}, sources={len(res.sources)}"
            )
        except Exception as e:
            logger.warning(f"Phishing check failed: {e}")
            results["phishing"] = {"error": str(e)}

    # 3. Redirect Analysis
    if "redirect_chain" in enabled:
        try:
            from analysis.redirect_analyzer import RedirectAnalyzer
            analyzer = RedirectAnalyzer()
            res = await analyzer.analyze(url)
            results["redirects"] = res.to_dict()
            logger.info(
                f"Redirect analysis: {res.total_hops} hops, suspicious={bool(res.suspicion_flags)}"
            )
        except Exception as e:
            logger.warning(f"Redirect analysis failed: {e}")
            results["redirects"] = {"error": str(e)}

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

    return {"security_results": results}


# ============================================================
# Routing Functions
# ============================================================

def route_after_scout(state: AuditState) -> str:
    """Route after Scout: → VISION (success) | → ABORT (too many failures)."""
    failures = state.get("scout_failures", 0)
    scout_results = state.get("scout_results", [])

    # If 3+ consecutive failures with no successful results → abort
    if failures >= 3 and not scout_results:
        logger.warning("Scout failed 3+ times with no results — aborting")
        return "abort"

    # If we have results → continue to vision
    if scout_results:
        return "vision"

    # Edge case: failures but below threshold
    return "abort"


def route_after_judge(state: AuditState) -> str:
    """Route after Judge: → END (verdict) | → SCOUT (more investigation) | → force_verdict."""
    judge = state.get("judge_decision", {})
    status = state.get("status", "running")

    if status in ("completed", "aborted"):
        return "end"

    if judge.get("action") == "REQUEST_MORE_INVESTIGATION":
        pending = judge.get("investigate_urls", [])
        investigated = state.get("investigated_urls", [])
        max_pages = state.get("max_pages", settings.MAX_PAGES_PER_AUDIT)

        # Check page budget
        if len(investigated) >= max_pages:
            logger.info("Page budget exhausted — forcing verdict")
            return "force_verdict"

        if pending:
            return "scout"

    return "end"


async def force_verdict_node(state: AuditState) -> dict:
    """
    Force a verdict when the audit budget is exhausted but the Judge wanted
    more investigation.  Computes a trust score from whatever evidence we have.
    """
    from config.trust_weights import SubSignal, compute_trust_score

    vr = state.get("vision_result") or {}
    gr = state.get("graph_result") or {}

    visual_score = vr.get("visual_score", 0.5) if isinstance(vr, dict) else 0.5
    temporal_score = vr.get("temporal_score", 0.5) if isinstance(vr, dict) else 0.5
    graph_score = gr.get("graph_score", 0.5) if isinstance(gr, dict) else 0.5
    meta_score = gr.get("meta_score", 0.5) if isinstance(gr, dict) else 0.5

    # Structural score placeholder (DOM analysis not always present)
    structural_score = 0.5

    signals = {
        "visual": SubSignal(name="visual", raw_score=visual_score, confidence=0.7),
        "structural": SubSignal(name="structural", raw_score=structural_score, confidence=0.3),
        "temporal": SubSignal(name="temporal", raw_score=temporal_score, confidence=0.6),
        "graph": SubSignal(name="graph", raw_score=graph_score, confidence=0.7),
        "meta": SubSignal(name="meta", raw_score=meta_score, confidence=0.8),
        "security": SubSignal(name="security", raw_score=0.5, confidence=0.3),
    }

    # Extract override info from graph result
    di = gr.get("domain_intel", {}) if isinstance(gr, dict) else {}
    ssl_status = di.get("has_ssl") if isinstance(di, dict) else None
    if ssl_status is None:
        # Check scout metadata
        for sr in state.get("scout_results", []):
            if isinstance(sr, dict):
                meta = sr.get("page_metadata", {})
                ssl_status = meta.get("has_ssl")
                break

    domain_age_days = di.get("age_days") if isinstance(di, dict) else None

    tsr = compute_trust_score(
        signals,
        ssl_status=ssl_status,
        domain_age_days=domain_age_days,
    )

    logger.info(
        f"Forced verdict: {tsr.final_score}/100 ({tsr.risk_level.value}) "
        f"[budget exhausted, partial evidence]"
    )

    judge_dict = {
        "action": "RENDER_VERDICT",
        "reason": "Budget exhausted — verdict based on available evidence",
        "narrative": (
            f"Audit terminated due to page budget. Based on partial evidence: "
            f"visual score {visual_score:.2f}, graph score {graph_score:.2f}, "
            f"meta score {meta_score:.2f}. "
            f"Domain age: {domain_age_days or 'unknown'} days. "
            f"Trust score: {tsr.final_score}/100 ({tsr.risk_level.value})."
        ),
        "recommendations": ["Run a deeper audit tier for a more thorough investigation."],
        "dark_pattern_summary": [],
        "entity_verification_summary": [],
        "evidence_timeline": [],
        "trust_score_result": {
            "final_score": tsr.final_score,
            "risk_level": tsr.risk_level.value,
            "pre_override_score": tsr.pre_override_score,
            "weighted_breakdown": tsr.weighted_breakdown,
            "overrides_applied": [r.name for r in tsr.overrides_applied],
            "sub_signals": {
                s.name: {
                    "raw_score": s.raw_score,
                    "confidence": s.confidence,
                    "weighted_value": tsr.weighted_breakdown.get(s.name, 0),
                }
                for s in tsr.sub_signals
            },
            "explanation": tsr.explanation,
        },
    }

    return {
        "judge_decision": judge_dict,
        "status": "completed",
        "elapsed_seconds": time.time() - state.get("start_time", time.time()),
    }


# ============================================================
# Graph Builder
# ============================================================

def build_audit_graph() -> StateGraph:
    """
    Build the LangGraph state machine for a Veritas audit.

    Graph topology:
        START → scout → [route] → vision → graph → judge → [route] → END
                  ↑                                           |
                  └───────────── (more investigation) ────────┘
    """
    graph = StateGraph(AuditState)

    # Add nodes
    graph.add_node("scout", scout_node)
    graph.add_node("security", security_node)
    graph.add_node("vision", vision_node)
    graph.add_node("graph", graph_node)
    graph.add_node("judge", judge_node)
    graph.add_node("force_verdict", force_verdict_node)

    # Set entry point
    graph.set_entry_point("scout")

    # Add edges
    graph.add_conditional_edges(
        "scout",
        route_after_scout,
        {
            "vision": "security",   # Scout → Security → Vision
            "abort": END,
        },
    )
    graph.add_edge("security", "vision")
    graph.add_edge("vision", "graph")
    graph.add_edge("graph", "judge")
    graph.add_conditional_edges(
        "judge",
        route_after_judge,
        {
            "scout": "scout",
            "force_verdict": "force_verdict",
            "end": END,
        },
    )
    graph.add_edge("force_verdict", END)

    return graph


# ============================================================
# Orchestrator — High-Level API
# ============================================================

class VeritasOrchestrator:
    """
    High-level API for running a Veritas audit.

    Usage:
        orchestrator = VeritasOrchestrator()
        result = await orchestrator.audit("https://suspicious-site.com")

        print(f"Score: {result['judge_decision']['trust_score']['final_score']}")
        print(f"Risk: {result['judge_decision']['trust_score']['risk_level']}")
    """

    def __init__(self):
        self._graph = build_audit_graph()
        self._compiled = self._graph.compile()

    async def audit(
        self,
        url: str,
        tier: str = "standard_audit",
        verdict_mode: str = "expert",
        enabled_security_modules: Optional[list[str]] = None,
    ) -> AuditState:
        """
        Run a complete audit on a URL using sequential node execution.

        This bypasses LangGraph's ainvoke to avoid Python 3.14 asyncio
        CancelledError issues, while keeping all node logic intact.

        Args:
            url: Target URL to audit
            tier: "quick_scan", "standard_audit", or "deep_forensic"

        Returns:
            Final AuditState dict with all results
        """
        tier_config = settings.AUDIT_TIERS.get(tier, settings.AUDIT_TIERS["standard_audit"])

        state: AuditState = {
            "url": url,
            "audit_tier": tier,
            "iteration": 0,
            "max_iterations": settings.MAX_ITERATIONS,
            "max_pages": tier_config["pages"],
            "status": "running",
            "scout_results": [],
            "vision_result": None,
            "graph_result": None,
            "judge_decision": None,
            "pending_urls": [url],
            "investigated_urls": [],
            "start_time": time.time(),
            "elapsed_seconds": 0,
            "errors": [],
            "scout_failures": 0,
            "nim_calls_used": 0,
            # V2 fields
            "site_type": "",
            "site_type_confidence": 0.0,
            "verdict_mode": verdict_mode,
            "security_results": {},
            "enabled_security_modules": enabled_security_modules or getattr(
                settings, 'ENABLED_SECURITY_MODULES', ["security_headers", "phishing_db"]
            ),
        }

        logger.info(f"Starting Veritas audit: {url} | tier={tier} | max_pages={tier_config['pages']}")

        def _emit(phase: str, step: str, pct: int, detail: str = "", **extra):
            """Emit a structured progress marker for UI streaming."""
            msg = {"phase": phase, "step": step, "pct": pct, "detail": detail}
            msg.update(extra)
            print(f"##PROGRESS:{_json.dumps(msg)}", flush=True)

        _emit("init", "starting", 0, f"Initializing {tier} audit for {url}")

        try:
            for iteration in range(settings.MAX_ITERATIONS):
                state["iteration"] = iteration + 1
                logger.info(f"--- Iteration {state['iteration']} ---")
                _emit("iteration", "start", 5, f"Iteration {state['iteration']}", iteration=state["iteration"])

                # 1. Scout
                _emit("scout", "navigating", 10, f"Scout agent navigating to target...", iteration=state["iteration"])
                try:
                    scout_update = await scout_node(state)
                    state.update(scout_update)
                    n_shots = sum(len(sr.get("screenshots", [])) for sr in state.get("scout_results", []))
                    _emit("scout", "done", 25, f"Captured {n_shots} screenshots", screenshots=n_shots, iteration=state["iteration"])
                except Exception as e:
                    logger.error(f"Scout failed: {e}")
                    state["errors"].append(f"Scout: {e}")
                    state["scout_failures"] = state.get("scout_failures", 0) + 1
                    _emit("scout", "error", 25, str(e))

                # Route after scout
                route = route_after_scout(state)
                if route == "abort":
                    state["status"] = "aborted"
                    state["errors"].append("Scout failed too many times — aborted")
                    break

                # 1b. Security modules
                _emit("security", "scanning", 27, "Running security analysis modules...", iteration=state["iteration"])
                try:
                    sec_update = await security_node(state)
                    state.update(sec_update)
                    sec_modules = list((state.get("security_results") or {}).keys())
                    _emit("security", "done", 30, f"Security modules: {', '.join(sec_modules)}", modules=sec_modules)
                except Exception as e:
                    logger.error(f"Security node failed: {e}")
                    state["errors"].append(f"Security: {e}")
                    _emit("security", "error", 30, str(e))

                # 2. Vision
                _emit("vision", "analyzing", 30, "Vision agent analyzing screenshots with NIM VLM...", iteration=state["iteration"])
                try:
                    vision_update = await vision_node(state)
                    state.update(vision_update)
                    vr = state.get("vision_result") or {}
                    n_findings = len(vr.get("findings", []))
                    n_calls = vr.get("nim_calls_made", 0)
                    _emit("vision", "done", 55, f"{n_findings} dark patterns detected, {n_calls} NIM calls", findings=n_findings, nim_calls=n_calls)
                except Exception as e:
                    logger.error(f"Vision failed: {e}")
                    state["errors"].append(f"Vision: {e}")
                    _emit("vision", "error", 55, str(e))

                # 3. Graph
                _emit("graph", "investigating", 60, "Graph agent running WHOIS, DNS & web verification...", iteration=state["iteration"])
                try:
                    graph_update = await graph_node(state)
                    state.update(graph_update)
                    gr = state.get("graph_result") or {}
                    age = gr.get("domain_age_days", "?")
                    n_nodes = gr.get("graph_node_count", 0)
                    _emit("graph", "done", 75, f"Domain age: {age}d, {n_nodes} graph nodes", domain_age=age, nodes=n_nodes)
                except Exception as e:
                    logger.error(f"Graph failed: {e}")
                    state["errors"].append(f"Graph: {e}")
                    _emit("graph", "error", 75, str(e))

                # 4. Judge
                _emit("judge", "deliberating", 80, "Judge agent synthesizing evidence & computing trust score...", iteration=state["iteration"])
                try:
                    judge_update = await judge_node(state)
                    state.update(judge_update)
                    jd = state.get("judge_decision") or {}
                    tr = jd.get("trust_score_result") or {}
                    score = tr.get("final_score", "?")
                    risk = tr.get("risk_level", "?")
                    _emit("judge", "done", 90, f"Trust Score: {score}/100 ({risk})", trust_score=score, risk_level=risk)
                except Exception as e:
                    logger.error(f"Judge failed: {e}")
                    state["errors"].append(f"Judge: {e}")
                    _emit("judge", "error", 90, str(e))

                # Route after judge
                route = route_after_judge(state)
                if route == "end":
                    break
                elif route == "force_verdict":
                    try:
                        verdict_update = await force_verdict_node(state)
                        state.update(verdict_update)
                    except Exception as e:
                        logger.error(f"Force verdict failed: {e}")
                        state["errors"].append(f"ForceVerdict: {e}")
                    break
                elif route == "scout":
                    # Add investigate URLs to pending
                    jd = state.get("judge_decision", {})
                    if isinstance(jd, dict):
                        new_urls = jd.get("investigate_urls", [])
                        state["pending_urls"] = new_urls
                    continue

            # Finalize
            if state["status"] == "running":
                state["status"] = "completed"
            state["elapsed_seconds"] = time.time() - state["start_time"]

            _emit("complete", "done", 100, f"Audit complete in {state['elapsed_seconds']:.0f}s",
                  elapsed=round(state["elapsed_seconds"], 1))

            logger.info(
                f"Audit complete: {url} | "
                f"status={state.get('status')} | "
                f"elapsed={state['elapsed_seconds']:.1f}s | "
                f"pages={len(state.get('investigated_urls', []))} | "
                f"errors={len(state.get('errors', []))}"
            )

            return state

        except BaseException as e:
            logger.error(f"Orchestrator exception: {e}", exc_info=True)
            state["status"] = "aborted"
            state["errors"].append(f"Orchestrator exception: {str(e)}")
            state["elapsed_seconds"] = time.time() - state["start_time"]
            return state
