"""
Unit tests for Vision pass-priority gating (should_run_pass).

Pass 2 (dark-pattern detection) is the core forensic pass and must run on every
page regardless of whether Pass 1's quick scan found anything. Gating it made
clean-looking sites get a shallow first look, which forced the Judge to loop.
"""
from elliot.agents.vision import should_run_pass


def test_pass_1_always_runs():
    assert should_run_pass(1, prior_findings=[]) is True


def test_pass_2_runs_even_with_no_prior_findings():
    # The regression fix: dark-pattern detection must not be gated on Pass 1.
    assert should_run_pass(2, prior_findings=[]) is True
    assert should_run_pass(2, prior_findings=["finding"]) is True


def test_pass_3_runs_only_with_temporal_changes():
    assert should_run_pass(3, prior_findings=[], has_temporal_changes=False) is False
    assert should_run_pass(3, prior_findings=[], has_temporal_changes=True) is True


def test_pass_4_stays_conditional_on_prior_findings():
    # Cross-reference pass legitimately only adds value once there are findings.
    assert should_run_pass(4, prior_findings=[]) is False
    assert should_run_pass(4, prior_findings=["finding"]) is True


def test_pass_5_always_runs():
    assert should_run_pass(5, prior_findings=[]) is True
