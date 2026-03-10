"""
Veritas — Routing Nodes

Graph routing functions and force verdict node for the audit graph.
Moved from veritas.core.orchestrator as part of Phase 13-04 refactoring.
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from veritas.config import settings

logger = logging.getLogger("veritas.orchestrator")

# Import AuditState for runtime type annotation resolution (needed by LangGraph introspection).
# Safe: AuditState is defined before nodes are imported in orchestrator.py.
try:
    from veritas.core.orchestrator import AuditState  # type: ignore[attr-defined]
except ImportError:
    AuditState = dict  # type: ignore[assignment,misc]


def route_after_scout(state: AuditState) -> str:
    """Route after Scout: -> VISION (success) | -> ABORT (too many failures)."""
    failures = state.get("scout_failures", 0)
    scout_results = state.get("scout_results", [])

    # If 3+ consecutive failures with no successful results -> abort
    if failures >= 3 and not scout_results:
        logger.warning("Scout failed 3+ times with no results - aborting")
        return "abort"

    # If we have results -> continue to vision
    if scout_results:
        return "vision"

    # Edge case: failures but below threshold
    return "abort"


def route_after_judge(state: AuditState) -> str:
    """Route after Judge: -> END (verdict) | -> SCOUT (more investigation) | -> force_verdict."""
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
            logger.info("Page budget exhausted - forcing verdict")
            return "force_verdict"

        if pending:
            return "scout"

    return "end"


async def force_verdict_node(state: AuditState) -> dict:
    """
    Force a verdict when the audit budget is exhausted but the Judge wanted
    more investigation.  Computes a trust score from whatever evidence we have.
    """
    from veritas.config.trust_weights import SubSignal, compute_trust_score

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
        "reason": "Budget exhausted - verdict based on available evidence",
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
