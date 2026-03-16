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
import multiprocessing
import os
import time
from dataclasses import asdict
from typing import Annotated, Any, Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from veritas.agents.graph_investigator import GraphInvestigator, GraphResult
from veritas.agents.judge import AuditEvidence, JudgeAgent, JudgeDecision
from veritas.agents.scout import ScoutResult, StealthScout
from veritas.agents.vision import VisionAgent, VisionResult
from veritas.config import settings
from veritas.config.trust_weights import TrustScoreResult
from veritas.core.complexity_analyzer import ComplexityAnalyzer
from veritas.core.degradation import DegradedResult, FallbackManager, FallbackMode
from veritas.core.ipc import ProgressEvent, SecurityModeCompleted, SecurityModeStarted, safe_put
from veritas.core.nim_client import NIMClient
from veritas.core.timeout_manager import ComplexityMetrics, TimeoutManager, TimeoutStrategy

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
    security_mode: str                   # "agent", "function", or "function_fallback"
    security_summary: dict               # Aggregated metrics for the security phase
    enabled_security_modules: list[str]  # Which security modules to run


# ============================================================
# ============================================================
# Node Functions — imported from veritas.core.nodes package
# ============================================================
# AuditState is defined above, so nodes can safely import it
from veritas.core.nodes import (  # noqa: E402
    scout_node,
    vision_node,
    graph_node,
    judge_node,
    security_node_with_agent,
    security_node,
    route_after_scout,
    route_after_judge,
    force_verdict_node,
)
from veritas.core.nodes.security import _get_security_modules_for_tier  # noqa: E402

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
    graph.add_node("security", security_node_with_agent)
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

    def __init__(
        self,
        progress_queue: Optional[multiprocessing.Queue] = None,
        use_adaptive_timeout: bool = False,
        use_circuit_breaker: bool = False,
        progress_emitter: Optional["ProgressEmitter"] = None,
        use_progress_streaming: bool = False
    ):
        """
        Initialize VeritasOrchestrator.

        Args:
            progress_queue: Optional multiprocessing queue for progress events
            use_adaptive_timeout: Enable adaptive timeout management (requires complexity analysis)
            use_circuit_breaker: Enable circuit breaker with graceful degradation
            progress_emitter: ProgressEmitter for WebSocket streaming with token-bucket rate limiting
            use_progress_streaming: Enable WebSocket-based progress streaming
        """
        self._graph = build_audit_graph()
        self._compiled = self._graph.compile()
        self.progress_queue = progress_queue
        self.use_adaptive_timeout = use_adaptive_timeout
        self.use_circuit_breaker = use_circuit_breaker

        # Initialize progress streaming components
        self._progress_emitter = progress_emitter
        self.use_progress_streaming = use_progress_streaming
        self._time_estimator: Optional["CompletionTimeEstimator"] = None

        if use_progress_streaming:
            from veritas.core.progress import ProgressEmitter, CompletionTimeEstimator
            self._progress_emitter = progress_emitter or ProgressEmitter()
            self._time_estimator = CompletionTimeEstimator()
            logger.info("ProgressStreaming enabled with WebSocket")

        # Initialize smart orchestrator components
        self._timeout_manager: Optional[TimeoutManager] = None
        self._fallback_manager: Optional[FallbackManager] = None
        self._complexity_analyzer = ComplexityAnalyzer()

        if use_adaptive_timeout:
            self._timeout_manager = TimeoutManager(
                strategy=TimeoutStrategy.ADAPTIVE
            )
            logger.info("TimeoutManager enabled with ADAPTIVE strategy")

        if use_circuit_breaker:
            self._fallback_manager = FallbackManager()
            self._register_fallback_functions()
            logger.info("FallbackManager enabled with circuit breakers")

        # Track quality penalties from degraded agents
        self._accumulated_quality_penalty: float = 0.0

    def _emit(self, phase: str, step: str, pct: int, detail: str = "", **extra):
        """Emit progress via Queue or fallback to stdout.

        Args:
            phase: Audit phase name (e.g., "Scout", "Vision", "Graph", "Judge")
            step: Step within phase (e.g., "navigating", "scanning", "done", "error")
            pct: Progress percentage (0-100)
            detail: Human-readable detail message
            **extra: Additional fields to include in event
        """
        if self.progress_queue is not None:
            # Queue mode: Use ProgressEvent dataclass
            event = ProgressEvent(
                type="progress",
                phase=phase,
                step=step,
                pct=pct,
                detail=detail,
                summary=extra.get("summary") or {},
                timestamp=time.time(),
            )
            # Add extra fields to event
            for k, v in extra.items():
                if k not in ("summary",):
                    setattr(event, k, v)
            safe_put(self.progress_queue, event, logger, timeout=1.0)
        else:
            # Legacy stdout fallback (existing behavior)
            msg = {"phase": phase, "step": step, "pct": pct, "detail": detail}
            msg.update(extra)
            print(f"##PROGRESS:{_json.dumps(msg)}", flush=True)

    def _register_fallback_functions(self):
        """Register fallback functions for each agent type with FallbackManager."""
        if self._fallback_manager is None:
            return

        # Vision fallback: simplified analysis
        async def vision_fallback(**kwargs) -> dict:
            return {
                "visual_score": 0.5,
                "temporal_score": 0.5,
                "findings": [],
                "temporal_findings": [],
                "screenshots_analyzed": 0,
                "fallback_used": True,
                "errors": ["Vision agent unavailable"],
            }

        self._fallback_manager.register_fallback("vision", vision_fallback, FallbackMode.SIMPLIFIED)

        # Graph fallback: basic metadata only
        async def graph_fallback(**kwargs) -> dict:
            return {
                "graph_score": 0.5,
                "meta_score": 0.5,
                "meta_analysis": {},
                "ip_geolocation": {},
                "domain_age_days": -1,
                "has_ssl": False,
                "graph_node_count": 0,
                "entities": [],
                "fallback_used": True,
                "errors": ["Graph agent unavailable"],
            }

        self._fallback_manager.register_fallback("graph", graph_fallback, FallbackMode.SIMPLIFIED)

        # Security fallback: empty results
        async def security_fallback(**kwargs) -> dict:
            return {
                "overall_score": 0.5,
                "findings": [],
                "modules_run": [],
                "errors": ["Security modules unavailable"],
            }

        self._fallback_manager.register_fallback("security", security_fallback, FallbackMode.SIMPLIFIED)

        # Judge fallback: placeholder verdict
        async def judge_fallback(**kwargs) -> dict:
            # Force verdict from partial evidence
            from veritas.config.trust_weights import SubSignal, compute_trust_score

            vr = kwargs.get("vision_result", {})
            gr = kwargs.get("graph_result", {})

            visual_score = vr.get("visual_score", 0.5) if isinstance(vr, dict) else 0.5
            temporal_score = vr.get("temporal_score", 0.5) if isinstance(vr, dict) else 0.5
            graph_score = gr.get("graph_score", 0.5) if isinstance(gr, dict) else 0.5
            meta_score = gr.get("meta_score", 0.5) if isinstance(gr, dict) else 0.5

            signals = {
                "visual": SubSignal(name="visual", raw_score=visual_score, confidence=0.7),
                "structural": SubSignal(name="structural", raw_score=0.5, confidence=0.3),
                "temporal": SubSignal(name="temporal", raw_score=temporal_score, confidence=0.6),
                "graph": SubSignal(name="graph", raw_score=graph_score, confidence=0.7),
                "meta": SubSignal(name="meta", raw_score=meta_score, confidence=0.8),
                "security": SubSignal(name="security", raw_score=0.5, confidence=0.3),
            }

            tsr = compute_trust_score(signals)

            return {
                "action": "RENDER_VERDICT",
                "reason": "Fallback verdict due to agent unavailability",
                "narrative": f"Trust score: {tsr.final_score}/100 ({tsr.risk_level.value}) based on partial evidence.",
                "recommendations": ["Run a deeper audit tier for more thorough investigation."],
                "dark_pattern_summary": [],
                "entity_verification_summary": [],
                "evidence_timeline": [],
                "trust_score_result": {
                    "final_score": tsr.final_score,
                    "risk_level": tsr.risk_level.value,
                    "pre_override_score": tsr.pre_override_score,
                    "weighted_breakdown": tsr.weighted_breakdown,
                    "overrides_applied": [r.name for r in tsr.overrides_applied],
                    "explanation": tsr.explanation,
                },
                "fallback_used": True,
            }

        self._fallback_manager.register_fallback("judge", judge_fallback, FallbackMode.ALTERNATIVE)

        # OSINT fallback: empty results
        async def osint_fallback(**kwargs) -> dict:
            return {
                "osint_sources": [],
                "osint_findings": [],
                "cti_findings": [],
                "errors": ["OSINT unavailable"],
            }

        self._fallback_manager.register_fallback("osint", osint_fallback, FallbackMode.NONE)

    async def _execute_agent_smart(
        self,
        agent_name: str,
        primary_fn: Callable,
        state: AuditState,
        timeout: Optional[int] = None
    ) -> tuple[dict, float]:
        """
        Execute agent with timeout and circuit breaker support.

        Args:
            agent_name: Name of agent (vision, graph, security, judge)
            primary_fn: Async function to execute
            state: Current audit state
            timeout: Optional timeout override in seconds

        Returns:
            Tuple of (result_dict, quality_penalty)
        """
        start_time = time.time()
        quality_penalty = 0.0

        # Build context dict for function execution
        context = {
            "state": state,
            **state
        }

        if self.use_circuit_breaker and self._fallback_manager is not None:
            # Execute with circuit breaker
            degraded_result = await self._fallback_manager.execute_with_fallback(
                agent_name, primary_fn, context, timeout=timeout
            )

            result = degraded_result.result_data

            # Track degradation
            if degraded_result.is_degraded():
                quality_penalty = degraded_result.quality_penalty
                self._accumulated_quality_penalty += quality_penalty

                # Track degraded agents
                if agent_name not in state.get("_degraded_agents", []):
                    existing = state.get("_degraded_agents", [])
                    if isinstance(state, dict):
                        state["_degraded_agents"] = existing + [agent_name]

                logger.warning(
                    f"Agent '{agent_name}' degraded: "
                    f"mode={degraded_result.fallback_mode.value}, "
                    f"penalty={quality_penalty:.2f}, "
                    f"missing={degraded_result.missing_data}"
                )

                # Emit degradation via ProgressEmitter
                if self.use_progress_streaming and self._progress_emitter:
                    await self._progress_emitter.emit_agent_status(
                        agent_name,
                        "degraded",
                        f"Fallback mode: {degraded_result.fallback_mode.value}"
                    )
                    await self._progress_emitter.emit_error(
                        "agent_degraded",
                        f"{agent_name} using fallback: {degraded_result.error_message or 'Unknown reason'}",
                        agent_name,
                        recoverable=True
                    )

                if degraded_result.error_message:
                    state["errors"].append(f"{agent_name} degraded: {degraded_result.error_message}")
        else:
            # Direct execution with timeout
            try:
                if timeout:
                    result = await asyncio.wait_for(primary_fn(state), timeout=timeout)
                else:
                    result = await primary_fn(state)
            except asyncio.TimeoutError:
                logger.error(f"Agent '{agent_name}' timeout after {timeout}s")
                quality_penalty = 0.5
                self._accumulated_quality_penalty += quality_penalty
                state["errors"].append(f"{agent_name}: timeout after {timeout}s")
                result = {}
            except Exception as e:
                logger.error(f"Agent '{agent_name}' error: {e}")
                quality_penalty = 0.7
                self._accumulated_quality_penalty += quality_penalty
                state["errors"].append(f"{agent_name}: {str(e)}")
                result = {}

        # Record execution time for learning
        elapsed_ms = int((time.time() - start_time) * 1000)
        if self._timeout_manager is not None:
            site_type = state.get("site_type", "unknown")
            self._timeout_manager.record_execution(
                site_type, agent_name, elapsed_ms, success=(quality_penalty == 0.0)
            )

            # Emit adaptive timeout adjustment via ProgressEmitter
            if self.use_progress_streaming and self._progress_emitter and timeout:
                await self._progress_emitter.emit_progress(
                    agent_name,
                    "timeout_adjusted",
                    50,
                    f"Timeout adjusted to {timeout}s"
                )

        # Update quality penalty in state
        if isinstance(state, dict):
            state["_quality_penalty"] = self._accumulated_quality_penalty

        return result, quality_penalty

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

        # Reset quality penalty for each audit
        self._accumulated_quality_penalty = 0.0

        # Add complexity tracking fields to state
        state_with_complexity = {
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
            "security_mode": "",  # Will be set by security_node_with_agent
            "security_summary": {},
            "enabled_security_modules": enabled_security_modules or _get_security_modules_for_tier(tier),
            # Smart orchestrator fields (added via dict after to maintain TypedDict compatibility)
            "_timeout_config": None,  # TimeoutConfig computed from complexity
            "_complexity_score": 0.0,  # Complexity score from analysis
            "_estimated_remaining_time": 0,  # Estimated time for remaining agents
            "_quality_penalty": 0.0,  # Accumulated quality penalty
            "_degraded_agents": [],  # List of degraded agent names
        }

        state: AuditState = state_with_complexity  # type: ignore

        logger.info(f"Starting Veritas audit: {url} | tier={tier} | max_pages={tier_config['pages']}")

        self._emit("init", "starting", 0, f"Initializing {tier} audit for {url}")

        # Emit orchestrator start via ProgressEmitter
        if self.use_progress_streaming and self._progress_emitter:
            await self._progress_emitter.emit_agent_status("Orchestrator", "running", f"Starting audit: {url}")

        try:
            for iteration in range(settings.MAX_ITERATIONS):
                state["iteration"] = iteration + 1
                logger.info(f"--- Iteration {state['iteration']} ---")
                self._emit("iteration", "start", 5, f"Iteration {state['iteration']}", iteration=state["iteration"])

                # 1. Scout
                self._emit("scout", "navigating", 10, f"Scout agent navigating to target...", iteration=state["iteration"])
                try:
                    scout_update = await scout_node(state)
                    state.update(scout_update)
                    n_shots = sum(len(sr.get("screenshots", [])) for sr in state.get("scout_results", []))
                    self._emit("scout", "done", 25, f"Captured {n_shots} screenshots", screenshots=n_shots, iteration=state["iteration"])

                    # Emit Scout completion via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        site_type = state.get("site_type", "unknown")
                        await self._progress_emitter.emit_agent_status("Scout", "completed")
                        await self._progress_emitter.emit_progress("Overall", "Scout", 25, f"Scout complete: {n_shots} screenshots")
                except Exception as e:
                    logger.error(f"Scout failed: {e}")
                    state["errors"].append(f"Scout: {e}")
                    state["scout_failures"] = state.get("scout_failures", 0) + 1
                    self._emit("scout", "error", 25, str(e))

                    # Emit Scout error via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        await self._progress_emitter.emit_error("scout_error", str(e), "Scout", recoverable=True)
                        await self._progress_emitter.emit_agent_status("Scout", "failed", str(e))

                # Route after scout
                route = route_after_scout(state)
                if route == "abort":
                    state["status"] = "aborted"
                    state["errors"].append("Scout failed too many times — aborted")
                    break

                # Collect complexity metrics after Scout completes (only once per audit)
                if self.use_adaptive_timeout and iteration == 0 and state.get("scout_results"):
                    try:
                        # Create mock result objects from state data
                        primary_scout = state.get("scout_results", [{}])[0]
                        state["url"] = state.get("url", primary_scout.get("url", url))

                        # Analyze complexity from scout results
                        complexity_metrics = self._complexity_analyzer.analyze_page(
                            scout_result=primary_scout,
                            vision_result=None,  # Vision not run yet
                            security_result=None
                        )

                        complexity_score = complexity_metrics.calculate_complexity_score()

                        if isinstance(state, dict):
                            state["_complexity_score"] = complexity_score
                            state["site_type"] = complexity_metrics.site_type

                        # Calculate timeout config
                        if self._timeout_manager is not None:
                            timeout_config = self._timeout_manager.calculate_timeout_config(
                                complexity_metrics
                            )

                            if isinstance(state, dict):
                                state["_timeout_config"] = timeout_config.to_dict()

                            logger.info(
                                f"Complexity analysis: score={complexity_score:.3f}, "
                                f"site_type={complexity_metrics.site_type}"
                            )

                        # Calculate estimated remaining time
                        if self._timeout_manager is not None:
                            remaining_agents = ["vision", "graph", "judge"]
                            estimated_sec = self._timeout_manager.get_estimated_remaining_time(
                                complexity_metrics.site_type, remaining_agents
                            )

                            if isinstance(state, dict):
                                state["_estimated_remaining_time"] = estimated_sec

                            self._emit(
                                "estimate",
                                "calculated",
                                27,
                                f"Estimated {estimated_sec}s remaining for {len(remaining_agents)} agents",
                                estimated_remaining=estimated_sec
                            )

                            # Emit estimated time via ProgressEmitter
                            if self.use_progress_streaming and self._progress_emitter:
                                await self._progress_emitter.emit_progress(
                                    "Overall",
                                    "estimated_time",
                                    27,
                                    f"Estimated {estimated_sec}s remaining"
                                )
                    except Exception as e:
                        logger.warning(f"Complexity analysis failed: {e}")

                # 1b. Security modules
                self._emit("security", "scanning", 27, "Running security analysis modules...", iteration=state["iteration"])
                try:
                    # Get timeout from adaptive config or use default
                    timeout = None
                    if self.use_adaptive_timeout and self._timeout_manager is not None:
                        tc_dict = state.get("_timeout_config", {})
                        timeout = tc_dict.get("security")

                    # Execute with smart wrapper
                    sec_update, sec_penalty = await self._execute_agent_smart(
                        "security", security_node_with_agent, state, timeout
                    )
                    state.update(sec_update)
                    sec_modules = list((state.get("security_results") or {}).keys())
                    security_mode = sec_update.get("security_mode", "unknown")
                    degr_str = " (degraded)" if sec_penalty > 0 else ""
                    self._emit("security", "done", 30, f"Security modules: {', '.join(sec_modules)} (mode={security_mode}){degr_str}", modules=sec_modules, security_mode=security_mode, security_results=state.get("security_results", {}))
                except Exception as e:
                    logger.error(f"Security node failed: {e}")
                    state["errors"].append(f"Security: {e}")
                    self._emit("security", "error", 30, str(e))

                # 2. Vision
                self._emit("vision", "analyzing", 30, "Vision agent analyzing screenshots with NIM VLM...", iteration=state["iteration"])
                try:
                    # Get timeout from adaptive config or use default
                    timeout = None
                    if self.use_adaptive_timeout and self._timeout_manager is not None:
                        tc_dict = state.get("_timeout_config", {})
                        timeout = tc_dict.get("vision")

                    # Execute with smart wrapper
                    vision_update, vision_penalty = await self._execute_agent_smart(
                        "vision", vision_node, state, timeout
                    )
                    state.update(vision_update)
                    vr = state.get("vision_result") or {}
                    n_findings = len(vr.get("findings", []))
                    n_calls = vr.get("nim_calls_made", 0)
                    degr_str = " (degraded)" if vision_penalty > 0 else ""
                    self._emit("vision", "done", 55, f"{n_findings} dark patterns detected, {n_calls} NIM calls{degr_str}", findings=n_findings, nim_calls=n_calls)

                    # Emit Vision completion via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        await self._progress_emitter.emit_agent_status("Vision", "completed")
                        await self._progress_emitter.emit_progress("Overall", "Vision", 50, f"Vision complete: {n_findings} findings")
                except Exception as e:
                    logger.error(f"Vision failed: {e}")
                    state["errors"].append(f"Vision: {e}")
                    self._emit("vision", "error", 55, str(e))

                    # Emit Vision error via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        await self._progress_emitter.emit_error("vision_error", str(e), "Vision", recoverable=True)
                        await self._progress_emitter.emit_agent_status("Vision", "failed", str(e))

                # 3. Graph
                self._emit("graph", "investigating", 60, "Graph agent: full investigation (WHOIS, DNS, SSL, MetaAnalyzer, Entity Verification, OSINT, CTI)...", iteration=state["iteration"])
                try:
                    # Get timeout from adaptive config or use default
                    timeout = None
                    if self.use_adaptive_timeout and self._timeout_manager is not None:
                        tc_dict = state.get("_timeout_config", {})
                        timeout = tc_dict.get("graph")

                    # Execute with smart wrapper
                    graph_update, graph_penalty = await self._execute_agent_smart(
                        "graph", graph_node, state, timeout
                    )
                    state.update(graph_update)
                    gr = state.get("graph_result") or {}
                    age = gr.get("domain_age_days", "?")
                    n_nodes = gr.get("graph_node_count", 0)
                    n_verify = len(gr.get("verifications", []))
                    n_incon = len(gr.get("inconsistencies", []))
                    n_osint = len([k for k in gr.get("osint_sources", {}) if k != "_consensus"])
                    degr_str = " (degraded)" if graph_penalty > 0 else ""
                    detail = (
                        f"Domain age: {age}d, {n_nodes} graph nodes, "
                        f"{n_verify} verifications, {n_incon} inconsistencies, "
                        f"{n_osint} OSINT sources{degr_str}"
                    )
                    self._emit("graph", "done", 75, detail, domain_age=age, nodes=n_nodes, graph_result=state.get("graph_result", {}))

                    # Emit Graph completion via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        await self._progress_emitter.emit_agent_status("Graph", "completed")
                        await self._progress_emitter.emit_progress("Overall", "Graph", 70, f"Graph complete: {n_nodes} entities")
                except Exception as e:
                    logger.error(f"Graph failed: {e}")
                    state["errors"].append(f"Graph: {e}")
                    self._emit("graph", "error", 75, str(e))

                    # Emit Graph error via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        await self._progress_emitter.emit_error("graph_error", str(e), "Graph", recoverable=True)
                        await self._progress_emitter.emit_agent_status("Graph", "failed", str(e))

                # 4. Judge
                self._emit("judge", "deliberating", 80, "Judge agent synthesizing evidence & computing trust score...", iteration=state["iteration"])
                try:
                    # Get timeout from adaptive config or use default
                    timeout = None
                    if self.use_adaptive_timeout and self._timeout_manager is not None:
                        tc_dict = state.get("_timeout_config", {})
                        timeout = tc_dict.get("judge")

                    # Execute with smart wrapper
                    judge_update, judge_penalty = await self._execute_agent_smart(
                        "judge", judge_node, state, timeout
                    )
                    state.update(judge_update)
                    jd = state.get("judge_decision") or {}
                    tr = jd.get("trust_score_result") or {}
                    score = tr.get("final_score", "?")
                    risk = tr.get("risk_level", "?")
                    degr_str = " (degraded)" if judge_penalty > 0 else ""
                    self._emit("judge", "done", 90, f"Trust Score: {score}/100 ({risk}){degr_str}", trust_score=score, risk_level=risk)

                    # Emit Judge completion via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        await self._progress_emitter.emit_agent_status("Judge", "completed")
                        await self._progress_emitter.emit_progress("Overall", "Judge", 90, f"Judge complete: Score {score}/100 ({risk})")

                        # Interesting highlight for findings
                        n_findings = len((state.get("vision_result") or {}).get("findings", []))
                        if n_findings > 0:
                            await self._progress_emitter.emit_interesting_highlight(
                                f"Judge reviewed {n_findings} findings, computed final trust score",
                                phase="Judge"
                            )
                except Exception as e:
                    logger.error(f"Judge failed: {e}")
                    state["errors"].append(f"Judge: {e}")
                    self._emit("judge", "error", 90, str(e))

                    # Emit Judge error via ProgressEmitter
                    if self.use_progress_streaming and self._progress_emitter:
                        await self._progress_emitter.emit_error("judge_error", str(e), "Judge", recoverable=True)
                        await self._progress_emitter.emit_agent_status("Judge", "failed", str(e))

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

            # Apply quality penalty to final trust score
            quality_penalty = self._accumulated_quality_penalty
            if quality_penalty > 0:
                jd = state.get("judge_decision")
                if isinstance(jd, dict):
                    tr = jd.get("trust_score_result")
                    if isinstance(tr, dict):
                        original_score = tr.get("final_score", 100)
                        # Subtract penalty percentage (penalty is 0.0-1.0)
                        adjusted_score = int(original_score * (1.0 - quality_penalty))
                        adjusted_score = max(0, min(100, adjusted_score))

                        tr["final_score"] = adjusted_score
                        tr["quality_penalty_applied"] = quality_penalty
                        tr["original_score"] = original_score
                        tr["degraded_agents"] = state.get("_degraded_agents", [])

                        # Recalculate risk level if needed
                        if adjusted_score <= 20:
                            tr["risk_level"] = "CRITICAL"
                        elif adjusted_score <= 40:
                            tr["risk_level"] = "HIGH"
                        elif adjusted_score <= 50:
                            tr["risk_level"] = "MODERATE"
                        elif adjusted_score <= 75:
                            tr["risk_level"] = "LOW"
                        else:
                            tr["risk_level"] = "SAFE"

                        logger.info(
                            f"Quality penalty applied: {quality_penalty:.2%} "
                            f"({original_score} -> {adjusted_score}) "
                            f"degraded agents: {state.get('_degraded_agents', [])}"
                        )

            # Emit completion message with quality penalty info
            penalty_msg = f" (degraded: {quality_penalty:.0%})" if quality_penalty > 0 else ""
            self._emit("complete", "done", 100, f"Audit complete in {state['elapsed_seconds']:.0f}s{penalty_msg}",
                  elapsed=round(state["elapsed_seconds"], 1),
                  quality_penalty=quality_penalty,
                  degraded_agents=state.get("_degraded_agents", []))

            # Flush and emit completion via ProgressEmitter
            if self.use_progress_streaming and self._progress_emitter:
                # Flush any buffered findings
                await self._progress_emitter.flush()

                # Emit final progress update
                await self._progress_emitter.emit_progress("Overall", "complete", 100, f"Audit complete in {state['elapsed_seconds']:.0f}s")
                await self._progress_emitter.emit_agent_status("Orchestrator", "completed")

            logger.info(
                f"Audit complete: {url} | "
                f"status={state.get('status')} | "
                f"elapsed={state['elapsed_seconds']:.1f}s | "
                f"pages={len(state.get('investigated_urls', []))} | "
                f"errors={len(state.get('errors', []))} | "
                f"quality_penalty={quality_penalty:.2%}"
            )

            return state

        except BaseException as e:
            logger.error(f"Orchestrator exception: {type(e).__name__}: {e}", exc_info=True)
            state["status"] = "aborted"
            state["errors"].append(f"Orchestrator exception: {type(e).__name__}: {str(e) or 'no message'}")
            state["elapsed_seconds"] = time.time() - state["start_time"]

            # Emit error via ProgressEmitter
            if self.use_progress_streaming and self._progress_emitter:
                await self._progress_emitter.emit_error("orchestrator_exception", str(e), "Orchestrator", recoverable=True)
                await self._progress_emitter.emit_agent_status("Orchestrator", "failed", str(e))

            return state

