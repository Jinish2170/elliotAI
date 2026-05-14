"""
Unit tests for JudgeAgent._should_investigate_more early-exit confidence gate.

The early-exit gate lets the judge render a verdict once vision and graph agree
confidently, instead of crawling the full page budget. Regression target: audits
that looped 5-8 iterations when the verdict was already conclusive at iteration 1.
"""
from elliot.agents.judge import AuditEvidence, JudgeAgent
from elliot.agents.scout import ScoutResult
from elliot.agents.vision import VisionResult
from elliot.agents.graph_investigator import GraphResult


def _judge():
    # _should_investigate_more is pure decision logic — no NIM client needed.
    return JudgeAgent(nim_client=object())


def _scout_with_links():
    return ScoutResult(
        url="https://example.com",
        status="SUCCESS",
        page_metadata={"internal_links": ["https://example.com/about"]},
    )


def _evidence(vision_score, graph_score, iteration=1):
    return AuditEvidence(
        url="https://example.com",
        scout_results=[_scout_with_links()],
        vision_result=VisionResult(visual_score=vision_score),
        graph_result=GraphResult(graph_score=graph_score),
        iteration=iteration,
        max_iterations=5,
        max_pages=8,
        pages_investigated=1,
    )


def test_early_exit_when_both_signals_confidently_safe():
    # Both >= 0.75 confidence floor → render verdict, don't burn page budget.
    assert _judge()._should_investigate_more(_evidence(0.92, 0.85)) is False


def test_early_exit_when_both_signals_confidently_malicious():
    # Both <= 0.25 → conclusive malicious verdict, stop investigating.
    assert _judge()._should_investigate_more(_evidence(0.15, 0.20)) is False


def test_no_early_exit_before_min_iteration():
    # iteration 0 < early_exit_min_iteration → gate must not fire; deep-scan
    # block still requests more investigation.
    assert _judge()._should_investigate_more(_evidence(0.92, 0.85, iteration=0)) is True


def test_no_early_exit_when_signals_ambiguous():
    # min=0.55 < 0.75 and max=0.92 > 0.25 → not conclusive either way, and
    # delta 0.37 is below the conflict threshold, so deep-scan keeps going.
    assert _judge()._should_investigate_more(_evidence(0.92, 0.55)) is True


def test_signal_conflict_still_triggers_investigation():
    # delta 0.55 > signal_conflict_delta (0.4) → genuine disagreement must
    # still force another pass; the early-exit gate must not swallow it.
    assert _judge()._should_investigate_more(_evidence(0.95, 0.40)) is True
