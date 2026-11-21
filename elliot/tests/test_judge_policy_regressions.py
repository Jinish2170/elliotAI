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


def test_narrative_evidence_includes_tls_whois_dns_and_security():
    """Regression: the narrative claimed SSL/WHOIS were 'not provided' because the
    evidence text never contained them."""
    from elliot.config.trust_weights import compute_trust_score

    gr = GraphResult(meta_analysis={
        "ssl": {"is_valid": True, "issuer": "Let's Encrypt", "days_until_expiry": 62, "is_self_signed": False},
        "domain_age": {"registrar": "Spaceship, Inc.", "is_privacy_protected": False},
        "dns": {"has_spf": True, "has_dmarc": False, "mx_records": ["mx1"]},
    })
    ev = J.AuditEvidence.__new__(J.AuditEvidence)
    ev.url, ev.scout_results, ev.vision_result, ev.graph_result = "https://x.example", [], None, gr
    ev.security_results = {"security_headers": {"findings": [{"severity": "HIGH"}]}}
    agent = J.JudgeAgent.__new__(J.JudgeAgent)
    text = agent._build_evidence_summary_text(ev, compute_trust_score({}))
    for needle in ("TLS certificate valid: True", "Let's Encrypt", "WHOIS registrar: Spaceship",
                   "DMARC=False", "security_headers: 1 finding(s) (high)"):
        assert needle in text
