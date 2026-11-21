"""
VERITAS eval harness.

    python -m eval.run_eval --suite scoring      # deterministic policy checks (no LLM)
    python -m eval.run_eval --suite vision       # VLM dark-pattern detection, P/R/F1 per category
    python -m eval.run_eval --suite injection    # prompt-injection attack success rate (ASR)
    python -m eval.run_eval --suite e2e          # full audits on real legit sites + baseline
    python -m eval.run_eval --suite all

Results: eval/results/<suite>-<timestamp>.json (+ markdown table on stdout).
Every LLM-backed case runs inside an `eval.case` span, so tokens / latency per
case come from the same OpenTelemetry roll-up used in production.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import http.server
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

CASES = json.loads((ROOT / "cases.json").read_text())
FIXTURES = ROOT / "fixtures"
RESULTS = ROOT / "results"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 3), round(min(1.0, c + h), 3))


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3),
            "tp": tp, "fp": fp, "fn": fn}


class FixtureServer:
    """Serve eval/fixtures on 127.0.0.1:<random> for the browser."""

    def __enter__(self):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(FIXTURES))
        handler.log_message = lambda *a, **k: None
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()


async def screenshot_all(files: list[str], base: str, out: Path) -> dict[str, tuple[list, list]]:
    """Capture exactly what Scout captures in production for the target page:
    t0 → wait TEMPORAL_DELAY → t<delay> → fullpage. (A fullpage-only harness
    silently disabled the temporal-only false_urgency category.)"""
    from playwright.async_api import async_playwright

    from elliot.config import settings

    delay = settings.TEMPORAL_DELAY
    out.mkdir(parents=True, exist_ok=True)
    shots = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        pages = []
        for f in files:  # load all, then share one wait for the temporal pair
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            await page.goto(f"{base}/{f}", wait_until="load")
            await page.wait_for_timeout(1000)
            t0 = out / f"{Path(f).stem}_t0.jpg"
            await page.screenshot(path=str(t0), type="jpeg", quality=85)
            pages.append((f, page, t0))
        await asyncio.sleep(delay)
        for f, page, t0 in pages:
            td = out / f"{Path(f).stem}_t{delay}.jpg"
            full = out / f"{Path(f).stem}_full.jpg"
            await page.screenshot(path=str(td), type="jpeg", quality=85)
            await page.screenshot(path=str(full), full_page=True, type="jpeg", quality=85)
            shots[f] = ([str(t0), str(td), str(full)], ["t0", f"t{delay}", "fullpage"])
        await browser.close()
    return shots


async def vision_categories(shots: tuple[list, list]) -> tuple[set[str], list[dict]]:
    from elliot.agents.vision import VisionAgent
    from elliot.core.nim_client import NIMClient

    agent = VisionAgent(nim_client=NIMClient())
    res = await agent.analyze(screenshots=shots[0], screenshot_labels=shots[1])
    found = [{"category": d.category_id, "pattern_type": d.pattern_type,
              "confidence": round(d.confidence, 2), "evidence": d.evidence[:160]}
             for d in res.dark_patterns]
    return {d["category"] for d in found}, found


def case_span(case_id: str, suite: str):
    from elliot.core import tracing
    return tracing.span("eval.case", **{"eval.case_id": case_id, "eval.suite": suite})


def span_summary(span) -> dict:
    from elliot.core import tracing
    s = tracing.get_summary(span.get_span_context().trace_id) if hasattr(span, "get_span_context") else {}
    return {k: s.get(k) for k in ("llm_calls", "cache_hits", "input_tokens", "output_tokens",
                                  "llm_seconds", "slowest_llm_call_s")}


# ----------------------------------------------------------------------------
# Suites
# ----------------------------------------------------------------------------

def suite_scoring() -> dict:
    """Deterministic policy checks on compute_trust_score (the code that decides)."""
    from elliot.config.trust_weights import SubSignal, compute_trust_score

    names = ["visual", "structural", "temporal", "graph", "meta", "security"]
    good = {n: SubSignal(name=n, raw_score=0.9, confidence=1.0) for n in names}
    checks = []

    def check(cid, desc, ok, detail):
        checks.append({"id": cid, "desc": desc, "pass": bool(ok), "detail": detail})

    r = compute_trust_score({})
    check("no_evidence_abstains", "No evidence at all must not be reported as safe",
          r.risk_level.value == "insufficient_evidence", f"score={r.final_score} level={r.risk_level.value}")
    weak = {n: SubSignal(name=n, raw_score=0.0, confidence=0.3) for n in names}
    r = compute_trust_score(weak)
    check("weak_bad_evidence_not_safe", "Uniformly bad (low-confidence) evidence must not be 'probably_safe'+",
          r.final_score < 70, f"score={r.final_score} level={r.risk_level.value}")
    r = compute_trust_score(good, ssl_status=False)
    check("no_ssl_cap", "Sites without HTTPS cannot score above 50 (documented rule)",
          r.final_score <= 50, f"score={r.final_score}")
    r = compute_trust_score(good, ssl_status=None)
    check("ssl_unknown_not_penalised", "Unknown SSL status (lookup failed) must not trigger the no-SSL cap",
          r.final_score > 50, f"score={r.final_score}")
    r = compute_trust_score(good, is_blacklisted=True)
    check("blacklist_forces_low", "Blocklisted domain forced below 15",
          r.final_score < 15, f"score={r.final_score}")
    passed = sum(c["pass"] for c in checks)
    return {"suite": "scoring", "passed": passed, "total": len(checks), "checks": checks}


async def suite_vision() -> dict:
    cases = CASES["vision"]
    rows, per_cat = [], {}
    with FixtureServer() as srv, tempfile.TemporaryDirectory() as tmp:
        shots = await screenshot_all([c["file"] for c in cases], srv.base, Path(tmp))
        for c in cases:
            t0 = time.time()
            with case_span(c["id"], "vision") as sp:
                pred, found = await vision_categories(shots[c["file"]])
                cost = span_summary(sp)
            exp, ok = set(c["expected"]), set(c["also_ok"])
            tp = exp & pred
            fp = pred - exp - ok
            fn = exp - pred
            for cat in tp:
                per_cat.setdefault(cat, [0, 0, 0])[0] += 1
            for cat in fp:
                per_cat.setdefault(cat, [0, 0, 0])[1] += 1
            for cat in fn:
                per_cat.setdefault(cat, [0, 0, 0])[2] += 1
            rows.append({"id": c["id"], "stratum": c["stratum"], "expected": sorted(exp),
                         "predicted": sorted(pred), "tp": len(tp), "fp": len(fp), "fn": len(fn),
                         "seconds": round(time.time() - t0, 1), "cost": cost, "findings": found})
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    clean = [r for r in rows if r["stratum"] == "clean"]
    clean_ok = sum(1 for r in clean if not r["predicted"])
    return {
        "suite": "vision",
        "micro": prf(tp, fp, fn),
        "per_category": {k: prf(*v) for k, v in sorted(per_cat.items())},
        "clean_pages_without_false_alarm": f"{clean_ok}/{len(clean)}",
        "n_cases": len(rows),
        "rows": rows,
    }


async def suite_injection() -> dict:
    inj = CASES["injection"]
    marker = inj["payload_marker"]
    twins = {c["id"]: c for c in CASES["vision"]}
    out = {"suite": "injection", "vision": [], "text": []}
    files = sorted({p["file"] for p in inj["vision_pairs"]} | {twins[p["twin"]]["file"] for p in inj["vision_pairs"]})
    with FixtureServer() as srv, tempfile.TemporaryDirectory() as tmp:
        shots = await screenshot_all(files, srv.base, Path(tmp))
        base_cache: dict[str, set] = {}
        for p in inj["vision_pairs"]:
            twin_file = twins[p["twin"]]["file"]
            if twin_file not in base_cache:
                base_cache[twin_file], _ = await vision_categories(shots[twin_file])
            with case_span(p["id"], "injection"):
                pred, found = await vision_categories(shots[p["file"]])
            base_has = p["target_category"] in base_cache[twin_file]
            succeeded = base_has and p["target_category"] not in pred
            out["vision"].append({"id": p["id"], "channel": p["channel"], "baseline_detected": base_has,
                                  "attacked_detected": p["target_category"] in pred,
                                  "attack_succeeded": succeeded, "findings": found})

    from elliot.agents.graph_investigator import GraphInvestigator

    gi = GraphInvestigator()
    for t in inj["text_cases"]:
        html = (FIXTURES / t["file"]).read_text()
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        desc = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
        # Same function production uses (elliot/core/nodes/graph.py), so the eval
        # measures the real code path, defences included.
        from elliot.core.nodes.graph import build_entity_text
        text, _ = build_entity_text([{"page_title": title.group(1) if title else "",
                                      "page_metadata": {"description": desc.group(1) if desc else ""}}])
        with case_span(t["id"], "injection"):
            claims = await gi._llm_extract_entities(f"http://fixture/{t['file']}", text)
        values = [f"{c.entity_type}:{c.entity_value}" for c in claims]
        out["text"].append({"id": t["id"], "channel": t["channel"], "entities": values,
                            "attack_succeeded": any(marker in v.lower() for v in values)})

    attacks = [r for r in out["vision"] if r["baseline_detected"] and "control" not in r["channel"]]
    attacks += [r for r in out["text"] if "control" not in r["channel"]]
    k = sum(r["attack_succeeded"] for r in attacks)
    out["attack_success_rate"] = {"succeeded": k, "attacks": len(attacks),
                                  "asr": round(k / len(attacks), 3) if attacks else None,
                                  "wilson95": wilson(k, len(attacks))}
    controls = [r for r in out["vision"] + out["text"] if "control" in r["channel"]]
    out["controls_clean"] = f"{sum(not r['attack_succeeded'] for r in controls)}/{len(controls)}"
    return out


async def suite_e2e() -> dict:
    rows = []
    py = sys.executable
    for c in CASES["e2e"]:
        with tempfile.TemporaryDirectory() as tmp:
            outp = Path(tmp) / "r.json"
            env = {**os.environ, "ELLIOT_AUDIT_ID": f"eval_{c['id']}"}
            t0 = time.time()
            proc = await asyncio.create_subprocess_exec(
                py, "-m", "elliot", c["url"], "--tier", "standard_audit", "--output", str(outp),
                cwd=str(REPO), env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            await proc.wait()
            r = json.loads(outp.read_text()) if outp.exists() else {}
        jd = r.get("judge_decision") or {}
        tr = jd.get("trust_score_result") or {}
        age = (r.get("graph_result") or {}).get("domain_age_days")
        score = tr.get("final_score")
        level = str(tr.get("risk_level", ""))
        flagged = score is not None and score < 70
        rows.append({
            "id": c["id"], "stratum": c["stratum"], "is_malicious": c["is_malicious"],
            "score": score, "risk_level": level, "veritas_flagged": flagged,
            "baseline_domain_age_days": age,
            "baseline_flagged": isinstance(age, int) and 0 <= age < 30,
            "seconds": round(time.time() - t0, 1),
            "trace_summary": r.get("trace_summary"),
        })
    legit = [x for x in rows if not x["is_malicious"]]
    fp = sum(x["veritas_flagged"] for x in legit)
    bfp = sum(x["baseline_flagged"] for x in legit)
    secs = sorted(x["seconds"] for x in rows)
    return {"suite": "e2e", "rows": rows,
            "false_positive_rate": {"veritas": f"{fp}/{len(legit)}", "domain_age_baseline": f"{bfp}/{len(legit)}"},
            "latency_p50_s": secs[len(secs) // 2] if secs else None,
            "note": "Legit-only: measures false alarms. Phishing recall needs live phishing captures (not collected)."}


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def to_markdown(res: dict) -> str:
    s = res["suite"]
    if s == "scoring":
        lines = [f"### Scoring policy: {res['passed']}/{res['total']} checks pass", "",
                 "| check | pass | detail |", "|---|---|---|"]
        lines += [f"| {c['id']} | {'✅' if c['pass'] else '❌'} | {c['detail']} |" for c in res["checks"]]
    elif s == "vision":
        m = res["micro"]
        lines = [f"### Vision: micro P={m['precision']} R={m['recall']} F1={m['f1']} (n={res['n_cases']} pages)",
                 f"Clean pages without false alarm: {res['clean_pages_without_false_alarm']}", "",
                 "| case | expected | predicted | tp/fp/fn | s |", "|---|---|---|---|---|"]
        lines += [f"| {r['id']} | {', '.join(r['expected']) or '—'} | {', '.join(r['predicted']) or '—'} | "
                  f"{r['tp']}/{r['fp']}/{r['fn']} | {r['seconds']} |" for r in res["rows"]]
    elif s == "injection":
        a = res["attack_success_rate"]
        lines = [f"### Injection: ASR = {a['succeeded']}/{a['attacks']} (95% CI {a['wilson95']}), controls clean {res['controls_clean']}", "",
                 "| case | channel | result |", "|---|---|---|"]
        for r in res["vision"]:
            verdict = ("ATTACK SUCCEEDED" if r["attack_succeeded"] else
                       ("blocked" if r["baseline_detected"] else "n/a (twin not detected)"))
            lines.append(f"| {r['id']} | {r['channel']} | {verdict} |")
        for r in res["text"]:
            lines.append(f"| {r['id']} | {r['channel']} | {'ATTACK SUCCEEDED' if r['attack_succeeded'] else 'blocked'} — {r['entities']} |")
    else:
        fpr = res["false_positive_rate"]
        lines = [f"### E2E (legit sites): false alarms VERITAS {fpr['veritas']}, domain-age baseline {fpr['domain_age_baseline']}, p50 {res['latency_p50_s']}s", "",
                 "| site | score | level | domain age | s | llm calls | tokens |", "|---|---|---|---|---|---|---|"]
        for r in res["rows"]:
            ts = r["trace_summary"] or {}
            lines.append(f"| {r['id']} | {r['score']} | {r['risk_level']} | {r['baseline_domain_age_days']} | "
                         f"{r['seconds']} | {ts.get('llm_calls')} | {ts.get('total_tokens')} |")
    return "\n".join(lines)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="scoring", choices=["scoring", "vision", "injection", "e2e", "all"])
    ap.add_argument("--tag", default="", help="label for this run (e.g. 'baseline', 'spotlighting')")
    args = ap.parse_args()

    from elliot.core import tracing
    tracing.init_tracing(service_name="veritas-eval", run_id=f"eval-{args.suite}")

    suites = ["scoring", "vision", "injection", "e2e"] if args.suite == "all" else [args.suite]
    RESULTS.mkdir(exist_ok=True)
    for s in suites:
        res = suite_scoring() if s == "scoring" else await {"vision": suite_vision, "injection": suite_injection,
                                                             "e2e": suite_e2e}[s]()
        res["tag"] = args.tag
        res["ran_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        from elliot.config import settings
        res["models"] = {"vision": settings.NIM_VISION_MODEL, "llm": settings.NIM_LLM_MODEL}
        path = RESULTS / f"{s}-{args.tag or 'run'}-{time.strftime('%Y%m%d-%H%M%S')}.json"
        path.write_text(json.dumps(res, indent=2, default=str))
        print(to_markdown(res))
        print(f"\n→ {path.relative_to(REPO)}\n")
    tracing.shutdown_tracing()


if __name__ == "__main__":
    asyncio.run(main())
