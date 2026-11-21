"""Regressions for policy bugs found by the scoring eval and code sweep (2026-11-21)."""
from types import SimpleNamespace

from elliot.agents import judge as J
from elliot.agents.graph_investigator import GraphResult
from elliot.config.trust_weights import RiskLevel, SubSignal, compute_trust_score


def _recs(level):
    agent = J.JudgeAgent.__new__(J.JudgeAgent)
    ev = SimpleNamespace(vision_result=None, graph_result=None, security_results={}, scout_results=[])
    return agent._generate_simple_recommendations(SimpleNamespace(risk_level=level), ev)


def test_judge_uses_trust_weights_risk_level():
    assert J.RiskLevel is RiskLevel  # was shadowed by judge_core.verdict.RiskLevel


def test_fraudulent_site_gets_warning_not_reassurance():
    recs = " ".join(_recs(RiskLevel.LIKELY_FRAUDULENT))
    assert "looks okay" not in recs and "credit card" in recs


def test_no_evidence_abstains_instead_of_probably_safe():
    r = compute_trust_score({})
    assert r.abstained and r.risk_level is RiskLevel.INSUFFICIENT_EVIDENCE
    assert "unverified" in " ".join(_recs(r.risk_level))


def test_strong_evidence_does_not_abstain():
    s = {n: SubSignal(name=n, raw_score=0.9, confidence=1.0)
         for n in ["visual", "structural", "temporal", "graph", "meta", "security"]}
    r = compute_trust_score(s)
    assert not r.abstained and r.risk_level is RiskLevel.TRUSTED


def test_force_below_means_strictly_below():
    r = compute_trust_score({}, is_blacklisted=True)
    assert r.final_score < 15 and not r.abstained  # hard stop beats abstention


def test_has_ssl_is_unknown_when_lookup_missing():
    assert GraphResult().has_ssl is None  # was False → no-SSL cap on HTTPS sites
    assert GraphResult(meta_analysis={"ssl": {"is_valid": True}}).has_ssl is True
    assert GraphResult(meta_analysis={"ssl": {"is_valid": False}}).has_ssl is False


def test_injection_attempt_caps_score_to_high_risk():
    s = {n: SubSignal(name=n, raw_score=0.95, confidence=1.0)
         for n in ["visual", "structural", "temporal", "graph", "meta", "security"]}
    r = compute_trust_score(s, injection_detected=True)
    assert r.final_score <= 39 and r.risk_level is RiskLevel.HIGH_RISK
