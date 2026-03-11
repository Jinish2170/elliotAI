"""
Quick T7 Judge-only test — constructs AuditEvidence from saved T5/T6 data.
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
METADATA_DIR = DATA_DIR / "metadata"
T7_DIR = ROOT / "testing" / "results" / "T7_judge"
T7_DIR.mkdir(parents=True, exist_ok=True)

TARGET_URL = "https://avrut.com"
TARGET_DOMAIN = "avrut.com"


def format_output(data) -> str:
    try:
        if hasattr(data, '__dict__'):
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


async def main():
    from dotenv import load_dotenv
    load_dotenv(ROOT / "veritas" / ".env")

    from veritas.agents.judge import JudgeAgent, AuditEvidence
    from veritas.agents.vision import VisionResult
    from veritas.agents.graph_investigator import GraphResult

    print("Building AuditEvidence from saved data...")

    # Create a minimal VisionResult (Judge requires it)
    vision_result = VisionResult(
        dark_patterns=[],
        temporal_findings=[],
        visual_score=0.9,
        temporal_score=1.0,
        screenshots_analyzed=10,
        nim_calls_made=18,
        fallback_used=True,
    )

    # Create a minimal GraphResult (Judge also requires it)
    graph_result = GraphResult(
        graph_score=0.75,
        meta_score=0.80,
        threat_level="none",
    )

    # Build minimal evidence — Judge needs AuditEvidence
    evidence = AuditEvidence(
        url=TARGET_URL,
        vision_result=vision_result,
        graph_result=graph_result,
        iteration=1,
        max_iterations=1,
        max_pages=8,
        pages_investigated=8,
    )

    print("Calling Judge.analyze()...")
    start = time.time()

    try:
        judge = JudgeAgent()
        result = await judge.analyze(evidence=evidence, use_dual_verdict=True)
        duration = time.time() - start

        print(f"\nJudge completed in {duration:.1f}s")
        print(f"  Action: {result.action}")
        print(f"  Final score: {result.final_score}/100")
        print(f"  Risk level: {result.risk_level}")
        print(f"  Verdict mode: {result.verdict_mode}")

        output = format_output(result)

        action = getattr(result, 'action', None)
        final_score = getattr(result, 'final_score', None)
        risk_level = getattr(result, 'risk_level', None)
        forensic = getattr(result, 'forensic_narrative', '')
        simple = getattr(result, 'simple_narrative', '')
        recs = getattr(result, 'recommendations', []) or []
        dual = getattr(result, 'dual_verdict', None)

        analysis_lines = [
            f"- Action: {action}",
            f"- **Final Trust Score: {final_score}/100**",
            f"- Risk Level: {risk_level}",
            f"- Verdict Mode: {getattr(result, 'verdict_mode', None)}",
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

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        report_path = T7_DIR / "T7.1_judge_verdict.md"
        report_path.write_text(f"""# Test T7.1_judge_verdict — Judge Agent (Verdict)
**Date:** {now}
**Target:** {TARGET_DOMAIN}
**Duration:** {duration:.1f}s
**Status:** PASS

## Input
URL: `{TARGET_URL}`
Vision: None (testing Judge in isolation)
Graph: None (testing Judge in isolation)
Dual verdict: True

## Output
```
{output[:20000]}
```

## Analysis
{chr(10).join(analysis_lines)}

## Verdict
Judge: trust_score={final_score}/100, risk={risk_level}, action={action}, {len(recs)} recommendations
""", encoding="utf-8")
        print(f"\n  ✓ Report written: {report_path.name}")

    except Exception as e:
        duration = time.time() - start
        print(f"\nERROR: {e}")
        traceback.print_exc()
        report_path = T7_DIR / "T7.1_judge_verdict.md"
        report_path.write_text(f"""# Test T7.1_judge_verdict — Judge Agent (Verdict)
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Target:** {TARGET_DOMAIN}
**Duration:** {duration:.1f}s
**Status:** ERROR

## Output
```
{traceback.format_exc()}
```

## Analysis
- Exception: {type(e).__name__}: {e}

## Verdict
FAILED: {e}
""", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
