"""
OpenTelemetry tracing for ELLIOT audits (OpenInference conventions, Phoenix-compatible).

One audit = one trace:

    audit (CHAIN)
    ├── agent.scout / agent.security / agent.vision / agent.graph / agent.judge (CHAIN)
    │   └── nim.analyze_image | nim.generate_text (CHAIN)   cache_hit, model, fallback
    │       └── nim.call (CHAIN)                            queue wait, attempt, timeout
    │           └── ChatCompletion (LLM, auto)              tokens, latency, messages

Exporters (all optional, never fatal):
  * Phoenix / any OTLP collector  — when PHOENIX_COLLECTOR_ENDPOINT is set
  * Local JSONL file per process  — ELLIOT_TRACE_LOCAL (default on), in ELLIOT_TRACE_DIR
  * In-memory summary             — always; powers `trace_summary` in the audit result

If the OpenTelemetry packages are missing, every helper degrades to a no-op.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

logger = logging.getLogger("elliot.tracing")

try:  # pragma: no cover - import guard
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor, TracerProvider
    from opentelemetry.sdk.trace.export import (BatchSpanProcessor, SimpleSpanProcessor,
                                                SpanExporter, SpanExportResult)
    from opentelemetry.trace import Status, StatusCode

    _OTEL = True
except ImportError:  # pragma: no cover
    _OTEL = False

# OpenInference attribute keys (kept as literals so this module has no hard
# dependency on openinference-semantic-conventions).
KIND = "openinference.span.kind"
TOK_IN = "llm.token_count.prompt"
TOK_OUT = "llm.token_count.completion"
MODEL = "llm.model_name"

_provider: Optional["TracerProvider"] = None
_summary: Optional["AuditSummaryProcessor"] = None
_lock = threading.Lock()


# ----------------------------------------------------------------------------
# Summary processor: per-trace cost / latency / token accounting
# ----------------------------------------------------------------------------

if _OTEL:

    class AuditSummaryProcessor(SpanProcessor):
        """Aggregates LLM + NIM spans per trace id into a compact summary dict."""

        def __init__(self) -> None:
            self._by_trace: dict[int, dict] = {}
            self._mu = threading.Lock()

        def _bucket(self, trace_id: int) -> dict:
            return self._by_trace.setdefault(trace_id, {
                "llm_calls": 0, "llm_errors": 0, "input_tokens": 0, "output_tokens": 0,
                "llm_seconds": 0.0, "nim_requests": 0, "cache_hits": 0, "fallbacks": 0,
                "retries": 0, "queue_wait_seconds": 0.0, "agents": {}, "models": {},
                "slowest_llm_call_s": 0.0,
            })

        def on_end(self, span: "ReadableSpan") -> None:
            attrs = span.attributes or {}
            dur = ((span.end_time or 0) - (span.start_time or 0)) / 1e9
            with self._mu:
                b = self._bucket(span.context.trace_id)
                if attrs.get(KIND) == "LLM":
                    b["llm_calls"] += 1
                    b["llm_seconds"] += dur
                    b["slowest_llm_call_s"] = max(b["slowest_llm_call_s"], dur)
                    b["input_tokens"] += int(attrs.get(TOK_IN, 0) or 0)
                    b["output_tokens"] += int(attrs.get(TOK_OUT, 0) or 0)
                    m = str(attrs.get(MODEL, "unknown"))
                    b["models"][m] = b["models"].get(m, 0) + 1
                    if span.status.status_code == StatusCode.ERROR:
                        b["llm_errors"] += 1
                elif span.name in ("nim.analyze_image", "nim.generate_text"):
                    b["nim_requests"] += 1
                    b["cache_hits"] += int(bool(attrs.get("elliot.cache_hit")))
                    b["fallbacks"] += int(bool(attrs.get("elliot.fallback_used")))
                elif span.name == "nim.call":
                    b["queue_wait_seconds"] += float(attrs.get("elliot.queue_wait_s", 0.0) or 0.0)
                    if int(attrs.get("elliot.attempt", 1) or 1) > 1:
                        b["retries"] += 1
                elif span.name.startswith("agent."):
                    agent = span.name.split(".", 1)[1]
                    b["agents"][agent] = round(b["agents"].get(agent, 0.0) + dur, 2)
                elif span.name == "audit":
                    b["audit_seconds"] = round(dur, 2)

        def summary(self, trace_id: int) -> dict:
            from elliot.config import settings  # local: avoid import cycle

            with self._mu:
                b = dict(self._bucket(trace_id))
            price_in = float(getattr(settings, "NIM_PRICE_INPUT_PER_1M", 0.0))
            price_out = float(getattr(settings, "NIM_PRICE_OUTPUT_PER_1M", 0.0))
            b["est_cost_usd"] = round(
                b["input_tokens"] / 1e6 * price_in + b["output_tokens"] / 1e6 * price_out, 6
            )
            b["total_tokens"] = b["input_tokens"] + b["output_tokens"]
            b["llm_seconds"] = round(b["llm_seconds"], 2)
            b["queue_wait_seconds"] = round(b["queue_wait_seconds"], 2)
            b["slowest_llm_call_s"] = round(b["slowest_llm_call_s"], 2)
            b["trace_id"] = format(trace_id, "032x")
            return b

        def shutdown(self) -> None:  # noqa: D401
            pass

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return True

    class JsonlSpanExporter(SpanExporter):
        """Writes one JSON object per finished span (offline debugging, eval replay)."""

        def __init__(self, path: Path) -> None:
            self._path = path
            path.parent.mkdir(parents=True, exist_ok=True)
            self._mu = threading.Lock()

        def export(self, spans) -> "SpanExportResult":
            try:
                with self._mu, self._path.open("a", encoding="utf-8") as f:
                    for s in spans:
                        f.write(json.dumps(json.loads(s.to_json())) + "\n")
                return SpanExportResult.SUCCESS
            except Exception as e:  # never break an audit over tracing
                logger.warning(f"JSONL trace export failed: {e}")
                return SpanExportResult.FAILURE

        def shutdown(self) -> None:
            pass


# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------

def init_tracing(service_name: str = "elliot-audit", run_id: str = "") -> bool:
    """Idempotently configure tracing. Returns True when tracing is active."""
    global _provider, _summary
    if not _OTEL:
        return False
    with _lock:
        if _provider is not None:
            return True
        from elliot.config import settings

        provider = TracerProvider(resource=Resource.create({
            "service.name": service_name,
            "openinference.project.name": os.getenv("PHOENIX_PROJECT_NAME", "elliotai"),
        }))
        _summary = AuditSummaryProcessor()
        provider.add_span_processor(_summary)

        endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "").rstrip("/")
        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
                    OTLPSpanExporter

                url = endpoint if endpoint.endswith("/v1/traces") else f"{endpoint}/v1/traces"
                # Phoenix Cloud / auth-enabled Phoenix: API key as a bearer header.
                key = os.getenv("PHOENIX_API_KEY", "")
                headers = {"authorization": f"Bearer {key}"} if key else None
                provider.add_span_processor(BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=url, headers=headers)))
                logger.info(f"Tracing → OTLP {url}")
            except Exception as e:
                logger.warning(f"OTLP exporter unavailable: {e}")

        if getattr(settings, "TRACE_LOCAL", True):
            name = f"{run_id or time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}.jsonl"
            path = Path(settings.TRACE_DIR) / name
            provider.add_span_processor(SimpleSpanProcessor(JsonlSpanExporter(path)))
            logger.info(f"Tracing → {path}")

        trace.set_tracer_provider(provider)
        _provider = provider

        try:  # auto-instrument the OpenAI client used for NIM
            from openinference.instrumentation import TraceConfig
            from openinference.instrumentation.openai import OpenAIInstrumentor

            OpenAIInstrumentor().instrument(
                tracer_provider=provider,
                # Screenshots are 0.5-2MB base64 each: never store them in traces.
                config=TraceConfig(hide_input_images=True),
            )
        except Exception as e:
            logger.warning(f"OpenAI auto-instrumentation unavailable: {e}")
        return True


def shutdown_tracing() -> None:
    """Flush exporters (call before process exit)."""
    if _provider is not None:
        try:
            _provider.force_flush()
            _provider.shutdown()
        except Exception as e:  # pragma: no cover
            logger.warning(f"Tracing shutdown failed: {e}")


def get_summary(trace_id: int) -> dict:
    return _summary.summary(trace_id) if _summary is not None else {}


# ----------------------------------------------------------------------------
# Span helpers
# ----------------------------------------------------------------------------

class _NoSpan:
    def set_attribute(self, *_a, **_k): pass
    def set_attributes(self, *_a, **_k): pass
    def add_event(self, *_a, **_k): pass
    def record_exception(self, *_a, **_k): pass
    def set_status(self, *_a, **_k): pass

    @property
    def trace_id(self) -> int:
        return 0


def _clean(attrs: dict) -> dict:
    out = {}
    for k, v in attrs.items():
        if v is None:
            continue
        out[k] = v if isinstance(v, (str, bool, int, float)) else str(v)
    return out


@contextmanager
def span(name: str, kind: str = "CHAIN", **attrs: Any) -> Iterator[Any]:
    """Start a span as the current span; records exceptions and re-raises."""
    if not _OTEL:
        yield _NoSpan()
        return
    tracer = trace.get_tracer("elliot")
    with tracer.start_as_current_span(name, record_exception=False,
                                      set_status_on_exception=False) as s:
        s.set_attribute(KIND, kind)
        s.set_attributes(_clean(attrs))
        try:
            yield s
        except BaseException as e:
            s.record_exception(e)
            s.set_status(Status(StatusCode.ERROR, f"{type(e).__name__}: {e}"[:300]))
            raise


def current_trace_id() -> int:
    if not _OTEL:
        return 0
    return trace.get_current_span().get_span_context().trace_id
