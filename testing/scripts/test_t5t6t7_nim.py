"""
Veritas Independent Module Testing — Phases T5-T7: NIM-Powered Agents
======================================================================
Tests Vision (T5), Graph Investigator (T6), and Judge (T7) agents.
These use NIM API credits — the .env NVIDIA_NIM_API_KEY is required.

T5 uses screenshots from T2, T6 uses metadata from T2/T3,
T7 combines results from T5+T6 into AuditEvidence.

Usage:
    python testing/scripts/test_t5t6t7_nim.py

Output:
    testing/results/T5_vision/, T6_graph/, T7_judge/
"""

import asyncio
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "testing" / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
HTML_DIR = DATA_DIR / "html"
METADATA_DIR = DATA_DIR / "metadata"

T5_DIR = ROOT / "testing" / "results" / "T5_vision"
T6_DIR = ROOT / "testing" / "results" / "T6_graph"
T7_DIR = ROOT / "testing" / "results" / "T7_judge"
for d in [T5_DIR, T6_DIR, T7_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TARGET_DOMAIN = "avrut.com"
TARGET_URL = "https://avrut.com"
PER_TEST_TIMEOUT = 120


def write_report(results_dir: Path, test_id: str, module_name: str, duration: float,
                 status: str, input_desc: str, output_data: str, analysis: str, verdict: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    path = results_dir / f"{test_id}.md"
    content = f"""# Test {test_id} — {module_name}
**Date:** {now}
**Target:** {TARGET_DOMAIN}
**Duration:** {duration:.1f}s
**Status:** {status}

## Input
{input_desc}

## Output
```
{output_data}
```

## Analysis
{analysis}

## Verdict
{verdict}
"""
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ Report written: {path.name}")
    return path


def format_output(data) -> str:
    try:
        if hasattr(data, 'to_dict'):
            return json.dumps(data.to_dict(), indent=2, default=str)
        elif hasattr(data, '__dict__'):
            d = {}
            for k, v in data.__dict__.items():
                if k.startswith('_'):
                    continue
                try:
                    json.dumps(v, default=str)
                    d[k] = v
                except (TypeError, ValueError):
                    d[k] = str(v)
            return json.dumps(d, indent=2, default=str)
        elif isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)
        else:
            return str(data)
    except Exception:
        return str(data)


# Shared state — results from earlier phases feed into later ones
_vision_result = None
_graph_result = None


# ============================================================
# T5.1 — Vision Agent (5-Pass Pipeline)
# ============================================================
async def test_t5_1_vision():
    global _vision_result
    test_id = "T5.1_vision_5pass"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Vision Agent (5-Pass Pipeline)")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.agents.vision import VisionAgent

        # Gather T2 screenshots
        all_screenshots = sorted(SCREENSHOTS_DIR.glob("*.jpg")) + sorted(SCREENSHOTS_DIR.glob("*.png"))
        # Also include multi-page screenshots
        multi_dir = SCREENSHOTS_DIR / "multi_page"
        if multi_dir.exists():
            all_screenshots += sorted(multi_dir.glob("*.jpg")) + sorted(multi_dir.glob("*.png"))

        if not all_screenshots:
            raise FileNotFoundError("No screenshots found from T2. Run T2 first.")

        # Use up to 10 screenshots for a thorough test
        screenshots = [str(s) for s in all_screenshots[:10]]
        labels = [s.stem for s in all_screenshots[:10]]

        print(f"  Using {len(screenshots)} screenshots")
        for s in screenshots[:5]:
            print(f"    - {Path(s).name}")
        if len(screenshots) > 5:
            print(f"    ... and {len(screenshots) - 5} more")

        agent = VisionAgent()  # Will create NIMClient internally

        result = await agent.analyze(
            screenshots=screenshots,
            screenshot_labels=labels,
            url=TARGET_URL,
            use_5_pass_pipeline=True,
            max_passes=5,
        )

        _vision_result = result
        duration = time.time() - start
        output = format_output(result)

        patterns = getattr(result, 'dark_patterns', []) or []
        score = getattr(result, 'visual_score', None)
        analyzed = getattr(result, 'screenshots_analyzed', 0)
        nim_calls = getattr(result, 'nim_calls_made', 0)
        fallback = getattr(result, 'fallback_used', False)
        errors = getattr(result, 'errors', []) or []

        analysis_lines = [
            f"- Visual score: {score}",
            f"- Dark patterns found: {len(patterns)}",
            f"- Screenshots analyzed: {analyzed}/{len(screenshots)}",
            f"- NIM calls made: {nim_calls}",
            f"- Fallback used: {fallback}",
            f"- Errors: {len(errors)}",
            "",
            "### Dark Patterns Found:",
        ]
        for p in patterns[:20]:
            cat = getattr(p, 'category', '?')
            sev = getattr(p, 'severity', '?')
            desc = getattr(p, 'description', str(p))
            conf = getattr(p, 'confidence', '?')
            analysis_lines.append(f"  - [{sev}] {cat} (conf={conf}): {str(desc)[:200]}")

        if errors:
            analysis_lines.append("")
            analysis_lines.append("### Errors:")
            for e in errors[:10]:
                analysis_lines.append(f"  - {e}")

        status = "PASS" if not fallback else "PARTIAL"
        verdict = f"Vision 5-Pass: visual_score={score}, {len(patterns)} dark patterns, {nim_calls} NIM calls, {analyzed} screenshots"

        write_report(T5_DIR, test_id, "Vision Agent (5-Pass)", duration, status,
                     f"URL: `{TARGET_URL}`\nScreenshots: {len(screenshots)}\nPipeline: 5-pass, max_passes=5\nLabels: {labels[:5]}...",
                     output[:15000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(T5_DIR, test_id, "Vision Agent (5-Pass)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T6.1 — Graph Investigator
# ============================================================
async def test_t6_1_graph():
    global _graph_result
    test_id = "T6.1_graph"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Graph Investigator")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.agents.graph_investigator import GraphInvestigator

        # Load T2 metadata
        scout_path = METADATA_DIR / "avrut_scout_result.json"
        links_path = METADATA_DIR / "avrut_links.json"
        html_path = HTML_DIR / "avrut_landing.html"

        page_metadata = {}
        if scout_path.exists():
            page_metadata = json.loads(scout_path.read_text(encoding="utf-8"))
            print(f"  Loaded scout metadata: {len(page_metadata)} keys")

        external_links = []
        if links_path.exists():
            links_data = json.loads(links_path.read_text(encoding="utf-8"))
            external_links = [l.get('url', '') for l in links_data if l.get('url')]
            print(f"  Loaded {len(external_links)} links")

        page_html = None
        if html_path.exists():
            page_html = html_path.read_text(encoding="utf-8")
            print(f"  Loaded HTML: {len(page_html)} chars")

        investigator = GraphInvestigator()  # Will create NIMClient internally

        result = await investigator.investigate(
            url=TARGET_URL,
            page_metadata=page_metadata,
            page_text="",
            external_links=external_links[:20],
            page_html=page_html,
        )

        _graph_result = result
        duration = time.time() - start
        output = format_output(result)

        graph_score = getattr(result, 'graph_score', None)
        claims = getattr(result, 'claims_extracted', []) or []
        verifications = getattr(result, 'verifications', []) or []
        inconsistencies = getattr(result, 'inconsistencies', []) or []
        domain_intel = getattr(result, 'domain_intel', None)
        threat_level = getattr(result, 'threat_level', None)
        osint_consensus = getattr(result, 'osint_consensus', None)

        analysis_lines = [
            f"- Graph score: {graph_score}",
            f"- Claims extracted: {len(claims)}",
            f"- Verifications: {len(verifications)}",
            f"- Inconsistencies: {len(inconsistencies)}",
            f"- Threat level: {threat_level}",
            f"- OSINT consensus: {format_output(osint_consensus)[:500] if osint_consensus else 'N/A'}",
            "",
            "### Domain Intel:",
        ]
        if domain_intel:
            analysis_lines.append(f"  - {format_output(domain_intel)[:1000]}")

        analysis_lines.append("")
        analysis_lines.append("### Claims:")
        for c in claims[:15]:
            analysis_lines.append(f"  - {format_output(c)[:200]}")

        analysis_lines.append("")
        analysis_lines.append("### Inconsistencies:")
        for i in inconsistencies[:10]:
            analysis_lines.append(f"  - {format_output(i)[:200]}")

        status = "PASS"
        verdict = f"Graph: graph_score={graph_score}, {len(claims)} claims, {len(verifications)} verifications, {len(inconsistencies)} inconsistencies, threat={threat_level}"

        write_report(T6_DIR, test_id, "Graph Investigator", duration, status,
                     f"URL: `{TARGET_URL}`\nMetadata: {'Yes' if page_metadata else 'No'}\nLinks: {len(external_links)}\nHTML: {'Yes' if page_html else 'No'}",
                     output[:15000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(T6_DIR, test_id, "Graph Investigator", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# T7.1 — Judge Agent (Verdict)
# ============================================================
async def test_t7_1_judge():
    test_id = "T7.1_judge_verdict"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Judge Agent (Verdict)")
    print(f"{'='*60}")

    start = time.time()
    try:
        from veritas.agents.judge import JudgeAgent, AuditEvidence

        # Build AuditEvidence from previous phase results
        evidence_kwargs = {
            "url": TARGET_URL,
            "iteration": 1,
            "max_iterations": 1,
            "max_pages": 8,
            "pages_investigated": 8,
        }

        if _vision_result:
            evidence_kwargs["vision_result"] = _vision_result
            print("  Using Vision result from T5")

        if _graph_result:
            evidence_kwargs["graph_result"] = _graph_result
            print("  Using Graph result from T6")

        evidence = AuditEvidence(**evidence_kwargs)

        judge = JudgeAgent()  # Will create NIMClient internally

        result = await judge.analyze(
            evidence=evidence,
            use_dual_verdict=True,
        )

        duration = time.time() - start
        output = format_output(result)

        action = getattr(result, 'action', None)
        final_score = getattr(result, 'final_score', None)
        risk_level = getattr(result, 'risk_level', None)
        forensic = getattr(result, 'forensic_narrative', '')
        simple = getattr(result, 'simple_narrative', '')
        recs = getattr(result, 'recommendations', []) or []
        simple_recs = getattr(result, 'simple_recommendations', []) or []
        site_type = getattr(result, 'site_type', None)
        verdict_mode = getattr(result, 'verdict_mode', None)
        dual = getattr(result, 'dual_verdict', None)

        analysis_lines = [
            f"- Action: {action}",
            f"- **Final Trust Score: {final_score}/100**",
            f"- Risk Level: {risk_level}",
            f"- Site Type: {site_type}",
            f"- Verdict Mode: {verdict_mode}",
            f"- Recommendations: {len(recs)}",
            "",
            "### Forensic Narrative:",
            str(forensic)[:3000],
            "",
            "### Simple Narrative:",
            str(simple)[:2000],
            "",
            "### Recommendations:",
        ]
        for r in recs[:10]:
            analysis_lines.append(f"  - {str(r)[:200]}")

        if dual:
            analysis_lines.append("")
            analysis_lines.append("### Dual Verdict (V2):")
            analysis_lines.append(format_output(dual)[:3000])

        status = "PASS"
        verdict = f"Judge: trust_score={final_score}/100, risk={risk_level}, action={action}, {len(recs)} recommendations"

        write_report(T7_DIR, test_id, "Judge Agent (Verdict)", duration, status,
                     f"URL: `{TARGET_URL}`\nVision: {'✅' if _vision_result else '❌'}\nGraph: {'✅' if _graph_result else '❌'}\nDual verdict: True",
                     output[:20000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(T7_DIR, test_id, "Judge Agent (Verdict)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


# ============================================================
# Main Runner
# ============================================================
async def main():
    print("=" * 60)
    print("VERITAS — Phases T5-T7: NIM-Powered Agents")
    print(f"Target: {TARGET_DOMAIN}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check NIM key
    from dotenv import load_dotenv
    import os
    env_path = ROOT / "veritas" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    nim_key = os.environ.get("NVIDIA_NIM_API_KEY", "")
    if not nim_key:
        print("⚠️  WARNING: No NVIDIA_NIM_API_KEY found — NIM agents will fail!")
    else:
        print(f"  NIM API key: ...{nim_key[-8:]}")

    tests = [
        ("T5.1", "Vision 5-Pass", test_t5_1_vision, T5_DIR),
        ("T6.1", "Graph Investigator", test_t6_1_graph, T6_DIR),
        ("T7.1", "Judge Verdict", test_t7_1_judge, T7_DIR),
    ]

    results = {}
    total_start = time.time()

    for tid, name, func, rdir in tests:
        try:
            r = await asyncio.wait_for(func(), timeout=PER_TEST_TIMEOUT)
        except asyncio.TimeoutError:
            r = "TIMEOUT"
            write_report(rdir, f"{tid}_timeout", name, PER_TEST_TIMEOUT, "TIMEOUT",
                         f"URL: `{TARGET_URL}`", f"Test exceeded {PER_TEST_TIMEOUT}s timeout",
                         "- Test timed out", f"TIMEOUT after {PER_TEST_TIMEOUT}s")
        results[tid] = r
        print(f"  → {tid} {name}: {r}")

    total_duration = time.time() - total_start

    print(f"\n{'='*60}")
    print("PHASES T5-T7 SUMMARY")
    print(f"{'='*60}")
    print(f"Total duration: {total_duration:.1f}s")

    pass_count = sum(1 for v in results.values() if v in ("PASS", "PARTIAL"))
    fail_count = sum(1 for v in results.values() if v in ("FAIL", "ERROR", "TIMEOUT"))

    for tid, r in results.items():
        icon = "✅" if r == "PASS" else ("⚠️" if r == "PARTIAL" else "❌")
        print(f"  {icon} {tid}: {r}")

    print(f"\n  PASS: {pass_count} | FAIL/ERROR: {fail_count} | TOTAL: {len(results)}")

    # Write summaries for each phase
    for phase_name, rdir, phase_tests in [
        ("T5", T5_DIR, [("T5.1", "Vision 5-Pass")]),
        ("T6", T6_DIR, [("T6.1", "Graph Investigator")]),
        ("T7", T7_DIR, [("T7.1", "Judge Verdict")]),
    ]:
        summary = rdir / f"{phase_name}_SUMMARY.md"
        rows = "\n".join(f"| {tid} | {name} | {'✅' if results.get(tid) == 'PASS' else '❌'} {results.get(tid, 'N/A')} |"
                         for tid, name in phase_tests)
        summary.write_text(f"""# Phase {phase_name} Summary
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Target:** {TARGET_DOMAIN}
**Duration:** {total_duration:.1f}s

| # | Module | Status |
|---|--------|--------|
{rows}
""", encoding="utf-8")

    print(f"\nComplete! Total duration: {total_duration:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
