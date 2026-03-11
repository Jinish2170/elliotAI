"""
Veritas Independent Module Testing — Phase T8: Full Pipeline
=============================================================
Runs the complete audit orchestrator end-to-end via `python -m veritas`.
Uses standard_audit tier to test full integration.

Usage:
    python testing/scripts/test_t8_pipeline.py

Output:
    testing/results/T8_pipeline/T8.1_full_pipeline.md
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

RESULTS_DIR = ROOT / "testing" / "results" / "T8_pipeline"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DOMAIN = "avrut.com"
TARGET_URL = "https://avrut.com"


def write_report(test_id: str, module_name: str, duration: float, status: str,
                 input_desc: str, output_data: str, analysis: str, verdict: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    path = RESULTS_DIR / f"{test_id}.md"
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


async def test_t8_1_full_pipeline():
    test_id = "T8.1_full_pipeline"
    print(f"\n{'='*60}")
    print(f"Running {test_id}: Full Pipeline (standard_audit)")
    print(f"{'='*60}")

    start = time.time()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / "veritas" / ".env")

        from veritas.core.orchestrator import VeritasOrchestrator

        orchestrator = VeritasOrchestrator()

        result = await orchestrator.audit(
            url=TARGET_URL,
            tier="standard_audit",
            verdict_mode="expert",
        )

        duration = time.time() - start

        # result is a dict from the orchestrator
        output = json.dumps(result, indent=2, default=str) if isinstance(result, dict) else str(result)

        if isinstance(result, dict):
            trust_score = result.get('trust_score', result.get('final_score', '?'))
            risk_level = result.get('risk_level', '?')
            forensic = result.get('forensic_narrative', '')
            simple = result.get('simple_narrative', '')
            recs = result.get('recommendations', [])
            judge = result.get('judge_decision', {})
            if isinstance(judge, dict):
                trust_score = judge.get('final_score', trust_score)
                risk_level = judge.get('risk_level', risk_level)
                forensic = judge.get('forensic_narrative', forensic)

            # Agent details
            scout_pages = result.get('pages_investigated', '?')
            vision_score = result.get('visual_score', '?')
            graph_score = result.get('graph_score', '?')
            security_score = result.get('security_score', result.get('composite_security_score', '?'))

            analysis_lines = [
                f"- **Trust Score: {trust_score}**",
                f"- **Risk Level: {risk_level}**",
                f"- Scout pages: {scout_pages}",
                f"- Vision score: {vision_score}",
                f"- Graph score: {graph_score}",
                f"- Security score: {security_score}",
                f"- Recommendations: {len(recs) if isinstance(recs, list) else '?'}",
                "",
                "### Forensic Narrative (first 2000 chars):",
                str(forensic)[:2000],
                "",
                "### Simple Narrative (first 1000 chars):",
                str(simple)[:1000],
            ]
        else:
            analysis_lines = [f"- Raw result type: {type(result).__name__}"]

        status = "PASS"
        verdict = f"Full Pipeline: trust_score={trust_score if isinstance(result, dict) else '?'}, completed in {duration:.0f}s"

        write_report(test_id, "Full Pipeline (standard_audit)", duration, status,
                     f"URL: `{TARGET_URL}`\nTier: standard_audit\nVerdict mode: expert\nMethod: VeritasOrchestrator().audit()",
                     output[:25000], "\n".join(analysis_lines), verdict)
        return status

    except Exception as e:
        duration = time.time() - start
        write_report(test_id, "Full Pipeline (standard_audit)", duration, "ERROR",
                     f"URL: `{TARGET_URL}`\nTier: standard_audit",
                     traceback.format_exc(),
                     f"- Exception: {type(e).__name__}: {e}", f"FAILED: {e}")
        return "ERROR"


async def main():
    print("=" * 60)
    print("VERITAS — Phase T8: Full Pipeline")
    print(f"Target: {TARGET_DOMAIN}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    total_start = time.time()
    result = await test_t8_1_full_pipeline()
    total_duration = time.time() - total_start

    print(f"\n{'='*60}")
    print("PHASE T8 SUMMARY")
    print(f"{'='*60}")
    print(f"Total duration: {total_duration:.1f}s")
    icon = "✅" if result == "PASS" else ("⚠️" if result == "PARTIAL" else "❌")
    print(f"  {icon} T8.1: {result}")

    summary = RESULTS_DIR / "T8_SUMMARY.md"
    summary.write_text(f"""# Phase T8 — Full Pipeline Summary
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Target:** {TARGET_DOMAIN}
**Duration:** {total_duration:.1f}s
**Result:** {result}

| # | Module | Status |
|---|--------|--------|
| T8.1 | Full Pipeline (standard_audit) | {icon} {result} |
""", encoding="utf-8")
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    asyncio.run(main())
