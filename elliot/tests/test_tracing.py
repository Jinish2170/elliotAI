"""Tracing roll-up + cache-key regression tests."""
import pytest

from elliot.config import settings
from elliot.core import tracing


@pytest.fixture(scope="module", autouse=True)
def _tracing():
    mp = pytest.MonkeyPatch()
    mp.setattr(settings, "TRACE_LOCAL", False)
    mp.delenv("PHOENIX_COLLECTOR_ENDPOINT", raising=False)
    assert tracing.init_tracing(service_name="test")
    yield
    mp.undo()


def test_summary_rolls_up_tokens_cache_retries_and_agents(monkeypatch):
    monkeypatch.setattr(settings, "NIM_PRICE_INPUT_PER_1M", 1.0)
    monkeypatch.setattr(settings, "NIM_PRICE_OUTPUT_PER_1M", 2.0)
    with tracing.span("audit") as root:
        with tracing.span("agent.vision"):
            with tracing.span("nim.analyze_image", **{"elliot.cache_hit": True}):
                pass
            with tracing.span("nim.analyze_image", **{"elliot.fallback_used": True}):
                with tracing.span("nim.call", **{"elliot.attempt": 1, "elliot.queue_wait_s": 0.5}):
                    with tracing.span("ChatCompletion", kind="LLM", **{
                        tracing.TOK_IN: 1000, tracing.TOK_OUT: 200, tracing.MODEL: "m1"}):
                        pass
                with tracing.span("nim.call", **{"elliot.attempt": 2}):
                    with tracing.span("ChatCompletion", kind="LLM", **{
                        tracing.TOK_IN: 1000, tracing.TOK_OUT: 300, tracing.MODEL: "m1"}):
                        pass
        tid = tracing.current_trace_id()
    s = tracing.get_summary(tid)
    assert s["llm_calls"] == 2
    assert (s["input_tokens"], s["output_tokens"], s["total_tokens"]) == (2000, 500, 2500)
    assert s["nim_requests"] == 2 and s["cache_hits"] == 1 and s["fallbacks"] == 1
    assert s["retries"] == 1 and s["queue_wait_seconds"] == 0.5
    assert s["models"] == {"m1": 2}
    assert "vision" in s["agents"] and "audit_seconds" in s
    assert s["est_cost_usd"] == pytest.approx(2000 / 1e6 * 1.0 + 500 / 1e6 * 2.0)


def test_error_span_counts_llm_error_and_reraises():
    with pytest.raises(TimeoutError):
        with tracing.span("audit"):
            tid = tracing.current_trace_id()
            with tracing.span("ChatCompletion", kind="LLM"):
                raise TimeoutError("slow")
    assert tracing.get_summary(tid)["llm_errors"] == 1


def test_traces_are_isolated_per_audit():
    with tracing.span("audit"):
        a = tracing.current_trace_id()
        with tracing.span("ChatCompletion", kind="LLM", **{tracing.TOK_IN: 5}):
            pass
    with tracing.span("audit"):
        b = tracing.current_trace_id()
    assert a != b
    assert tracing.get_summary(b)["input_tokens"] == 0


def test_cache_key_depends_on_model(tmp_path, monkeypatch):
    """Regression: the cache key used to omit the model, so switching models
    served the previous model's cached answers (A/B comparisons measured nothing)."""
    from elliot.core.nim_client import NIMClient

    img = tmp_path / "s.jpg"
    img.write_bytes(b"\xff\xd8fake")
    c = NIMClient()
    monkeypatch.setattr(settings, "NIM_VISION_MODEL", "model-a")
    k_a = c.get_cache_key(str(img), "p", pass_type=1)
    monkeypatch.setattr(settings, "NIM_VISION_MODEL", "model-b")
    k_b = c.get_cache_key(str(img), "p", pass_type=1)
    assert k_a != k_b
